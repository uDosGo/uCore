"""episodic_log — Append a correction, lesson, or decision to the log.

Writes a single structured entry to the durable episodic log used by
brain_sync synthesis and the correction history runbook.

Usage:
  POST /api/skills/episodic_log/run
  Body: {
    "type": "correction",
    "description": "Fixed missing settings import in attach_context",
    "context": "Surfaced by test_skills_memory.py",
    "severity": "medium",
    "tags": ["python", "import"]
  }
"""
from __future__ import annotations

from app.services.episodic_store import (
    ENTRY_TYPES,
    SEVERITIES,
    append_entry,
)
from app.skills.base import BaseSkill, SkillMeta, SkillParam


class EpisodicLog(BaseSkill):
    meta = SkillMeta(
        id="episodic_log",
        name="Episodic Log",
        description=(
            "Append a correction, lesson, or decision to the "
            "durable episodic log"
        ),
        category="memory",
        timeout=10,
        params=[
            SkillParam(
                name="type",
                type="string",
                required=True,
                description=(
                    f"Entry type: {', '.join(sorted(ENTRY_TYPES))}"
                ),
            ),
            SkillParam(
                name="description",
                type="string",
                required=True,
                description=(
                    "Short description of what happened or was learned"
                ),
            ),
            SkillParam(
                name="context",
                type="string",
                required=False,
                default="",
                description="Optional supporting context or cause",
            ),
            SkillParam(
                name="severity",
                type="string",
                required=False,
                default="low",
                description=(
                    f"Importance level: {', '.join(sorted(SEVERITIES))}"
                ),
            ),
            SkillParam(
                name="tags",
                type="string",
                required=False,
                default="",
                description=(
                    "Comma-separated topic tags (or pass as a list)"
                ),
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        entry_type = str(kwargs.get("type", "")).strip()
        description = str(kwargs.get("description", "")).strip()
        if not entry_type:
            return {
                "success": False,
                "error": "type is required",
            }
        if not description:
            return {
                "success": False,
                "error": "description is required",
            }

        context = str(kwargs.get("context", "")).strip()
        severity = str(kwargs.get("severity", "low")).strip()

        raw_tags = kwargs.get("tags") or []
        if isinstance(raw_tags, str):
            raw_tags = [t.strip() for t in raw_tags.split(",")]
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]

        try:
            entry = append_entry(
                entry_type=entry_type,
                description=description,
                context=context,
                severity=severity,
                tags=tags,
                source="skill",
            )
        except ValueError as exc:
            return {"success": False, "error": str(exc)}

        return {"success": True, "entry": entry}
