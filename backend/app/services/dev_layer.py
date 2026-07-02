"""dev_layer — Dev Mode toggle service.

Simple 3-state toggle persisted to ~/.ucore/config.yaml.
Exposed via REST API at /api/dev-layer/state and /api/dev-layer/toggle.
"""
from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path

import yaml

log = logging.getLogger("ucore.services.dev_layer")

CONFIG_FILE = Path.home() / ".ucore" / "config.yaml"


class DevMode(Enum):
    ON = "on"
    OFF = "off"
    MINIMAL = "minimal"


class DevLayer:
    """Dev Mode Layer — 3-state toggle with YAML persistence."""

    def __init__(self) -> None:
        self.mode: DevMode = DevMode.OFF
        self._load()

    def toggle(self) -> DevMode:
        """Cycle OFF → MINIMAL → ON → OFF."""
        cycle = [DevMode.OFF, DevMode.MINIMAL, DevMode.ON]
        idx = cycle.index(self.mode) if self.mode in cycle else 0
        self.mode = cycle[(idx + 1) % len(cycle)]
        self._save()
        log.info("Dev Mode → %s", self.mode.value)
        return self.mode

    def get_status(self) -> dict:
        return {"mode": self.mode.value}

    # ── Persistence ──────────────────────────────────────────

    def _load(self) -> None:
        try:
            if not CONFIG_FILE.exists():
                return
            data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
            raw = data.get("dev_layer", {}).get("mode", "off")
            self.mode = DevMode(raw.lower())
        except Exception as e:
            log.warning("Failed to load dev layer config: %s", e)

    def _save(self) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if CONFIG_FILE.exists():
            try:
                data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
            except Exception:
                data = {}
        data["dev_layer"] = {"mode": self.mode.value}
        CONFIG_FILE.write_text(yaml.dump(data), encoding="utf-8")


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
