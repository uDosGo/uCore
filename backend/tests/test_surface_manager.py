"""Tests for SurfaceManager service."""
from __future__ import annotations

import pytest
from app.models.surface import SurfaceType, SurfaceState
from app.services.surface_manager import SurfaceManager


class TestSurfaceManager:
    def setup_method(self):
        self.mgr = SurfaceManager(persist=False)

    def test_create_surface(self):
        s = self.mgr.create_surface("Test", SurfaceType.PROSE)
        assert s.name == "Test"
        assert s.type == SurfaceType.PROSE
        assert s.state == SurfaceState.CREATED
        assert len(s.id) > 0

    def test_get_surface(self):
        s = self.mgr.create_surface("Find Me", SurfaceType.GRID)
        found = self.mgr.get_surface(s.id)
        assert found is not None
        assert found.name == "Find Me"

    def test_get_nonexistent(self):
        assert self.mgr.get_surface("nope") is None

    def test_list_surfaces(self):
        self.mgr.create_surface("A", SurfaceType.PROSE)
        self.mgr.create_surface("B", SurfaceType.GRID)
        self.mgr.create_surface("C", SurfaceType.TERMINAL)
        assert len(self.mgr.list_surfaces()) == 3

    def test_list_by_type(self):
        self.mgr.create_surface("A", SurfaceType.PROSE)
        self.mgr.create_surface("B", SurfaceType.PROSE)
        self.mgr.create_surface("C", SurfaceType.GRID)
        assert len(self.mgr.list_by_type(SurfaceType.PROSE)) == 2
        assert len(self.mgr.list_by_type(SurfaceType.GRID)) == 1
        assert len(self.mgr.list_by_type(SurfaceType.TERMINAL)) == 0

    def test_transition_state(self):
        s = self.mgr.create_surface("Test", SurfaceType.PROSE)
        self.mgr.transition_state(s.id, SurfaceState.RUNNING)
        updated = self.mgr.get_surface(s.id)
        assert updated is not None
        assert updated.state == SurfaceState.RUNNING

    def test_transition_nonexistent(self):
        result = self.mgr.transition_state("nope", SurfaceState.RUNNING)
        assert result is None

    def test_delete_surface(self):
        s = self.mgr.create_surface("Delete Me", SurfaceType.PROSE)
        assert self.mgr.count() == 1
        assert self.mgr.delete_surface(s.id) is True
        assert self.mgr.count() == 0
        assert self.mgr.delete_surface("nope") is False

    def test_update_surface(self):
        s = self.mgr.create_surface("Original", SurfaceType.PROSE)
        self.mgr.update_surface(s.id, name="Updated", metadata={"key": "val"})
        updated = self.mgr.get_surface(s.id)
        assert updated is not None
        assert updated.name == "Updated"
        assert updated.metadata.get("key") == "val"

    def test_persistent_create_and_get(self):
        """Test that persistent mode stores and retrieves correctly."""
        from app.core.database import migrate_db
        migrate_db()  # Ensure tables exist
        mgr = SurfaceManager(persist=True)
        s = mgr.create_surface("Persist Test", SurfaceType.GRID, metadata={"env": "test"})
        mgr2 = SurfaceManager(persist=True)
        loaded = mgr2.get_surface(s.id)
        assert loaded is not None
        assert loaded.name == "Persist Test"
        assert loaded.type == SurfaceType.GRID
        assert loaded.metadata.get("env") == "test"
        mgr2.delete_surface(s.id)
        # Verify cleanup
        assert mgr2.get_surface(s.id) is None

    def test_persistent_list(self):
        """Test listing surfaces works with persistence."""
        mgr = SurfaceManager(persist=True)
        s1 = mgr.create_surface("Persist A")
        s2 = mgr.create_surface("Persist B")
        all_surfaces = mgr.list_surfaces()
        # We should have at least 2 (may have stale data from other tests)
        assert len(all_surfaces) >= 2
        # Verify our two are in there
        ids = [s.id for s in all_surfaces]
        assert s1.id in ids
        assert s2.id in ids
        mgr.delete_surface(s1.id)
        mgr.delete_surface(s2.id)
