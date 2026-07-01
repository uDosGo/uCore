"""docs_roundup — End-of-dev-round docs automation.

Performs a complete docs round before commit:
1. Archive completed tasks from .tasker to .tasker.archived
2. Update devlog.mcp.yaml with session completion data
3. Organise docs: remove legacy files, consolidate related docs
4. Update specs that need updating
5. Archive old/unused specs
6. Plan new docs needed for next round

Usage:
  POST /api/skills/docs_roundup/run
  Body: {
    "action": "roundup",
    "session_summary": "Implemented tasker_ingest bridge + dev_layer + docs_roundup",
    "next_round_plans": ["Phase 2: Web Chat bridge", "Phase 3: GitHub automation"],
    "dry_run": false
  }
"""
from __future__ import annotations

import logging
import re
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.settings import settings
from app.services.spool_writer import write_spool
from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.docs_roundup")

PROJECT_ROOT = settings.udos_root / "uCore"
DEFAULT_TASKER_DIR = PROJECT_ROOT / ".tasker"
DEFAULT_ARCHIVE_DIR = PROJECT_ROOT / ".tasker.archived"
DEFAULT_DEVLOG_FILE = PROJECT_ROOT / "devlog.mcp.yaml"
DEFAULT_DOCS_DIR = PROJECT_ROOT / "docs"
DEFAULT_TASKER_FILE = PROJECT_ROOT / ".tasker.dev-flow.yaml"


