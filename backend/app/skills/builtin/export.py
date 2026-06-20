from __future__ import annotations
from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.services.surface_manager import SurfaceManager

class ExportSurface(BaseSkill):
    meta = SkillMeta(id="export", name="Export Surface",
        description="Export surface data as JSON",
        category="data", timeout=30,
        params=[SkillParam(name="surface_id", type="string", required=True)])
    async def run(self, **kwargs) -> dict:
        mgr = SurfaceManager()
        sid = kwargs["surface_id"]
        s = mgr.get_surface(sid)
        if not s: return {"success": False, "error": f"Surface {sid} not found"}
        return {"success": True, "surface_id": sid, "data": s.model_dump(mode="json")}
