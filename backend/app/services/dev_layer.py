"""dev_layer — Dev Mode Layer toggle service.

Controls visibility of development controls across the uCore surface:
- ON: full dev surface (tasker board, kanban, spool viewer, plate refresh,
      vault tools, MCP diagnostics, all dev controls)
- OFF: production/user surface only (no dev tools visible)
- MINIMAL: status indicators only (popcorn icon color, tray text)

State is persisted to ~/.ucore/config.yaml and exposed via REST API.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger("ucore.services.dev_layer")

CONFIG_DIR = Path.home() / ".ucore"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class DevMode(Enum):
    ON = "on"
    OFF = "off"
    MINIMAL = "minimal"


@dataclass
class DevLayerState:
    """Current state of the Dev Mode Layer."""

    mode: DevMode = DevMode.OFF
    surfaces_visible: list[str] = field(default_factory=list)
    features_enabled: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "surfaces_visible": self.surfaces_visible,
            "features_enabled": self.features_enabled,
        }


# Map of Dev Mode → which surfaces are visible
SURFACE_VISIBILITY = {
    DevMode.ON: [
        "tasker_board",
        "kanban_board",
        "spool_viewer",
        "slate_refresh",
        "vault_tools",
        "mcp_diagnostics",
        "skill_runner",
        "catalog_browser",
        "hivemind_dashboard",
    ],
    DevMode.OFF: [],
    DevMode.MINIMAL: [
        "hivemind_dashboard",  # Status-only
    ],
}

# Map of Dev Mode → which features are enabled
FEATURE_VISIBILITY = {
    DevMode.ON: [
        "destroy_rebuild",
        "template_management",
        "distribution_sync",
        "secret_store_edit",
        "database_browse",
        "spool_clear",
        "wisdom_edit",
    ],
    DevMode.OFF: [],
    DevMode.MINIMAL: [],
}


class DevLayer:
    """Dev Mode Layer — controls visibility of dev surfaces and features."""

    def __init__(self) -> None:
        self._state = DevLayerState()
        self._load()

    # ── Public API ─────────────────────────────────────────────

    @property
    def mode(self) -> DevMode:
        return self._state.mode

    @mode.setter
    def mode(self, value: DevMode | str) -> None:
        if isinstance(value, str):
            try:
                value = DevMode(value.lower())
            except ValueError:
                log.warning("Invalid dev mode: %s (use on/off/minimal)", value)
                return
        if value != self._state.mode:
            self._state.mode = value
            self._refresh_visibility()
            self._save()
            log.info("Dev Mode → %s", value.value)

    def toggle(self) -> DevMode:
        """Cycle through OFF → MINIMAL → ON → OFF."""
        cycle = [DevMode.OFF, DevMode.MINIMAL, DevMode.ON]
        idx = cycle.index(self._state.mode) if self._state.mode in cycle else 0
        next_mode = cycle[(idx + 1) % len(cycle)]
        self.mode = next_mode
        return next_mode

    @property
    def surfaces(self) -> list[str]:
        """List of visible surface IDs based on current mode."""
        return self._state.surfaces_visible

    @property
    def features(self) -> list[str]:
        """List of enabled feature IDs based on current mode."""
        return self._state.features_enabled

    def is_surface_visible(self, surface_id: str) -> bool:
        """Check if a specific surface is visible in current mode."""
        return surface_id in self._state.surfaces_visible

    def is_feature_enabled(self, feature_id: str) -> bool:
        """Check if a specific feature is enabled in current mode."""
        return feature_id in self._state.features_enabled

    def set_surface_override(self, surface_id: str, visible: bool) -> None:
        """Override visibility for a specific surface."""
        if visible and surface_id not in self._state.surfaces_visible:
            self._state.surfaces_visible.append(surface_id)
        elif not visible and surface_id in self._state.surfaces_visible:
            self._state.surfaces_visible.remove(surface_id)
        self._save()

    def get_status(self) -> dict[str, Any]:
        """Return full status for API response."""
        return {
            "mode": self._state.mode.value,
            "surfaces": {
                "visible": self._state.surfaces_visible,
                "count": len(self._state.surfaces_visible),
            },
            "features": {
                "enabled": self._state.features_enabled,
                "count": len(self._state.features_enabled),
            },
        }

    def describe(self) -> str:
        """Human-readable description of current state."""
        mode_labels = {
            DevMode.ON: "🟢 ON — Full development surface visible",
            DevMode.OFF: "⚫ OFF — Production/user surface only",
            DevMode.MINIMAL: "🟡 MINIMAL — Status indicators only",
        }
        lines = [
            mode_labels.get(self._state.mode, "Unknown"),
            f"\nVisible surfaces ({len(self._state.surfaces_visible)}):",
        ]
        for s in self._state.surfaces_visible:
            lines.append(f"  • {s}")
        lines.append(f"\nEnabled features ({len(self._state.features_enabled)}):")
        for f in self._state.features_enabled:
            lines.append(f"  • {f}")
        return "\n".join(lines)

    # ── Persistence ────────────────────────────────────────────

    def _load(self) -> None:
        """Load persisted state from config file."""
        if not CONFIG_FILE.exists():
            self._refresh_visibility()
            return
        try:
            data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
            dev = data.get("dev_layer", {})
            mode_str = dev.get("mode", "off")
            try:
                self._state.mode = DevMode(mode_str.lower())
            except ValueError:
                self._state.mode = DevMode.OFF
            self._refresh_visibility()
        except Exception as e:
            log.warning("Failed to load dev layer config: %s", e)
            self._refresh_visibility()

    def _save(self) -> None:
        """Persist current state to config file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            existing = {}
            if CONFIG_FILE.exists():
                existing = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
            existing["dev_layer"] = {
                "mode": self._state.mode.value,
            }
            CONFIG_FILE.write_text(
                yaml.dump(existing, default_flow_style=False, sort_keys=False),
                encoding="utf-8",
            )
        except Exception as e:
            log.error("Failed to save dev layer config: %s", e)

    def _refresh_visibility(self) -> None:
        """Recompute visible surfaces and features based on current mode."""
        self._state.surfaces_visible = list(SURFACE_VISIBILITY.get(self._state.mode, []))
        self._state.features_enabled = list(FEATURE_VISIBILITY.get(self._state.mode, []))


# Singleton instance
_dev_layer: DevLayer | None = None


def get_dev_layer() -> DevLayer:
    """Get the singleton DevLayer instance."""
    global _dev_layer
    if _dev_layer is None:
        _dev_layer = DevLayer()
    return _dev_layer


def reset_dev_layer() -> None:
    """Reset the singleton (useful for testing)."""
    global _dev_layer
    _dev_layer = None
