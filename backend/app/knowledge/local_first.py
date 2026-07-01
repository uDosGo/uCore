"""Local-first AppFlowy SQLite integration helpers.

This module intentionally avoids cloud dependencies and operates only on local
SQLite databases discovered on disk.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SPOOL_PATH = Path(
    os.getenv("UCORE_SNACKS_REPLIES", "~/.local/share/snackmachine/replies.jsonl"),
).expanduser()
BACKUP_DIR = Path(os.getenv("UCORE_APPFLOWY_BACKUPS", "~/.ucore/backups/appflowy")).expanduser()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@contextmanager
def _spool_lock_file():
    lock_path = SPOOL_PATH.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as f:
        try:
            import fcntl  # POSIX only

            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            yield
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            # Best-effort fallback if fcntl is unavailable.
            yield


def spool_event(event: dict[str, Any]) -> None:
    SPOOL_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": _utc_now(), **event}
    with _spool_lock_file(), SPOOL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def discover_databases() -> dict[str, str]:
    """Discover known local AppFlowy sqlite locations.

    Supports both explicit local-first path and desktop app support paths.
    """
    found: dict[str, str] = {}

    # Local-first path mentioned in integration checklist.
    candidate_db = Path.home() / "AppFlowy/data/database.sqlite"
    candidate_chat = Path.home() / "AppFlowy/data/chat.sqlite"
    if candidate_db.exists():
        found["database"] = str(candidate_db)
    if candidate_chat.exists():
        found["chat"] = str(candidate_chat)

    # Desktop AppFlowy flutter path fallback.
    base = Path.home() / "Library/Application Support/com.appflowy.appflowy.flutter"
    cloud_dir = base / "data_beta.appflowy.cloud"
    local_dir = base / "data"

    if cloud_dir.exists():
        for sub in sorted(cloud_dir.iterdir()):
            db = sub / "flowy-database.db"
            if db.exists() and "database" not in found:
                found["database"] = str(db)
            vec = sub / "vector.db"
            if vec.exists() and "vector" not in found:
                found["vector"] = str(vec)

    if local_dir.exists():
        for sub in sorted(local_dir.iterdir()):
            db = sub / "flowy-database.db"
            if db.exists() and "database" not in found:
                found["database"] = str(db)

    return found


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(db_path: str) -> list[str]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        ).fetchall()
        return [r["name"] for r in rows]


def _is_safe_read_sql(sql: str) -> bool:
    s = sql.strip().lower()
    return s.startswith("select") or s.startswith("pragma") or s.startswith("with")


def _is_safe_write_sql(sql: str) -> bool:
    s = sql.strip().lower()
    return s.startswith("insert") or s.startswith("update") or s.startswith("delete")


def _backup_db(db_path: str) -> str:
    src = Path(db_path)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dst = BACKUP_DIR / f"{src.stem}-{stamp}{src.suffix}"
    shutil.copy2(src, dst)
    return str(dst)


def run_query(db_path: str, sql: str, params: list[Any] | None = None, write: bool = False) -> dict[str, Any]:
    params = params or []

    if write:
        if not _is_safe_write_sql(sql):
            raise ValueError("Only INSERT/UPDATE/DELETE statements are allowed in write mode")
    elif not _is_safe_read_sql(sql):
        raise ValueError("Only SELECT/PRAGMA/WITH statements are allowed in read mode")

    backup_file = None
    with _connect(db_path) as conn:
        if write:
            backup_file = _backup_db(db_path)
            cur = conn.execute(sql, params)
            conn.commit()
            rowcount = cur.rowcount
            result = {"write": True, "rowcount": rowcount, "backup": backup_file}
        else:
            cur = conn.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            result = {"write": False, "rows": rows, "count": len(rows)}

    spool_event(
        {
            "type": "appflowy_sqlite_query",
            "status": "success",
            "db_path": db_path,
            "write": write,
            "sql": re.sub(r"\s+", " ", sql).strip()[:500],
            "params": params,
            "result_count": result.get("count", result.get("rowcount", 0)),
            "backup": backup_file,
        },
    )
    return result


def export_to_vault(vault_dir: str = "~/vault/@appflowy", limit_per_table: int = 2000) -> dict[str, Any]:
    dbs = discover_databases()
    out_base = Path(vault_dir).expanduser()
    out_base.mkdir(parents=True, exist_ok=True)

    exported: list[dict[str, Any]] = []

    for key, db_path in dbs.items():
        db_out = out_base / key
        db_out.mkdir(parents=True, exist_ok=True)

        try:
            tables = list_tables(db_path)
        except Exception as exc:
            exported.append({"database": key, "error": str(exc)})
            continue

        with _connect(db_path) as conn:
            for table in tables:
                rows = conn.execute(f'SELECT * FROM "{table}" LIMIT ?', (limit_per_table,)).fetchall()
                out_file = db_out / f"{table}.jsonl"
                with out_file.open("w", encoding="utf-8") as f:
                    for row in rows:
                        f.write(json.dumps(dict(row), ensure_ascii=True) + "\n")
                exported.append(
                    {
                        "database": key,
                        "table": table,
                        "rows": len(rows),
                        "file": str(out_file),
                    },
                )

    spool_event(
        {
            "type": "appflowy_export",
            "status": "success",
            "vault_dir": str(out_base),
            "count": len(exported),
        },
    )

    return {"vault_dir": str(out_base), "exports": exported, "count": len(exported)}
