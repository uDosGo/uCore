from __future__ import annotations
import json
from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.services.surface_manager import SurfaceManager

class ImportSurface(BaseSkill):
    meta = SkillMeta(id="import", name="Import Surface",
        description="Import a surface from JSON data",
        category="data", timeout=30,
        params=[SkillParam(name="data", type="object", required=True, description="Surface JSON data")])
    async def run(self, **kwargs) -> dict:
        mgr = SurfaceManager()
        data = kwargs["data"]
        if isinstance(data, str): data = json.loads(data)
        s = mgr.create_surface(**data)
        return {"success": bool(s), "surface": s.model_dump(mode="json") if s else None}
