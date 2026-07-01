"""MCP handlers: Tasker domain (boards, tasks, sync)."""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.mcp_handlers.tasker")


async def handle_tasker_list_boards(arguments: dict, request_id: Any) -> web.Response:
    """Handle tasker_list_boards tool."""
    from app.api.mcp import list_tasker_boards

    boards = list_tasker_boards(arguments.get("tasker_dir"))
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(boards, indent=2)}],
        },
        "id": request_id,
    })


async def handle_tasker_read_task(arguments: dict, request_id: Any) -> web.Response:
    """Handle tasker_read_task tool."""
    from app.api.mcp import read_task_markdown

    board = arguments.get("board")
    task = arguments.get("task")
    if not board or not task:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": "board and task are required"},
            "id": request_id,
        }, status=400)

    result = read_task_markdown(
        board=board, task=task, tasker_dir=arguments.get("tasker_dir")
    )
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
        },
        "id": request_id,
    })


async def handle_tasker_write_task(arguments: dict, request_id: Any) -> web.Response:
    """Handle tasker_write_task tool."""
    from app.api.mcp import write_task_markdown

    title = str(arguments.get("title", ""))
    if not title:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": "title is required"},
            "id": request_id,
        }, status=400)

    metadata = arguments.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": "metadata must be an object"},
            "id": request_id,
        }, status=400)

    try:
        result = write_task_markdown(
            title=title,
            board=str(arguments.get("board", "inbox")),
            status=str(arguments.get("status", "todo")),
            body=str(arguments.get("body", "")),
            source=str(arguments.get("source", "manual")),
            source_id=str(arguments["source_id"]) if "source_id" in arguments else None,
            metadata=metadata,
            task=str(arguments["task"]) if "task" in arguments else None,
            tasker_dir=arguments.get("tasker_dir"),
        )
    except ValueError as exc:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": str(exc)},
            "id": request_id,
        }, status=400)

    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
        },
        "id": request_id,
    })


async def handle_tasker_sync_export(arguments: dict, request_id: Any) -> web.Response:
    """Handle tasker_sync_export tool."""
    from app.api.mcp import get_skill

    skill = get_skill("tasker_sync")
    if not skill:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": "Tool 'tasker_sync_export' not available"},
            "id": request_id,
        }, status=404)

    result = await skill.run(**arguments)
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
        },
        "id": request_id,
    })
