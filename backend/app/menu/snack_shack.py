"""SnackShack — Consolidated snack management and publishing flow.

Provides:
- Unified snack queue management
- Spool-based log monitoring
- macOS notifications for critical events
- Publishing/restore flow (GitHub-like)
- Dogfooding protection via version tracking
- Lane tagging (System Operations, Dev Mode, User Mission Operations)
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

from snackmachine.registry import SnackPlugin, SnackSpec, register_snack
from app.services.spool_reader import read_spool

log = logging.getLogger("snack-shack")

UCORE_URL = "http://127.0.0.1:8484"
import os
SNACKS_REPO_PATH = Path(os.environ.get("UCORE_BACKEND_DIR", str(Path.home() / "Code" / "uCore" / "backend"))) / "app" / "snacks"
SNACKS_USER_PATH = Path.home() / ".ucore/snacks"
SNACKS_TEMPLATE_PATH = SNACKS_REPO_PATH / "templates"


class SnackShack(SnackPlugin):
    """Consolidated snack management and publishing flow."""

    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate
        self._last_error_count = 0
        self._last_spool_check = 0

    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(
            id="snack-shack",
            name="SnackShack",
            icon="�",
            kind="multi-action",
            category="system",
            enabled=True,
            actions=[
                "open-snackmachine",
                "check-spool",
                "monitor-errors",
                "publish-snack",
                "restore-snack",
                "list-snacks",
            ],
            metadata={
                "description": "Unified snack management and publishing",
            },
        )

    def is_available(self) -> bool:
        return True

    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if action == "open-snackmachine":
            return self._open_snackmachine()
        elif action == "check-spool":
            return self._check_spool()
        elif action == "monitor-errors":
            return self._monitor_errors()
        elif action == "publish-snack":
            snack_id = kwargs.get("snack_id")
            return self._publish_snack(snack_id)
        elif action == "restore-snack":
            snack_id = kwargs.get("snack_id")
            return self._restore_snack(snack_id)
        elif action == "list-snacks":
            return self._list_snacks()
        return False

    def _open_snackmachine(self) -> bool:
        """Open SnackMachine surface."""
        if self._menu_delegate:
            self._menu_delegate.openSnackMachine_(None)
            return True
        return False

    def _check_spool(self, hours: int = 1) -> dict:
        """Check spool for recent activity."""
        entries = read_spool(max_entries=100)
        errors = [e for e in entries if e.is_error]
        warnings = [e for e in entries if e.is_warning]
        return {
            "success": True,
            "total": len(entries),
            "errors": len(errors),
            "warnings": len(warnings),
            "recent_errors": [e.to_dict() for e in errors[:5]],
        }

    def _monitor_errors(self) -> bool:
        """Monitor spool for new errors and notify."""
        now = time.time()
        if now - self._last_spool_check < 30:
            return True

        self._last_spool_check = now
        result = self._check_spool()

        if result["errors"] > self._last_error_count:
            new_errors = result["errors"] - self._last_error_count
            self._last_error_count = result["errors"]
            if new_errors > 0 and self._menu_delegate:
                self._post_notification(
                    "uCore Errors Detected",
                    f"{new_errors} new error(s) in logs. Check SnackMachine for details.",
                )
        return True

    def _post_notification(self, title: str, message: str) -> bool:
        """Post macOS notification via menu delegate."""
        if self._menu_delegate:
            try:
                from app.menu.unified_menu_simple import post_notification
                post_notification(title, message)
                return True
            except Exception as e:
                log.warning(f"Failed to post notification: {e}")
        return False

    def _list_snacks(self) -> dict:
        """List all available snacks (repo + user)."""
        snacks = {"repo": [], "user": []}
        
        # List repo snacks
        for f in SNACKS_REPO_PATH.glob("*.py"):
            if f.name.startswith("_"):
                continue
            snacks["repo"].append(f.stem)
        
        # List user snacks
        if SNACKS_USER_PATH.exists():
            for f in SNACKS_USER_PATH.glob("*.py"):
                snacks["user"].append(f.stem)
        
        return {"success": True, "snacks": snacks}

    def _publish_snack(self, snack_id: str) -> dict:
        """Publish a snack to the repo (GitHub flow)."""
        if not snack_id:
            return {"success": False, "error": "snack_id required"}
        
        user_snack = SNACKS_USER_PATH / f"{snack_id}.py"
        if not user_snack.exists():
            return {"success": False, "error": f"Snack not found: {snack_id}"}
        
        # Copy to repo (would be git commit in real flow)
        dest = SNACKS_REPO_PATH / f"{snack_id}.py"
        shutil.copy(user_snack, dest)
        
        return {"success": True, "message": f"Published {snack_id} to repo"}

    def _restore_snack(self, snack_id: str) -> dict:
        """Restore a snack from repo to user space."""
        if not snack_id:
            return {"success": False, "error": "snack_id required"}
        
        repo_snack = SNACKS_REPO_PATH / f"{snack_id}.py"
        if not repo_snack.exists():
            return {"success": False, "error": f"Snack not found in repo: {snack_id}"}
        
        SNACKS_USER_PATH.mkdir(parents=True, exist_ok=True)
        dest = SNACKS_USER_PATH / f"{snack_id}.py"
        shutil.copy(repo_snack, dest)
        
        return {"success": True, "message": f"Restored {snack_id} to user space"}


# Register on import
def register(menu_delegate=None):
    """Register the SnackShack snack."""
    plugin = SnackShack(menu_delegate)
    register_snack(plugin)
    return plugin