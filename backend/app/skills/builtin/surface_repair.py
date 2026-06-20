from __future__ import annotations
from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.services.surface_manager import SurfaceManager
from app.models.surface import SurfaceState

class SurfaceRepair(BaseSkill):
    meta = SkillMeta(id="surface_repair", name="Repair Surface",
        description="Diagnose and fix surface issues",
        category="surfaces", timeout=30,
        params=[SkillParam(name="surface_id", type="string", required=True)])
    async def run(self, **kwargs) -> dict:
        mgr = SurfaceManager()
        sid = kwargs["surface_id"]
        s = mgr.get_surface(sid)
        if not s: return {"success": False, "error": f"Surface {sid} not found"}
        issues, fixes = [], []
        if s.state == SurfaceState.ERROR:
            issues.append("ERROR state")
            mgr.transition_state(sid, SurfaceState.STOPPED)
            fixes.append("Reset to STOPPED")
        if not s.name:
            issues.append("No name")
            mgr.update_surface(sid, name=f"Surface-{sid[:8]}")
            fixes.append("Assigned default name")
        return {"success": True, "surface_id": sid, "issues": issues, "fixes": fixes}
