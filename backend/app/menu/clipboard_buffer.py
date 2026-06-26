"""Mac-friendly clipboard buffer backed by JSONL spool + SQLite index.

Local-first storage:
- JSONL append log: ~/Library/Application Support/Snackbar/clipboard.jsonl
- SQLite index:     ~/Library/Application Support/Snackbar/clipboard.db

This module avoids cloud dependencies and is safe to use from API handlers and
system snack integrations.
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(
    os.getenv("UCORE_CLIPBOARD_DIR", "~/Library/Application Support/Snackbar"),
).expanduser()
JSONL_PATH = BASE_DIR / "clipboard.jsonl"
SQLITE_PATH = BASE_DIR / "clipboard.db"
IMAGES_DIR = BASE_DIR / "images"

DEFAULT_MAX_ITEMS = int(os.getenv("UCORE_CLIPBOARD_MAX_ITEMS", "500"))
DEFAULT_MAX_DAYS = int(os.getenv("UCORE_CLIPBOARD_MAX_DAYS", "30"))


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _new_id() -> str:
    return f"clip_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _ensure_storage() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clipboard_items (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT,
                metadata_json TEXT,
                pinned INTEGER NOT NULL DEFAULT 0,
                deleted INTEGER NOT NULL DEFAULT 0
            )
            """,
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_clip_timestamp ON clipboard_items(timestamp DESC)",
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_clip_pinned ON clipboard_items(pinned, deleted)",
        )


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _append_jsonl(event: dict[str, Any]) -> None:
    _ensure_storage()
    with JSONL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=True) + "\n")


def _row_to_item(row: sqlite3.Row) -> dict[str, Any]:
    metadata_json = row["metadata_json"] or "{}"
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError:
        metadata = {}
    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "source": row["source"],
        "type": row["type"],
        "content": row["content"],
        "metadata": metadata,
        "pinned": bool(row["pinned"]),
    }


def add_clipboard_item(
    *,
    source: str,
    type: str,
    content: str,
    metadata: dict[str, Any] | None = None,
    pinned: bool = False,
    item_id: str | None = None,
) -> dict[str, Any]:
    _ensure_storage()
    item_id = item_id or _new_id()
    item = {
        "id": item_id,
        "timestamp": _utc_now(),
        "source": source,
        "type": type,
        "content": content,
        "metadata": metadata or {},
        "pinned": bool(pinned),
    }

    with _db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO clipboard_items
            (id, timestamp, source, type, content, metadata_json, pinned, deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                item["id"],
                item["timestamp"],
                item["source"],
                item["type"],
                item["content"],
                json.dumps(item["metadata"], ensure_ascii=True),
                1 if item["pinned"] else 0,
            ),
        )
        conn.commit()

    _append_jsonl({"event": "upsert", **item})
    return item


