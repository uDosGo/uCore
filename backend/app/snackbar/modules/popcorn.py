"""Popcorn orchestration routes (macOS only)."""
from __future__ import annotations

import platform as plat_module

from aiohttp import web


async def popcorn_status_handler(request: web.Request) -> web.Response:
    """GET /api/surfaces/popcorn/status — get Popcorn status."""
    try:
        if plat_module.system() != "Darwin":
            return web.json_response(
                {"error": "Popcorn is macOS-only"}, status=501,
            )

        from app.services.popcorn_manager import get_popcorn_status

        status = get_popcorn_status()
        return web.json_response(status)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def popcorn_action_handler(request: web.Request) -> web.Response:
    """POST /api/surfaces/popcorn/{action} — control Popcorn."""
    try:
        if plat_module.system() != "Darwin":
            return web.json_response(
                {"error": "Popcorn is macOS-only"}, status=501,
            )

        action = request.match_info.get("action", "").lower()
        from app.services.popcorn_manager import perform_action

        result = perform_action(action)
        status_code = 200 if result.get("success") else 400
        return web.json_response(result, status=status_code)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def register(app: web.Application) -> None:
    app.router.add_get(
        "/api/surfaces/popcorn/status", popcorn_status_handler,
    )
    app.router.add_post(
        "/api/surfaces/popcorn/{action}", popcorn_action_handler,
    )
