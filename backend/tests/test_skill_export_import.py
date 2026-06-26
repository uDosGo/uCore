"""Tests for Export and Import Surface skills."""
from __future__ import annotations

import pytest
from app.services.surface_manager import SurfaceManager
from app.skills.builtin.export import ExportSurface
from app.skills.builtin.import_skill import ImportSurface


@pytest.mark.asyncio
async def test_export_nonexistent():
    skill = ExportSurface()
    result = await skill.run(surface_id="nonexistent")
    assert result["success"] is False
    assert "not found" in result.get("error", "")


@pytest.mark.asyncio
async def test_export_success():
    mgr = SurfaceManager(persist=False)
    s = mgr.create_surface("ExportTest", type="prose", metadata={"key": "val"})

    import app.skills.builtin.export as mod
    mod.SurfaceManager = lambda: mgr

    skill = ExportSurface()
    result = await skill.run(surface_id=s.id)
    assert result["success"] is True
    assert result["data"]["name"] == "ExportTest"
    assert result["data"]["type"] == "prose"
    assert result["data"]["metadata"]["key"] == "val"


@pytest.mark.asyncio
async def test_import_surface():
    mgr = SurfaceManager(persist=False)

    import app.skills.builtin.import_skill as mod
    mod.SurfaceManager = lambda: mgr

    skill = ImportSurface()
    result = await skill.run(data={"name": "Imported", "type": "grid"})
    assert result["success"] is True
    assert result["surface"]["name"] == "Imported"
    assert result["surface"]["type"] == "grid"


@pytest.mark.asyncio
async def test_import_roundtrip():
    """Export a surface, then re-import just the name/type/metadata (skip id)."""
    mgr = SurfaceManager(persist=False)
    s = mgr.create_surface("Roundtrip", type="dashboard")

    import app.skills.builtin.export as export_mod
    import app.skills.builtin.import_skill as import_mod
    export_mod.SurfaceManager = lambda: mgr
    import_mod.SurfaceManager = lambda: mgr

    export_skill = ExportSurface()
    exported = await export_skill.run(surface_id=s.id)

    # Strip id/state fields before re-importing
    import_data = {k: v for k, v in exported["data"].items() if k in ("name", "type", "metadata")}
    import_skill = ImportSurface()
    result = await import_skill.run(data=import_data)
    assert result["success"] is True
    assert result["surface"]["name"] == "Roundtrip"
