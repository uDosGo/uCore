"""MCP handlers: Knowledge domain (search, workspaces, documents)."""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.mcp_handlers.knowledge")


async def handle_knowledge_search(arguments: dict, request_id: Any) -> web.Response:
    """Handle knowledge_search tool."""
    from app.knowledge.appflowy import semantic_search

    query = str(arguments.get("query", "")).strip()
    if not query:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": "query is required"},
            "id": request_id,
        }, status=400)

    try:
        limit = int(arguments.get("limit", 10))
    except (TypeError, ValueError):
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": "limit must be an integer"},
            "id": request_id,
        }, status=400)

    workspace_id = arguments.get("workspace_id")
    results = semantic_search(query, workspace_id, max(1, limit))
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(results, indent=2)}],
        },
        "id": request_id,
    })


async def handle_knowledge_list_workspaces(arguments: dict, request_id: Any) -> web.Response:
    """Handle knowledge_list_workspaces tool."""
    from app.knowledge.appflowy import list_workspaces

    ws = list_workspaces()
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(ws, indent=2)}],
        },
        "id": request_id,
    })


async def handle_knowledge_list_documents(arguments: dict, request_id: Any) -> web.Response:
    """Handle knowledge_list_documents tool."""
    from app.knowledge.appflowy import list_documents

    workspace_id = arguments.get("workspace_id")
    docs = list_documents(str(workspace_id) if workspace_id else None)
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(docs, indent=2)}],
        },
        "id": request_id,
    })
