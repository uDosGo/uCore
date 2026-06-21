"""MCP Integration — Expose uCore skills/tools as MCP tools.

The Model Context Protocol (MCP) lets editors like VS Code/Continue
discover and call uCore skills directly.

MCP Server spec: https://modelcontextprotocol.io
"""
from __future__ import annotations

import json
import logging
from aiohttp import web
from app.skills.registry import list_skills as _list_skills, run_skill_by_id, get_skill
from app.tools.registry import list_tools

log = logging.getLogger("ucore.api.mcp")

# ─── MCP Protocol Types ────────────────────────────────────

MCP_SCHEMA = {
    "jsonrpc": "2.0",
    "method": None,
    "params": {},
    "id": None,
}


async def handle_mcp_discover(request: web.Request) -> web.Response:
    """GET /api/mcp/tools — list all MCP-compatible tools.

    Returns tools in the MCP function-calling format that
    Continue/Cline can consume.
    """
    tools = []
    for skill in _list_skills():
        tools.append({
            "name": f"skill_{skill['id']}",
            "description": skill.get("description", ""),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"Parameters for {skill['name']}",
                    }
                },
                "required": ["query"],
            },
        })

    # Also add read-only knowledge tools
    tools.append({
        "name": "knowledge_search",
        "description": "Search AppFlowy knowledge base",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "number", "description": "Max results"},
            },
            "required": ["query"],
        },
    })
    tools.append({
        "name": "knowledge_list_workspaces",
        "description": "List AppFlowy workspaces",
        "input_schema": {"type": "object", "properties": {}},
    })
    tools.append({
        "name": "knowledge_list_documents",
        "description": "List AppFlowy documents",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "Workspace ID"},
            },
        },
    })

    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "tools": tools,
            "protocolVersion": "2025-03-26",
            "serverInfo": {
                "name": "uCore MCP",
                "version": "4.0.0",
            },
        },
        "id": None,
    })


async def handle_mcp_call(request: web.Request) -> web.Response:
    """POST /api/mcp/call — Execute a tool via MCP.

    Body: { "name": "skill_backup", "arguments": {"query": "..."} }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None,
        }, status=400)

    tool_name = body.get("name", "")
    arguments = body.get("arguments", {}) or {}

    # Route to skill or knowledge
    if tool_name.startswith("skill_"):
        skill_id = tool_name[6:]  # Remove "skill_" prefix
        skill = get_skill(skill_id)
        if not skill:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
                "id": body.get("id"),
            }, status=404)

        result = await skill.run(**arguments)
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
            "id": body.get("id"),
        })

    # Knowledge tools
    if tool_name == "knowledge_search":
        from app.knowledge.appflowy import semantic_search
        results = semantic_search(
            arguments.get("query", ""),
            arguments.get("workspace_id"),
            int(arguments.get("limit", 10)),
        )
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": json.dumps(results, indent=2)}]
            },
            "id": body.get("id"),
        })

    if tool_name == "knowledge_list_workspaces":
        from app.knowledge.appflowy import list_workspaces
        ws = list_workspaces()
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": json.dumps(ws, indent=2)}]},
            "id": body.get("id"),
        })

    if tool_name == "knowledge_list_documents":
        from app.knowledge.appflowy import list_documents
        docs = list_documents(arguments.get("workspace_id"))
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": json.dumps(docs, indent=2)}]},
            "id": body.get("id"),
        })

    return web.json_response({
        "jsonrpc": "2.0",
        "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
        "id": body.get("id"),
    }, status=404)
