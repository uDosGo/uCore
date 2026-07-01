"""Spool Monitor Snack - Monitors logs and triggers notifications.

Category: system
Tags: System Operations, Maintenance
"""
from __future__ import annotations

import logging
import subprocess
import time
from typing import Any, Optional

from snackmachine.registry import SnackPlugin, SnackSpec, register_snack
from app.services.spool_reader import read_spool

log = logging.getLogger("spool-monitor-snack")


class SpoolMonitorSnack(SnackPlugin):
    """Monitor spool for errors and send notifications."""

    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate
        self._last_error_count = 0
        self._last_check = 0

    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(
            id="spool-monitor",
            name="Spool Monitor",
            icon="📊",
            kind="action",
            category="system",
            enabled=True,
            actions=["check", "monitor"],
            metadata={
                "description": "Monitor logs and send notifications",
                "tags": ["System Operations", "Maintenance"],
                "version": "1.0.0",
            },
        )

    def is_available(self) -> bool:
        return True

    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if action == "check":
            return self._check_spool()
        elif action == "monitor":
            return self._monitor_spool()
        return False

    def _check_spool(self) -> dict:
        """Check spool for errors."""
        entries = read_spool(max_entries=100)
        errors = [e for e in entries if e.is_error]
        return {
            "success": True,
            "total": len(entries),
            "errors": len(errors),
            "recent_errors": [e.to_dict() for e in errors[:5]],
        }

    def _monitor_spool(self) -> bool:
        """Monitor spool and notify on new errors."""
        now = time.time()
        if now - self._last_check < 60:
            return True

        self._last_check = now
        result = self._check_spool()

        if result["errors"] > self._last_error_count:
            new_errors = result["errors"] - self._last_error_count
            self._last_error_count = result["errors"]
            if new_errors > 0:
                self._notify(f"{new_errors} new error(s) detected in logs")
        return True

    def _notify(self, message: str) -> None:
        """Send macOS notification."""
        try:
            subprocess.run(
                ["osascript", "-e", f'display notification "{message}" with title "uCore Spool Monitor"'],
                capture_output=True, check=False
            )
        except Exception as e:
            log.warning(f"Failed to notify: {e}")


# Register on import
def register(menu_delegate=None):
    plugin = SpoolMonitorSnack(menu_delegate)
    register_snack(plugin)
    return plugin