"""AppFlowy DB Triggers — SQLite triggers for sync tracking.

Installs triggers on the AppFlowy collab_snapshot table that log
changes into a ucore_sync_log table. This enables the sync engine
to detect which documents were created/updated/deleted by the
AppFlowy app and propagate changes back to file-system vaults.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from typing import Any

from app.knowledge.appflowy import _find_database

log = logging.getLogger("ucore.af_triggers")

SYNC_LOG_TABLE = "ucore_sync_log"

TRIGGER_SQL = """
CREATE TABLE IF NOT EXISTS ucore_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL,
    action TEXT NOT NULL,
    title TEXT,
    collab_type TEXT,
    timestamp TEXT NOT NULL,
    processed INTEGER DEFAULT 0,
    processed_at TEXT,
    sync_source TEXT DEFAULT 'appflowy'
);

CREATE INDEX IF NOT EXISTS idx_sync_log_unprocessed
    ON ucore_sync_log(processed, timestamp);

CREATE TRIGGER IF NOT EXISTS ucore_trg_collab_insert
AFTER INSERT ON collab_snapshot
FOR EACH ROW
BEGIN
    INSERT INTO ucore_sync_log
        (object_id, action, title, collab_type, timestamp)
    VALUES
        (NEW.object_id, 'created', NEW.title, NEW.collab_type,
         datetime('now'));
END;

CREATE TRIGGER IF NOT EXISTS ucore_trg_collab_update
AFTER UPDATE ON collab_snapshot
FOR EACH ROW
WHEN NEW.title IS NOT OLD.title
   OR NEW.data IS NOT OLD.data
   OR NEW.desc IS NOT OLD.desc
BEGIN
    INSERT INTO ucore_sync_log
        (object_id, action, title, collab_type, timestamp)
    VALUES
        (NEW.object_id, 'updated', NEW.title, NEW.collab_type,
         datetime('now'));
END;

CREATE TRIGGER IF NOT EXISTS ucore_trg_collab_delete
AFTER DELETE ON collab_snapshot
FOR EACH ROW
BEGIN
    INSERT INTO ucore_sync_log
        (object_id, action, title, collab_type, timestamp)
    VALUES
        (OLD.object_id, 'deleted', OLD.title, OLD.collab_type,
         datetime('now'));
END;
"""

DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS ucore_trg_collab_insert;
DROP TRIGGER IF EXISTS ucore_trg_collab_update;
DROP TRIGGER IF EXISTS ucore_trg_collab_delete;
"""


def install_triggers(db_path: str | None = None) -> dict[str, Any]:
    """Install sync tracking triggers on the AppFlowy database."""
    if db_path is None:
        path = _find_database()
        if path is None:
            return {"status": "error", "message": "No AppFlowy database found"}
        db_path = str(path)

    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(TRIGGER_SQL)
        conn.commit()
        cur = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='trigger' AND name LIKE 'ucore_trg_%'",
        )
        triggers = [row[0] for row in cur.fetchall()]
        conn.close()
        log.info("Installed %d sync triggers on %s", len(triggers), db_path)
        return {
            "status": "ok",
            "db_path": db_path,
            "triggers_installed": triggers,
            "sync_log_table": SYNC_LOG_TABLE,
        }
    except Exception as exc:
        log.error("Failed to install triggers: %s", exc)
        return {"status": "error", "db_path": db_path, "message": str(exc)}


def remove_triggers(db_path: str | None = None) -> dict[str, Any]:
    """Remove sync tracking triggers (DESTROY phase)."""
    if db_path is None:
        path = _find_database()
        if path is None:
            return {"status": "error", "message": "No AppFlowy database found"}
        db_path = str(path)

    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(DROP_TRIGGER_SQL)
        conn.commit()
        conn.close()
        log.info("Removed sync triggers from %s", db_path)
        return {"status": "ok", "db_path": db_path, "message": "Triggers removed"}
    except Exception as exc:
        return {"status": "error", "db_path": db_path, "message": str(exc)}


def get_sync_log(
    db_path: str | None = None,
    unprocessed_only: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Read the sync log for pending or recent changes."""
    if db_path is None:
        path = _find_database()
        if path is None:
            return []
        db_path = str(path)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        if unprocessed_only:
            cur = conn.execute(
                f"SELECT * FROM {SYNC_LOG_TABLE} "
                "WHERE processed = 0 ORDER BY timestamp ASC LIMIT ?",
                (limit,),
            )
        else:
            cur = conn.execute(
                f"SELECT * FROM {SYNC_LOG_TABLE} "
                "ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
        results = [dict(row) for row in cur.fetchall()]
        conn.close()
        return results
    except Exception:
        return []


def mark_processed(log_ids: list[int], db_path: str | None = None) -> int:
    """Mark sync log entries as processed."""
    if not log_ids:
        return 0
    if db_path is None:
        path = _find_database()
        if path is None:
            return 0
        db_path = str(path)

    now = datetime.now(UTC).isoformat()
    try:
        conn = sqlite3.connect(db_path)
        placeholders = ",".join("?" * len(log_ids))
        conn.execute(
            f"UPDATE {SYNC_LOG_TABLE} "
            f"SET processed = 1, processed_at = ? "
            f"WHERE id IN ({placeholders})",
            (now, *log_ids),
        )
        conn.commit()
        count = conn.total_changes
        conn.close()
        return count
    except Exception:
        return 0


def rebuild_triggers(db_path: str | None = None) -> dict[str, Any]:
    """DESTROY and REBUILD triggers (self-heal path)."""
    removed = remove_triggers(db_path)
    installed = install_triggers(db_path)
    return {
        "destroy": removed,
        "rebuild": installed,
        "status": installed.get("status", "error"),
    }
