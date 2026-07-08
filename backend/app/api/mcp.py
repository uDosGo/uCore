"""MCP Integration — Expose uCore skills/tools as MCP tools.

The Model Context Protocol (MCP) lets editors like VS Code/Continue
discover and call uCore skills directly.

MCP Server spec: https://modelcontextprotocol.io

Guardrails: Run ``validate_mcp_integrity()`` from ``app.api.mcp_guardrails``
to check structural health. The ``skill_mcp_self_heal`` skill can auto-repair
common issues.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

from app.api.mcp_handlers import dispatch_tool
from app.clipboard.clipboard_buffer import (
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
from app.skills.registry import get_skill
from app.skills.registry import list_skills as _list_skills

log = logging.getLogger("ucore.api.mcp")


# ─── MCP Discovery ────────────────────────────────────────

async def handle_mcp_discover(request: web.Request) -> web.Response:
    """GET /api/mcp/tools — Return all available MCP tools.

    Exposes every registered skill plus built-in knowledge, clipboard,
    tasker, gridsmith, toon, and flow-router tools.
    """
    tools: list[dict[str, Any]] = []

    # ── Skill tools ─────────────────────────────────────────
    for skill_meta in _list_skills():
        tools.append({
            "name": f"skill_{skill_meta['id']}",
            "description": skill_meta.get("description", ""),
            "input_schema": {
                "type": "object",
                "properties": {
                    p["name"]: {
                        "type": p.get("type", "string"),
                        "description": p.get("description", ""),
                    }
                    for p in skill_meta.get("params", [])
                },
            },
        })

    # ── Knowledge tools ──────────────────────────────────────
    tools.append({
        "name": "knowledge_search",
        "description": "Semantic search across knowledge workspaces",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "workspace_id": {"type": "string", "description": "Optional workspace filter"},
                "limit": {"type": "number", "description": "Max results (default 10)", "default": 10},
            },
            "required": ["query"],
        },
    })
    tools.append({
        "name": "knowledge_list_workspaces",
        "description": "List all knowledge workspaces",
        "input_schema": {"type": "object", "properties": {}},
    })
    tools.append({
        "name": "knowledge_list_documents",
        "description": "List documents in a workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "Workspace ID (omit for all)"},
            },
        },
    })

    # ── Clipboard tools ──────────────────────────────────────
    tools.append({
        "name": "clipboard_capture",
        "description": "Capture current clipboard content",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Capture source", "default": "user_copy"},
                "metadata": {"type": "object", "description": "Optional metadata"},
            },
        },
    })
    tools.append({
        "name": "clipboard_get",
        "description": "Get clipboard item(s)",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Specific item ID (omit for recent)"},
                "limit": {"type": "number", "description": "Max items (default 50)", "default": 50},
                "include_pinned": {"type": "boolean", "description": "Include pinned items", "default": True},
            },
        },
    })
    tools.append({
        "name": "clipboard_delete",
        "description": "Delete a clipboard item",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Item to delete"},
            },
            "required": ["item_id"],
        },
    })

    # ── Tasker tools ─────────────────────────────────────────
    tools.append({
        "name": "tasker_list_boards",
        "description": "List all tasker boards",
        "input_schema": {
            "type": "object",
            "properties": {
                "tasker_dir": {"type": "string", "description": "Custom tasker directory"},
            },
        },
    })
    tools.append({
        "name": "tasker_read_task",
        "description": "Read a task from a board",
        "input_schema": {
            "type": "object",
            "properties": {
                "board": {"type": "string", "description": "Board name"},
                "task": {"type": "string", "description": "Task ID"},
                "tasker_dir": {"type": "string", "description": "Custom tasker directory"},
            },
            "required": ["board", "task"],
        },
    })
    tools.append({
        "name": "tasker_write_task",
        "description": "Create or update a task",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "board": {"type": "string", "description": "Board name (default: inbox)", "default": "inbox"},
                "status": {"type": "string", "description": "Task status (default: todo)", "default": "todo"},
                "body": {"type": "string", "description": "Task body/markdown"},
                "source": {"type": "string", "description": "Creation source"},
                "source_id": {"type": "string", "description": "Source ID"},
                "metadata": {"type": "object", "description": "Custom metadata"},
                "task": {"type": "string", "description": "Task ID (for updates)"},
                "tasker_dir": {"type": "string", "description": "Custom tasker directory"},
            },
            "required": ["title"],
        },
    })
    tools.append({
        "name": "tasker_sync_export",
        "description": "Sync and export tasker data",
        "input_schema": {
            "type": "object",
            "properties": {
                "tasker_dir": {"type": "string", "description": "Custom tasker directory"},
            },
        },
    })

    # ── Gridsmith tools ──────────────────────────────────────
    tools.append({
        "name": "gridsmith_tools_list",
        "description": "List available gridsmith tools",
        "input_schema": {"type": "object", "properties": {}},
    })
    tools.append({
        "name": "gridsmith_create_grid",
        "description": "Create a new grid",
        "input_schema": {
            "type": "object",
            "properties": {
                "cols": {"type": "number", "description": "Columns (default 80)", "default": 80},
                "rows": {"type": "number", "description": "Rows (default 24)", "default": 24},
            },
        },
    })
    tools.append({
        "name": "gridsmith_latlon_to_ucode",
        "description": "Convert lat/lon to uCode coordinate",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "level": {"type": "number", "description": "Precision level (default 340)", "default": 340},
            },
            "required": ["lat", "lon"],
        },
    })
    tools.append({
        "name": "gridsmith_ucode_to_latlon",
        "description": "Convert uCode coordinate to lat/lon",
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
        "description": "Import a basic program into a world",
        "input_schema": {
            "type": "object",
            "properties": {
                "program": {"type": "string", "description": "Program code"},
                "world_name": {"type": "string", "description": "Target world name"},
            },
            "required": ["program", "world_name"],
        },
    })

    # ── Toon tools ───────────────────────────────────────────
    tools.append({
        "name": "toon_encode",
        "description": "Encode data to toon format",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data to encode"},
            },
            "required": ["data"],
        },
    })
    tools.append({
        "name": "toon_stats",
        "description": "Get toon encoding statistics",
        "input_schema": {"type": "object", "properties": {}},
    })
    tools.append({
        "name": "toon_clear",
        "description": "Clear toon state",
        "input_schema": {"type": "object", "properties": {}},
    })

    # ── Flow Router tools ────────────────────────────────────
    tools.append({
        "name": "flow_router_route",
        "description": "Route a flow task",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task to route"},
            },
            "required": ["task"],
        },
    })
    tools.append({
        "name": "flow_router_analytics",
        "description": "Get flow router analytics",
        "input_schema": {"type": "object", "properties": {}},
    })
    tools.append({
        "name": "flow_router_history",
        "description": "Get flow routing history",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "number", "description": "Max entries (default 100)", "default": 100},
            },
        },
    })

    # ── Autostart Health Check ───────────────────────────────
    tools.append({
        "name": "autostart_health_check",
        "description": "Check and auto-start snackbar services (backend, menu, MCP)",
        "input_schema": {
            "type": "object",
            "properties": {
                "check_only": {
                    "type": "boolean",
                    "description": "Only check status, don't auto-start",
                    "default": False,
                },
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

    Accepts multiple payload shapes:
      - Standard MCP: { "name": "tool_name", "arguments": {...} }
      - VS Code/Continue: { "tool": "tool_name", "params": {...} } or { "tool": "tool_name", "input": {...} }

    Delegates all tool execution to the modular dispatcher in mcp_handlers.py.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None,
        }, status=400)

    return await dispatch_tool(body)


async def handle_mcp_diagnostics(request: web.Request) -> web.Response:
    """GET /api/mcp/diagnostics — Return MCP layer diagnostics.

    Implements the spec from docs/mcp-diagnostics.md:
      - current tool registry snapshot (names, ids, and schemas)
      - last N tool calls attempted (from spool)
      - health status and a quick router health check
      - a short recommended remediation path
    """
    from app.api.mcp_guardrails import validate_mcp_integrity
    from app.skills.registry import list_skills as _list_skills

    # ── 1. Integrity check ──────────────────────────────────
    try:
        integrity_report = validate_mcp_integrity()
    except Exception as exc:
        log.error("MCP integrity check failed: %s", exc)
        integrity_report = {
            "ok": False,
            "errors": [f"Integrity check crashed: {exc}"],
            "checks": [],
        }

    # ── 2. Tool registry snapshot ───────────────────────────
    from app.api.mcp_handlers import TOOL_HANDLERS

    tool_snapshot = []
    for name, handler in sorted(TOOL_HANDLERS.items()):
        tool_snapshot.append({
            "name": name,
            "handler": getattr(handler, "__name__", str(handler)),
            "module": getattr(handler, "__module__", "unknown"),
        })

    # Add dynamic skill tools
    skill_tools = []
    for skill_meta in _list_skills():
        skill_tools.append({
            "name": f"skill_{skill_meta['id']}",
            "skill_id": skill_meta["id"],
            "category": skill_meta.get("category", ""),
        })

    # ── 3. Recent tool calls from spool ─────────────────────
    recent_calls: list[dict[str, Any]] = []
    try:
        from app.services.spool_reader import read_spool
        spool_entries = read_spool(max_entries=20, search="mcp")
        for entry in spool_entries:
            recent_calls.append({
                "timestamp": entry.timestamp,
                "level": entry.level,
                "module": entry.module,
                "message": entry.message[:200],
                "source": entry.source,
            })
    except Exception:
        # Spool reader may not be available
        pass

    # ── 4. Recommended remediation path ─────────────────────
    remediation: list[str] = []
    if not integrity_report.get("ok", False):
        for check in integrity_report.get("checks", []):
            if check.get("ok"):
                continue
            check_name = check.get("check", "unknown")
            if check_name == "syntax":
                remediation.append(
                    "Fix syntax errors in mcp.py/mcp_handlers.py manually — "
                    "run: python -c \"from app.api.mcp_guardrails import validate_mcp_integrity; validate_mcp_integrity()\""
                )
            elif check_name == "exports":
                remediation.append(
                    "Restore missing MCP exports (handle_mcp_discover, handle_mcp_call) — "
                    "check git history for last known good version"
                )
            elif check_name == "handler_signatures":
                remediation.append(
                    "Run skill_mcp_self_heal with dry_run=false to auto-normalize handler signatures"
                )
            elif check_name == "tool_registry":
                remediation.append(
                    "Run skill_mcp_self_heal with dry_run=false to add missing tools to registry"
                )
            elif check_name == "frontend_port_consistency":
                remediation.append(
                    "Run skill_mcp_self_heal with dry_run=false to auto-fix stale port references"
                )
            elif check_name == "dispatch_tool":
                remediation.append(
                    "Restore dispatch_tool() in mcp_handlers.py — check git history"
                )

    if not remediation:
        remediation.append("No issues detected — MCP layer is healthy")

    return web.json_response({
        "status": "ok" if integrity_report.get("ok") else "degraded",
        "timestamp": _utc_now_iso(),
        "integrity": integrity_report,
        "tool_registry": {
            "registered_tools": len(TOOL_HANDLERS),
            "tools": tool_snapshot,
            "skill_tools": skill_tools,
            "skill_tool_count": len(skill_tools),
        },
        "recent_calls": recent_calls,
        "remediation": remediation,
    })


def _utc_now_iso() -> str:
    from datetime import UTC, datetime
    return datetime.now(UTC).isoformat()
