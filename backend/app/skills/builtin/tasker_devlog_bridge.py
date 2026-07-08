"""tasker_devlog_bridge — MCP bridge for tasker/devlog/spool integration.

Creates a unified bridge between .tasker Markdown files, devlog.mcp.yaml, and spool logs.
Provides read/write capabilities for the MCP feed system.

Usage:
  POST /api/skills/tasker_devlog_bridge/run
  Body: {
    "action": "sync",
    "tasker_dir": ".tasker",
    "devlog_file": "devlog.mcp.yaml",
    "hours": 24
  }
"""
from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from app.core.settings import settings
from app.services.spool_reader import read_spool
from app.skills.base import BaseSkill, SkillMeta, SkillParam

PROJECT_ROOT = settings.udos_root / "uCore"
DEFAULT_TASKER_DIR = PROJECT_ROOT / ".tasker"
DEFAULT_DEVLOG_FILE = PROJECT_ROOT / "devlog.mcp.yaml"


class TaskerDevlogBridge(BaseSkill):
    meta = SkillMeta(
        id="tasker_devlog_bridge",
        name="Tasker Devlog Bridge",
        description="MCP bridge for tasker/devlog/spool integration - read/write MCP feed",
        category="workflow",
        timeout=60,
        params=[
            SkillParam(
                name="action",
                type="string",
                required=True,
                description="Action: sync, read, write, archive, purge",
            ),
            SkillParam(
                name="tasker_dir",
                type="string",
                required=False,
                default=str(DEFAULT_TASKER_DIR),
                description="Path to .tasker directory",
            ),
            SkillParam(
                name="devlog_file",
                type="string",
                required=False,
                default=str(DEFAULT_DEVLOG_FILE),
                description="Path to devlog.mcp.yaml",
            ),
            SkillParam(
                name="hours",
                type="integer",
                required=False,
                default=24,
                description="Hours of spool activity to include",
            ),
            SkillParam(
                name="max_age_days",
                type="integer",
                required=False,
                default=7,
                description="Days before archiving old tasks",
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                required=False,
                default=False,
                description="Preview without writing changes",
            ),
        ],
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        action = str(kwargs.get("action", "sync")).strip().lower()
        tasker_dir = Path(kwargs.get("tasker_dir", DEFAULT_TASKER_DIR)).expanduser()
        devlog_file = Path(kwargs.get("devlog_file", DEFAULT_DEVLOG_FILE)).expanduser()
        hours = int(kwargs.get("hours", 24))
        max_age_days = int(kwargs.get("max_age_days", 7))
        dry_run = bool(kwargs.get("dry_run", False))

        if action == "sync":
            return await self._sync(tasker_dir, devlog_file, hours, dry_run)
        elif action == "read":
            return self._read(tasker_dir, devlog_file)
        elif action == "write":
            return self._write(tasker_dir, devlog_file, kwargs.get("content", ""), dry_run)
        elif action == "archive":
            return self._archive_old_tasks(tasker_dir, max_age_days, dry_run)
        elif action == "purge":
            return self._purge_legacy_docs(PROJECT_ROOT / "docs", dry_run)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def _sync(self, tasker_dir: Path, devlog_file: Path, hours: int, dry_run: bool) -> dict:
        """Sync .tasker with devlog.mcp.yaml and spool activity."""
        # Collect completed tasks
        completed_tasks = self._collect_completed_tasks(tasker_dir)

        # Collect spool activity
        cutoff = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
        spool_entries = read_spool(since=cutoff)

        # Generate MCP devlog
        devlog_content = self._render_devlog(
            completed_tasks=completed_tasks,
            spool_entries=spool_entries,
            hours=hours,
        )

        if not dry_run:
            devlog_file.write_text(devlog_content, encoding="utf-8")

        return {
            "success": True,
            "action": "sync",
            "devlog_path": str(devlog_file),
            "completed_tasks": len(completed_tasks),
            "spool_entries": len(spool_entries),
            "hours": hours,
            "dry_run": dry_run,
        }

    def _read(self, tasker_dir: Path, devlog_file: Path) -> dict:
        """Read current state of tasker and devlog."""
        tasks = []
        if tasker_dir.exists():
            for task_file in tasker_dir.rglob("*.md"):
                if task_file.name == "README.md":
                    continue
                try:
                    content = task_file.read_text(encoding="utf-8")
                    tasks.append({
                        "path": str(task_file.relative_to(tasker_dir.parent)),
                        "content": content[:500],  # Preview
                    })
                except Exception:
                    continue

        devlog_content = ""
        if devlog_file.exists():
            devlog_content = devlog_file.read_text(encoding="utf-8")

        return {
            "success": True,
            "action": "read",
            "tasks": tasks,
            "devlog_preview": devlog_content[:1000] if devlog_content else None,
        }

    def _write(self, tasker_dir: Path, devlog_file: Path, content: str, dry_run: bool) -> dict:
        """Write content to devlog.mcp.yaml."""
        if not dry_run:
            devlog_file.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "action": "write",
            "devlog_path": str(devlog_file),
            "dry_run": dry_run,
        }

    def _archive_old_tasks(self, tasker_dir: Path, max_age_days: int, dry_run: bool) -> dict:
        """Archive completed tasks older than max_age_days."""
        archived_dir = tasker_dir.parent / ".tasker.archived"
        archived_count = 0

        if not tasker_dir.exists():
            return {"success": True, "archived": 0, "dry_run": dry_run}

        cutoff = datetime.now(UTC) - timedelta(days=max_age_days)

        for task_file in tasker_dir.rglob("*.md"):
            if task_file.name == "README.md":
                continue
            try:
                content = task_file.read_text(encoding="utf-8")
                if "status: done" in content or "status: completed" in content:
                    # Check file modification time
                    mtime = datetime.fromtimestamp(task_file.stat().st_mtime, tz=UTC)
                    if mtime < cutoff:
                        relative = task_file.relative_to(tasker_dir)
                        dest = archived_dir / relative
                        if not dry_run:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            dest.write_text(content, encoding="utf-8")
                            task_file.unlink(missing_ok=True)
                        archived_count += 1
            except Exception:
                continue

        return {
            "success": True,
            "action": "archive",
            "archived": archived_count,
            "dry_run": dry_run,
        }

    def _purge_legacy_docs(self, docs_dir: Path, dry_run: bool) -> dict:
        """Purge legacy completed documentation reports."""
        purged = []
        legacy_patterns = [
            r"COMPLETE.*\.md$",
            r"DONE.*\.md$",
            r"REPORT_.*\.md$",
            r"CHECKLIST.*\.md$",
        ]

        if not docs_dir.exists():
            return {"success": True, "purged": [], "dry_run": dry_run}

        for doc_file in docs_dir.rglob("*.md"):
            for pattern in legacy_patterns:
                if re.search(pattern, doc_file.name, re.IGNORECASE):
                    if not dry_run:
                        doc_file.unlink(missing_ok=True)
                    purged.append(str(doc_file.relative_to(docs_dir.parent)))
                    break

        return {
            "success": True,
            "action": "purge",
            "purged": purged,
            "dry_run": dry_run,
        }

    def _collect_completed_tasks(self, tasker_dir: Path) -> list[dict[str, Any]]:
        """Collect completed tasks from .tasker directory."""
        tasks = []
        if not tasker_dir.exists():
            return tasks

        for task_file in tasker_dir.rglob("*.md"):
            if task_file.name == "README.md":
                continue
            try:
                content = task_file.read_text(encoding="utf-8")
                if "status: done" in content or "status: completed" in content:
                    # Parse frontmatter
                    task_info = self._parse_task_file(task_file, content)
                    tasks.append(task_info)
            except Exception:
                continue

        return tasks

    def _parse_task_file(self, path: Path, content: str) -> dict[str, Any]:
        """Parse task file to extract metadata."""
        lines = content.split("\n")
        title = lines[0].replace("#", "").strip() if lines else path.stem

        # Extract key fields
        status = "done"
        for line in lines[:20]:
            if line.startswith("- status:"):
                status = line.split(":", 1)[1].strip()
                break

        return {
            "file": str(path.relative_to(path.parent.parent)),
            "archived": True,
            "title": title,
            "status": status,
        }

    def _render_devlog(
        self,
        completed_tasks: list[dict[str, Any]],
        spool_entries: list[dict[str, Any]],
        hours: int,
    ) -> str:
        """Render MCP-formatted devlog."""
        lines = [
            f"# Devlog MCP — Generated: {datetime.now(UTC).isoformat()}",
            "",
            'version: "1.0.0"',
            'generated_by: "Copilot-Poolside-Laguana-M1"',
            f"hours: {hours}",
            f"completed_tasks: {len(completed_tasks)}",
            f"spool_entries: {len(spool_entries)}",
            "",
            "## Completed Tasks",
        ]

        for task in completed_tasks:
            lines.append(f"- file: {task['file']}")
            lines.append(f"  archived: {task['archived']}")
            lines.append("")

        lines.append("## Spool Activity")
        for entry in spool_entries[-50:]:  # Last 50 entries
            lines.append(f"- timestamp: {entry.get('timestamp', 'unknown')}")
            lines.append(f"  level: {entry.get('level', 'INFO')}")
            lines.append(f"  module: {entry.get('module', 'unknown')}")
            lines.append(f"  message: {entry.get('message', '')}")
            lines.append("")

        return "\n".join(lines)
