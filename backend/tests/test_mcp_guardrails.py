"""Tests for MCP integrity guardrails and self-heal skill."""
from __future__ import annotations

import pytest

from app.api.mcp_guardrails import (
    REQUIRED_MCP_EXPORTS,
    REQUIRED_TOOL_NAMES,
    validate_dispatch_tool,
    validate_handler_signatures,
    validate_mcp_exports,
    validate_mcp_integrity,
    validate_mcp_syntax,
    validate_tool_registry,
)


class TestMCPGuardrails:
    """Validate that the MCP layer is structurally sound."""

    def test_syntax_check_passes(self):
        report = validate_mcp_syntax()
        assert report["ok"], f"Syntax errors: {report['errors']}"

    def test_exports_check_passes(self):
        report = validate_mcp_exports()
        assert report["ok"], f"Missing exports: {report['missing']}"

    def test_handler_signatures_check_passes(self):
        report = validate_handler_signatures()
        assert report["ok"], f"Signature errors: {report['errors']}"

    def test_tool_registry_check_passes(self):
        report = validate_tool_registry()
        assert report["ok"], f"Missing tools: {report['missing']}"

    def test_dispatch_tool_check_passes(self):
        report = validate_dispatch_tool()
        assert report["ok"], f"dispatch_tool error: {report.get('error')}"

    def test_full_integrity_check_passes(self):
        report = validate_mcp_integrity()
        assert report["ok"], f"Integrity errors: {report['errors']}"

    def test_required_exports_are_complete(self):
        """Ensure the expected exports list covers the critical functions."""
        assert "handle_mcp_discover" in REQUIRED_MCP_EXPORTS
        assert "handle_mcp_call" in REQUIRED_MCP_EXPORTS

    def test_required_tools_are_complete(self):
        """Ensure the expected tools list covers all built-in tools."""
        assert "knowledge_search" in REQUIRED_TOOL_NAMES
        assert "clipboard_capture" in REQUIRED_TOOL_NAMES
        assert "tasker_list_boards" in REQUIRED_TOOL_NAMES
        assert "gridsmith_create_grid" in REQUIRED_TOOL_NAMES
        assert "toon_encode" in REQUIRED_TOOL_NAMES
        assert "flow_router_route" in REQUIRED_TOOL_NAMES
        assert "autostart_health_check" in REQUIRED_TOOL_NAMES


class TestMCPSelfHealSkill:
    """Test the MCP self-heal skill."""

    def test_self_heal_dry_run(self):
        import asyncio

        from app.skills.builtin.skill_mcp_self_heal import MCPSelfHealSkill

        skill = MCPSelfHealSkill()
        result = asyncio.run(skill.run(dry_run=True))
        assert result["success"] is True

    def test_self_heal_detects_healthy_state(self):
        import asyncio

        from app.skills.builtin.skill_mcp_self_heal import MCPSelfHealSkill

        skill = MCPSelfHealSkill()
        result = asyncio.run(skill.run(dry_run=True))
        # When MCP is healthy, no repairs needed
        if not result.get("repairs"):
            assert "no repairs needed" in result.get("message", "").lower() or result["success"]
