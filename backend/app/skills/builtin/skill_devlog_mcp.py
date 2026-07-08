"""Devlog MCP — Generate MCP-formatted devlog from completed tasks and spool activity.

Creates a structured devlog in MCP format for AI consumption, linking completed
tasks to spool history and archive system.

Usage:
  POST /api/skills/devlog_mcp/run
    Body: {
        "tasker_dir": ".tasker",
        "output_file": "devlog.mcp.yaml",
        "hours": 24
    }
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.settings import settings
from app.services.spool_reader import read_spool
from app.skills.base import BaseSkill, SkillMeta, SkillParam

PROJECT_ROOT = settings.udos_root / "uCore"
DEFAULT_TASKER_DIR = PROJECT_ROOT / ".tasker"


class DevlogMCP(BaseSkill):
    meta = SkillMeta(
        id="devlog_mcp",
        name="Devlog MCP",
        description="Generate MCP-formatted devlog from completed tasks and spool activity",
        category="workflow",
        timeout=60,
        params=[
            SkillParam(
                name="tasker_dir",
                type="string",
                required=False,
                default=str(DEFAULT_TASKER_DIR),
                description="Path to .tasker directory",
            ),
            SkillParam(
                name="output_file",
                type="string",
                required=False,
                default="devlog.mcp.yaml",
                description="Output filename for MCP devlog",
            ),
            SkillParam(
                name="hours",
                type="integer",
                required=False,
                default=24,
                description="Hours of spool activity to include",
            ),
            SkillParam(
                name="include_archived",
                type="boolean",
                required=False,
                default=True,
                description="Include archived tasks",
            ),
        ],
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        tasker_dir = Path(kwargs.get("tasker_dir", DEFAULT_TASKER_DIR)).expanduser()
        output_file = kwargs.get("output_file", "devlog.mcp.yaml")
        hours = int(kwargs.get("hours", 24))
        include_archived = bool(kwargs.get("include_archived", True))

        # Collect completed tasks
        completed_tasks = self._collect_completed_tasks(tasker_dir, include_archived)

        # Collect spool activity
        cutoff = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
        spool_entries = read_spool(since=cutoff)

        # Generate MCP devlog
        devlog_content = self._render_devlog(
            completed_tasks=completed_tasks,
            spool_entries=spool_entries,
            hours=hours,
        )

        # Write output
        output_path = tasker_dir.parent / output_file
        output_path.write_text(devlog_content, encoding="utf-8")

        return {
            "success": True,
            "output_path": str(output_path),
            "completed_tasks": len(completed_tasks),
            "spool_entries": len(spool_entries),
            "hours": hours,
        }

    def _collect_completed_tasks(
        self,
        tasker_dir: Path,
        include_archived: bool,
    ) -> list[dict[str, Any]]:
        """Collect completed tasks from .tasker and optionally .tasker.archived."""
        tasks = []

        for source_dir in [tasker_dir]:
            if not source_dir.exists():
                continue
            for task_file in source_dir.rglob("*.md"):
                if task_file.name == "README.md":
                    continue
                try:
                    content = task_file.read_text(encoding="utf-8")
                    if "status: done" in content or "status: completed" in content:
                        tasks.append({
                            "file": str(task_file.relative_to(tasker_dir.parent)),
                            "content": content,
                        })
                except Exception:
                    continue

        if include_archived:
            archived_dir = tasker_dir.parent / ".tasker.archived"
            if archived_dir.exists():
                for task_file in archived_dir.rglob("*.md"):
                    try:
                        content = task_file.read_text(encoding="utf-8")
                        tasks.append({
                            "file": str(task_file.relative_to(tasker_dir.parent)),
                            "content": content,
                            "archived": True,
                        })
                    except Exception:
                        continue

        return tasks

    def _render_devlog(
        self,
        completed_tasks: list[dict[str, Any]],
        spool_entries: list[dict[str, Any]],
        hours: int,
    ) -> str:
        """Render MCP-formatted devlog."""
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        lines = [
            f"# Devlog MCP — Generated: {timestamp}",
            "",
            "version: \"1.0.0\"",
            "generated_by: \"Copilot-Poolside-Laguana-M1\"",
            f"hours: {hours}",
            f"completed_tasks: {len(completed_tasks)}",
            f"spool_entries: {len(spool_entries)}",
            "",
            "## Completed Tasks",
            "",
        ]

        for task in completed_tasks:
            lines.append(f"- file: {task['file']}")
            lines.append(f"  archived: {task.get('archived', False)}")
            lines.append("")

        lines.extend([
            "## Spool Activity",
            "",
        ])

        for entry in spool_entries[:50]:  # Limit to 50 entries
            lines.append(f"- timestamp: {entry.timestamp}")
            lines.append(f"  level: {entry.level}")
            lines.append(f"  module: {entry.module}")
            lines.append(f"  message: {entry.message[:100]}")
            lines.append("")

        return "\n".join(lines)
