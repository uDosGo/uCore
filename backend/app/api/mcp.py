"""MCP Integration — Expose uCore skills/tools as MCP tools.

The Model Context Protocol (MCP) lets editors like VS Code/Continue
discover and call uCore skills directly.

MCP Server spec: https://modelcontextprotocol.io
"""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

from app.menu.clipboard_buffer import (
    capture_current_clipboard,
    delete_item,
    get_item_by_id,
    get_recent_items,
)
from app.services.gridsmith_bridge import get_gridsmith_bridge
from app.services.tasker_ops import (
    list_tasker_boards,
    read_task_markdown,
    write_task_markdown,
)
from app.skills.registry import (
    get_skill,
)
from app.skills.registry import (
    list_skills as _list_skills,
)

log = logging.getLogger("ucore.api.mcp")

# ─── MCP Protocol Types ────────────────────────────────────

MCP_SCHEMA: dict[str, Any] = {
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
                    },
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
                "workspace_id": {
                    "type": "string",
                    "description": "Workspace ID",
                },
            },
        },
    })

    tools.append({
        "name": "clipboard_capture",
        "description": (
            "Capture current macOS clipboard text into local history"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Clipboard event source",
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata for the capture event",
                },
            },
        },
    })
    tools.append({
        "name": "clipboard_get",
        "description": "Get recent clipboard entries or a single entry by id",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "string",
                    "description": "Specific clipboard item id",
                },
                "limit": {
                    "type": "number",
                    "description": "Max number of recent clipboard items",
                },
                "include_pinned": {
                    "type": "boolean",
                    "description": "Include pinned items in recent results",
                },
            },
        },
    })
    tools.append({
        "name": "clipboard_delete",
        "description": "Delete a clipboard entry by id",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "string",
                    "description": "Clipboard item id to delete",
                },
            },
            "required": ["item_id"],
        },
    })
    tools.append({
        "name": "tasker_list_boards",
        "description": "List .tasker boards and markdown card counts",
        "input_schema": {
            "type": "object",
            "properties": {
                "tasker_dir": {
                    "type": "string",
                    "description": "Optional .tasker directory override",
                },
            },
        },
    })
    tools.append({
        "name": "tasker_read_task",
        "description": "Read a markdown task from a .tasker board",
        "input_schema": {
            "type": "object",
            "properties": {
                "board": {
                    "type": "string",
                    "description": "Board directory name",
                },
                "task": {
                    "type": "string",
                    "description": "Markdown task filename",
                },
                "tasker_dir": {
                    "type": "string",
                    "description": "Optional .tasker directory override",
                },
            },
            "required": ["board", "task"],
        },
    })
    tools.append({
        "name": "tasker_write_task",
        "description": "Create or update a markdown task in a .tasker board",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title",
                },
                "board": {
                    "type": "string",
                    "description": "Board directory name",
                },
                "status": {
                    "type": "string",
                    "description": "Task status for frontmatter and filename",
                },
                "body": {
                    "type": "string",
                    "description": "Task summary/body text",
                },
                "source": {
                    "type": "string",
                    "description": "Task source metadata",
                },
                "source_id": {
                    "type": "string",
                    "description": "Stable source identifier",
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata lines",
                },
                "task": {
                    "type": "string",
                    "description": "Optional existing filename to overwrite",
                },
                "tasker_dir": {
                    "type": "string",
                    "description": "Optional .tasker directory override",
                },
            },
            "required": ["title"],
        },
    })
    tools.append({
        "name": "tasker_sync_export",
        "description": (
            "Export AppFlowy rows into .tasker markdown via "
            "tasker_sync"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "db": {
                    "type": "string",
                    "description": "Known DB key or absolute sqlite path",
                },
                "sql": {
                    "type": "string",
                    "description": "Read-only SQL query for task rows",
                },
                "tasker_dir": {
                    "type": "string",
                    "description": "Destination .tasker directory",
                },
                "board": {
                    "type": "string",
                    "description": "Board/folder name",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview exports without writing files",
                },
            },
        },
    })

    tools.append({
        "name": "gridsmith_tools_list",
        "description": "List GridSmith world-building tool contracts",
        "input_schema": {"type": "object", "properties": {}},
    })
    tools.append({
        "name": "gridsmith_create_grid",
        "description": "Create a GridSmith grid scaffold",
        "input_schema": {
            "type": "object",
            "properties": {
                "cols": {"type": "number", "description": "Grid columns"},
                "rows": {"type": "number", "description": "Grid rows"},
            },
        },
    })
    tools.append({
        "name": "gridsmith_latlon_to_ucode",
        "description": "Convert lat/lon into a uCode coordinate",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "level": {"type": "number", "description": "uCode level"},
            },
            "required": ["lat", "lon"],
        },
    })
    tools.append({
        "name": "gridsmith_ucode_to_latlon",
        "description": "Convert a uCode coordinate into lat/lon",
        "input_schema": {
            "type": "object",
            "properties": {
                "coord": {"type": "string", "description": "uCode coordinate"},
            },
            "required": ["coord"],
        },
    })
    tools.append({
        "name": "gridsmith_import_basic_program",
        "description": "Import a BASIC program into the live GridSmith workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "program": {"type": "string", "description": "Inline BASIC source or file path"},
                "world_name": {"type": "string", "description": "Generated world name"},
            },
            "required": ["program", "world_name"],
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
                "error": {
                    "code": -32601,
                    "message": f"Tool '{tool_name}' not found",
                },
                "id": body.get("id"),
            }, status=404)

        result = await skill.run(**arguments)
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(result, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    # Knowledge tools
    if tool_name == "knowledge_search":
        from app.knowledge.appflowy import semantic_search

        query = str(arguments.get("query", "")).strip()
        if not query:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "query is required",
                },
                "id": body.get("id"),
            }, status=400)

        try:
            limit = int(arguments.get("limit", 10))
        except (TypeError, ValueError):
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "limit must be an integer",
                },
                "id": body.get("id"),
            }, status=400)

        workspace_id = arguments.get("workspace_id")
        results = semantic_search(
            query,
            workspace_id,
            max(1, limit),
        )
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(results, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "knowledge_list_workspaces":
        from app.knowledge.appflowy import list_workspaces
        ws = list_workspaces()
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(ws, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "knowledge_list_documents":
        from app.knowledge.appflowy import list_documents

        workspace_id = arguments.get("workspace_id")
        docs = list_documents(str(workspace_id) if workspace_id else None)
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(docs, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "clipboard_capture":
        source = arguments.get("source", "user_copy")
        metadata = arguments.get("metadata") or {}
        try:
            item = capture_current_clipboard(source=source, metadata=metadata)
        except Exception as exc:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(exc)},
                "id": body.get("id"),
            }, status=400)
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(item, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "clipboard_get":
        item_id = arguments.get("item_id")
        payload: dict[str, Any] | list[dict[str, Any]]
        if item_id:
            found_item = get_item_by_id(str(item_id))
            if not found_item:
                return web.json_response({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32004,
                        "message": f"Clipboard item '{item_id}' not found",
                    },
                    "id": body.get("id"),
                }, status=404)
            payload = found_item
        else:
            limit = int(arguments.get("limit", 50))
            include_pinned = bool(arguments.get("include_pinned", True))
            items = get_recent_items(
                limit=limit,
                include_pinned=include_pinned,
            )
            payload = {"items": items, "count": len(items)}

        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(payload, indent=2),
                    },
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "clipboard_delete":
        item_id = str(arguments.get("item_id", "")).strip()
        if not item_id:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "item_id is required",
                },
                "id": body.get("id"),
            }, status=400)

        deleted = delete_item(item_id)
        if not deleted:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32004,
                    "message": f"Clipboard item '{item_id}' not found",
                },
                "id": body.get("id"),
            }, status=404)

        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [{
                    "type": "text",
                    "text": json.dumps(
                        {"status": "deleted", "id": item_id},
                        indent=2,
                    ),
                }],
            },
            "id": body.get("id"),
        })

    if tool_name == "tasker_list_boards":
        payload = list_tasker_boards(arguments.get("tasker_dir"))
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(payload, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "tasker_read_task":
        try:
            payload = read_task_markdown(
                board=str(arguments.get("board", "")),
                task=str(arguments.get("task", "")),
                tasker_dir=arguments.get("tasker_dir"),
            )
        except ValueError as exc:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": str(exc)},
                "id": body.get("id"),
            }, status=400)
        except FileNotFoundError:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32004, "message": "Task not found"},
                "id": body.get("id"),
            }, status=404)

        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(payload, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "gridsmith_tools_list":
        payload = await get_gridsmith_bridge().run("tools", "list")
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(payload, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "gridsmith_create_grid":
        payload = await get_gridsmith_bridge().run(
            "grid",
            "create",
            "--cols",
            str(int(arguments.get("cols", 80))),
            "--rows",
            str(int(arguments.get("rows", 24))),
        )
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(payload, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "gridsmith_latlon_to_ucode":
        if arguments.get("lat") is None or arguments.get("lon") is None:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "lat and lon are required"},
                "id": body.get("id"),
            }, status=400)
        payload = await get_gridsmith_bridge().run(
            "location",
            "latlon-to-ucode",
            "--lat",
            str(arguments.get("lat")),
            "--lon",
            str(arguments.get("lon")),
            "--level",
            str(int(arguments.get("level", 340))),
        )
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(payload, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "gridsmith_ucode_to_latlon":
        coord = str(arguments.get("coord", "")).strip()
        if not coord:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "coord is required"},
                "id": body.get("id"),
            }, status=400)
        payload = await get_gridsmith_bridge().run(
            "location",
            "ucode-to-latlon",
            "--coord",
            coord,
        )
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(payload, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "gridsmith_import_basic_program":
        program = str(arguments.get("program", "")).strip()
        world_name = str(arguments.get("world_name", "")).strip()
        if not program or not world_name:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "program and world_name are required"},
                "id": body.get("id"),
            }, status=400)
        payload = await get_gridsmith_bridge().run(
            "world",
            "import-basic",
            "--program",
            program,
            "--world-name",
            world_name,
        )
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(payload, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "tasker_write_task":
        metadata = arguments.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "metadata must be an object",
                },
                "id": body.get("id"),
            }, status=400)

        try:
            payload = write_task_markdown(
                title=str(arguments.get("title", "")),
                board=str(arguments.get("board", "inbox")),
                status=str(arguments.get("status", "todo")),
                body=str(arguments.get("body", "")),
                source=str(arguments.get("source", "manual")),
                source_id=(
                    str(arguments["source_id"])
                    if "source_id" in arguments
                    else None
                ),
                metadata=metadata,
                task=(
                    str(arguments["task"])
                    if "task" in arguments
                    else None
                ),
                tasker_dir=arguments.get("tasker_dir"),
            )
        except ValueError as exc:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": str(exc)},
                "id": body.get("id"),
            }, status=400)

        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(payload, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    if tool_name == "tasker_sync_export":
        skill = get_skill("tasker_sync")
        if not skill:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": "Tool 'tasker_sync_export' not available",
                },
                "id": body.get("id"),
            }, status=404)

        result = await skill.run(**arguments)
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(result, indent=2)},
                ],
            },
            "id": body.get("id"),
        })

    return web.json_response({
        "jsonrpc": "2.0",
        "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
        "id": body.get("id"),
    }, status=404)
