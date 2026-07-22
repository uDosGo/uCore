"""History Service — action log with git snapshots and rollback.

Tracks every significant action in the Developer Surface:
  - File modifications (auto-diff via git)
  - Skill executions (snapshot before + log after)
  - Manual snapshots (user-triggered via History tab)
  - Undo/rollback operations

Database: ~/.ucore/history/actions.db
"""
from __future__ import annotations

import json
import logging
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.history")

DB_PATH = Path.home() / ".ucore" / "history" / "actions.db"
UCORE_ROOT = Path.home() / "Code" / "uCore"

SCHEMA = """
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action_type TEXT NOT NULL,
    lane TEXT NOT NULL DEFAULT 'ecosystem',
    workspace TEXT,
    file_path TEXT,
    skill_id TEXT,
    description TEXT,
    git_commit_hash TEXT,
    diff_json TEXT,
    status TEXT NOT NULL DEFAULT 'completed',
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON actions(timestamp);
CREATE INDEX IF NOT EXISTS idx_actions_type ON actions(action_type);
CREATE INDEX IF NOT EXISTS idx_actions_lane ON actions(lane);
"""


class HistoryService:
    """Action history with git integration for snapshots and rollback."""

    _instance: "HistoryService | None" = None

    def __init__(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(DB_PATH))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    @classmethod
    def get(cls) -> "HistoryService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def log_action(
        self,
        action_type: str,
        lane: str = "ecosystem",
        workspace: str | None = None,
        file_path: str | None = None,
        skill_id: str | None = None,
        description: str = "",
        git_commit_hash: str | None = None,
        diff_json: str | None = None,
        status: str = "completed",
        metadata: dict | None = None,
    ) -> int:
        """Record an action in the history log."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT INTO actions (timestamp, action_type, lane, workspace,
               file_path, skill_id, description, git_commit_hash,
               diff_json, status, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                now, action_type, lane, workspace,
                file_path, skill_id, description, git_commit_hash,
                diff_json, status, json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        return self._conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def list_actions(
        self, limit: int = 50, lane: str | None = None,
    ) -> list[dict]:
        """Return recent actions, newest first."""
        if lane:
            rows = self._conn.execute(
                "SELECT * FROM actions WHERE lane = ? "
                "ORDER BY id DESC LIMIT ?",
                (lane, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM actions ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def undo_last(self, lane: str = "ecosystem") -> dict:
        """Undo the most recent reversible action."""
        row = self._conn.execute(
            "SELECT * FROM actions WHERE lane = ? "
            "AND action_type != 'rollback' "
            "AND status = 'completed' ORDER BY id DESC LIMIT 1",
            (lane,),
        ).fetchone()

        if not row:
            return {"success": False, "error": "No reversible actions found"}

        action = dict(row)
        action_id = action["id"]

        self._conn.execute(
            "UPDATE actions SET status = 'reverted' WHERE id = ?",
            (action_id,),
        )
        self._conn.commit()

        if action.get("git_commit_hash") and action.get("file_path"):
            try:
                subprocess.run(
                    ["git", "checkout", action["git_commit_hash"], "--",
                     action["file_path"]],
                    cwd=str(UCORE_ROOT),
                    capture_output=True, text=True, timeout=10, check=True,
                )
            except Exception as exc:
                log.warning("Git revert failed: %s", exc)

        self.log_action(
            action_type="rollback",
            lane=lane,
            description=f"Undid #{action_id}: {action.get('description', '')}",
            metadata={"reverted_action_id": action_id},
        )

        return {
            "success": True,
            "undone_action_id": action_id,
            "undone_description": action.get("description", ""),
        }

    def create_snapshot(self, label: str, lane: str = "ecosystem") -> dict:
        """Create an auto-commit snapshot before a significant action."""
        workspace = str(UCORE_ROOT)
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=workspace, capture_output=True, text=True, timeout=10,
            )
            result = subprocess.run(
                ["git", "commit", "-m", f"Snapshot: {label}",
                 "--allow-empty"],
                cwd=workspace, capture_output=True, text=True, timeout=10,
            )
            commit_hash = None
            if result.returncode == 0:
                hr = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=workspace, capture_output=True, text=True, timeout=5,
                )
                commit_hash = hr.stdout.strip()[:8] if hr.stdout else None

            try:
                diff = subprocess.run(
                    ["git", "diff", "HEAD~1", "--stat"],
                    cwd=workspace, capture_output=True, text=True, timeout=5,
                )
                diff_text = diff.stdout.strip()
            except Exception:
                diff_text = ""

            action_id = self.log_action(
                action_type="snapshot",
                lane=lane,
                workspace=workspace,
                description=label,
                git_commit_hash=commit_hash,
                diff_json=diff_text,
            )

            return {
                "success": True,
                "action_id": action_id,
                "commit_hash": commit_hash,
                "label": label,
            }
        except Exception as exc:
            log.error("Snapshot failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def restore_snapshot(self, action_id: int) -> dict:
        """Restore to a previous snapshot."""
        row = self._conn.execute(
            "SELECT * FROM actions WHERE id = ? AND action_type = 'snapshot'",
            (action_id,),
        ).fetchone()

        if not row:
            return {
                "success": False,
                "error": f"Snapshot #{action_id} not found",
            }

        action = dict(row)
        commit_hash = action.get("git_commit_hash")
        if not commit_hash:
            return {"success": False, "error": "Snapshot has no commit hash"}

        try:
            subprocess.run(
                ["git", "checkout", commit_hash],
                cwd=str(UCORE_ROOT),
                capture_output=True, text=True, timeout=30, check=True,
            )
            self.log_action(
                action_type="rollback",
                lane=action.get("lane", "ecosystem"),
                description=f"Restored snapshot #{action_id}",
                metadata={
                    "restored_snapshot_id": action_id,
                    "commit": commit_hash,
                },
            )
            return {
                "success": True,
                "restored_snapshot_id": action_id,
                "commit": commit_hash,
            }
        except Exception as exc:
            log.error("Snapshot restore failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def get_stats(self, lane: str | None = None) -> dict:
        """Return history statistics."""
        base = (
            "FROM actions" + (f" WHERE lane = '{lane}'" if lane else "")
        )
        total = self._conn.execute(
            f"SELECT COUNT(*) as c {base}"
        ).fetchone()["c"]

        by_type = {}
        for row in self._conn.execute(
            f"SELECT action_type, COUNT(*) as c {base} "
            "GROUP BY action_type"
        ).fetchall():
            by_type[row["action_type"]] = row["c"]

        snaps = self._conn.execute(
            f"SELECT COUNT(*) as c {base} "
            "AND action_type = 'snapshot'"
        ).fetchone()["c"]

        return {"total": total, "by_type": by_type, "snapshots": snaps}


def get_history() -> HistoryService:
    return HistoryService.get()