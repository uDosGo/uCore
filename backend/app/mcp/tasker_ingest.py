"""tasker_ingest — MCP bridge: Cline task_progress → persistent .tasker/spool/wisdom.

Ingests ephemeral task_progress checklists from Cline (or any AI agent) sessions
and syncs them into the persistent .tasker.dev-flow.yaml, spool, devlog.mcp.yaml,
and wisdom.md systems. Also triggers optional git commit.

Usage:
  POST /api/skills/tasker_ingest/run
  Body: {
    "action": "ingest",
    "workspace": "uCore",
    "session_id": "cline-2026-07-01-001",
    "checklist": "# Progress\\n- [x] Step 1 done\\n- [ ] Step 2 pending",
    "outcome": "completed",
    "summary": "Implemented tasker_ingest bridge",
    "lessons": ["Use MCP tools for persistence", "Always update wisdom.md"],
    "auto_commit": false
  }
"""
from __future__ import annotations

import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from app.core.settings import settings
from app.services.spool_writer import write_spool
from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.mcp.tasker_ingest")

PROJECT_ROOT = settings.udos_root / "uCore"
DEFAULT_TASKER_FILE = PROJECT_ROOT / ".tasker.dev-flow.yaml"
DEFAULT_DEVLOG_FILE = PROJECT_ROOT / "devlog.mcp.yaml"
DEFAULT_WISDOM_FILE = PROJECT_ROOT / "wisdom.md"


