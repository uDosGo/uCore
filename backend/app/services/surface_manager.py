"""SurfaceManager — lifecycle management for UI surfaces in uCore.

Supports both in-memory and SQLite persistence backends.
Use SQLite by enabling the `persist=True` flag (default).
"""
from __future__ import annotations

from typing import Optional
import json
from datetime import datetime, timezone

from app.models.surface import Surface, SurfaceState, SurfaceType
from app.core.database import get_db, surface_from_row, now_iso


class SurfaceManager:
    """Manages the lifecycle of Surface instances with optional SQLite persistence."""

    def __init__(self, persist: bool = True) -> None:
        self._persist = persist
        self._cache: dict[str, Surface] = {}

    # ─── SQL Helpers ─────────────────────────────────────────────

    def _load_from_db(self, surface_id: str) -> Optional[Surface]:
        """Load a single surface from the database."""
        if not self._persist:
            return self._cache.get(surface_id)
        with get_db() as db:
            cursor = db.execute("SELECT * FROM surfaces WHERE id = ?", (surface_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return Surface(**surface_from_row(row))

    def _load_all_from_db(self) -> list[Surface]:
        """Load all surfaces from the database."""
        if not self._persist:
            return list(self._cache.values())
        with get_db() as db:
            cursor = db.execute("SELECT * FROM surfaces ORDER BY created_at ASC")
            return [Surface(**surface_from_row(row)) for row in cursor.fetchall()]

    def _save_to_db(self, surface: Surface) -> None:
        """Insert or replace a surface in the database."""
        if not self._persist:
            self._cache[surface.id] = surface
            return
        with get_db() as db:
            db.execute(
                """INSERT OR REPLACE INTO surfaces
                   (id, name, type, state, metadata_json, parent_id, position, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    surface.id,
                    surface.name,
                    surface.type.value,
                    surface.state.value,
                    json.dumps(surface.metadata),
                    surface.parent_id,
                    surface.position,
                    surface.created_at.isoformat(),
                    surface.updated_at.isoformat(),
                ),
            )

    def _delete_from_db(self, surface_id: str) -> bool:
        """Delete a surface from the database."""
        if not self._persist:
            if surface_id in self._cache:
                del self._cache[surface_id]
                return True
            return False
        with get_db() as db:
            cursor = db.execute("DELETE FROM surfaces WHERE id = ?", (surface_id,))
            return cursor.rowcount > 0

    # ─── Public API ──────────────────────────────────────────────

    def create_surface(
        self,
        name: str,
        type: SurfaceType = SurfaceType.PROSE,
        metadata: Optional[dict] = None,
        parent_id: Optional[str] = None,
        position: Optional[int] = None,
    ) -> Surface:
        """Create a new surface and persist it."""
        surface = Surface(
            name=name,
            type=type,
            state=SurfaceState.CREATED,
            metadata=metadata or {},
            parent_id=parent_id,
            position=position,
        )
        self._save_to_db(surface)
        return surface

    def get_surface(self, surface_id: str) -> Optional[Surface]:
        """Retrieve a surface by ID."""
        return self._load_from_db(surface_id)

    def list_surfaces(self) -> list[Surface]:
        """Return all registered surfaces."""
        return self._load_all_from_db()

    def list_by_type(self, type: SurfaceType) -> list[Surface]:
        """Return surfaces filtered by type."""
        return [s for s in self.list_surfaces() if s.type == type]

    def update_surface(
        self,
        surface_id: str,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
        position: Optional[int] = None,
    ) -> Optional[Surface]:
        """Update mutable fields on an existing surface."""
        surface = self._load_from_db(surface_id)
        if surface is None:
            return None
        if name is not None:
            surface.name = name
        if metadata is not None:
            surface.metadata.update(metadata)
        if position is not None:
            surface.position = position
        surface.updated_at = datetime.now(timezone.utc)
        self._save_to_db(surface)
        return surface

    def transition_state(self, surface_id: str, new_state: SurfaceState) -> Optional[Surface]:
        """Transition a surface to a new lifecycle state."""
        surface = self._load_from_db(surface_id)
        if surface is None:
            return None
        surface.update_state(new_state)
        self._save_to_db(surface)
        return surface

    def delete_surface(self, surface_id: str) -> bool:
        """Remove a surface. Returns True if deleted."""
        return self._delete_from_db(surface_id)

    def count(self) -> int:
        """Return the number of registered surfaces."""
        return len(self.list_surfaces())
