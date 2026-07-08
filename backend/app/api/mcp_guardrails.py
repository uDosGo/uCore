#!/usr/bin/env python3
"""MCP Integrity Guardrails — Structural validation for the MCP layer.

This module provides runtime checks that catch the class of corruption
that broke mcp.py (garbled code from bad merges, missing functions,
orphaned dead code, mismatched handler signatures).

Usage:
    from app.api.mcp_guardrails import validate_mcp_integrity

    # At startup or in tests
    report = validate_mcp_integrity()
    if report["errors"]:
        log.error("MCP integrity check failed: %s", report["errors"])
"""
from __future__ import annotations

import ast
import inspect
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.api.mcp_guardrails")

# ─── Expected MCP API surface ──────────────────────────────────

REQUIRED_MCP_EXPORTS = {
    "handle_mcp_discover",
    "handle_mcp_call",
}

REQUIRED_HANDLER_SIGNATURES = {
    # All handlers must accept (arguments: dict, request_id: Any)
    "handle_skill_tool": ["tool_name", "arguments", "request_id"],
    "handle_knowledge_search": ["arguments", "request_id"],
    "handle_knowledge_list_workspaces": ["arguments", "request_id"],
    "handle_knowledge_list_documents": ["arguments", "request_id"],
    "handle_clipboard_capture": ["arguments", "request_id"],
    "handle_clipboard_get": ["arguments", "request_id"],
    "handle_clipboard_delete": ["arguments", "request_id"],
    "handle_tasker_list_boards": ["arguments", "request_id"],
    "handle_tasker_read_task": ["arguments", "request_id"],
    "handle_tasker_write_task": ["arguments", "request_id"],
    "handle_tasker_sync_export": ["arguments", "request_id"],
    "handle_flow_router_route": ["arguments", "request_id"],
    "handle_flow_router_analytics": ["arguments", "request_id"],
    "handle_flow_router_history": ["arguments", "request_id"],
    "handle_gridsmith_tools_list": ["arguments", "request_id"],
    "handle_gridsmith_create_grid": ["arguments", "request_id"],
    "handle_gridsmith_latlon_to_ucode": ["arguments", "request_id"],
    "handle_gridsmith_ucode_to_latlon": ["arguments", "request_id"],
    "handle_gridsmith_import_basic_program": ["arguments", "request_id"],
    "handle_toon_encode": ["arguments", "request_id"],
    "handle_toon_stats": ["arguments", "request_id"],
    "handle_toon_clear": ["arguments", "request_id"],
    "handle_autostart_health_check": ["arguments", "request_id"],
}

# Domain modules that make up the mcp_handlers package
HANDLER_DOMAIN_MODULES = [
    "knowledge",
    "clipboard",
    "tasker",
    "gridsmith",
    "flow_router",
    "toon",
    "autostart",
    "skill",
]

REQUIRED_TOOL_NAMES = {
    "knowledge_search",
    "knowledge_list_workspaces",
    "knowledge_list_documents",
    "clipboard_capture",
    "clipboard_get",
    "clipboard_delete",
    "tasker_list_boards",
    "tasker_read_task",
    "tasker_write_task",
    "tasker_sync_export",
    "flow_router_route",
    "flow_router_analytics",
    "flow_router_history",
    "gridsmith_tools_list",
    "gridsmith_create_grid",
    "gridsmith_latlon_to_ucode",
    "gridsmith_ucode_to_latlon",
    "gridsmith_import_basic_program",
    "toon_encode",
    "toon_stats",
    "toon_clear",
    "autostart_health_check",
}


# ─── Validation functions ──────────────────────────────────────

def validate_mcp_syntax() -> dict[str, Any]:
    """Check that mcp.py, mcp_guardrails.py, and all mcp_handlers/ domain
    modules parse as valid Python."""
    errors: list[str] = []
    api_dir = Path(__file__).parent

    # Top-level MCP source files
    for name in ("mcp.py", "mcp_guardrails.py"):
        path = api_dir / name
        try:
            ast.parse(path.read_text())
        except SyntaxError as e:
            errors.append(f"{name}:{e.lineno}: {e.msg}")
        except FileNotFoundError:
            errors.append(f"{name}: file not found")

    # mcp_handlers package — walk all *.py files inside it
    handlers_dir = api_dir / "mcp_handlers"
    if not handlers_dir.is_dir():
        errors.append("mcp_handlers/: directory not found")
    else:
        for py_file in sorted(handlers_dir.rglob("*.py")):
            rel = py_file.relative_to(api_dir)
            try:
                ast.parse(py_file.read_text())
            except SyntaxError as e:
                errors.append(f"{rel}:{e.lineno}: {e.msg}")

    return {"check": "syntax", "errors": errors, "ok": len(errors) == 0}


