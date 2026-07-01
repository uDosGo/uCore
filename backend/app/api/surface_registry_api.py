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

from aiohttp import web

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
    """Register all surface registry routes.

    Note: This module was originally written for FastAPI-style decorators.
    It has been adapted for aiohttp's web.Application route registration.
    """

    async def handle_discover(request):
        result = await _registry().run(action="discover")
        return web.json_response(result)

    async def handle_validate(request):
        target = request.query.get("target", "")
        result = await _registry().run(action="validate", target=target)
        return web.json_response(result)

    async def handle_scaffold(request):
        data = await request.json() if request.can_read_body else {}
        name = data.get("name", "")
        if not name:
            return web.json_response(
                {"success": False, "error": "name required"}, status=400,
            )
        result = await _registry().run(action="scaffold", target=name)
        return web.json_response(result)

    async def handle_repair(request):
        data = await request.json() if request.can_read_body else {}
        target = data.get("target", "")
        dry_run = data.get("dry_run", False)
        result = await _registry().run(
            action="repair", target=target, dry_run=dry_run,
        )
        return web.json_response(result)

    async def handle_wire(request):
        data = await request.json() if request.can_read_body else {}
        target = data.get("target", "")
        backend_runtime = data.get("backend_runtime", "")
        result = await _registry().run(
            action="wire",
            target=target,
            backend_runtime=backend_runtime,
        )
        return web.json_response(result)

    async def handle_report(request):
        result = await _registry().run(action="report")
        return web.json_response(result)

    app.router.add_get("/api/surfaces/discover", handle_discover)
    app.router.add_get("/api/surfaces/validate", handle_validate)
    app.router.add_post("/api/surfaces/scaffold", handle_scaffold)
    app.router.add_post("/api/surfaces/repair", handle_repair)
    app.router.add_post("/api/surfaces/wire", handle_wire)
    app.router.add_get("/api/surfaces/report", handle_report)

    log.info("Surface registry routes registered")