"""uCore API — health check endpoints"""
from __future__ import annotations

from aiohttp import web
from ..core.logging import log


async def health_handler(request: web.Request) -> web.Response:
    """Return service health status."""
    return web.json_response({
        "status": "ok",
        "service": "uCore",
    })
