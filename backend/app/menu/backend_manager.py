"""Backend management utilities for uCore menu bar app."""
from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────

UCORE_BACKEND_DIR = os.environ.get("UCORE_BACKEND_DIR", str(Path.home() / "Code" / "uCore" / "backend"))
UCORE_URL = "http://127.0.0.1:8484"
UCORE_PORT = 8484

log = logging.getLogger("ucore-menu")


def _port_in_use(port: int = UCORE_PORT) -> bool:
    """Quick socket-level check if something is listening on the port."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except Exception:
        return False


def is_ucore_alive() -> bool:
    """Check if snackbar API is responding.
    
    Uses raw TCP socket probe to avoid a known aiohttp bug where Python
    stdlib HTTP clients (urllib, http.client) cause the backend event
    loop to hang permanently.
    """
    return _port_in_use()


def ensure_backend_running(timeout_s: float = 8.0) -> bool:
    """Ensure backend is running; launch it if needed.

    Hardened version with:
    - Configurable timeout
    - Venv detection with fallback
    - Port-in-use check to avoid duplicate launches
    - Proper error handling
    - Health check polling
    """
    if is_ucore_alive():
        return True

    # Don't try to start if port is already in use (backend hung but listening)
    if _port_in_use():
        log.warning(
            "Port %d is in use but health check failed — backend may be hung. "
            "Kill the existing process and restart manually.",
            UCORE_PORT,
        )
        return False

    log.info("Starting backend...")
    try:
        # Use venv python if available, otherwise system python
        venv_python = Path(UCORE_BACKEND_DIR) / ".venv" / "bin" / "python"
        python_bin = str(venv_python) if venv_python.exists() else "/usr/bin/python3"

        subprocess.Popen(
            [python_bin, "-m", "app.core.snackbar", "--port", "8484", "--auto-start"],
            cwd=UCORE_BACKEND_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as e:
        log.exception("Failed to start backend: %s", e)
        return False

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if is_ucore_alive():
            log.info("Backend started successfully")
            return True
        time.sleep(0.3)

    log.warning("Backend failed to start within %s seconds", timeout_s)
    return False


def restart_backend() -> bool:
    """Restart the uCore backend daemon."""
    log.info("Restarting backend...")
    try:
        subprocess.run(["pkill", "-f", "python.*-m app"], capture_output=True)
        time.sleep(1)
        return ensure_backend_running(timeout_s=5.0)
    except Exception as e:
        log.exception("Failed to restart backend: %s", e)
        return False
