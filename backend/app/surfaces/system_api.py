"""System Surface — pages, tools, and settings backend."""

from __future__ import annotations

import logging

from aiohttp import web

log = logging.getLogger("ucore")

# ─── S-Pages Registry ──────────────────────────────────────────────

S_PAGES: list[dict] = [
    {"id": "S100", "title": "Tool Builder", "icon": "build"},
    {"id": "S101", "title": "Story Builder", "icon": "auto_stories"},
    {"id": "S300", "title": "Workflow Builder", "icon": "account_tree"},
    {
        "id": "S310",
        "title": "Clipboard Orchestration",
        "icon": "content_paste",
    },
    {"id": "S320", "title": "Knowledge Tools", "icon": "psychology"},
    {"id": "S330", "title": "Migration Dashboard", "icon": "migration"},
    {"id": "S600", "title": "Learning Hub", "icon": "school"},
]


def register_system_api_routes(app: web.Application) -> None:  # noqa: C901
    """Register system surface API routes."""

    # ── Pages ──────────────────────────────────────────────────
    async def handle_pages(_request: web.Request) -> web.Response:
        return web.json_response({"pages": S_PAGES, "count": len(S_PAGES)})

    # ── Tools (wrapper around /api/tools) ──────────────────────
    async def handle_system_tools(_request: web.Request) -> web.Response:
        try:
            from app.api.tools import handle_list_tools  # noqa: PLC0415
            resp = await handle_list_tools(_request)
            import json  # noqa: PLC0415
            if hasattr(resp, "body"):
                data = json.loads(resp.body)
            else:
                data = {}
            tools = data.get("tools", [])
            mapped = [
                {
                    "id": t.get("id", ""),
                    "name": t.get("name", ""),
                    "icon": t.get("icon", "build"),
                    "description": t.get("description", ""),
                }
                for t in (tools if isinstance(tools, list) else [])
            ]
            return web.json_response(
                {"tools": mapped, "count": len(mapped)},
            )
        except Exception as exc:
            log.warning("System tools aggregation failed: %s", exc)
            return web.json_response(
                {"tools": [], "count": 0, "error": str(exc)},
            )

    # ── Settings (persist via key-value store) ──────────────────
    _settings: dict[str, dict] = {}

    async def handle_get_settings(_request: web.Request) -> web.Response:
        return web.json_response({"settings": _settings})

    async def handle_update_settings(request: web.Request) -> web.Response:
        try:
            body = await request.json()
            scope = body.get("scope", "global")
            for key, value in body.get("values", {}).items():
                _settings.setdefault(scope, {})[key] = value
            return web.json_response(
                {"status": "ok", "settings": _settings},
            )
        except Exception as exc:
            return web.json_response(
                {"status": "error", "error": str(exc)},
            )

    app.router.add_get("/api/system/pages", handle_pages)
    app.router.add_get("/api/system/tools", handle_system_tools)
    app.router.add_get("/api/system/settings", handle_get_settings)
    app.router.add_post("/api/system/settings", handle_update_settings)