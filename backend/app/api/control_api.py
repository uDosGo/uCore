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

    async def handle_control_recover(request: web.Request) -> web.Response:
        try:
            from app.services.control_service import recover_offline_services

            payload = await recover_offline_services()
            status = 200 if payload.get("success") else 500
            return web.json_response(payload, status=status)
        except Exception as exc:
            log.error("Control recovery failed: %s", exc)
            return web.json_response(
                {"error": str(exc), "success": False},
                status=500,
            )

    app.router.add_get("/api/control/status", handle_control_status)
    app.router.add_post("/api/control/recover", handle_control_recover)
    log.info("Control Panel API routes registered")
