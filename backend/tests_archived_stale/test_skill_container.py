"""Tests for ContainerStart and ContainerStop skills."""
from __future__ import annotations

import pytest
from app.skills.builtin.container_start import ContainerStart
from app.skills.builtin.container_stop import ContainerStop

from app.services.container_manager import ContainerManager


@pytest.mark.asyncio
async def test_container_start_nonexistent():
    skill = ContainerStart()
    result = await skill.run(container_id="nonexistent")
    assert result["success"] is False
    assert "not found" in result.get("error", "")


@pytest.mark.asyncio
async def test_container_start_success():
    mgr = ContainerManager(persist=False)
    c = mgr.create_container("TestStart", runtime="python")

    import app.skills.builtin.container_start as mod
    mod.ContainerManager = lambda: mgr

    skill = ContainerStart()
    result = await skill.run(container_id=c.id)
    assert result["success"] is True
    updated = mgr.get_container(c.id)
    from app.models.container import ContainerStatus
    assert updated.status == ContainerStatus.RUNNING


@pytest.mark.asyncio
async def test_container_stop_nonexistent():
    skill = ContainerStop()
    result = await skill.run(container_id="nonexistent")
    assert result["success"] is False
    assert "not found" in result.get("error", "")


@pytest.mark.asyncio
async def test_container_stop_success():
    mgr = ContainerManager(persist=False)
    c = mgr.create_container("TestStop", runtime="python")

    import app.skills.builtin.container_stop as mod
    mod.ContainerManager = lambda: mgr

    skill = ContainerStop()
    result = await skill.run(container_id=c.id)
    assert result["success"] is True
    updated = mgr.get_container(c.id)
    from app.models.container import ContainerStatus
    assert updated.status == ContainerStatus.STOPPED
