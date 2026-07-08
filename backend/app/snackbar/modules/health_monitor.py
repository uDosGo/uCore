"""Health monitoring routes — detailed status and logs."""
from __future__ import annotations

from aiohttp import web


async def health_status_handler(request: web.Request) -> web.Response:
    """GET /api/health/status — detailed health status."""
    try:
        from app.services.health_monitor import get_health_monitor

        monitor = get_health_monitor()
        status = monitor.get_status()
        return web.json_response(status)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def health_logs_handler(request: web.Request) -> web.Response:
    """GET /api/health/logs — get recent health monitor logs."""
    try:
        from app.services.health_monitor import get_health_monitor

        monitor = get_health_monitor()
        lines = int(request.query.get("lines", 100))
        logs = monitor.get_logs(lines)
        return web.json_response({"logs": logs})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def register(app: web.Application) -> None:
    app.router.add_get("/api/health/status", health_status_handler)
    app.router.add_get("/api/health/logs", health_logs_handler)
