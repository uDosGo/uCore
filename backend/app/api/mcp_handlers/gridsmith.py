"""MCP handlers: Gridsmith domain (grids, coordinates, programs)."""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.mcp_handlers.gridsmith")


async def handle_gridsmith_tools_list(arguments: dict, request_id: Any) -> web.Response:
    """Handle gridsmith_tools_list tool."""
    from app.api.mcp import get_gridsmith_bridge

    bridge = get_gridsmith_bridge()
    payload = bridge.run("tools", "list")
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        },
        "id": request_id,
    })


async def handle_gridsmith_create_grid(arguments: dict, request_id: Any) -> web.Response:
    """Handle gridsmith_create_grid tool."""
    from app.api.mcp import get_gridsmith_bridge

    bridge = get_gridsmith_bridge()
    payload = bridge.run(
        "grid", "create",
        "--cols", str(int(arguments.get("cols", 80))),
        "--rows", str(int(arguments.get("rows", 24))),
    )
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        },
        "id": request_id,
    })


async def handle_gridsmith_latlon_to_ucode(arguments: dict, request_id: Any) -> web.Response:
    """Handle gridsmith_latlon_to_ucode tool."""
    from app.api.mcp import get_gridsmith_bridge

    bridge = get_gridsmith_bridge()
    payload = bridge.run(
        "location", "latlon-to-ucode",
        "--lat", str(arguments.get("lat")),
        "--lon", str(arguments.get("lon")),
        "--level", str(int(arguments.get("level", 340))),
    )
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        },
        "id": request_id,
    })


async def handle_gridsmith_ucode_to_latlon(arguments: dict, request_id: Any) -> web.Response:
    """Handle gridsmith_ucode_to_latlon tool."""
    from app.api.mcp import get_gridsmith_bridge

    bridge = get_gridsmith_bridge()
    payload = bridge.run(
        "location", "ucode-to-latlon",
        "--coord", str(arguments.get("coord", "")),
    )
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        },
        "id": request_id,
    })


async def handle_gridsmith_import_basic_program(arguments: dict, request_id: Any) -> web.Response:
    """Handle gridsmith_import_basic_program tool."""
    from app.api.mcp import get_gridsmith_bridge

    bridge = get_gridsmith_bridge()
    payload = bridge.run(
        "world", "import-basic",
        "--program", str(arguments.get("program", "")),
        "--world-name", str(arguments.get("world_name", "")),
    )
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        },
        "id": request_id,
    })
