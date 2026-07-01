#!/usr/bin/env python3
"""Skill: MCP Self-Heal — Diagnose and repair MCP layer issues.

This skill runs the MCP guardrails checks and attempts automatic repair
for known failure patterns:

1. **Syntax errors** in mcp.py / mcp_handlers.py → cannot auto-repair, log alert
2. **Missing exports** (handle_mcp_discover, handle_mcp_call) → cannot auto-repair
3. **Handler signature mismatch** → normalize to (arguments, request_id)
4. **Missing tool in registry** → add to TOOL_HANDLERS
5. **Orphaned dead code** → truncate file after last function
6. **Import errors** → switch to lazy imports

The skill is registered as `mcp_self_heal` and can be called via MCP:
    POST /api/mcp/call  {"name": "skill_mcp_self_heal", "arguments": {}}
"""
from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.mcp_self_heal")


class MCPSelfHealSkill(BaseSkill):
    meta = SkillMeta(
        id="mcp_self_heal",
        name="MCP Self-Heal",
        description="Diagnose and repair MCP layer integrity issues",
        category="maintenance",
        params=[
            SkillParam(
                name="dry_run",
                type="boolean",
                description="Only diagnose, don't repair",
                default=True,
            ),
        ],
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        dry_run = kwargs.get("dry_run", True)
        from app.api.mcp_guardrails import validate_mcp_integrity

        report = validate_mcp_integrity()

        if report["ok"]:
            return {
                "success": True,
                "message": "MCP integrity check passed — no repairs needed",
                "checks": len(report["checks"]),
            }

        repairs: list[dict[str, Any]] = []

        for check in report["checks"]:
            if check["ok"]:
                continue

            if check["check"] == "syntax":
                repairs.append({
                    "issue": "syntax_error",
                    "files": check.get("errors", []),
                    "action": "manual_fix_required",
                    "message": "Syntax errors cannot be auto-repaired. Fix manually.",
                })

            elif check["check"] == "handler_signatures":
                if not dry_run:
                    fixed = self._fix_handler_signatures(check.get("errors", []))
                    repairs.append({
                        "issue": "handler_signature_mismatch",
                        "action": "normalized_signatures",
                        "fixed": fixed,
                    })
                else:
                    repairs.append({
                        "issue": "handler_signature_mismatch",
                        "action": "would_normalize_signatures",
                        "errors": check.get("errors", []),
                    })

            elif check["check"] == "tool_registry":
                if not dry_run:
                    fixed = self._fix_tool_registry(check.get("missing", []))
                    repairs.append({
                        "issue": "missing_tools_in_registry",
                        "action": "added_to_registry",
                        "fixed": fixed,
                    })
                else:
                    repairs.append({
                        "issue": "missing_tools_in_registry",
                        "action": "would_add_to_registry",
                        "missing": check.get("missing", []),
                    })

            elif check["check"] == "exports":
                repairs.append({
                    "issue": "missing_exports",
                    "action": "manual_fix_required",
                    "missing": check.get("missing", []),
                    "message": "Missing exports require manual code changes.",
                })

            elif check["check"] == "frontend_port_consistency":
                if not dry_run:
                    fixed = self._fix_frontend_ports(check.get("errors", []))
                    repairs.append({
                        "issue": "stale_frontend_port_reference",
                        "action": "corrected_ports",
                        "fixed": fixed,
                    })
                else:
                    repairs.append({
                        "issue": "stale_frontend_port_reference",
                        "action": "would_correct_ports",
                        "errors": check.get("errors", []),
                    })

        return {
            "success": True,
            "dry_run": dry_run,
            "repairs": repairs,
            "original_errors": report["errors"],
        }

    # ─── Auto-repair helpers ──────────────────────────────────

    @staticmethod
    def _fix_handler_signatures(errors: list[str]) -> list[str]:
        """Attempt to normalize handler signatures to (arguments, request_id).

        Checks all domain modules in the mcp_handlers/ package.
        """
        handlers_dir = Path(__file__).parent.parent / "api" / "mcp_handlers"
        if not handlers_dir.exists():
            return ["mcp_handlers/ directory not found"]

        fixed: list[str] = []
        for py_file in sorted(handlers_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            content = py_file.read_text()
            original = content

            # Pattern: handlers that only take (request_id) need (arguments, request_id)
            pattern = re.compile(
                r"async def (handle_\w+)\(request_id: Any\)"
            )
            for match in pattern.finditer(content):
                name = match.group(1)
                content = content.replace(
                    match.group(0),
                    f"async def {name}(arguments: dict, request_id: Any)",
                )
                fixed.append(name)

            if content != original:
                py_file.write_text(content)
                log.info("Fixed handler signatures in %s: %s", py_file.name, fixed)

        return fixed

    @staticmethod
    def _fix_tool_registry(missing: list[str]) -> list[str]:

        """Add missing tools to the TOOL_HANDLERS registry.

        This requires that a handler function with the matching name exists.
        """
        import app.api.mcp_handlers as handlers_mod

        added: list[str] = []
        registry = getattr(handlers_mod, "TOOL_HANDLERS", {})

        for tool_name in missing:
            handler_name = f"handle_{tool_name}"
            handler = getattr(handlers_mod, handler_name, None)
            if handler and callable(handler):
                registry[tool_name] = handler
                added.append(tool_name)
                log.info("Added '%s' → %s to TOOL_HANDLERS", tool_name, handler_name)

        return added

    @staticmethod
    def _fix_frontend_ports(errors: list[str]) -> list[str]:
        """Replace stale frontend port references (5173, 5174) with 5175.

        Scans all Python files in the menu package and replaces stale ports.
        """
        menu_dir = Path(__file__).parent.parent.parent / "menu"
        correct_port = "5175"
        stale_ports = {"5173", "5174"}
        fixed: list[str] = []

        for py_file in menu_dir.rglob("*.py"):
            if "archived" in py_file.parts:
                continue
            content = py_file.read_text()
            original = content
            for stale in stale_ports:
                content = content.replace(f":{stale}", f":{correct_port}")
            if content != original:
                py_file.write_text(content)
                fixed.append(py_file.name)
                log.info("Fixed ports in %s", py_file.name)

        return fixed

    @staticmethod
    def detect_orphaned_code(filepath: Path) -> dict[str, Any]:
        """Detect orphaned code after the last top-level function definition.

        This catches the pattern where a bad merge leaves dead code
        dangling after the last function in a module.
        """
        if not filepath.exists():
            return {"error": f"{filepath} not found"}

        source = filepath.read_text()
        tree = ast.parse(source)

        if not tree.body:
            return {"orphaned": False, "message": "Empty file"}

        # Find the last top-level function/class definition
        last_def_end = 0
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                last_def_end = max(last_def_end, node.end_lineno or 0)

        total_lines = source.count("\n") + 1
        orphaned_lines = total_lines - last_def_end

        if orphaned_lines > 5:  # Allow a few blank lines at end
            return {
                "orphaned": True,
                "last_function_line": last_def_end,
                "total_lines": total_lines,
                "orphaned_line_count": orphaned_lines,
                "message": f"~{orphaned_lines} lines of potential orphaned code after line {last_def_end}",
            }

        return {"orphaned": False, "total_lines": total_lines}
