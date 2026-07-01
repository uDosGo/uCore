"""MCP handlers: Toon domain (encode, stats, clear)."""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.mcp_handlers.toon")


async def handle_toon_encode(arguments: dict, request_id: Any) -> web.Response:
    """Handle toon_encode tool."""
    from app.api.toon import handle_toon_encode as _encode_handler
    from app.skills.shared_utils import create_mock_request

    mock_request = create_mock_request(arguments)
    response = await _encode_handler(mock_request)
    response_data = await response.json()
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(response_data, indent=2)}],
        },
        "id": request_id,
    })


async def handle_toon_stats(arguments: dict, request_id: Any) -> web.Response:
    """Handle toon_stats tool."""
    from app.api.toon import handle_toon_stats as _stats_handler
    from app.skills.shared_utils import create_mock_request

    mock_request = create_mock_request({})
    response = await _stats_handler(mock_request)
    response_data = await response.json()
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(response_data, indent=2)}],
        },
        "id": request_id,
    })


async def handle_toon_clear(arguments: dict, request_id: Any) -> web.Response:
    """Handle toon_clear tool."""
    from app.api.toon import handle_toon_clear as _clear_handler
    from app.skills.shared_utils import create_mock_request

    mock_request = create_mock_request({})
    response = await _clear_handler(mock_request)
    response_data = await response.json()
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(response_data, indent=2)}],
        },
        "id": request_id,
    })
