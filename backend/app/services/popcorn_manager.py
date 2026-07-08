"""Popcorn Manager — macOS tray menu lifecycle management.

This module manages the uCore macOS menu bar (popcorn) tray icon.
It provides status checks and lifecycle actions for the menu process,
backend server, and frontend dev server.

All launchd operations delegate to launchd_manager.py (single source of truth).
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path

log = logging.getLogger("popcorn-manager")

# ─── Config ──────────────────────────────────────────────────────────

UCORE_BACKEND_DIR = os.environ.get(
    "UCORE_BACKEND_DIR",
    str(Path.home() / "Code" / "uCore" / "backend"),
)
UCORE_URL = "http://127.0.0.1:8484"
UI_HUB_URL = "http://localhost:5175"

# ─── Status Checks ───────────────────────────────────────────────────


def _is_backend_alive() -> bool:
    """Check if the uCore backend (snackbar) is listening on port 8484.

    Uses a socket connect check instead of hitting the health endpoint
    to avoid a recursive loop (the health endpoint calls this function).
    """
    import socket

    try:
        sock = socket.create_connection(("127.0.0.1", 8484), timeout=2)
        sock.close()
        return True
    except (OSError, socket.timeout):
        return False


def _is_frontend_alive() -> bool:
    """Check if the Vue frontend is responding on port 5175."""
    try:
        import urllib.request

        req = urllib.request.Request(UI_HUB_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status < 500
    except Exception:
        return False


def _is_menu_running() -> bool:
    """Check if the menu process is running via lockfile."""
    from app.menu.lockfile import LOCKFILE_PATH

    if not LOCKFILE_PATH.exists():
        return False
    try:
        pid = int(LOCKFILE_PATH.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError, OSError):
        return False


# ─── Public API ──────────────────────────────────────────────────────


def get_popcorn_status() -> dict:
    """Get the full status of the popcorn (tray menu) system.

    Returns:
        dict with keys: menu, backend, frontend, launchd, version
    """
    from app.menu.launchd_manager import get_status as get_launchd_status

    launchd_status = get_launchd_status()

    return {
        "menu": {
            "running": _is_menu_running(),
            "installed": launchd_status.get("installed", False),
            "label": "com.udos.ucore-menu",
        },
        "backend": {
            "running": _is_backend_alive(),
            "port": 8484,
        },
        "frontend": {
            "running": _is_frontend_alive(),
            "port": 5175,
            "installed": launchd_status.get("frontend_installed", False),
        },
        "launchd": launchd_status,
        "version": "1.0.0",
    }


def perform_action(action: str) -> dict:
    """Perform a lifecycle action on the popcorn system.

    Supported actions:
        - start-menu: Start the menu bar app
        - stop-menu: Stop the menu bar app
        - restart-menu: Restart the menu bar app
        - start-backend: Start the backend server
        - stop-backend: Stop the backend server
        - restart-backend: Restart the backend server
        - start-frontend: Start the frontend dev server
        - stop-frontend: Stop the frontend dev server
        - restart-frontend: Restart the frontend dev server
        - status: Get current status (same as get_popcorn_status)
        - install: Install launchd agents for auto-start
        - uninstall: Remove launchd agents

    Args:
        action: The action to perform.

    Returns:
        dict with keys: success, action, message, status
    """
    from app.menu.launchd_manager import (
        install as install_launchd,
    )
    from app.menu.launchd_manager import (
        install_frontend,
        uninstall_frontend,
    )
    from app.menu.launchd_manager import (
        uninstall as uninstall_launchd,
    )

    action = action.lower().strip()

    try:
        if action == "status":
            return {"success": True, "action": action, "status": get_popcorn_status()}

        elif action == "start-menu":
            if _is_menu_running():
                return {
                    "success": True,
                    "action": action,
                    "message": "Menu already running",
                }
            install_launchd()
            # Give it a moment to start
            time.sleep(1)
            return {
                "success": _is_menu_running(),
                "action": action,
                "message": "Menu started" if _is_menu_running() else "Menu failed to start",
            }

        elif action == "stop-menu":
            if not _is_menu_running():
                return {
                    "success": True,
                    "action": action,
                    "message": "Menu not running",
                }
            uninstall_launchd()
            return {
                "success": True,
                "action": action,
                "message": "Menu stopped",
            }

        elif action == "restart-menu":
            uninstall_launchd()
            time.sleep(0.5)
            install_launchd()
            time.sleep(1)
            return {
                "success": _is_menu_running(),
                "action": action,
                "message": "Menu restarted" if _is_menu_running() else "Menu failed to restart",
            }

        elif action == "start-backend":
            if _is_backend_alive():
                return {
                    "success": True,
                    "action": action,
                    "message": "Backend already running",
                }
            from app.menu.backend_manager import ensure_backend_running

            result = ensure_backend_running(timeout_s=8.0)
            return {
                "success": result,
                "action": action,
                "message": "Backend started" if result else "Backend failed to start",
            }

        elif action == "stop-backend":
            if not _is_backend_alive():
                return {
                    "success": True,
                    "action": action,
                    "message": "Backend not running",
                }
            subprocess.run(
                ["pkill", "-f", "python.*-m app.core.snackbar"],
                capture_output=True,
                timeout=5,
            )
            time.sleep(0.5)
            return {
                "success": not _is_backend_alive(),
                "action": action,
                "message": "Backend stopped",
            }

        elif action == "restart-backend":
            subprocess.run(
                ["pkill", "-f", "python.*-m app.core.snackbar"],
                capture_output=True,
                timeout=5,
            )
            time.sleep(1)
            from app.menu.backend_manager import ensure_backend_running

            result = ensure_backend_running(timeout_s=8.0)
            return {
                "success": result,
                "action": action,
                "message": "Backend restarted" if result else "Backend failed to restart",
            }

        elif action == "start-frontend":
            if _is_frontend_alive():
                return {
                    "success": True,
                    "action": action,
                    "message": "Frontend already running",
                }
            install_frontend()
            # Wait for frontend to start
            for _ in range(20):
                if _is_frontend_alive():
                    return {
                        "success": True,
                        "action": action,
                        "message": "Frontend started",
                    }
                time.sleep(0.5)
            return {
                "success": False,
                "action": action,
                "message": "Frontend failed to start within timeout",
            }

        elif action == "stop-frontend":
            if not _is_frontend_alive():
                return {
                    "success": True,
                    "action": action,
                    "message": "Frontend not running",
                }
            uninstall_frontend()
            subprocess.run(
                ["pkill", "-f", "vite.*5175"],
                capture_output=True,
                timeout=5,
            )
            return {
                "success": True,
                "action": action,
                "message": "Frontend stopped",
            }

        elif action == "restart-frontend":
            uninstall_frontend()
            subprocess.run(
                ["pkill", "-f", "vite.*5175"],
                capture_output=True,
                timeout=5,
            )
            time.sleep(0.5)
            install_frontend()
            for _ in range(20):
                if _is_frontend_alive():
                    return {
                        "success": True,
                        "action": action,
                        "message": "Frontend restarted",
                    }
                time.sleep(0.5)
            return {
                "success": False,
                "action": action,
                "message": "Frontend failed to restart within timeout",
            }

        elif action == "install":
            install_launchd()
            return {
                "success": True,
                "action": action,
                "message": "Launchd agents installed",
            }

        elif action == "uninstall":
            uninstall_launchd()
            return {
                "success": True,
                "action": action,
                "message": "Launchd agents removed",
            }

        else:
            return {
                "success": False,
                "action": action,
                "error": f"Unknown action: {action}. "
                f"Supported: start-menu, stop-menu, restart-menu, "
                f"start-backend, stop-backend, restart-backend, "
                f"start-frontend, stop-frontend, restart-frontend, "
                f"install, uninstall, status",
            }

    except Exception as e:
        log.exception("Action '%s' failed: %s", action, e)
        return {
            "success": False,
            "action": action,
            "error": str(e),
        }
