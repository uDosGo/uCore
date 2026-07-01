"""API endpoints for system tools detection."""
from __future__ import annotations

from aiohttp import web

from app.tools.registry import check_tool as ct
from app.tools.registry import list_tools as lt


async def handle_list_tools(request: web.Request) -> web.Response:
    """GET /api/tools — list installed tools with versions."""
    tools = await lt()
    return web.json_response({
        "tools": [t.model_dump() for t in tools],
        "count": len(tools),
    })


async def handle_tool_status(request: web.Request) -> web.Response:
    """GET /api/tools/{tool_id}/status — check if a tool is available."""
    tool_id = request.match_info.get("tool_id", "")
    result = await ct(tool_id)
    if isinstance(result, dict):
        return web.json_response(result)
    return web.json_response(result.model_dump())
