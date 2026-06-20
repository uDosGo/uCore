from __future__ import annotations
from app.skills.base import BaseSkill, SkillMeta, SkillParam

class MySkill(BaseSkill):
    meta = SkillMeta(id="my_skill", name="My Skill",
        description="Description", category="general",
        params=[SkillParam(name="input", type="string", required=True)],
        timeout=30)
    async def run(self, **kwargs) -> dict:
        return {"success": True, "result": f"Processed: {kwargs.get('input')}"}
