"""Snack Registry — Modular plugin system for uCore menu bar snacks.

Each snack is a self-contained module that registers itself with the registry.
Snacks can be loaded dynamically from backend API or defined locally.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

log = logging.getLogger("snack-registry")


@dataclass
class SnackSpec:
    """Specification for a snack plugin."""
    id: str
    name: str
    icon: str = "🍎"
    kind: str = "action"  # action, multi-action, badge, toggle, separator
    category: str = "custom"  # clipboard, ai, surface, system, custom
    enabled: bool = True
    handler: Optional[Callable] = None
    shortcut: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)  # for multi-action snacks

    def to_dict(self) -> dict:
        """Convert to dictionary for API serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "kind": self.kind,
            "category": self.category,
            "enabled": self.enabled,
            "shortcut": self.shortcut,
            "metadata": self.metadata,
            "actions": self.actions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnackSpec":
        """Create from dictionary (e.g., from backend API)."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            icon=data.get("icon", "🍎"),
            kind=data.get("kind", "action"),
            category=data.get("category", "custom"),
            enabled=data.get("enabled", True),
            shortcut=data.get("shortcut"),
            metadata=data.get("metadata", {}),
            actions=data.get("actions", []),
        )


class SnackPlugin(ABC):
    """Base class for snack plugins."""

    @property
    @abstractmethod
    def spec(self) -> SnackSpec:
        """Return the snack specification."""
        pass

    @abstractmethod
    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        """Execute the snack action."""
        pass

    def is_available(self) -> bool:
        """Check if snack is available (e.g., backend connected)."""
        return True


class SnackRegistry:
    """Registry for managing snack plugins."""

    def __init__(self):
        self._snacks: dict[str, SnackPlugin] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, plugin: SnackPlugin) -> None:
        """Register a snack plugin."""
        spec = plugin.spec
        self._snacks[spec.id] = plugin
        if spec.category not in self._categories:
            self._categories[spec.category] = []
        if spec.id not in self._categories[spec.category]:
            self._categories[spec.category].append(spec.id)
        log.info(f"Registered snack: {spec.id} ({spec.category})")

    def unregister(self, snack_id: str) -> bool:
        """Unregister a snack plugin."""
        if snack_id in self._snacks:
            plugin = self._snacks.pop(snack_id)
            category = plugin.spec.category
            if category in self._categories and snack_id in self._categories[category]:
                self._categories[category].remove(snack_id)
            log.info(f"Unregistered snack: {snack_id}")
            return True
        return False

    def get(self, snack_id: str) -> Optional[SnackPlugin]:
        """Get a snack plugin by ID."""
        return self._snacks.get(snack_id)

    def get_all(self, category: Optional[str] = None, enabled_only: bool = True) -> list[SnackPlugin]:
        """Get all snacks, optionally filtered by category and enabled status."""
        snacks = list(self._snacks.values())
        if category:
            snacks = [s for s in snacks if s.spec.category == category]
        if enabled_only:
            snacks = [s for s in snacks if s.spec.enabled and s.is_available()]
        return snacks

    def get_by_category(self, enabled_only: bool = True) -> dict[str, list[SnackPlugin]]:
        """Get snacks grouped by category."""
        result = {}
        for category, snack_ids in self._categories.items():
            snacks = [self._snacks[sid] for sid in snack_ids if sid in self._snacks]
            if enabled_only:
                snacks = [s for s in snacks if s.spec.enabled and s.is_available()]
            if snacks:
                result[category] = snacks
        return result

    def get_specs(self, category: Optional[str] = None, enabled_only: bool = True) -> list[dict]:
        """Get snack specifications as dictionaries (for API/menu building)."""
        return [s.spec.to_dict() for s in self.get_all(category, enabled_only)]

    def update_from_backend(self, backend_snacks: list[dict]) -> None:
        """Update registry from backend API response."""
        backend_ids = set()
        for snack_data in backend_snacks:
            snack_id = snack_data.get("id")
            if not snack_id:
                continue
            backend_ids.add(snack_id)

            # If we have a local plugin with this ID, update its spec
            if snack_id in self._snacks:
                plugin = self._snacks[snack_id]
                # Merge backend spec with local spec (backend wins for dynamic fields)
                backend_spec = SnackSpec.from_dict(snack_data)
                local_spec = plugin.spec
                # Preserve local handler but update other fields
                backend_spec.handler = local_spec.handler
                # Update the plugin's spec (would need a setter or recreate)
                # For now, just log
                log.debug(f"Backend update for snack: {snack_id}")
            else:
                # Could dynamically create a generic plugin for backend-only snacks
                log.debug(f"Backend-only snack (no local plugin): {snack_id}")

        # Optionally remove snacks that are no longer in backend
        # (but keep local-only snacks)

    def execute(self, snack_id: str, action: Optional[str] = None, **kwargs) -> Any:
        """Execute a snack by ID."""
        plugin = self.get(snack_id)
        if plugin:
            return plugin.execute(action, **kwargs)
        log.warning(f"Snack not found: {snack_id}")
        return None


# Global registry instance
_registry: Optional[SnackRegistry] = None


def get_registry() -> SnackRegistry:
    """Get the global snack registry."""
    global _registry
    if _registry is None:
        _registry = SnackRegistry()
    return _registry


def register_snack(plugin: SnackPlugin) -> None:
    """Convenience function to register a snack."""
    get_registry().register(plugin)
