"""Dev Mode Snack - Development workflow operations.

Category: dev
Tags: Dev Mode
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from snackmachine.registry import SnackPlugin, SnackSpec, register_snack

log = logging.getLogger("dev-mode-snack")


class DevModeSnack(SnackPlugin):
    """Development mode operations."""

    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate

    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(
            id="dev-mode",
            name="Dev Mode",
            icon="🛠️",
            kind="multi-action",
            category="dev",
            enabled=True,
            actions=["start-dev", "stop-dev", "restart-dev", "open-devtools"],
            metadata={
                "description": "Development workflow operations",
                "tags": ["Dev Mode"],
                "version": "1.0.0",
            },
        )

    def is_available(self) -> bool:
        return True

    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if action == "start-dev":
            return self._start_dev()
        elif action == "stop-dev":
            return self._stop_dev()
        elif action == "restart-dev":
            return self._restart_dev()
        elif action == "open-devtools":
            return self._open_devtools()
        return False

    def _start_dev(self) -> bool:
        """Start development servers."""
        try:
            subprocess.Popen(
                ["pnpm", "--filter", "frontend-vue", "run", "dev"],
                cwd=os.environ.get("UCORE_ROOT", str(Path.home() / "Code" / "uCore")),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except Exception as e:
            log.error(f"Failed to start dev: {e}")
            return False

    def _stop_dev(self) -> bool:
        """Stop development servers."""
        try:
            subprocess.run(["pkill", "-f", "vite"], capture_output=True)
            return True
        except Exception as e:
            log.error(f"Failed to stop dev: {e}")
            return False

    def _restart_dev(self) -> bool:
        """Restart development servers."""
        self._stop_dev()
        return self._start_dev()

    def _open_devtools(self) -> bool:
        """Open dev tools in browser."""
        try:
            subprocess.run(
                ["open", "http://localhost:5174"],
                capture_output=True, check=False
            )
            return True
        except Exception as e:
            log.error(f"Failed to open devtools: {e}")
            return False


# Register on import
def register(menu_delegate=None):
    plugin = DevModeSnack(menu_delegate)
    register_snack(plugin)
    return plugin
