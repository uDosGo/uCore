"""Tests for the tools registry — discovery, listing, and checking."""
from __future__ import annotations

import pytest

from app.tools.registry import check_tool, get_tool, list_tools


@pytest.mark.asyncio
async def test_list_tools():
    """list_tools returns all discovered tools."""
    tools = await list_tools()
    assert len(tools) >= 6  # github_cli, git, python, node, docker, ollama, vscode
    tool_ids = {t.id for t in tools}
    assert "github_cli" in tool_ids
    assert "git" in tool_ids
    assert "python" in tool_ids
    assert "vscode" in tool_ids


@pytest.mark.asyncio
async def test_list_tools_structure():
    """Each tool has required fields."""
    tools = await list_tools()
    for t in tools:
        assert t.id
        assert t.name
        assert hasattr(t, "installed")
        assert hasattr(t, "version")


def test_get_tool():
    """get_tool returns the tool instance by id."""
    tool = get_tool("git")
    assert tool is not None
    assert tool.id == "git"
    assert tool.name == "Git"


def test_get_tool_nonexistent():
    """get_tool returns None for unknown tools."""
    tool = get_tool("nonexistent_tool_xyz")
    assert tool is None


@pytest.mark.asyncio
async def test_check_tool():
    """check_tool returns ToolInfo for a known tool."""
    info = await check_tool("git")
    assert info.id == "git"
    assert info.installed is True  # git should always be available


@pytest.mark.asyncio
async def test_check_tool_nonexistent():
    """check_tool returns dict with error for unknown tool."""
    result = await check_tool("nonexistent_tool_xyz")
    assert isinstance(result, dict)
    assert result.get("installed") is False
    assert "not found" in result.get("error", "")


@pytest.mark.asyncio
async def test_github_cli_tool():
    """GitHub CLI tool check works (may or may not be installed)."""
    info = await check_tool("github_cli")
    assert info.id == "github_cli"
    assert isinstance(info.installed, bool)
    # If installed, version should be set
    if info.installed:
        assert info.version