def validate_mcp_exports() -> dict[str, Any]:
    """Check that mcp.py exports the required functions."""
    import app.api.mcp as mcp_mod

    missing = REQUIRED_MCP_EXPORTS - set(dir(mcp_mod))
    return {
        "check": "exports",
        "missing": sorted(missing),
        "ok": len(missing) == 0,
    }


def validate_handler_signatures() -> dict[str, Any]:
    """Check that all MCP handlers have the expected (arguments, request_id) signature."""
    import app.api.mcp_handlers as handlers_mod

    errors: list[str] = []
    for name, expected_params in REQUIRED_HANDLER_SIGNATURES.items():
        fn = getattr(handlers_mod, name, None)
        if fn is None:
            errors.append(f"Handler '{name}' not found in mcp_handlers")
            continue
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        if params != expected_params:
            errors.append(
                f"Handler '{name}' signature is {params}, expected {expected_params}"
            )
    return {"check": "handler_signatures", "errors": errors, "ok": len(errors) == 0}


def validate_tool_registry() -> dict[str, Any]:
    """Check that TOOL_HANDLERS in mcp_handlers.py covers all required tools."""
    import app.api.mcp_handlers as handlers_mod

    registry = getattr(handlers_mod, "TOOL_HANDLERS", {})
    registered = set(registry.keys())
    missing = REQUIRED_TOOL_NAMES - registered
    extra = registered - REQUIRED_TOOL_NAMES - {"skill_*"}
    return {
        "check": "tool_registry",
        "missing": sorted(missing),
        "extra": sorted(extra),
        "registered_count": len(registered),
        "ok": len(missing) == 0,
    }


def validate_dispatch_tool() -> dict[str, Any]:
    """Check that dispatch_tool exists and is callable."""
    import app.api.mcp_handlers as handlers_mod

    fn = getattr(handlers_mod, "dispatch_tool", None)
    if fn is None:
        return {"check": "dispatch_tool", "ok": False, "error": "dispatch_tool not found"}
    if not callable(fn):
        return {"check": "dispatch_tool", "ok": False, "error": "dispatch_tool not callable"}
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    if "body" not in params:
        return {"check": "dispatch_tool", "ok": False, "error": f"dispatch_tool params: {params}"}
    return {"check": "dispatch_tool", "ok": True}


def validate_frontend_port_consistency() -> dict[str, Any]:
    """Check that all backend port references for the frontend use the correct port.

    The Vue frontend runs on port 5175. Stale references to 5173 (React) or
    5174 (old Vue) will cause the menu to fail to connect.
    """
    import re
    correct_port = "5175"
    stale_ports = {"5173", "5174"}
    patterns = [
        r"http://localhost:(\d+)",
        r"port[=:]\s*(\d+)",
        r"create_connection\(\(\"127\.0\.0\.1\",\s*(\d+)\)",
    ]
    errors: list[str] = []

    # Check all Python files in the menu package (skip archived/)
    menu_dir = Path(__file__).parent.parent / "menu"
    for py_file in menu_dir.rglob("*.py"):
        if "archived" in py_file.parts:
            continue
        content = py_file.read_text()
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                port = match.group(1)
                if port in stale_ports:
                    errors.append(
                        f"{py_file.name}:{port} — stale port, should be {correct_port}"
                    )

    return {
        "check": "frontend_port_consistency",
        "errors": errors,
        "ok": len(errors) == 0,
    }


def validate_mcp_integrity() -> dict[str, Any]:
    """Run all MCP integrity checks and return a combined report.

    Returns:
        dict with 'checks' list, 'errors' list, and 'ok' boolean.
    """
    checks = [
        validate_mcp_syntax(),
        validate_mcp_exports(),
        validate_handler_signatures(),
        validate_tool_registry(),
        validate_dispatch_tool(),
        validate_frontend_port_consistency(),
    ]
    all_errors = []
    for c in checks:
        if not c.get("ok"):
            all_errors.extend(c.get("errors", []) or c.get("missing", []) or [c.get("error", "unknown")])

    report = {
        "checks": checks,
        "errors": all_errors,
        "ok": len(all_errors) == 0,
    }

    if report["ok"]:
        log.info("MCP integrity check passed (%d checks)", len(checks))
    else:
        log.error("MCP integrity check FAILED: %s", all_errors)

    return report
