"""Tests for the SurfaceRepair skill."""
from __future__ import annotations

import pytest

from app.skills.builtin.surface_repair import SurfaceRepair
from app.services.surface_manager import SurfaceManager


@pytest.mark.asyncio
async def test_repair_nonexistent_surface():
    skill = SurfaceRepair()
    result = await skill.run(surface_id="nonexistent")
    assert result["success"] is False
    assert "not found" in result.get("error", "")


@pytest.mark.asyncio
async def test_repair_healthy_surface():
    mgr = SurfaceManager(persist=False)
    s = mgr.create_surface("Healthy", type="prose")

    # Patch the SurfaceManager used by the skill
    import app.skills.builtin.surface_repair as mod
    mod.SurfaceManager = lambda: mgr

    skill = SurfaceRepair()
    result = await skill.run(surface_id=s.id)
    assert result["success"] is True
    assert len(result.get("issues", [])) == 0


@pytest.mark.asyncio
async def test_repair_repairs_issues():
    mgr = SurfaceManager(persist=False)
    from app.models.surface import SurfaceState
    s = mgr.create_surface("", type="prose")  # Empty name
    mgr.transition_state(s.id, SurfaceState.ERROR)

    import app.skills.builtin.surface_repair as mod
    mod.SurfaceManager = lambda: mgr

    skill = SurfaceRepair()
    result = await skill.run(surface_id=s.id)
    assert result["success"] is True
    # Should have repaired the surface
    repaired = mgr.get_surface(s.id)
    assert repaired.state == SurfaceState.STOPPED
    assert repaired.name != ""
