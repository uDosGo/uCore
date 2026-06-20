from __future__ import annotations
from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.services.container_manager import ContainerManager

class ContainerStop(BaseSkill):
    meta = SkillMeta(id="container_stop", name="Stop Container",
        description="Stop a container by ID", category="containers", timeout=30,
        params=[SkillParam(name="container_id", type="string", required=True)])
    async def run(self, **kwargs) -> dict:
        mgr = ContainerManager()
        cid = kwargs["container_id"]
        c = mgr.get_container(cid)
        if not c: return {"success": False, "error": f"Container {cid} not found"}
        stopped = mgr.transition_state(cid, "stopped")
        return {"success": bool(stopped), "container_id": cid}
