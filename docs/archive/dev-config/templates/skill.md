"""Skill Template — {skill_name}

{Description of what this skill does.}

Usage:
  POST /api/skills/{skill_id}/run
    Body: {{
        "param1": "value1"
    }}
"""
from __future__ import annotations

from pathlib import Path

from app.core.settings import settings
from app.skills.base import BaseSkill, SkillMeta, SkillParam

PROJECT_ROOT = settings.udos_root / "uCore"


class {SkillName}(BaseSkill):
    meta = SkillMeta(
        id="{skill_id}",
        name="{Skill Name}",
        description="{Brief description}",
        category="maintenance",
        timeout=60,
        params=[
            SkillParam(
                name="param1",
                type="string",
                required=False,
                default="default_value",
                description="Parameter description",
            ),
        ],
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        # Implementation here
        return {
            "success": True,
            "message": "Skill executed successfully",
        }