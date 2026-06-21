"""Tests for the SurfaceRestart skill."""
from __future__ import annotations

import pytest

from app.skills.builtin.surface_restart import SurfaceRestart
from app.services.surface_manager import SurfaceManager


@pytest.mark.asyncio
async def test_restart_nonexistent_surface():
    skill = SurfaceRestart()
    result = await skill.run(surface_id="nonexistent")
    assert result["success"] is False
    assert "not found" in result.get("error", "")


@pytest.mark.asyncio
async def test_restart_created_surface():
    mgr = SurfaceManager(persist=False)
    s = mgr.create_surface("RestartTest", type="prose")

    import app.skills.builtin.surface_restart as mod
    mod.SurfaceManager = lambda: mgr

    skill = SurfaceRestart()
    result = await skill.run(surface_id=s.id)
    assert result["success"] is True
    updated = mgr.get_surface(s.id)
    from app.models.surface import SurfaceState
    assert updated.state == SurfaceState.RUNNING


@pytest.mark.asyncio
async def test_restart_running_surface():
    mgr = SurfaceManager(persist=False)
    from app.models.surface import SurfaceState
    s = mgr.create_surface("Running", type="prose")
    mgr.transition_state(s.id, SurfaceState.RUNNING)

    import app.skills.builtin.surface_restart as mod
    mod.SurfaceManager = lambda: mgr

    skill = SurfaceRestart()
    result = await skill.run(surface_id=s.id)
    assert result["success"] is True
