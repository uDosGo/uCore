"""Enhancement Planner Skill — bridges ecosystem audits to actionable tasks.

Takes ecosystem audit output and skill audit reports, groups items
by enhancement area, and generates .tasker Markdown items for each gap.

Actions:
  - plan — read audit reports, generate .tasker items
  - generate — write ENHANCEMENT_PLAN.md to docs/
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.enhancement_planner")

UCORE_ROOT = Path(__file__).parent.parent.parent.parent.parent
DOCS_DIR = UCORE_ROOT / "docs"
SEEDS_DIR = UCORE_ROOT / "seeds"
TASKER_DIR = UCORE_ROOT / ".tasker"

CATEGORIES = {
    "skills": "Skills & Automation",
    "mcp_servers": "MCP Servers",
    "runtimes": "Backend Runtimes",
    "routes": "API Routes",
    "secrets": "Secrets & Config",
    "variables": "Variables",
    "paths": "File System Paths",
}


class EnhancementPlannerSkill(BaseSkill):
    """Generate .tasker items from ecosystem audit gaps."""

    meta = SkillMeta(
        id="enhancement-planner",
        name="Enhancement Planner",
        description=(
            "Bridges ecosystem audits to actionable .tasker items."
            " Reads audit reports, groups gaps by area, and generates"
            " prioritized enhancement tasks."
        ),
        category="developer",
        params=[
            SkillParam(
                name="action",
                type="string",
                description="'plan' (generate tasks) or 'generate' (write to docs)",
                required=False,
                default="plan",
            ),
            SkillParam(
                name="output",
                type="string",
                description="Output path for ENHANCEMENT_PLAN.md",
                required=False,
                default=str(DOCS_DIR / "ENHANCEMENT_PLAN.md"),
            ),
        ],
        timeout=60,
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        action = kwargs.get("action", "plan")
        output_path = kwargs.get("output", str(DOCS_DIR / "ENHANCEMENT_PLAN.md"))

        # Load audit data
        skills_audit = self._load_json("skill-audit-report.json")
        eco_assess = self._load_json("ecosystem-registry.json")

        # Generate tasks grouped by category
        tasks = self._generate_tasks(skills_audit, eco_assess)

        if action == "generate":
            md = self._render_markdown(tasks, skills_audit, eco_assess)
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(md)
            return {
                "success": True,
                "action": "generate",
                "output": str(out),
                "task_count": len(tasks),
            }

        return {
            "success": True,
            "action": "plan",
            "task_count": len(tasks),
            "tasks": tasks,
            "recommendations": self._plan_recommendations(tasks),
        }

    # ─── Data Loading ─────────────────────────────────────────────

    @staticmethod
    def _load_json(filename: str) -> dict:
        """Load a JSON report from seeds/."""
        path = SEEDS_DIR / filename
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}

    # ─── Task Generation ──────────────────────────────────────────

    def _generate_tasks(
        self, skills_audit: dict, eco_assess: dict,
    ) -> list[dict]:
        """Generate prioritized enhancement tasks from audit data."""
        tasks: list[dict] = []
        tid = 0

        tid = self._tasks_from_skills(skills_audit, tasks, tid)
        tid = self._tasks_from_ecosystem(eco_assess, tasks, tid)
        tid = self._tasks_from_services(tasks, tid)

        # Sort by priority
        priority_order = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}
        tasks.sort(key=lambda t: priority_order.get(str(t.get("priority", "p2")), 2))

        # Assign sequential IDs
        for i, t in enumerate(tasks, 1):
            t["id"] = f"task.enhance.{i:03d}"

        return tasks

    def _tasks_from_skills(
        self, audit: dict, tasks: list[dict], tid: int,
    ) -> int:
        """Generate tasks for broken/untested skills."""
        if not audit:
            return tid

        # Broken skills
        broken = [
            s for s in audit.get("skills", [])
            if s.get("execute_status") == "failed"
            or s.get("import_status") == "failed"
        ]
        for s in broken[:10]:
            tid += 1
            tasks.append({
                "id": f"task.enhance.{tid:03d}",
                "title": f"Fix broken skill: {s.get('name', 'unknown')}",
                "category": "skills",
                "priority": "p0",
                "status": "backlog",
                "description": (
                    f"Skill **{s.get('name')}** fails to "
                    f"load or execute. Error: {s.get('error', 'unknown')}"
                ),
                "tags": ["broken", "skills", "audit"],
            })

        # Untested skills
        untested = [
            s for s in audit.get("skills", [])
            if s.get("execute_status") not in ("success", "failed")
            and s.get("import_status") != "failed"
        ]
        for s in untested[:15]:
            tid += 1
            tasks.append({
                "id": f"task.enhance.{tid:03d}",
                "title": f"Smoke-test skill: {s.get('name', 'unknown')}",
                "category": "skills",
                "priority": "p1",
                "status": "backlog",
                "description": (
                    f"Skill **{s.get('name')}** has never been verified."
                    " Run with dry_run=True and confirm it executes."
                ),
                "tags": ["untested", "skills", "audit"],
            })

        # Skills without BaseSkill subclass
        no_base = [
            s for s in audit.get("skills", [])
            if not s.get("is_base_skill") and s.get("has_module_run")
        ]
        for s in no_base[:10]:
            tid += 1
            tasks.append({
                "id": f"task.enhance.{tid:03d}",
                "title": f"Convert to BaseSkill: {s.get('name', 'unknown')}",
                "category": "skills",
                "priority": "p2",
                "status": "backlog",
                "description": (
                    f"**{s.get('name')}** uses module-level run()."
                    " Convert to BaseSkill subclass for registry integration."
                ),
                "tags": ["refactor", "skills", "base-skill"],
            })

        return tid

    def _tasks_from_ecosystem(
        self, assess: dict, tasks: list[dict], tid: int,
    ) -> int:
        """Generate tasks from ecosystem assess report."""
        eco = assess.get("ecosystem", {})
        health = assess.get("health", {})

        # Broken ecosystem items
        for cat_key, cat_label in CATEGORIES.items():
            items = eco.get(cat_key, [])
            if not isinstance(items, list):
                items = items.get("items", []) if isinstance(items, dict) else []

            for item in items:
                if isinstance(item, dict) and item.get("health") == "broken":
                    tid += 1
                    name = item.get("name", item.get("key", item.get("path", "unknown")))
                    tasks.append({
                        "id": f"task.enhance.{tid:03d}",
                        "title": f"Fix broken {cat_label[:-1]}: {name}",
                        "category": cat_key,
                        "priority": "p0",
                        "status": "backlog",
                        "description": (
                            f"**{name}** in {cat_label} is marked broken."
                            f" Issues: {item.get('issues', [])}"
                        ),
                        "tags": ["broken", cat_key, "ecosystem"],
                    })

        # Orphaned items
        for cat_key in ["skills", "mcp_servers", "runtimes"]:
            items = eco.get(cat_key, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and item.get("health") == "orphaned":
                    tid += 1
                    name = item.get("name", "unknown")
                    tasks.append({
                        "id": f"task.enhance.{tid:03d}",
                        "title": f"Review orphaned {cat_key[:-1]}: {name}",
                        "category": cat_key,
                        "priority": "p2",
                        "status": "backlog",
                        "description": (
                            f"**{name}** is orphaned — no references found."
                            " Consider archiving or re-wiring."
                        ),
                        "tags": ["orphaned", cat_key, "ecosystem"],
                    })

        # High untested count
        if health.get("untested", 0) > 10:
            tid += 1
            tasks.append({
                "id": f"task.enhance.{tid:03d}",
                "title": "Smoke-test untested ecosystem items",
                "category": "ecosystem",
                "priority": "p1",
                "status": "backlog",
                "description": (
                    f"{health['untested']} ecosystem items are untested."
                    " Run ecosystem-audit assess and smoke-test each."
                ),
                "tags": ["untested", "ecosystem"],
            })

        return tid

    def _tasks_from_services(
        self, tasks: list[dict], tid: int,
    ) -> int:
        """Generate tasks for service health."""
        # General recommendations
        tid += 1
        tasks.append({
            "id": f"task.enhance.{tid:03d}",
            "title": "Run ucore-index health-report weekly",
            "category": "ecosystem",
            "priority": "p2",
            "status": "backlog",
            "description": (
                "Schedule a weekly ucore-index health-report to track"
                " ecosystem health over time. Add to maintenance scheduler."
            ),
            "tags": ["monitoring", "health", "scheduled"],
        })

        tid += 1
        tasks.append({
            "id": f"task.enhance.{tid:03d}",
            "title": "Integrate GH Actions for CI health checks",
            "category": "runtimes",
            "priority": "p2",
            "status": "backlog",
            "description": (
                "Add a GitHub Action that runs ucore-index health-report"
                " on push and alerts on degraded/critical status."
            ),
            "tags": ["ci", "health", "github"],
        })

        return tid

    # ─── Markdown Rendering ───────────────────────────────────────

    def _render_markdown(
        self, tasks: list[dict], skills_audit: dict, eco_assess: dict,
    ) -> str:
        """Render ENHANCEMENT_PLAN.md."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        health = eco_assess.get("health", {})

        lines = [
            "# uCore Enhancement Plan",
            f"**Generated:** {now}",
            f"**Source:** ecosystem-audit assess + skill-audit",
            "",
            "## Ecosystem Health Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Items | {health.get('total_items', '—')} |",
            f"| Working | {health.get('working', '—')} |",
            f"| Untested | {health.get('untested', '—')} |",
            f"| Broken | {health.get('broken', '—')} |",
            f"| Health % | {health.get('health_pct', '—')}% |",
            "",
            "## Skill Health Summary",
            "",
        ]

        if skills_audit:
            lines += [
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Total Skills | {skills_audit.get('total_skills', '—')} |",
                f"| Working | {skills_audit.get('working', '—')} |",
                f"| Untested | {skills_audit.get('untested', '—')} |",
                f"| Broken | {skills_audit.get('broken', '—')} |",
                f"| Health % | {skills_audit.get('health_pct', '—')}% |",
                "",
            ]

        lines += [
            "## Prioritized Tasks",
            "",
            f"**Total:** {len(tasks)} tasks generated from audit gaps.",
            "",
        ]

        # Group by priority
        for prio_label, prio_key in [
            ("### P0 — Critical (Fix Broken)", "p0"),
            ("### P1 — High (Smoke-Test)", "p1"),
            ("### P2 — Medium (Improve)", "p2"),
            ("### P3 — Low (Nice-to-Have)", "p3"),
        ]:
            prio_tasks = [t for t in tasks if t.get("priority") == prio_key]
            if not prio_tasks:
                continue
            lines.append(prio_label)
            lines.append("")
            for t in prio_tasks:
                lines.append(
                    f"- [ ] **{t['id']}** — {t['title']} "
                    f"(`{t.get('category', '')}`)"
                )
                lines.append(f"  {t.get('description', '')}")
                tags = t.get("tags", [])
                if tags:
                    lines.append(f"  Tags: {', '.join('`' + tag + '`' for tag in tags)}")
                lines.append("")
            lines.append("")

        lines += [
            "## How to Use This Plan",
            "",
            "1. Import tasks into .tasker: `tasker ingest --from ENHANCEMENT_PLAN.md`",
            "2. Assign tasks to agents using kanban",
            "3. Run `dev-mode-executor` with task UIDs to auto-execute",
            "4. Re-run `ecosystem-audit assess` weekly to track progress",
            "",
            "## Regenerate",
            "",
            "To regenerate this plan after fixing items:",
            "```bash",
            "curl -X POST http://localhost:8484/api/skills/enhancement-planner/run \\",
            '  -H "Content-Type: application/json" \\',
            '  -d \'{"action": "generate"}\'',
            "```",
            "",
        ]

        return "\n".join(lines) + "\n"

    # ─── Recommendations ──────────────────────────────────────────

    @staticmethod
    def _plan_recommendations(tasks: list[dict]) -> list[str]:
        """Generate top-level recommendations from the plan."""
        p0 = sum(1 for t in tasks if t.get("priority") == "p0")
        p1 = sum(1 for t in tasks if t.get("priority") == "p1")
        p2 = sum(1 for t in tasks if t.get("priority") == "p2")

        recs = []
        if p0 > 0:
            recs.append(
                f"Address {p0} critical (P0) tasks first — "
                "these are broken items blocking functionality"
            )
        if p1 > 0:
            recs.append(
                f"Complete {p1} high-priority (P1) tasks — "
                "smoke-testing untested items"
            )
        if p2 > 0:
            recs.append(
                f"Schedule {p2} medium-priority (P2) tasks — "
                "conversions and improvements"
            )
        if not recs:
            recs.append("No enhancement tasks needed — ecosystem is healthy")
        return recs