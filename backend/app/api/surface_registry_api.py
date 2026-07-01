"""Surface Registry REST API endpoints.

GET  /api/surfaces/discover  — scan all surfaces
GET  /api/surfaces/validate  — validate all/single surface
POST /api/surfaces/scaffold  — generate a new surface
POST /api/surfaces/repair    — auto-fix registration gaps
POST /api/surfaces/wire      — link surface to backend runtime
GET  /api/surfaces/report    — full ecosystem health report
"""
from __future__ import annotations

import logging

from app.skills.builtin.skill_surface_registry import (
    SurfaceRegistrySkill,
)

log = logging.getLogger("ucore.api.surface_registry")

_skill: SurfaceRegistrySkill | None = None


def _registry() -> SurfaceRegistrySkill:
    global _skill
    if _skill is None:
        _skill = SurfaceRegistrySkill()
    return _skill


def register_surface_routes(app):
    """Register all surface registry routes."""

    @app.get("/api/surfaces/discover")
    async def handle_discover():
        return await _registry().run(action="discover")

    @app.get("/api/surfaces/validate")
    async def handle_validate(target: str = ""):
        return await _registry().run(action="validate", target=target)

    @app.post("/api/surfaces/scaffold")
    async def handle_scaffold(data: dict):
        name = data.get("name", "")
        if not name:
            return {"success": False, "error": "name required"}
        return await _registry().run(action="scaffold", target=name)

    @app.post("/api/surfaces/repair")
    async def handle_repair(data: dict):
        target = data.get("target", "")
        dry_run = data.get("dry_run", False)
        return await _registry().run(
            action="repair", target=target, dry_run=dry_run,
        )

    @app.post("/api/surfaces/wire")
    async def handle_wire(data: dict):
        target = data.get("target", "")
        backend_runtime = data.get("backend_runtime", "")
        return await _registry().run(
            action="wire",
            target=target,
            backend_runtime=backend_runtime,
        )

    @app.get("/api/surfaces/report")
    async def handle_report():
        return await _registry().run(action="report")

    log.info("Surface registry routes registered")