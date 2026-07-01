"""Auto-Start Skill — Health check and auto-start for snackbar services.

Provides:
- Check if snackbar backend is running
- Check if menu bar app is running
- Auto-start services if not running
- Integration with health API and MCP
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill

log = logging.getLogger("skill_autostart")

UCORE_URL = "http://127.0.0.1:8484"
UCORE_BACKEND_DIR = os.environ.get("UCORE_BACKEND_DIR", str(Path.home() / "Code" / "uCore" / "backend"))
UCORE_MENU_LABEL = "com.udos.ucore-menu"
UCORE_SERVER_LABEL = "com.udos.ucore-server"


def _api_get(path: str, timeout: float = 3.0) -> dict | None:
    """Call snackbar API and return parsed JSON, or None."""
    try:
        req = urllib.request.Request(f"{UCORE_URL}{path}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _api_post_json(
    path: str, payload: dict | None = None, timeout: float = 6.0
) -> dict | None:
    """POST JSON to snackbar API and return parsed JSON, or None."""
    try:
        body = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            f"{UCORE_URL}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def is_backend_alive() -> bool:
    """Check if snackbar backend is responding."""
    result = _api_get("/api/health")
    return result is not None and result.get("status") == "ok"


def is_menu_running() -> bool:
    """Check if uCore menu is running."""
    lockfile = Path.home() / ".ucore" / "ucore-menu.pid"
    if not lockfile.exists():
        return False
    try:
        pid = int(lockfile.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError):
        return False


def is_menu_installed() -> bool:
    """Check if menu launchd plist is installed."""
    plist = f"{UCORE_MENU_LABEL}.plist"
    plist_path = Path.home() / "Library/LaunchAgents" / plist
    return os.path.exists(plist_path)


def is_server_installed() -> bool:
    """Check if server launchd plist is installed."""
    plist = f"{UCORE_SERVER_LABEL}.plist"
    plist_path = Path.home() / "Library/LaunchAgents" / plist
    return os.path.exists(plist_path)


def is_appflowy_data_available() -> bool:
    """Check if AppFlowy data directory exists (self-hosted)."""
    try:
        from app.af_manager.config import load_config, get_appflowy_data_dir
        from app.secret.store import SecretStore

        # Check secret store first (preferred)
        store = SecretStore()
        store.load()
        data_dir = store.get("appflowy_data_dir")

        if not data_dir:
            # Fallback to config file
            config = load_config()
            data_dir = get_appflowy_data_dir(config)

        return Path(data_dir).expanduser().exists()
    except Exception:
        return False


def start_backend() -> bool:
    """Start the snackbar backend."""
    try:
        venv_python = Path(UCORE_BACKEND_DIR) / ".venv" / "bin" / "python"
        python_bin = (
            str(venv_python) if venv_python.exists() else "/usr/bin/python3"
        )

        subprocess.Popen(
            [python_bin, "-m", "app.core.snackbar", "--port", "8484"],
            cwd=UCORE_BACKEND_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        log.info("Backend start initiated")
        return True
    except Exception as e:
        log.error(f"Failed to start backend: {e}")
        return False


def start_menu() -> bool:
    """Start the uCore menu bar app."""
    try:
        venv_python = Path(UCORE_BACKEND_DIR) / ".venv" / "bin" / "python"
        python_bin = (
            str(venv_python) if venv_python.exists() else "/usr/bin/python3"
        )

        subprocess.Popen(
            [python_bin, "-m", "app.menu.unified_menu_simple"],
            cwd=UCORE_BACKEND_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        log.info("Menu start initiated")
        return True
    except Exception as e:
        log.error(f"Failed to start menu: {e}")
        return False


def check_and_start_services() -> dict[str, Any]:
    """Check all services and start if needed."""
    results = {
        "backend": {"running": False, "started": False},
        "menu": {"running": False, "started": False},
        "server_plist": {"installed": False},
        "menu_plist": {"installed": False},
    }

    # Check backend
    results["backend"]["running"] = is_backend_alive()
    if not results["backend"]["running"]:
        results["backend"]["started"] = start_backend()
        time.sleep(2)
        results["backend"]["running"] = is_backend_alive()

    # Check menu
    results["menu"]["running"] = is_menu_running()
    if not results["menu"]["running"]:
        results["menu"]["started"] = start_menu()
        time.sleep(1)
        results["menu"]["running"] = is_menu_running()

    # Check plists
    results["server_plist"]["installed"] = is_server_installed()
    results["menu_plist"]["installed"] = is_menu_installed()

    # Check AppFlowy integration
    results["appflowy"] = {
        "data_available": is_appflowy_data_available(),
    }

    return results


def run_health_check() -> dict[str, Any]:
    """Run comprehensive health check for auto-start services."""
    services = check_and_start_services()

    # Get detailed health from API if available
    health = _api_get("/api/health")
    if health:
        services["health_api"] = health

    # Get MCP status
    mcp_status = _api_get("/api/mcp/tools")
    if mcp_status:
        tools_count = len(mcp_status.get("tools", []))
        services["mcp"] = {"available": True, "tools": tools_count}
    else:
        services["mcp"] = {"available": False}

    # Determine overall status
    all_healthy = (
        services["backend"]["running"] and
        services["menu"]["running"] and
        services["server_plist"]["installed"] and
        services["menu_plist"]["installed"]
    )

    return {
        "success": True,
        "action": "autostart_health_check",
        "status": "ok" if all_healthy else "degraded",
        "services": services,
        "recommendations": _get_recommendations(services),
    }


def _get_recommendations(services: dict) -> list[str]:
    """Generate recommendations based on service status."""
    recs = []

    if not services["server_plist"]["installed"]:
        recs.append(
            "Install server plist: bash scripts/install_ucore_menu_launchd.sh "
            "--install-server"
        )

    if not services["menu_plist"]["installed"]:
        recs.append(
            "Install menu plist: bash scripts/install_ucore_menu_launchd.sh"
        )

    backend_ok = (
        services["backend"]["running"] or services["backend"]["started"]
    )
    if not backend_ok:
        recs.append("Backend failed to start - check logs")

    menu_ok = services["menu"]["running"] or services["menu"]["started"]
    if not menu_ok:
        recs.append("Menu failed to start - check logs")

    # AppFlowy recommendations
    appflowy = services.get("appflowy", {})
    if not appflowy.get("data_available", False):
        recs.append(
            "AppFlowy data not found - ensure AppFlowy is installed and "
            "sync_config.yaml points to correct data_dir"
        )

    return recs


# ─── Skill Class ─────────────────────────────────────────────────────

class AutoStartSkill(BaseSkill):
    """Skill for auto-start health checking and service management."""

    @property
    def meta(self):
        return type("Meta", (), {
            "id": "autostart_health_check",
            "name": "Auto-Start Health Check",
            "description": "Check and auto-start snackbar services",
            "category": "system",
            "timeout": 30,
        })()

    def validate(self, **kwargs) -> list[str]:
        return []

    async def run(self, **kwargs) -> dict[str, Any]:
        return run_health_check()


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(AutoStartSkill().run())
    print(json.dumps(result, indent=2, default=str))

