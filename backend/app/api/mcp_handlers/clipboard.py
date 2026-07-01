"""MCP handlers: Clipboard domain (capture, get, delete)."""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.mcp_handlers.clipboard")


async def handle_clipboard_capture(arguments: dict, request_id: Any) -> web.Response:
    """Handle clipboard_capture tool."""
    from app.api.mcp import capture_current_clipboard

    source = arguments.get("source", "user_copy")
    metadata = arguments.get("metadata") or {}
    try:
        item = capture_current_clipboard(source=source, metadata=metadata)
    except Exception as exc:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": str(exc)},
            "id": request_id,
        }, status=400)
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(item, indent=2)}],
        },
        "id": request_id,
    })


async def handle_clipboard_get(arguments: dict, request_id: Any) -> web.Response:
    """Handle clipboard_get tool."""
    from app.api.mcp import get_item_by_id, get_recent_items

    item_id = arguments.get("item_id")
    if item_id:
        found_item = get_item_by_id(str(item_id))
        if not found_item:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Item {item_id} not found"},
                "id": request_id,
            }, status=404)
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": json.dumps(found_item, indent=2)}],
            },
            "id": request_id,
        })

    limit = int(arguments.get("limit", 20))
    include_pinned = bool(arguments.get("include_pinned", True))
    items = get_recent_items(limit=limit, include_pinned=include_pinned)
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps({"items": items, "count": len(items)}, indent=2)}],
        },
        "id": request_id,
    })


async def handle_clipboard_delete(arguments: dict, request_id: Any) -> web.Response:
    """Handle clipboard_delete tool."""
    from app.api.mcp import delete_item

    item_id = arguments.get("item_id")
    if not item_id:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": "item_id is required"},
            "id": request_id,
        }, status=400)

    success = delete_item(str(item_id))
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps({"status": "deleted" if success else "not_found", "id": item_id})}],
        },
        "id": request_id,
    })
