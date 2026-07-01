"""MCP handlers: Flow Router domain (route, analytics, history)."""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.mcp_handlers.flow_router")


async def handle_flow_router_route(arguments: dict, request_id: Any) -> web.Response:
    """Handle flow_router_route tool."""
    from app.api.flow_router import handle_flow_router_route as _route_handler
    from app.skills.shared_utils import create_mock_request

    mock_request = create_mock_request(arguments)
    response = await _route_handler(mock_request)
    response_data = await response.json()
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(response_data, indent=2)}],
        },
        "id": request_id,
    })


async def handle_flow_router_analytics(arguments: dict, request_id: Any) -> web.Response:
    """Handle flow_router_analytics tool."""
    from app.api.flow_router.api import get_flow_router

    router = get_flow_router()
    analytics = router.get_analytics()
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(analytics, indent=2)}],
        },
        "id": request_id,
    })


async def handle_flow_router_history(arguments: dict, request_id: Any) -> web.Response:
    """Handle flow_router_history tool."""
    from app.api.flow_router.api import get_flow_router

    try:
        limit = int(arguments.get("limit", 100))
    except (TypeError, ValueError):
        limit = 100

    router = get_flow_router()
    history = router.get_routing_history(limit=limit)
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(history, indent=2)}],
        },
        "id": request_id,
    })
