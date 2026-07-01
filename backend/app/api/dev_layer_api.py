"""Dev Layer API — REST endpoints for Dev Mode toggle.

GET  /api/dev-layer/state    — Get current Dev Mode state
PUT  /api/dev-layer/state    — Set Dev Mode state
POST /api/dev-layer/toggle   — Cycle through OFF → MINIMAL → ON → OFF
"""
from __future__ import annotations

import logging

from aiohttp import web

from app.services.dev_layer import get_dev_layer

log = logging.getLogger("ucore.api.dev_layer")


async def handle_get_dev_state(request: web.Request) -> web.Response:
    """GET /api/dev-layer/state — get current Dev Mode state."""
    layer = get_dev_layer()
    return web.json_response(layer.get_status())


async def handle_set_dev_state(request: web.Request) -> web.Response:
    """PUT /api/dev-layer/state — set Dev Mode state.

    Body: { "mode": "on" | "off" | "minimal" }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    mode_str = str(body.get("mode", "")).strip().lower()
    if mode_str not in ("on", "off", "minimal"):
        return web.json_response({
            "error": "Invalid mode. Use: on, off, or minimal",
        }, status=400)

    layer = get_dev_layer()
    from app.services.dev_layer import DevMode as DM
    layer.mode = DM(mode_str)

    log.info("Dev Mode set to: %s (by %s)", mode_str, request.remote or "unknown")

    return web.json_response(layer.get_status())


async def handle_toggle_dev_state(request: web.Request) -> web.Response:
    """POST /api/dev-layer/toggle — cycle dev mode."""
    layer = get_dev_layer()
    new_mode = layer.toggle()

    log.info("Dev Mode toggled to: %s (by %s)", new_mode.value, request.remote or "unknown")

    return web.json_response(layer.get_status())


async def handle_describe_dev_state(request: web.Request) -> web.Response:
    """GET /api/dev-layer/describe — human-readable description."""
    layer = get_dev_layer()
    return web.json_response({"description": layer.describe()})


def register_dev_layer_routes(app: web.Application) -> None:
    """Register Dev Layer API routes."""
    app.router.add_get("/api/dev-layer/state", handle_get_dev_state)
    app.router.add_put("/api/dev-layer/state", handle_set_dev_state)
    app.router.add_post("/api/dev-layer/toggle", handle_toggle_dev_state)
    app.router.add_get("/api/dev-layer/describe", handle_describe_dev_state)
    log.debug("Dev Layer API routes registered")
