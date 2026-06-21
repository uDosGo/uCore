"""brain_sync — Synthesize recent project memory into wisdom.md.

Builds a lightweight local "Brain" layer by reviewing recent project files,
spool logs, and AppFlowy activity, then refreshing wisdom.md with durable
lessons, recent change summaries, and spool activity analysis.

Usage:
  POST /api/skills/brain_sync/run
  Body: { "hours": 24, "limit": 12, "include_spool": true, "include_appflowy": true }
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from app.core.settings import settings

from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.services.spool_reader import summarize_spool

PROJECT_ROOT = settings.udos_root / "uCore"
WISDOM_PATH = PROJECT_ROOT / "wisdom.md"
DEFAULT_SCAN_DIRS = ("backend", "docs", "frontend", "scripts", ".tasker")


class BrainSync(BaseSkill):
    meta = SkillMeta(
        id="brain_sync",
        name="Brain Sync",
        description="Synthesize recent project changes, spool activity, and AppFlowy events into wisdom.md",
        category="assist",
        timeout=30,
        params=[
            SkillParam(
                name="hours",
                type="integer",
                required=False,
                default=24,
                description="How many recent hours to scan for changes",
            ),
            SkillParam(
                name="limit",
                type="integer",
                required=False,
                default=12,
                description="Maximum number of recent files to summarize",
            ),
            SkillParam(
                name="include_spool",
                type="boolean",
                required=False,
                default=True,
                description="Include spool activity summary in wisdom.md",
            ),
            SkillParam(
                name="include_appflowy",
                type="boolean",
                required=False,
                default=True,
                description="Include AppFlowy activity summary in wisdom.md",
            ),
        ],
    )

    async def run(self, **kwargs) -> dict:
        hours = max(1, int(kwargs.get("hours", 24)))
        limit = max(1, int(kwargs.get("limit", 12)))
        include_spool = bool(kwargs.get("include_spool", True))
        include_appflowy = bool(kwargs.get("include_appflowy", True))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        recent_files = self._collect_recent_files(cutoff=cutoff, limit=limit)
        existing_sections = self._load_existing_sections()
        spool_summary = summarize_spool(hours=hours) if include_spool else None
        appflowy_summary = self._get_appflowy_activity() if include_appflowy else None

        refreshed = self._render_wisdom(
            recent_files=recent_files,
            existing_sections=existing_sections,
            spool_summary=spool_summary,
            appflowy_summary=appflowy_summary,
        )
        WISDOM_PATH.write_text(refreshed, encoding="utf-8")

        return {
            "success": True,
            "hours": hours,
            "limit": limit,
            "include_spool": include_spool,
            "include_appflowy": include_appflowy,
            "wisdom_path": str(WISDOM_PATH),
            "recent_files": [str(path.relative_to(PROJECT_ROOT)) for path in recent_files],
            "count": len(recent_files),
            "spool_included": spool_summary is not None,
            "appflowy_included": appflowy_summary is not None,
        }

    def _collect_recent_files(self, cutoff: datetime, limit: int) -> list[Path]:
        matches: list[tuple[float, Path]] = []
        for name in DEFAULT_SCAN_DIRS:
            base = PROJECT_ROOT / name
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                if path.name.startswith("."):
                    continue
                if "/__pycache__/" in str(path):
                    continue
                if path.suffix in {".pyc", ".log"}:
                    continue
                modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                if modified >= cutoff:
                    matches.append((path.stat().st_mtime, path))
        matches.sort(key=lambda item: item[0], reverse=True)
        return [path for _, path in matches[:limit]]

    def _load_existing_sections(self) -> list[str]:
        if not WISDOM_PATH.exists():
            return []
        lines = WISDOM_PATH.read_text(encoding="utf-8").splitlines()
        durable: list[str] = []
        in_durable = False
        for line in lines:
            if line.strip() == "## Durable Lessons":
                in_durable = True
                continue
            if line.startswith("## ") and line.strip() != "## Durable Lessons":
                in_durable = False
            if in_durable and line.strip().startswith("- "):
                durable.append(line.strip())
        return durable

    def _get_appflowy_activity(self) -> str | None:
        """Check AppFlowy local DB for recent activity."""
        try:
            from app.knowledge.local_first import discover_databases, run_query

            dbs = discover_databases()
            db_path = dbs.get("database")
            if not db_path:
                return None

            result = run_query(
                db_path=db_path,
                sql="SELECT name, COUNT(*) as updates FROM row_table "
                    "WHERE updated_at >= datetime('now', '-1 day') "
                    "GROUP BY name ORDER BY updates DESC LIMIT 10",
                params=[],
                write=False,
            )
            rows = result.get("rows", [])
            if not rows:
                return "No AppFlowy activity in the last 24h."
            lines = [f"- {row.get('name', 'unknown')}: {row.get('updates', 0)} updates" for row in rows]
            return "\n".join(lines)
        except Exception:
            return None

    def _render_wisdom(
        self,
        *,
        recent_files: list[Path],
        existing_sections: list[str],
        spool_summary: str | None = None,
        appflowy_summary: str | None = None,
    ) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        recent_lines = [
            f"- {path.relative_to(PROJECT_ROOT)}" for path in recent_files
        ] or ["- No files changed in the selected window."]
        durable = existing_sections or [
            "- Keep one canonical implementation path per subsystem.",
            "- Favor local-first operation and explicit documented orchestration.",
        ]

        parts = [
            "# uCore Wisdom",
            "",
            f"Date: {now}",
            "Status: Refreshed by brain_sync",
            "",
            "## Durable Lessons",
            *durable,
            "",
            "## Recent Change Scan",
            *recent_lines,
            "",
            "## Memory Architecture",
            "- Short-term: active AI/chat session context.",
            "- Long-term: AppFlowy, vault, and canonical docs.",
            "- Episodic: wisdom.md, spool logs, and recent change summaries.",
            "",
            "## Next Synthesis Targets",
            "- Migration checklist status and canonical doc destinations.",
            "- Snackbar/system orchestration refinements and tray workflows.",
            "- UI view wiring across frontend surfaces and system pages.",
            "- DocLang-style structured export for AI-efficient document context.",
        ]

        if spool_summary:
            parts.extend(["", spool_summary])

        if appflowy_summary:
            parts.extend([
                "",
                "## AppFlowy Activity (last 24h)",
                "",
                appflowy_summary,
            ])

        parts.append("")
        return "\n".join(parts)
