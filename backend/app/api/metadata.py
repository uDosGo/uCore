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
