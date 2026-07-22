"""Template API — Slate template management endpoints.

GET  /api/templates/list      — list all templates across all tiers
POST /api/templates/scaffold  — scaffold a project from a template
GET  /api/templates/{tid}     — get a single template manifest
"""
from __future__ import annotations

import logging

from aiohttp import web

log = logging.getLogger("ucore.api.templates")


def _get_manager() -> "TemplateManager":  # noqa: F821
    from app.services.template_manager import get_template_manager
    return get_template_manager()


async def handle_list_templates(request: web.Request) -> web.Response:
    """GET /api/templates/list"""
    try:
        tm = _get_manager()
        templates = tm.list_templates()
        return web.json_response({
            "templates": [t.to_dict() if hasattr(t, "to_dict") else t
                          for t in templates],
            "count": len(templates),
        })
    except Exception as exc:
        log.error("Template list failed: %s", exc)
        return web.json_response(
            {"error": str(exc)}, status=500,
        )


async def handle_get_template(request: web.Request) -> web.Response:
    """GET /api/templates/{template_id}"""
    template_id = request.match_info.get("template_id", "")
    if not template_id:
        return web.json_response(
            {"error": "template_id is required"}, status=400,
        )
    try:
        tm = _get_manager()
        t = tm.find_template(template_id)
        if t is None:
            return web.json_response(
                {"error": f"Template '{template_id}' not found"},
                status=404,
            )
        return web.json_response(t.to_dict() if hasattr(t, "to_dict") else t)
    except Exception as exc:
        log.error("Get template failed: %s", exc)
        return web.json_response(
            {"error": str(exc)}, status=500,
        )


async def handle_scaffold_template(request: web.Request) -> web.Response:
    """POST /api/templates/scaffold"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON body"}, status=400,
        )

    template_id = body.get("template_id", "").strip()
    target_dir = body.get("target_dir", "").strip()
    if not template_id or not target_dir:
        return web.json_response(
            {"error": "template_id and target_dir are required"},
            status=400,
        )

    try:
        tm = _get_manager()
        result = tm.scaffold_from_template(template_id, target_dir)
        return web.json_response({
            "success": True,
            "template_id": template_id,
            "target_dir": target_dir,
            "result": str(result) if result else "Scaffolded successfully",
        })
    except FileNotFoundError:
        return web.json_response(
            {"error": f"Template '{template_id}' not found"},
            status=404,
        )
    except Exception as exc:
        log.error("Scaffold failed: %s", exc)
        return web.json_response(
            {"error": str(exc)}, status=500,
        )


def register_template_routes(app: web.Application) -> None:
    """Register Slate template API routes."""
    app.router.add_get("/api/templates/list", handle_list_templates)
    app.router.add_get(
        "/api/templates/{template_id}", handle_get_template,
    )
    app.router.add_post("/api/templates/scaffold", handle_scaffold_template)
    log.info("Template (Slate) API routes registered")