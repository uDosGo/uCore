"""Diagnostics and self-healing skills routes."""
from __future__ import annotations

import json

from aiohttp import web


async def diagnostics_handler(request: web.Request) -> web.Response:
    """GET /api/diagnostics — system diagnostics."""
    try:
        from app.services.process_manager import get_process_manager

        pm = get_process_manager()
        diag = pm.get_system_diagnostics()
        diag_str = json.dumps(diag, default=str)
        return web.Response(
            text=diag_str, content_type="application/json",
        )
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def ports_handler(request: web.Request) -> web.Response:
    """GET /api/diagnostics/ports — port conflict report."""
    try:
        from app.services.process_manager import get_process_manager

        pm = get_process_manager()
        report = pm.get_port_conflict_report()
        return web.json_response(report)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def skills_handler(request: web.Request) -> web.Response:
    """GET /api/skills — list available skills."""
    try:
        from app.skills.self_heal import list_skills

        skills = list_skills()
        return web.json_response({"skills": skills})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def execute_skill_handler(request: web.Request) -> web.Response:
    """POST /api/skills/{skill_name} — execute a skill."""
    try:
        skill_name = request.match_info.get("skill_name", "").lower()

        kwargs = {}
        if request.can_read_body:
            try:
                body = await request.json()
                kwargs = body.get("params", {})
            except Exception:
                pass

        from app.skills.self_heal import execute_skill

        result = await execute_skill(skill_name, **kwargs)

        status_code = 200 if result.success else 400
        return web.json_response(
            {
                "skill": result.skill,
                "success": result.success,
                "message": result.message,
                "details": result.details,
                "timestamp": result.timestamp,
            },
            status=status_code,
        )
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def register(app: web.Application) -> None:
    app.router.add_get("/api/diagnostics", diagnostics_handler)
    app.router.add_get("/api/diagnostics/ports", ports_handler)
    app.router.add_get("/api/skills", skills_handler)
    app.router.add_post(
        "/api/skills/{skill_name}", execute_skill_handler,
    )