"""Tests for the VaultSync skill."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_vault_sync_no_config(tmp_path: Path, monkeypatch):
    """Should skip gracefully when config doesn't exist."""
    from app.skills.builtin.vault_sync import VaultSync

    fake_config = tmp_path / "nonexistent-config.yaml"

    skill = VaultSync()
    result = await skill.run(config=str(fake_config))
    assert result["success"] is True
    assert result.get("status") == "skipped"
    assert "config not found" in result.get("reason", "")


@pytest.mark.asyncio
async def test_vault_sync_no_script(tmp_path: Path, monkeypatch):
    """Should error when script doesn't exist."""
    from app.skills.builtin.vault_sync import VaultSync, SCRIPT_PATH

    # Point to a non-existent script
    fake_script = tmp_path / "nonexistent_script.py"
    monkeypatch.setattr("app.skills.builtin.vault_sync.SCRIPT_PATH", fake_script)

    skill = VaultSync()
    result = await skill.run(config=str(tmp_path / "config.yaml"))
    assert result["success"] is False
    assert "not found" in result.get("error", "")
