"""uCore API — metadata endpoints (system info, etc.)"""
from __future__ import annotations

from aiohttp import web
from ..core.settings import settings
import platform as plat


async def system_info_handler(request: web.Request) -> web.Response:
    """Return system/platform metadata."""
    return web.json_response({
        "platform": plat.system(),
        "machine": plat.machine(),
        "python": plat.python_version(),
        "hostname": plat.node(),
        "app": settings.app_name,
        "version": settings.version,
    })


async def maintenance_status_handler(request: web.Request) -> web.Response:
    """Return maintenance scheduler status and last-run information."""
    from app.services.maintenance_scheduler import get_maintenance_scheduler

    scheduler = get_maintenance_scheduler()
    if scheduler is None:
        return web.json_response({"status": "unavailable", "reason": "scheduler not started"}, status=503)
    return web.json_response({"status": "ok", **scheduler.status()})


async def workflow_status_handler(request: web.Request) -> web.Response:
    """Return workflow surface status for DevStudio/System UI wiring."""
    from app.services.maintenance_scheduler import get_maintenance_scheduler
    from app.services.workflow_status import build_workflow_status

    scheduler = get_maintenance_scheduler()
    maintenance = None
    if scheduler is not None:
        maintenance = {"status": "ok", **scheduler.status()}
    return web.json_response({"status": "ok", **build_workflow_status(maintenance=maintenance)})
