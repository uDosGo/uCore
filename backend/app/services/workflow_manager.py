"""Workflow manager with SQLite persistence for definitions, logs, and runs."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.settings import settings


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    schedule: str
    created_at: str
    steps: list[dict[str, Any]]


@dataclass
class WorkflowRun:
    run_id: str
    workflow_id: str
    workflow_name: str
    started_at: str
    finished_at: str
    status: str
    steps: list[dict[str, Any]]


class WorkflowManager:
    """Persistent workflow storage with SQLite backend."""

    def __init__(self):
        self._db_path = settings.data_dir / "workflows.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    schedule TEXT DEFAULT 'manual',
                    created_at TEXT NOT NULL,
                    steps TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    level TEXT DEFAULT 'info',
                    event TEXT NOT NULL,
                    message TEXT DEFAULT '',
                    run_id TEXT,
                    step_index INTEGER,
                    skill_id TEXT,
                    FOREIGN KEY (workflow_id)
                        REFERENCES workflows(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    workflow_name TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    FOREIGN KEY (workflow_id)
                        REFERENCES workflows(id)
                )
                """
            )
            conn.commit()

    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        steps: list[dict[str, Any]],
        description: str = "",
        schedule: str = "manual",
    ) -> dict[str, Any]:
        """Create a new workflow definition."""
        created_at = datetime.now(timezone.utc).isoformat()
        steps_json = json.dumps(steps)

        with self._connect() as conn:
            # If the workflow already exists, return it instead of attempting
            # a duplicate insert (keeps tests idempotent if DB pre-populated).
            existing = conn.execute("SELECT id FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
            if existing:
                # Return existing workflow payload
                row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
                steps_exist = json.loads(row["steps"] or "[]")
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "schedule": row["schedule"],
                    "created_at": row["created_at"],
                    "steps": steps_exist,
                    "step_count": len(steps_exist),
                }

            conn.execute(
                """
                INSERT INTO workflows
                (id, name, description, schedule, created_at, steps)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    name,
                    description,
                    schedule,
                    created_at,
                    steps_json,
                ),
            )
            conn.commit()

        return {
            "id": workflow_id,
            "name": name,
            "description": description,
            "schedule": schedule,
            "created_at": created_at,
            "steps": steps,
            "step_count": len(steps),
        }

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        """Fetch a workflow definition by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM workflows WHERE id = ?",
                (workflow_id,),
            ).fetchone()

        if not row:
            return None

        steps = json.loads(row["steps"] or "[]")
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "schedule": row["schedule"],
            "created_at": row["created_at"],
            "steps": steps,
            "step_count": len(steps),
        }

    def list_workflows(self) -> list[dict[str, Any]]:
        """List all workflow definitions, sorted by creation time."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, description, schedule, created_at, steps
                FROM workflows
                ORDER BY created_at DESC
                """
            ).fetchall()

        workflows = []
        for row in rows:
            steps = json.loads(row["steps"] or "[]")
            workflows.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "schedule": row["schedule"],
                    "created_at": row["created_at"],
                    "steps": steps,
                    "step_count": len(steps),
                }
            )
        return workflows

    def record_log(
        self,
        workflow_id: str,
        event: str,
        message: str = "",
        level: str = "info",
        run_id: str = "",
        step_index: int = 0,
        skill_id: str = "",
    ) -> None:
        """Record a workflow log entry."""
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_logs
                (workflow_id, timestamp, level, event, message,
                 run_id, step_index, skill_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    timestamp,
                    level,
                    event,
                    message,
                    run_id or "",
                    step_index or 0,
                    skill_id or "",
                ),
            )
            conn.commit()

    def get_logs(
        self,
        workflow_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch recent logs for a workflow."""
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, level, event, message, run_id,
                       step_index, skill_id
                FROM workflow_logs
                WHERE workflow_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (workflow_id, safe_limit),
            ).fetchall()

        logs = []
        for row in rows:
            log_entry = {
                "timestamp": row["timestamp"],
                "level": row["level"],
                "event": row["event"],
                "message": row["message"],
            }
            if row["run_id"]:
                log_entry["run_id"] = row["run_id"]
            if row["step_index"]:
                log_entry["step_index"] = row["step_index"]
            if row["skill_id"]:
                log_entry["skill_id"] = row["skill_id"]
            logs.append(log_entry)

        # Reverse to ascending order (oldest first)
        logs.reverse()
        return logs

    def save_run(
        self,
        run_id: str,
        workflow_id: str,
        workflow_name: str,
        started_at: str,
        finished_at: str,
        status: str,
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Save a completed workflow run."""
        steps_json = json.dumps(steps)

        with self._connect() as conn:
            # Avoid duplicate run_id insertion: if present, return existing run
            existing = conn.execute("SELECT run_id FROM workflow_runs WHERE run_id = ?", (run_id,)).fetchone()
            if existing:
                row = conn.execute("SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,)).fetchone()
                return {
                    "run_id": row["run_id"],
                    "workflow_id": row["workflow_id"],
                    "workflow_name": row["workflow_name"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "status": row["status"],
                    "steps": json.loads(row["steps"] or "[]"),
                }

            conn.execute(
                """
                INSERT INTO workflow_runs
                (run_id, workflow_id, workflow_name, started_at,
                 finished_at, status, steps)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    workflow_id,
                    workflow_name,
                    started_at,
                    finished_at,
                    status,
                    steps_json,
                ),
            )
            conn.commit()

        return {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "steps": steps,
        }

    def get_run_history(
        self,
        workflow_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch recent run history for a workflow."""
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, workflow_id, workflow_name, started_at,
                       finished_at, status, steps
                FROM workflow_runs
                WHERE workflow_id = ?
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (workflow_id, safe_limit),
            ).fetchall()

        runs = []
        for row in rows:
            steps = json.loads(row["steps"] or "[]")
            runs.append(
                {
                    "run_id": row["run_id"],
                    "workflow_id": row["workflow_id"],
                    "workflow_name": row["workflow_name"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "status": row["status"],
                    "steps": steps,
                }
            )
        return runs

    def get_all_runs(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch recent runs across all workflows."""
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, workflow_id, workflow_name, started_at,
                       finished_at, status, steps
                FROM workflow_runs
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

        runs = []
        for row in rows:
            steps = json.loads(row["steps"] or "[]")
            runs.append(
                {
                    "run_id": row["run_id"],
                    "workflow_id": row["workflow_id"],
                    "workflow_name": row["workflow_name"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "status": row["status"],
                    "steps": steps,
                }
            )
        return runs
