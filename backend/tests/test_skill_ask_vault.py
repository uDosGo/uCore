"""Tests for the AskVault skill."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_ask_vault_list_workspaces():
    from app.skills.builtin.ask_vault import AskVault
    skill = AskVault()
    result = await skill.run(query="list-workspaces")
    assert result["success"] is True
    assert result["action"] == "list-workspaces"


@pytest.mark.asyncio
async def test_ask_vault_list_docs():
    from app.skills.builtin.ask_vault import AskVault
    skill = AskVault()
    result = await skill.run(query="list-docs", limit=5)
    assert result["success"] is True
    assert result["action"] == "list-docs"


@pytest.mark.asyncio
async def test_ask_vault_search():
    from app.skills.builtin.ask_vault import AskVault
    skill = AskVault()
    result = await skill.run(query="test search query", limit=20)
    assert result["success"] is True
    assert result["action"] == "search"


@pytest.mark.asyncio
async def test_ask_vault_get_doc_not_found():
    from app.skills.builtin.ask_vault import AskVault
    skill = AskVault()
    result = await skill.run(query="get-doc::nonexistent_doc_id")
    assert result["success"] is False
    assert "not found" in result.get("error", "")
