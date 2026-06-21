"""brain_sync — Synthesize recent project memory into wisdom.md.

Builds a lightweight local "Brain" layer by reviewing recent project files and
refreshing a compact wisdom document that can later be injected into agent
context alongside CONTEXT.md.

Usage:
  POST /api/skills/brain_sync/run
  Body: { "hours": 24, "limit": 12 }
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

PROJECT_ROOT = Path.home() / "Code/uCore"
WISDOM_PATH = PROJECT_ROOT / "wisdom.md"
DEFAULT_SCAN_DIRS = ("backend", "docs", "frontend", "scripts")


class BrainSync(BaseSkill):
    meta = SkillMeta(
        id="brain_sync",
        name="Brain Sync",
        description="Synthesize recent project changes into wisdom.md",
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
        ],
    )

    async def run(self, **kwargs) -> dict:
        hours = max(1, int(kwargs.get("hours", 24)))
        limit = max(1, int(kwargs.get("limit", 12)))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        recent_files = self._collect_recent_files(cutoff=cutoff, limit=limit)
        existing_sections = self._load_existing_sections()
        refreshed = self._render_wisdom(recent_files=recent_files, existing_sections=existing_sections)
        WISDOM_PATH.write_text(refreshed, encoding="utf-8")

        return {
            "success": True,
            "hours": hours,
            "limit": limit,
            "wisdom_path": str(WISDOM_PATH),
            "recent_files": [str(path.relative_to(PROJECT_ROOT)) for path in recent_files],
            "count": len(recent_files),
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

    def _render_wisdom(self, *, recent_files: list[Path], existing_sections: list[str]) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        recent_lines = [
            f"- {path.relative_to(PROJECT_ROOT)}" for path in recent_files
        ] or ["- No files changed in the selected window."]
        durable = existing_sections or [
            "- Keep one canonical implementation path per subsystem.",
            "- Favor local-first operation and explicit documented orchestration.",
        ]

        return "\n".join(
            [
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
                "",
            ]
        )
