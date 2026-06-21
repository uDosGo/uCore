"""tasker_sync — Export AppFlowy/local rows into Markdown-first task files.

Creates Tasker-style Markdown tasks under a repo-local `.tasker/` directory so
workflow planning can live beside code and remain human-readable.

Usage:
  POST /api/skills/tasker_sync/run
  Body: {
    "db": "database",
    "sql": "SELECT * FROM row_table LIMIT 20",
    "tasker_dir": "/path/to/repo/.tasker",
    "board": "inbox"
  }
"""
from __future__ import annotations

from pathlib import Path

from app.knowledge.local_first import discover_databases, run_query
from app.services.tasker_bridge import export_rows_to_tasker
from app.skills.base import BaseSkill, SkillMeta, SkillParam

PROJECT_ROOT = Path.home() / "Code/uCore"
DEFAULT_TASKER_DIR = PROJECT_ROOT / ".tasker"
DEFAULT_SQL = "SELECT * FROM row_table LIMIT 20"


class TaskerSync(BaseSkill):
    meta = SkillMeta(
        id="tasker_sync",
        name="Tasker Sync",
        description="Export AppFlowy/local workflow rows into Markdown task files",
        category="workflow",
        timeout=120,
        params=[
            SkillParam(name="db", type="string", required=False, default="database", description="Known DB key or absolute sqlite path"),
            SkillParam(name="sql", type="string", required=False, default=DEFAULT_SQL, description="Read-only SQL query for task rows"),
            SkillParam(name="tasker_dir", type="string", required=False, default=str(DEFAULT_TASKER_DIR), description="Destination .tasker directory"),
            SkillParam(name="board", type="string", required=False, default="inbox", description="Tasker board/folder name"),
            SkillParam(name="title_field", type="string", required=False, default="title", description="Column used for task title"),
            SkillParam(name="body_fields", type="string", required=False, default="description,notes,content", description="Comma-separated columns included in task body"),
            SkillParam(name="status_field", type="string", required=False, default="status", description="Column used for task status"),
            SkillParam(name="id_field", type="string", required=False, default="id", description="Column used for stable source identifier"),
            SkillParam(name="dry_run", type="boolean", required=False, default=False, description="Preview exports without writing files"),
        ],
    )

    async def run(self, **kwargs) -> dict:
        db = str(kwargs.get("db", "database")).strip()
        sql = str(kwargs.get("sql", DEFAULT_SQL)).strip()
        tasker_dir = str(kwargs.get("tasker_dir", DEFAULT_TASKER_DIR)).strip()
        board = str(kwargs.get("board", "inbox")).strip() or "inbox"
        title_field = str(kwargs.get("title_field", "title")).strip() or "title"
        body_fields = [part.strip() for part in str(kwargs.get("body_fields", "description,notes,content")).split(",") if part.strip()]
        status_field = str(kwargs.get("status_field", "status")).strip() or "status"
        id_field = str(kwargs.get("id_field", "id")).strip() or "id"
        dry_run = bool(kwargs.get("dry_run", False))

        dbs = discover_databases()
        db_path = dbs.get(db, db)
        if not db_path:
            return {"success": False, "error": f"Database '{db}' not found"}

        try:
            result = run_query(db_path=db_path, sql=sql, params=[], write=False)
        except Exception as exc:
            return {
                "success": False,
                "db": db,
                "db_path": db_path,
                "error": str(exc),
            }

        rows = result.get("rows", [])
        exported = export_rows_to_tasker(
            rows,
            tasker_dir=tasker_dir,
            board=board,
            title_field=title_field,
            body_fields=body_fields,
            status_field=status_field,
            id_field=id_field,
            source="appflowy",
            dry_run=dry_run,
        )
        return {
            "success": True,
            "db": db,
            "db_path": db_path,
            "sql": sql,
            **exported,
        }
