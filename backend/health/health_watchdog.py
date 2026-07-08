#!/usr/bin/env python3
"""Health Watchdog — monitors snackbar health and auto-restarts services.

Checks backend health endpoint and restarts services if needed.
Integrates with MCP health API and self-healing skills.
"""
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

HEALTH_URL = "http://localhost:8484/api/health"
UCORE_MENU_LABEL = "com.udos.ucore-menu"
UCORE_SERVER_LABEL = "com.udos.ucore-server"
UCORE_BACKEND_DIR = os.environ.get("UCORE_BACKEND_DIR", str(Path.home() / "Code" / "uCore" / "backend"))

def check_health():
    """Check if snackbar backend is healthy."""
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=5) as resp:
            data = resp.read()
            obj = json.loads(data.decode())
            return obj.get("status", "unknown") == "ok"
    except Exception:
        return False

def check_menu_running():
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

def restart_services():
    """Restart uCore services via launchctl."""
    from app.menu.launchd_manager import install as launchd_install
    from app.menu.launchd_manager import uninstall as launchd_uninstall

    # Restart menu - uninstall then reinstall to ensure clean state
    launchd_uninstall()
    launchd_install()

    # Restart server
    uid = os.getuid()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}/{UCORE_SERVER_LABEL}"],
                   capture_output=True, check=False)
    subprocess.run(["launchctl", "bootstrap", f"gui/{uid}",
                    str(Path.home() / "Library/LaunchAgents" / f"{UCORE_SERVER_LABEL}.plist")],
                   capture_output=True, check=False)

    time.sleep(2)

def main(loop_seconds: int = 60):
    """Main watchdog loop - check health and restart if needed."""
    if check_health():
        print("HEALTH_OK")
        return

    print("HEALTH_FAIL_RESTARTING")
    restart_services()

    # Wait and check again
    time.sleep(3)
    if check_health():
        print("HEALTH_OK_AFTER_RESTART")
    else:
        print("HEALTH_STILL_FAIL")
        # Try to start server directly
        venv_python = Path(UCORE_BACKEND_DIR) / ".venv" / "bin" / "python"
        python_bin = str(venv_python) if venv_python.exists() else "/usr/bin/python3"
        subprocess.Popen(
            [python_bin, "-m", "app.core.snackbar", "--port", "8484"],
            cwd=UCORE_BACKEND_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print("SERVER_START_ATTEMPTED")

if __name__ == "__main__":
    main(60)
