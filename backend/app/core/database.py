"""uCore database — SQLite persistence layer.

Provides connection management, schema migrations, and CRUD helpers
for surfaces, snacks, and containers.

Usage:
    from app.core.database import get_db, migrate_db

    with get_db() as db:
        db.execute("SELECT * FROM surfaces")
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .settings import settings

# ─── Connection Management ───────────────────────────────────────

_local = threading.local()
_db_path: Path | None = None


def get_db_path() -> Path:
    """Get the database file path, ensuring directory exists."""
    global _db_path
    if _db_path is None:
        _db_path = settings.data_dir / "ucore.db"
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    return _db_path


@contextmanager
def get_db() -> sqlite3.Connection:
    """Get a database connection (one per thread, context manager)."""
    path = str(get_db_path())
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_conn() -> sqlite3.Connection:
    """Get a persistent connection for the current thread.

    Use this for long-lived operations. For short ops, prefer get_db().
    """
    if not hasattr(_local, "conn") or _local.conn is None:
        path = str(get_db_path())
        _local.conn = sqlite3.connect(path, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def close_conn() -> None:
    """Close the thread-local connection if open."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None


# ─── Schema ──────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS surfaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'prose',
    state TEXT NOT NULL DEFAULT 'created',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    parent_id TEXT,
    position INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snacks (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL DEFAULT 'message',
    priority INTEGER NOT NULL DEFAULT 2,
    status TEXT NOT NULL DEFAULT 'queued',
    content_json TEXT NOT NULL DEFAULT '{}',
    source TEXT NOT NULL DEFAULT 'system',
    target TEXT,
    timestamp TEXT NOT NULL,
    delivered_at TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    timeout_seconds INTEGER
);

CREATE TABLE IF NOT EXISTS containers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    runtime TEXT NOT NULL DEFAULT 'python',
    status TEXT NOT NULL DEFAULT 'created',
    image TEXT,
    dependencies_json TEXT NOT NULL DEFAULT '[]',
    env_vars_json TEXT NOT NULL DEFAULT '{}',
    ports_json TEXT NOT NULL DEFAULT '{}',
    volumes_json TEXT NOT NULL DEFAULT '[]',
    command TEXT,
    logs_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    stopped_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_surfaces_type ON surfaces(type);
CREATE INDEX IF NOT EXISTS idx_surfaces_state ON surfaces(state);
CREATE INDEX IF NOT EXISTS idx_snacks_status ON snacks(status);
CREATE INDEX IF NOT EXISTS idx_snacks_priority ON snacks(priority);
CREATE INDEX IF NOT EXISTS idx_containers_status ON containers(status);
CREATE INDEX IF NOT EXISTS idx_containers_runtime ON containers(runtime);
"""


def migrate_db() -> dict:
    """Apply schema migrations. Returns migration info."""
    path = str(get_db_path())
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        # Create schema_version table if needed
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # Get current version
        cursor = conn.execute("SELECT MAX(version) as v FROM schema_version")
        row = cursor.fetchone()
        current_version = row["v"] if row and row["v"] else 0

        applied = []
        if current_version < 1:
            # Apply initial schema
            conn.executescript(SCHEMA_SQL)
            conn.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (1)")
            applied.append("v1: initial schema")
            current_version = 1

        conn.commit()
        return {
            "status": "ok",
            "database": str(path),
            "version": current_version,
            "applied": applied,
        }
    finally:
        conn.close()


# ─── Serialization Helpers ───────────────────────────────────────

def now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(UTC).isoformat()


def to_json(obj: Any) -> str:
    """Serialize to JSON string."""
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, default=str)


def from_json(s: str) -> Any:
    """Deserialize from JSON string."""
    if not s:
        return {} if s is None else s
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s


# ─── Row-to-Model Helpers ────────────────────────────────────────

def surface_from_row(row: sqlite3.Row) -> dict:
    """Convert a surfaces table row to a dict suitable for model construction."""
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "state": row["state"],
        "metadata": from_json(row["metadata_json"]),
        "parent_id": row["parent_id"],
        "position": row["position"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def snack_from_row(row: sqlite3.Row) -> dict:
    """Convert a snacks table row to a dict suitable for model construction."""
    return {
        "id": row["id"],
        "type": row["type"],
        "priority": row["priority"],
        "status": row["status"],
        "content": from_json(row["content_json"]),
        "source": row["source"],
        "target": row["target"],
        "timestamp": row["timestamp"],
        "delivered_at": row["delivered_at"],
        "retry_count": row["retry_count"],
        "max_retries": row["max_retries"],
        "timeout_seconds": row["timeout_seconds"],
    }


def container_from_row(row: sqlite3.Row) -> dict:
    """Convert a containers table row to a dict suitable for model construction."""
    return {
        "id": row["id"],
        "name": row["name"],
        "runtime": row["runtime"],
        "status": row["status"],
        "image": row["image"],
        "dependencies": from_json(row["dependencies_json"]),
        "env_vars": from_json(row["env_vars_json"]),
        "ports": from_json(row["ports_json"]),
        "volumes": from_json(row["volumes_json"]),
        "command": row["command"],
        "logs": from_json(row["logs_json"]),
        "metadata": from_json(row["metadata_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "started_at": row["started_at"],
        "stopped_at": row["stopped_at"],
    }
