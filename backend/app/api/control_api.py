"""Control Panel API — aggregated ecosystem status endpoint.

GET /api/control/status — all statuses, feed, agents, cost, mission,
    tasker, MCP, slates, alerts in one payload.
"""
from __future__ import annotations

import logging

from aiohttp import web

log = logging.getLogger("ucore.api.control")


def register_control_routes(app: web.Application) -> None:
    """Register Control Panel API routes."""

    async def handle_control_status(request: web.Request) -> web.Response:
        try:
            from app.services.control_service import get_control_status
            payload = await get_control_status()
            return web.json_response(payload)
        except Exception as exc:
            log.error("Control status aggregation failed: %s", exc)
            return web.json_response(
                {"error": str(exc), "success": False},
                status=500,
            )

    app.router.add_get("/api/control/status", handle_control_status)
    log.info("Control Panel API routes registered")
