from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.settings import settings


def default_cache_path() -> Path:
    return settings.data_dir / "chat_cache.db"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatCache:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_cache_path()
        self._ensure_schema()
        self._stats = {
            "requests": 0,
            "hits": 0,
            "misses": 0,
            "writes": 0,
        }

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_cache (
                    key TEXT PRIMARY KEY,
                    prompt_hash TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    hit_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_cache_prompt_model
                ON chat_cache(prompt_hash, model)
                """
            )
            conn.commit()

    def make_key(
        self,
        *,
        provider: str,
        model: str,
        messages: list[dict[str, Any]],
    ) -> tuple[str, str]:
        payload = json.dumps(
            {
                "provider": provider,
                "model": model,
                "messages": messages,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        prompt_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"{provider}:{model}:{prompt_hash}", prompt_hash

    def get(
        self,
        *,
        provider: str,
        model: str,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        self._stats["requests"] += 1
        cache_key, _prompt_hash = self.make_key(
            provider=provider,
            model=model,
            messages=messages,
        )
        with self._connect() as conn:
            row = conn.execute(
                "SELECT response_json FROM chat_cache WHERE key = ?",
                (cache_key,),
            ).fetchone()
            if row is None:
                self._stats["misses"] += 1
                return None
            conn.execute(
                """
                UPDATE chat_cache
                SET accessed_at = ?, hit_count = hit_count + 1
                WHERE key = ?
                """,
                (_utc_now(), cache_key),
            )
            conn.commit()

        self._stats["hits"] += 1

        response = json.loads(row["response_json"])
        response["cache"] = {"hit": True}
        return response

    def set(
        self,
        *,
        provider: str,
        model: str,
        messages: list[dict[str, Any]],
        response: dict[str, Any],
    ) -> None:
        cache_key, prompt_hash = self.make_key(
            provider=provider,
            model=model,
            messages=messages,
        )
        now = _utc_now()
        payload = dict(response)
        payload.pop("cache", None)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_cache(
                    key,
                    prompt_hash,
                    provider,
                    model,
                    response_json,
                    created_at,
                    accessed_at,
                    hit_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    response_json = excluded.response_json,
                    accessed_at = excluded.accessed_at,
                    hit_count = chat_cache.hit_count
                """,
                (
                    cache_key,
                    prompt_hash,
                    provider,
                    model,
                    json.dumps(payload, ensure_ascii=True, sort_keys=True),
                    now,
                    now,
                    0,
                ),
            )
            conn.commit()
        self._stats["writes"] += 1

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS entries,
                    COALESCE(SUM(hit_count), 0) AS total_hits,
                    MAX(accessed_at) AS last_accessed_at
                FROM chat_cache
                """
            ).fetchone()

        requests = int(self._stats["requests"])
        hits = int(self._stats["hits"])
        misses = int(self._stats["misses"])
        hit_ratio = round(hits / requests, 3) if requests > 0 else 0.0

        return {
            "entries": int(row["entries"] if row is not None else 0),
            "requests": requests,
            "hits": hits,
            "misses": misses,
            "writes": int(self._stats["writes"]),
            "hit_ratio": hit_ratio,
            "persisted_hits": int(
                row["total_hits"] if row is not None else 0
            ),
            "last_accessed_at": (
                row["last_accessed_at"] if row is not None else None
            ),
        }
