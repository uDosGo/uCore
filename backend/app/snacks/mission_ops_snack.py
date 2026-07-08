"""Mission Operations Snack - User mission workflow operations.

Category: mission
Tags: User Mission Operations
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from snackmachine.registry import SnackPlugin, SnackSpec, register_snack

log = logging.getLogger("mission-ops-snack")


class MissionOpsSnack(SnackPlugin):
    """User mission operations."""

    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate

    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(
            id="mission-ops",
            name="Mission Ops",
            icon="🚀",
            kind="multi-action",
            category="mission",
            enabled=True,
            actions=["queue-mission", "list-missions", "clear-missions"],
            metadata={
                "description": "User mission workflow operations",
                "tags": ["User Mission Operations"],
                "version": "1.0.0",
            },
        )

    def is_available(self) -> bool:
        return True

    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if action == "queue-mission":
            return self._queue_mission(kwargs)
        elif action == "list-missions":
            return self._list_missions()
        elif action == "clear-missions":
            return self._clear_missions()
        return False

    def _queue_mission(self, params: dict) -> dict:
        """Queue a mission snack."""
        try:
            import json
            import urllib.request

            data = json.dumps(params).encode()
            req = urllib.request.Request(
                "http://127.0.0.1:8484/api/snacks",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return {"success": True, "result": resp.read().decode()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_missions(self) -> dict:
        """List pending missions."""
        try:
            import json
            import urllib.request

            req = urllib.request.Request("http://127.0.0.1:8484/api/snacks")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return {"success": True, "missions": data.get("snacks", [])}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _clear_missions(self) -> bool:
        """Clear all pending missions."""
        try:
            import urllib.request

            req = urllib.request.Request(
                "http://127.0.0.1:8484/api/snacks/queue",
                method="DELETE",
            )
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception as e:
            log.error(f"Failed to clear missions: {e}")
            return False


# Register on import
def register(menu_delegate=None):
    plugin = MissionOpsSnack(menu_delegate)
    register_snack(plugin)
    return plugin
