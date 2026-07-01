"""MCP Tool Handlers — Modular domain submodules.

This package splits the monolithic mcp_handlers.py into domain-specific
modules for better maintainability. Each module exports its handler functions
and is registered in the TOOL_HANDLERS registry below.

Usage:
    from app.api.mcp_handlers import dispatch_tool, TOOL_HANDLERS
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from aiohttp import web

from app.api.mcp_handlers.knowledge import (
    handle_knowledge_list_documents,
    handle_knowledge_list_workspaces,
    handle_knowledge_search,
)
from app.api.mcp_handlers.clipboard import (
    handle_clipboard_capture,
    handle_clipboard_delete,
    handle_clipboard_get,
)
from app.api.mcp_handlers.tasker import (
    handle_tasker_list_boards,
    handle_tasker_read_task,
    handle_tasker_sync_export,
    handle_tasker_write_task,
)
from app.api.mcp_handlers.gridsmith import (
    handle_gridsmith_create_grid,
    handle_gridsmith_import_basic_program,
    handle_gridsmith_latlon_to_ucode,
    handle_gridsmith_tools_list,
    handle_gridsmith_ucode_to_latlon,
)
from app.api.mcp_handlers.flow_router import (
    handle_flow_router_analytics,
    handle_flow_router_history,
    handle_flow_router_route,
)
from app.api.mcp_handlers.toon import (
    handle_toon_clear,
    handle_toon_encode,
    handle_toon_stats,
)
from app.api.mcp_handlers.autostart import (
    handle_autostart_health_check,
)
from app.api.mcp_handlers.skill import (
    handle_skill_tool,
)

log = logging.getLogger("ucore.api.mcp_handlers")


# ─── Tool Handler Registry ─────────────────────────────────────

TOOL_HANDLERS: dict[str, Any] = {
    "knowledge_search": handle_knowledge_search,
    "knowledge_list_workspaces": handle_knowledge_list_workspaces,
    "knowledge_list_documents": handle_knowledge_list_documents,
    "clipboard_capture": handle_clipboard_capture,
    "clipboard_get": handle_clipboard_get,
    "clipboard_delete": handle_clipboard_delete,
    "tasker_list_boards": handle_tasker_list_boards,
    "tasker_read_task": handle_tasker_read_task,
    "tasker_write_task": handle_tasker_write_task,
    "tasker_sync_export": handle_tasker_sync_export,
    "flow_router_route": handle_flow_router_route,
    "flow_router_analytics": handle_flow_router_analytics,
    "flow_router_history": handle_flow_router_history,
    "gridsmith_tools_list": handle_gridsmith_tools_list,
    "gridsmith_create_grid": handle_gridsmith_create_grid,
    "gridsmith_latlon_to_ucode": handle_gridsmith_latlon_to_ucode,
    "gridsmith_ucode_to_latlon": handle_gridsmith_ucode_to_latlon,
    "gridsmith_import_basic_program": handle_gridsmith_import_basic_program,
    "toon_encode": handle_toon_encode,
    "toon_stats": handle_toon_stats,
    "toon_clear": handle_toon_clear,
    "autostart_health_check": handle_autostart_health_check,
}


async def dispatch_tool(body: Dict[str, Any]) -> web.Response:
    """Dispatch an MCP request to the appropriate handler.

    Accepts multiple payload shapes:
      - Standard MCP: { "name": "tool_name", "arguments": {...} }
      - VS Code/Continue: { "tool": "tool_name", "params": {...} }
      - Alternate: { "tool_name": "tool_name", "input": {...} }

    Delegates to individual handler functions by domain module.
    """
    tool_name = body.get("name") or body.get("tool") or body.get("tool_name") or ""
    arguments = body.get("arguments") or body.get("params") or body.get("input") or {}
    request_id = body.get("id")

    log.info("[MCP call] tool=%r args_keys=%s", tool_name, list(arguments.keys()) if arguments else [])

    if tool_name.startswith("skill_"):
        return await handle_skill_tool(tool_name, arguments, request_id)

    handler = TOOL_HANDLERS.get(tool_name)
    if handler:
        return await handler(arguments, request_id)

    return web.json_response({
        "jsonrpc": "2.0",
        "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
        "id": request_id,
    }, status=404)
