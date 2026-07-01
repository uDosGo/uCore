"""MCP handlers: Dynamic skill dispatch (skill_xxx tools)."""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.mcp_handlers.skill")


async def handle_skill_tool(tool_name: str, arguments: dict, request_id: Any) -> web.Response:
    """Handle skill_xxx tool calls by dispatching to the skills registry."""
    from app.skills.registry import get_skill

    skill_id = tool_name[6:]  # Remove "skill_" prefix
    skill = get_skill(skill_id)
    if not skill:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
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
