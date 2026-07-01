"""Surface Snack — Dynamic surface management for uCore menu."""
from __future__ import annotations

import logging
import os
import subprocess
import urllib.request
import json
from pathlib import Path
from typing import Any, Optional

from snackmachine.registry import SnackPlugin, SnackSpec, register_snack
from app.skills.shared_utils import update_menu_delegate

log = logging.getLogger("surface-snack")

UCORE_URL = "http://127.0.0.1:8484"


class SurfaceSnack(SnackPlugin):
    """Dynamic surface management snack - loads surfaces from backend API."""
    
    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate
        self._surfaces = []
        self._connected = False
    
    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(
            id="surface-manager",
            name="Surfaces",
            icon="🖥️",
            kind="multi-action",
            category="surface",
            enabled=True,
            actions=["refresh", "open-ui-hub"],
            metadata={
                "surfaces": self._surfaces,
                "connected": self._connected,
                "description": "Open and manage UI surfaces",
            },
        )
    
    def is_available(self) -> bool:
        return self._connected
    
    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if action == "refresh":
            self._refresh_surfaces()
            return True
        elif action == "open-ui-hub":
            self._open_surface("ui-hub")
            return True
        elif action and action.startswith("open-"):
            surface_id = action[5:]  # Remove "open-" prefix
            self._open_surface(surface_id)
            return True
        return False
    
    def _refresh_surfaces(self) -> None:
        """Fetch surfaces from backend API."""
        try:
            req = urllib.request.Request(f"{UCORE_URL}/api/surfaces/list")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._surfaces = data.get("surfaces", [])
                self._connected = True
        except Exception as e:
            log.warning(f"Failed to fetch surfaces: {e}")
            self._surfaces = []
            self._connected = False
        
        if self._menu_delegate:
            self._menu_delegate.performSelectorOnMainThread_withObject_waitUntilDone_(
                "updateUI:", None, False
            )
    
    def _open_surface(self, surface_id: str) -> None:
        """Open a surface in browser, with auto-start if needed."""
        # Find surface URL
        surface = next((s for s in self._surfaces if s.get("id") == surface_id), None)
        if not surface:
            log.warning(f"Surface not found: {surface_id}")
            return
        
        url = surface.get("url") or surface.get("metadata", {}).get("url")
        if not url:
            # Default URL pattern
            url = f"http://localhost:5175/{surface_id}"
        
        # Auto-start backend if needed
        if not self._is_backend_alive():
            log.info("Backend not running, attempting to start...")
            try:
                subprocess.Popen(
                    ["/usr/bin/python3", "-m", "app"],
                    cwd=os.environ.get("UCORE_BACKEND_DIR", str(Path.home() / "Code" / "uCore" / "backend")),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                import time
                time.sleep(2)
            except Exception as e:
                log.warning(f"Failed to auto-start backend: {e}")
        
        # Open in browser
        from AppKit import NSWorkspace, NSURL
        NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(url))
        log.info(f"Opened surface: {surface_id} -> {url}")
    
    def _is_backend_alive(self) -> bool:
        try:
            req = urllib.request.Request(f"{UCORE_URL}/api/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("status") == "ok"
        except Exception:
            return False
    
    def update_surfaces(self, surfaces: list, connected: bool) -> None:
        """Update surfaces from external refresh."""
        self._surfaces = surfaces
        self._connected = connected
        update_menu_delegate(self._menu_delegate)


# Register on import
def register(menu_delegate=None):
    """Register the surface snack."""
    plugin = SurfaceSnack(menu_delegate)
    register_snack(plugin)
    return plugin