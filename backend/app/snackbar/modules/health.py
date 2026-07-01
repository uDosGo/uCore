"""Health, version, info, and shutdown routes."""
from __future__ import annotations

import asyncio
import platform as plat_module
import time

from aiohttp import web

from app.core.logging import log
from app.core.settings import settings

_start_time: float = time.time()


async def health_handler(request: web.Request) -> web.Response:
    health = {
        "status": "ok",
        "service": "uCore",
        "version": settings.version,
    }
    if plat_module.system() == "Darwin":
        try:
            from app.services.popcorn_manager import get_popcorn_status
            health["popcorn"] = get_popcorn_status()
        except Exception as e:
            log.warning("Failed to get Popcorn status: %s", e)
            health["popcorn"] = {"error": str(e)}
    return web.json_response(health)


async def version_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "app": settings.app_name,
        "version": settings.version,
        "python": plat_module.python_version(),
        "platform": plat_module.system(),
    })


async def info_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "app": settings.app_name,
        "version": settings.version,
        "host": settings.host,
        "port": settings.port,
        "debug": settings.debug,
        "platform": plat_module.system(),
        "machine": plat_module.machine(),
        "python": plat_module.python_version(),
        "uptime": time.time() - _start_time,
    })


async def shutdown_handler(request: web.Request) -> web.Response:
    asyncio.get_event_loop().stop()
    return web.json_response({"status": "shutting down"})


def register(app: web.Application) -> None:
    app.router.add_get("/api/health", health_handler)
    app.router.add_get("/api/version", version_handler)
    app.router.add_get("/api/info", info_handler)
    app.router.add_post("/api/shutdown", shutdown_handler)