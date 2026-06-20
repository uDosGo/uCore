from __future__ import annotations
from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.services.surface_manager import SurfaceManager
from app.models.surface import SurfaceState

class SurfaceRestart(BaseSkill):
    meta = SkillMeta(id="surface_restart", name="Restart Surface",
        description="Stop then start a surface by ID",
        category="surfaces", timeout=30,
        params=[SkillParam(name="surface_id", type="string", required=True)])
    async def run(self, **kwargs) -> dict:
        mgr = SurfaceManager()
        sid = kwargs["surface_id"]
        s = mgr.get_surface(sid)
        if not s: return {"success": False, "error": f"Surface {sid} not found"}
        mgr.transition_state(sid, SurfaceState.STOPPED)
        import asyncio; await asyncio.sleep(0.3)
        mgr.transition_state(sid, SurfaceState.RUNNING)
        return {"success": True, "surface_id": sid, "state": "restarted"}
