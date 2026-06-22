"""brain_sync — Synthesize recent project memory into wisdom.md.

Builds a lightweight local "Brain" layer by reviewing recent project files,
spool logs, and AppFlowy activity, then refreshing wisdom.md with durable
lessons, recent change summaries, and spool activity analysis.

Usage:
  POST /api/skills/brain_sync/run
    Body: {
        "hours": 24,
        "limit": 12,
        "include_spool": true,
        "include_appflowy": true,
        "include_test_failures": true
    }
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree

from app.core.settings import settings

from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.services.episodic_store import summarize_entries as summarize_episodic
from app.services.spool_reader import read_spool, summarize_spool

PROJECT_ROOT = settings.udos_root / "uCore"
WISDOM_PATH = PROJECT_ROOT / "wisdom.md"
DEFAULT_SCAN_DIRS = ("backend", "docs", "frontend", "scripts", ".tasker")
TEST_REPORT_PATTERNS = (
    "**/junit*.xml",
    "**/pytest*.xml",
    "**/test-results*.xml",
)
PYTEST_CACHE_FILES: tuple[Path, ...] = (
    PROJECT_ROOT / ".pytest_cache" / "v" / "cache" / "lastfailed",
    PROJECT_ROOT / "backend" / ".pytest_cache" / "v" / "cache" / "lastfailed",
)


class BrainSync(BaseSkill):
    meta = SkillMeta(
        id="brain_sync",
        name="Brain Sync",
        description=(
            "Synthesize recent project changes, spool activity, and "
            "AppFlowy events into wisdom.md"
        ),
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
            SkillParam(
                name="include_test_failures",
                type="boolean",
                required=False,
                default=True,
                description="Include recent test failure signals in wisdom.md",
            ),
            SkillParam(
                name="include_episodic",
                type="boolean",
                required=False,
                default=True,
                description=(
                    "Include recent episodic log entries in wisdom.md"
                ),
            ),
        ],
    )

    async def run(self, **kwargs) -> dict:
        hours = max(1, int(kwargs.get("hours", 24)))
        limit = max(1, int(kwargs.get("limit", 12)))
        include_spool = bool(kwargs.get("include_spool", True))
        include_appflowy = bool(kwargs.get("include_appflowy", True))
        include_test_failures = bool(kwargs.get("include_test_failures", True))
        include_episodic = bool(kwargs.get("include_episodic", True))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        recent_files = self._collect_recent_files(cutoff=cutoff, limit=limit)
        existing_sections = self._load_existing_sections()
        spool_summary = summarize_spool(hours=hours) if include_spool else None
        appflowy_summary = (
            self._get_appflowy_activity(hours=hours)
            if include_appflowy
            else None
        )
        test_failures = (
            self._collect_test_failures(cutoff=cutoff, limit=10)
            if include_test_failures
            else []
        )
        episodic_summary = (
            summarize_episodic(hours=hours)
            if include_episodic
            else None
        )

        refreshed = self._render_wisdom(
            recent_files=recent_files,
            existing_sections=existing_sections,
            spool_summary=spool_summary,
            appflowy_summary=appflowy_summary,
            test_failures=test_failures,
            episodic_summary=episodic_summary,
            hours=hours,
        )
        WISDOM_PATH.write_text(refreshed, encoding="utf-8")

        return {
            "success": True,
            "hours": hours,
            "limit": limit,
            "include_spool": include_spool,
            "include_appflowy": include_appflowy,
            "include_test_failures": include_test_failures,
            "wisdom_path": str(WISDOM_PATH),
            "recent_files": [
                str(path.relative_to(PROJECT_ROOT))
                for path in recent_files
            ],
            "count": len(recent_files),
            "spool_included": spool_summary is not None,
            "appflowy_included": appflowy_summary is not None,
            "test_failures_included": bool(test_failures),
            "test_failure_count": len(test_failures),
            "episodic_included": episodic_summary is not None,
        }

    def _collect_recent_files(
        self,
        cutoff: datetime,
        limit: int,
    ) -> list[Path]:
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
                modified = datetime.fromtimestamp(
                    path.stat().st_mtime,
                    tz=timezone.utc,
                )
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

    def _get_appflowy_activity(self, *, hours: int) -> str | None:
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
                    "WHERE updated_at >= datetime('now', ?) "
                    "GROUP BY name ORDER BY updates DESC LIMIT 10",
                params=[f"-{hours} hours"],
                write=False,
            )
            rows = result.get("rows", [])
            if not rows:
                return f"No AppFlowy activity in the last {hours}h."
            lines = [
                f"- {row.get('name', 'unknown')}: "
                f"{row.get('updates', 0)} updates"
                for row in rows
            ]
            return "\n".join(lines)
        except Exception:
            return None

    def _collect_test_failures(
        self,
        *,
        cutoff: datetime,
        limit: int,
    ) -> list[str]:
        items: list[str] = []
        seen: set[str] = set()

        def _push(prefix: str, detail: str) -> None:
            normalized = f"{prefix}: {detail.strip()}"
            if not detail.strip() or normalized in seen:
                return
            seen.add(normalized)
            items.append(normalized)

        for cache_path in PYTEST_CACHE_FILES:
            if not cache_path.exists():
                continue
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            for node_id, failed in payload.items():
                if bool(failed):
                    _push("pytest-cache", str(node_id))

        for pattern in TEST_REPORT_PATTERNS:
            for report in PROJECT_ROOT.glob(pattern):
                if not report.is_file():
                    continue
                modified = datetime.fromtimestamp(
                    report.stat().st_mtime,
                    tz=timezone.utc,
                )
                if modified < cutoff:
                    continue
                try:
                    root = ElementTree.parse(report).getroot()
                except Exception:
                    continue
                for case in root.iter("testcase"):
                    failure = case.find("failure")
                    error = case.find("error")
                    node = failure or error
                    if node is None:
                        continue
                    class_name = case.attrib.get("classname", "").strip()
                    case_name = case.attrib.get("name", "unknown").strip()
                    test_id = (
                        f"{class_name}::{case_name}"
                        if class_name
                        else case_name
                    )
                    message = (
                        (node.attrib.get("message") or (node.text or ""))
                        .strip()
                        .replace("\n", " ")
                    )
                    if message:
                        detail = f"{test_id} - {message[:140]}"
                    else:
                        detail = test_id
                    _push(f"junit:{report.name}", detail)

        spool_since = cutoff.isoformat()
        spool_entries = read_spool(
            max_entries=500,
            since=spool_since,
            search="pytest",
        )
        for entry in spool_entries:
            msg = entry.message.strip().lower()
            if (
                entry.is_error
                or "failed" in msg
                or "traceback" in msg
                or "assert" in msg
            ):
                _push(f"spool:{entry.module}", entry.message[:180])

        return items[:limit]

    def _render_wisdom(
        self,
        *,
        recent_files: list[Path],
        existing_sections: list[str],
        spool_summary: str | None = None,
        appflowy_summary: str | None = None,
        test_failures: list[str] | None = None,
        episodic_summary: str | None = None,
        hours: int = 24,
    ) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        recent_lines = [
            f"- {path.relative_to(PROJECT_ROOT)}" for path in recent_files
        ] or ["- No files changed in the selected window."]
        durable = existing_sections or [
            "- Keep one canonical implementation path per subsystem.",
            "- Favor local-first operation and explicit documented "
            "orchestration.",
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
            "## Synthesis Inputs",
            f"- Window: last {hours}h",
            "- Spool summary: "
            f"{'included' if spool_summary else 'not included'}",
            "- AppFlowy activity: "
            f"{'included' if appflowy_summary else 'not included'}",
            f"- Test failures: {len(test_failures or [])} signals",
            "- Episodic log: "
            f"{'included' if episodic_summary else 'not included'}",
            "",
            "## Next Synthesis Targets",
            "- Migration checklist status and canonical doc destinations.",
            "- Snackbar/system orchestration refinements and tray workflows.",
            "- UI view wiring across frontend surfaces and system pages.",
            "- DocLang-style structured export for AI-efficient "
            "document context.",
        ]

        if spool_summary:
            parts.extend(["", spool_summary])

        if appflowy_summary:
            parts.extend([
                "",
                f"## AppFlowy Activity (last {hours}h)",
                "",
                appflowy_summary,
            ])

        if test_failures:
            parts.extend([
                "",
                f"## Test Failure Signals (last {hours}h)",
                "",
            ])
            parts.extend([f"- {item}" for item in test_failures])

        if episodic_summary:
            parts.extend(["", episodic_summary])

        parts.append("")
        return "\n".join(parts)