def get_recent_items(limit: int = 50, include_pinned: bool = True) -> list[dict[str, Any]]:
    _ensure_storage()
    clause = "deleted = 0"
    if not include_pinned:
        clause += " AND pinned = 0"

    with _db() as conn:
        rows = conn.execute(
            f"""
            SELECT id, timestamp, source, type, content, metadata_json, pinned
            FROM clipboard_items
            WHERE {clause}
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (max(1, int(limit)),),
        ).fetchall()
    return [_row_to_item(r) for r in rows]


def get_item_by_id(item_id: str) -> dict[str, Any] | None:
    _ensure_storage()
    with _db() as conn:
        row = conn.execute(
            """
            SELECT id, timestamp, source, type, content, metadata_json, pinned
            FROM clipboard_items
            WHERE id = ? AND deleted = 0
            """,
            (item_id,),
        ).fetchone()
    return _row_to_item(row) if row is not None else None


def search_items(query: str, limit: int = 50) -> list[dict[str, Any]]:
    _ensure_storage()
    q = f"%{query.lower()}%"
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT id, timestamp, source, type, content, metadata_json, pinned
            FROM clipboard_items
            WHERE deleted = 0
              AND (
                lower(content) LIKE ?
                OR lower(source) LIKE ?
                OR lower(type) LIKE ?
                OR lower(metadata_json) LIKE ?
              )
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (q, q, q, q, max(1, int(limit))),
        ).fetchall()
    return [_row_to_item(r) for r in rows]


def pin_item(item_id: str, pinned: bool = True) -> bool:
    _ensure_storage()
    with _db() as conn:
        cur = conn.execute(
            "UPDATE clipboard_items SET pinned = ? WHERE id = ? AND deleted = 0",
            (1 if pinned else 0, item_id),
        )
        conn.commit()
        ok = cur.rowcount > 0
    if ok:
        _append_jsonl({"event": "pin", "id": item_id, "pinned": bool(pinned), "timestamp": _utc_now()})
    return ok


def delete_item(item_id: str) -> bool:
    _ensure_storage()
    with _db() as conn:
        cur = conn.execute(
            "UPDATE clipboard_items SET deleted = 1 WHERE id = ? AND deleted = 0",
            (item_id,),
        )
        conn.commit()
        ok = cur.rowcount > 0
    if ok:
        _append_jsonl({"event": "delete", "id": item_id, "timestamp": _utc_now()})
    return ok


def cleanup_history(max_items: int = DEFAULT_MAX_ITEMS, max_days: int = DEFAULT_MAX_DAYS) -> dict[str, int]:
    _ensure_storage()
    removed_age = 0
    removed_overflow = 0

    with _db() as conn:
        # Age cleanup for non-pinned items.
        if max_days > 0:
            cutoff = datetime.now(UTC).timestamp() - (max_days * 86400)
            cutoff_iso = datetime.fromtimestamp(cutoff, tz=UTC).isoformat()
            cur = conn.execute(
                """
                UPDATE clipboard_items
                SET deleted = 1
                WHERE deleted = 0 AND pinned = 0 AND timestamp < ?
                """,
                (cutoff_iso,),
            )
            removed_age = max(0, cur.rowcount)

        # Keep only newest max_items for non-pinned active entries.
        if max_items > 0:
            rows = conn.execute(
                """
                SELECT id FROM clipboard_items
                WHERE deleted = 0 AND pinned = 0
                ORDER BY timestamp DESC
                """,
            ).fetchall()
            ids = [r["id"] for r in rows]
            if len(ids) > max_items:
                to_delete = ids[max_items:]
                conn.executemany(
                    "UPDATE clipboard_items SET deleted = 1 WHERE id = ?",
                    [(i,) for i in to_delete],
                )
                removed_overflow = len(to_delete)

        conn.commit()

    _append_jsonl(
        {
            "event": "cleanup",
            "timestamp": _utc_now(),
            "removed_age": removed_age,
            "removed_overflow": removed_overflow,
            "max_items": max_items,
            "max_days": max_days,
        },
    )
    return {"removed_age": removed_age, "removed_overflow": removed_overflow}


def clear_history(include_pinned: bool = False) -> int:
    """Soft-delete clipboard items.

    By default this clears only non-pinned history and keeps saved items.
    """
    _ensure_storage()
    with _db() as conn:
        if include_pinned:
            cur = conn.execute("UPDATE clipboard_items SET deleted = 1 WHERE deleted = 0")
        else:
            cur = conn.execute(
                "UPDATE clipboard_items SET deleted = 1 WHERE deleted = 0 AND pinned = 0",
            )
        conn.commit()
        count = max(0, cur.rowcount)

    _append_jsonl(
        {
            "event": "clear",
            "timestamp": _utc_now(),
            "include_pinned": include_pinned,
            "count": count,
        },
    )
    return count


def read_clipboard_text() -> str:
    proc = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "pbpaste failed")
    return proc.stdout


def copy_text_to_clipboard(text: str) -> None:
    proc = subprocess.run(["pbcopy"], input=text, text=True, capture_output=True, timeout=2)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "pbcopy failed")


def capture_current_clipboard(source: str = "user_copy", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    text = read_clipboard_text().strip("\n")
    if not text:
        raise ValueError("Clipboard is empty or contains non-text content")
    return add_clipboard_item(source=source, type="text", content=text, metadata=metadata or {})