class DocsRoundup(BaseSkill):
    """End-of-round docs automation: archive, update, organise, plan."""

    meta = SkillMeta(
        id="docs_roundup",
        name="Docs Roundup",
        description=(
            "End-of-dev-round docs automation: archive completed tasks, "
            "update devlog, organise docs, update/archive specs, plan new docs"
        ),
        category="workflow",
        timeout=180,
        params=[
            SkillParam(
                name="action",
                type="string",
                required=True,
                description="Action: roundup, archive, organise, plan, full",
            ),
            SkillParam(
                name="session_summary",
                type="string",
                required=False,
                default="",
                description="Summary of what was accomplished this round",
            ),
            SkillParam(
                name="next_round_plans",
                type="list",
                required=False,
                default=[],
                description="List of planned items for next round",
            ),
            SkillParam(
                name="max_age_days",
                type="integer",
                required=False,
                default=14,
                description="Days before archiving old completed tasks",
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                required=False,
                default=False,
                description="Preview without making changes",
            ),
        ],
        requires_confirmation=True,  # Mutating operation
    )

    async def run(self, **kwargs) -> dict:
        action = str(kwargs.get("action", "full")).strip().lower()
        session_summary = str(kwargs.get("session_summary", ""))
        next_round_plans = kwargs.get("next_round_plans", [])
        max_age_days = int(kwargs.get("max_age_days", 14))
        dry_run = bool(kwargs.get("dry_run", False))

        if action == "roundup" or action == "full":
            return await self._full_roundup(
                session_summary, next_round_plans, max_age_days, dry_run,
            )
        elif action == "archive":
            return self._archive_old_tasks(max_age_days, dry_run)
        elif action == "organise":
            return self._organise_docs(dry_run)
        elif action == "plan":
            return self._plan_docs(session_summary, next_round_plans)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def _full_roundup(
        self,
        session_summary: str,
        next_round_plans: list[str],
        max_age_days: int,
        dry_run: bool,
    ) -> dict:
        """Run full docs roundup: archive → organise → update devlog → plan."""
        results: dict[str, Any] = {
            "archive": None,
            "organise": None,
            "devlog_updated": False,
            "plan": None,
        }

        # Step 1: Archive old tasks
        archive_result = self._archive_old_tasks(max_age_days, dry_run)
        results["archive"] = archive_result

        # Step 2: Organise docs (remove legacy, consolidate)
        organise_result = self._organise_docs(dry_run)
        results["organise"] = organise_result

        # Step 3: Update devlog with session completion
        if not dry_run:
            self._update_devlog(session_summary)
            results["devlog_updated"] = True

        # Step 4: Generate plan for next round
        plan_result = self._plan_docs(session_summary, next_round_plans)
        results["plan"] = plan_result

        # Step 5: Write to spool
        if not dry_run:
            write_spool(
                level="INFO",
                module="docs_roundup",
                message=(
                    f"Docs roundup complete: "
                    f"archived={archive_result.get('archived', 0)} tasks, "
                    f"cleaned={organise_result.get('cleaned', 0)} files, "
                    f"planned={len(next_round_plans)} items"
                ),
                tags=["docs-roundup"],
            )

        return {
            "success": True,
            "action": "full",
            "results": results,
            "dry_run": dry_run,
        }

    def _archive_old_tasks(self, max_age_days: int, dry_run: bool) -> dict:
        """Archive completed tasks older than max_age_days from .tasker."""
        tasker_dir = DEFAULT_TASKER_DIR
        archive_dir = DEFAULT_ARCHIVE_DIR
        archived_count = 0
        archive_list: list[str] = []

        if not tasker_dir.exists():
            return {"archived": 0, "cleaned": []}

        cutoff = datetime.now(UTC) - timedelta(days=max_age_days)

        for task_file in tasker_dir.rglob("*.md"):
            if task_file.name == "README.md":
                continue
            try:
                content = task_file.read_text(encoding="utf-8")
                if "status: done" in content or "status: completed" in content:
                    mtime = datetime.fromtimestamp(task_file.stat().st_mtime, tz=UTC)
                    if mtime < cutoff:
                        relative = task_file.relative_to(tasker_dir)
                        dest = archive_dir / relative
                        archive_list.append(str(relative))
                        if not dry_run:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            if dest.exists():
                                dest.write_text(content, encoding="utf-8")
                            else:
                                shutil.copy2(str(task_file), str(dest))
                            task_file.unlink(missing_ok=True)
                        archived_count += 1
            except Exception as e:
                log.warning("Failed to archive %s: %s", task_file, e)
                continue

        return {
            "archived": archived_count,
            "files": archive_list,
            "dry_run": dry_run,
        }

    def _organise_docs(self, dry_run: bool) -> dict:
        """Organise docs directory: remove legacy, consolidate related."""
        docs_dir = DEFAULT_DOCS_DIR
        cleaned = 0
        kept = 0
        legacy_patterns = [
            r"COMPLETE.*\.md$",
            r"DONE.*\.md$",
            r"REPORT_.*\.md$",
            r"CHECKLIST.*\.md$",
            r"OLD_.*\.md$",
            r"DEPRECATED_.*\.md$",
        ]

        if not docs_dir.exists():
            return {"cleaned": 0, "kept": 0, "files": []}

        removed_files: list[str] = []
        for doc_file in docs_dir.rglob("*.md"):
            # Skip archive directory
            if "archive" in doc_file.parts:
                kept += 1
                continue
            for pattern in legacy_patterns:
                if re.search(pattern, doc_file.name, re.IGNORECASE):
                    if not dry_run:
                        # Move to archive instead of delete
                        archive_dest = docs_dir / "archive" / doc_file.relative_to(docs_dir)
                        archive_dest.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            shutil.move(str(doc_file), str(archive_dest))
                            removed_files.append(str(doc_file.relative_to(docs_dir.parent)))
                            cleaned += 1
                        except Exception as e:
                            log.warning("Failed to move %s: %s", doc_file, e)
                    else:
                        removed_files.append(str(doc_file.relative_to(docs_dir.parent)))
                        cleaned += 1
                    break
            else:
                kept += 1

        return {
            "cleaned": cleaned,
            "kept": kept,
            "files": removed_files,
            "dry_run": dry_run,
        }

    def _update_devlog(self, session_summary: str) -> None:
        """Update devlog.mcp.yaml with roundup completion entry."""
        devlog_path = DEFAULT_DEVLOG_FILE
        now = datetime.now(UTC)

        entry = (
            f"\n## Docs Roundup: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
            f"\n- type: docs_roundup"
            f"\n- timestamp: {now.isoformat()}"
        )
        if session_summary:
            entry += f"\n- summary: {session_summary}"

        existing = ""
        if devlog_path.exists():
            existing = devlog_path.read_text(encoding="utf-8")
        devlog_path.write_text(existing + entry + "\n", encoding="utf-8")

    def _plan_docs(
        self,
        session_summary: str,
        next_round_plans: list[str],
    ) -> dict:
        """Generate a docs plan for the next round."""
        # Scan for existing specs that may need updating
        docs_dir = DEFAULT_DOCS_DIR
        existing_specs: list[str] = []
        if docs_dir.exists():
            for f in sorted(docs_dir.glob("*_SPEC*.md")):
                existing_specs.append(f.name)
            for f in sorted(docs_dir.glob("*_PLAN*.md")):
                existing_specs.append(f.name)

        # Identify stale specs (no changes in 30+ days)
        stale_specs: list[str] = []
        cutoff = datetime.now() - timedelta(days=30)
        for spec_name in existing_specs:
            spec_path = docs_dir / spec_name
            if spec_path.exists():
                mtime = datetime.fromtimestamp(spec_path.stat().st_mtime)
                if mtime < cutoff:
                    stale_specs.append(spec_name)

        return {
            "session_summary": session_summary or "No summary provided",
            "next_round_plans": next_round_plans or ["TBD"],
            "existing_specs": existing_specs,
            "stale_specs": stale_specs,
            "suggestions": [
                f"Review stale specs: {', '.join(stale_specs)}"
                if stale_specs else "No stale specs found",
                f"Docs archive has {len(existing_specs)} existing specs",
                "Consider adding to docs/archive/README.md index",
            ],
        }