class TaskerIngest(BaseSkill):
    """Ingest Cline task_progress into persistent dev-flow tracking."""

    meta = SkillMeta(
        id="tasker_ingest",
        name="Tasker Ingest",
        description=(
            "Bridge: ingest Cline/session task_progress checklists into "
            ".tasker.dev-flow.yaml, spool, devlog.mcp.yaml, and wisdom.md"
        ),
        category="workflow",
        timeout=120,
        params=[
            SkillParam(
                name="action",
                type="string",
                required=True,
                description="Action: ingest, status, archive, commit",
            ),
            SkillParam(
                name="workspace",
                type="string",
                required=False,
                default="uCore",
                description="Workspace/project name",
            ),
            SkillParam(
                name="session_id",
                type="string",
                required=False,
                default="",
                description="Unique session identifier (e.g. cline-YYYY-MM-DD-NNN)",
            ),
            SkillParam(
                name="checklist",
                type="string",
                required=False,
                default="",
                description="Markdown task_progress checklist from session",
            ),
            SkillParam(
                name="outcome",
                type="string",
                required=False,
                default="completed",
                description="Session outcome: completed, partial, failed",
            ),
            SkillParam(
                name="summary",
                type="string",
                required=False,
                default="",
                description="Human-readable summary of what was done",
            ),
            SkillParam(
                name="lessons",
                type="list",
                required=False,
                default=[],
                description="Durable lessons learned to append to wisdom.md",
            ),
            SkillParam(
                name="auto_commit",
                type="boolean",
                required=False,
                default=False,
                description="Auto git commit after ingest",
            ),
            SkillParam(
                name="tasker_file",
                type="string",
                required=False,
                default=str(DEFAULT_TASKER_FILE),
                description="Path to .tasker.dev-flow.yaml",
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
        action = str(kwargs.get("action", "ingest")).strip().lower()
        workspace = str(kwargs.get("workspace", "uCore"))
        session_id = str(kwargs.get("session_id", ""))
        checklist = str(kwargs.get("checklist", ""))
        outcome = str(kwargs.get("outcome", "completed"))
        summary = str(kwargs.get("summary", ""))
        lessons = kwargs.get("lessons", [])
        auto_commit = bool(kwargs.get("auto_commit", False))
        tasker_file = Path(kwargs.get("tasker_file", DEFAULT_TASKER_FILE)).expanduser()
        dry_run = bool(kwargs.get("dry_run", False))

        if action == "ingest":
            return await self._ingest(
                workspace=workspace,
                session_id=session_id,
                checklist=checklist,
                outcome=outcome,
                summary=summary,
                lessons=lessons,
                auto_commit=auto_commit,
                tasker_file=tasker_file,
                dry_run=dry_run,
            )
        elif action == "status":
            return self._status(tasker_file)
        elif action == "commit":
            return self._git_commit(tasker_file, summary, dry_run)
        elif action == "archive":
            return self._archive_completed(tasker_file, dry_run)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def _ingest(
        self,
        workspace: str,
        session_id: str,
        checklist: str,
        outcome: str,
        summary: str,
        lessons: list[str],
        auto_commit: bool,
        tasker_file: Path,
        dry_run: bool,
    ) -> dict:
        """Ingest a task_progress checklist into persistent storage."""
        now = datetime.now(UTC)
        timestamp = now.isoformat()
        results: dict[str, Any] = {
            "spool_written": False,
            "devlog_appended": False,
            "tasker_updated": False,
            "wisdom_appended": False,
            "git_committed": False,
        }

        # 1. Parse checklist into structured items
        parsed_items = self._parse_checklist(checklist)
        completed = [i for i in parsed_items if i.get("done")]
        pending = [i for i in parsed_items if not i.get("done")]
        total = len(parsed_items)

        # 2. Write to spool
        if not dry_run:
            write_spool(
                level="INFO",
                module="tasker_ingest",
                message=(
                    f"Ingested session={session_id or 'unknown'} "
                    f"workspace={workspace} outcome={outcome} "
                    f"items={total} completed={len(completed)} pending={len(pending)}"
                ),
                tags=["tasker-ingest", workspace, outcome],
            )
            results["spool_written"] = True

        # 3. Append to devlog.mcp.yaml
        devlog_path = PROJECT_ROOT / "devlog.mcp.yaml"
        if not dry_run:
            devlog_entry = self._render_devlog_entry(
                timestamp=timestamp,
                session_id=session_id,
                workspace=workspace,
                outcome=outcome,
                summary=summary,
                completed=completed,
                pending=pending,
            )
            existing = ""
            if devlog_path.exists():
                existing = devlog_path.read_text(encoding="utf-8")
            devlog_path.write_text(existing + "\n" + devlog_entry, encoding="utf-8")
            results["devlog_appended"] = True

        # 4. Update .tasker.dev-flow.yaml
        if not dry_run and tasker_file.exists():
            self._update_tasker_yaml(
                tasker_file=tasker_file,
                session_id=session_id or f"session-{now.strftime('%Y%m%d%H%M%S')}",
                summary=summary or f"Session {session_id}",
                outcome=outcome,
                items=parsed_items,
                workspace=workspace,
                timestamp=timestamp,
            )
            results["tasker_updated"] = True

        # 5. Append lessons to wisdom.md
        if not dry_run and lessons:
            wisdom_path = DEFAULT_WISDOM_FILE
            existing = ""
            if wisdom_path.exists():
                existing = wisdom_path.read_text(encoding="utf-8")
            wisdom_appends = []
            for lesson in lessons:
                if lesson and lesson not in existing:
                    wisdom_appends.append(f"- {lesson}")
            if wisdom_appends:
                lesson_block = (
                    f"\n## Session: {session_id or timestamp}\n"
                    + "\n".join(wisdom_appends)
                    + "\n"
                )
                wisdom_path.write_text(existing + lesson_block, encoding="utf-8")
                results["wisdom_appended"] = len(wisdom_appends)

        # 6. Auto git commit
        if not dry_run and auto_commit:
            commit_result = self._git_commit(tasker_file, summary, dry_run=False)
            results["git_committed"] = commit_result.get("success", False)
            results["git_result"] = commit_result

        return {
            "success": True,
            "action": "ingest",
            "workspace": workspace,
            "outcome": outcome,
            "items_total": total,
            "items_completed": len(completed),
            "items_pending": len(pending),
            "results": results,
            "dry_run": dry_run,
        }

    def _parse_checklist(self, checklist: str) -> list[dict[str, Any]]:
        """Parse markdown checklist into structured items."""
        items = []
        for line in checklist.split("\n"):
            line = line.strip()
            # Match: - [x] Description  or  - [ ] Description
            if line.startswith("- [x]") or line.startswith("- [X]") or line.startswith("- [*]"):
                items.append({
                    "text": line[5:].strip(),
                    "done": True,
                })
            elif line.startswith("- [ ]"):
                items.append({
                    "text": line[5:].strip(),
                    "done": False,
                })
            elif line.startswith("* [x]") or line.startswith("* [X]"):
                items.append({
                    "text": line[5:].strip(),
                    "done": True,
                })
            elif line.startswith("* [ ]"):
                items.append({
                    "text": line[5:].strip(),
                    "done": False,
                })
        return items

    def _render_devlog_entry(
        self,
        timestamp: str,
        session_id: str,
        workspace: str,
        outcome: str,
        summary: str,
        completed: list[dict],
        pending: list[dict],
    ) -> str:
        """Render a devlog entry in MCP format."""
        lines = [
            f"\n## Session: {session_id or 'unknown'}",
            f"- timestamp: {timestamp}",
            f"- workspace: {workspace}",
            f"- outcome: {outcome}",
            f"- completed: {len(completed)}",
            f"- pending: {len(pending)}",
        ]
        if summary:
            lines.append(f"- summary: {summary}")
        if completed:
            lines.append("- completed_items:")
            for item in completed:
                lines.append(f"  - {item['text']}")
        if pending:
            lines.append("- pending_items:")
            for item in pending:
                lines.append(f"  - {item['text']}")
        return "\n".join(lines)

    def _update_tasker_yaml(
        self,
        tasker_file: Path,
        session_id: str,
        summary: str,
        outcome: str,
        items: list[dict],
        workspace: str,
        timestamp: str,
    ) -> None:
        """Append session tasks to .tasker.dev-flow.yaml."""
        try:
            content = tasker_file.read_text(encoding="utf-8")
        except Exception:
            content = ""

        # Build new task entries
        new_tasks = []
        for i, item in enumerate(items):
            task_uid = f"task.ingest.{session_id}.{i:03d}" if session_id else f"task.auto.{i:03d}"
            status = "done" if item["done"] else "todo"
            new_tasks.append({
                "uid": task_uid,
                "title": item["text"],
                "description": f"From session {session_id}: {item['text']}",
                "status": status,
                "priority": "medium",
                "lane": "maintenance",
                "tags": ["tasker-ingest", workspace, outcome],
                "source": {
                    "file": "tasker_ingest.py",
                    "type": "session-ingest",
                },
                "created": timestamp,
                "updated": timestamp,
            })

        # Parse existing YAML, merge tasks
        try:
            data = yaml.safe_load(content) or {}
        except yaml.YAMLError:
            data = {}

        existing_tasks = data.get("tasks", [])
        # Avoid duplicating by uid
        existing_uids = {t.get("uid") for t in existing_tasks if t.get("uid")}
        merged_tasks = existing_tasks + [t for t in new_tasks if t["uid"] not in existing_uids]

        data["tasks"] = merged_tasks
        data["task_count"] = len(merged_tasks)
        data["completed_count"] = sum(1 for t in merged_tasks if t.get("status") == "done")
        data["updated"] = timestamp

        # Write back
        tasker_file.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")

    def _status(self, tasker_file: Path) -> dict:
        """Return current status of the tasker file."""
        if not tasker_file.exists():
            return {"success": False, "error": "tasker file not found"}

        try:
            content = tasker_file.read_text(encoding="utf-8")
            data = yaml.safe_load(content) or {}
            tasks = data.get("tasks", [])
            total = len(tasks)
            done = sum(1 for t in tasks if t.get("status") == "done")
            archived = sum(1 for t in tasks if t.get("status") == "archived")
            todo = total - done - archived

            return {
                "success": True,
                "action": "status",
                "total_tasks": total,
                "completed": done,
                "archived": archived,
                "pending": todo,
                "updated": data.get("updated", "unknown"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _git_commit(self, tasker_file: Path, message: str, dry_run: bool) -> dict:
        """Auto git commit the changes."""
        repo_dir = PROJECT_ROOT
        if not (repo_dir / ".git").exists():
            return {"success": False, "error": "not a git repository"}

        commit_msg = message or "chore: auto-sync tasker ingest"
        try:
            if not dry_run:
                subprocess.run(
                    ["git", "-C", str(repo_dir), "add", "-A"],
                    capture_output=True, text=True, check=False,
                )
                result = subprocess.run(
                    ["git", "-C", str(repo_dir), "commit", "-m", commit_msg],
                    capture_output=True, text=True, check=False,
                )
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "message": commit_msg,
                }
            return {
                "success": True,
                "dry_run": True,
                "message": commit_msg,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _archive_completed(self, tasker_file: Path, dry_run: bool) -> dict:
        """Move done tasks to archive section."""
        if not tasker_file.exists():
            return {"success": False, "error": "tasker file not found"}

        try:
            content = tasker_file.read_text(encoding="utf-8")
            data = yaml.safe_load(content) or {}
            tasks = data.get("tasks", [])
            archive = data.get("archive", [])

            done_tasks = [t for t in tasks if t.get("status") == "done" and t.get("uid", "").startswith("task.ingest.")]
            kept_tasks = [t for t in tasks if t not in done_tasks]

            for t in done_tasks:
                t["archived_reason"] = "auto-archive"
                t["archived_date"] = datetime.now(UTC).isoformat()
                archive.append(t)

            if not dry_run:
                data["tasks"] = kept_tasks
                data["archive"] = archive
                data["task_count"] = len(kept_tasks)
                tasker_file.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")

            return {
                "success": True,
                "action": "archive",
                "archived": len(done_tasks),
                "remaining": len(kept_tasks),
                "dry_run": dry_run,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
