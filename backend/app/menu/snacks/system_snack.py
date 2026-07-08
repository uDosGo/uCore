"""System Snack — Backend/frontend/service management for uCore menu."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Optional

from snackmachine.registry import SnackPlugin, SnackSpec, register_snack

from app.skills.shared_utils import update_menu_delegate

log = logging.getLogger("system-snack")

UCORE_URL = "http://127.0.0.1:8484"
UI_HUB_URL = "http://localhost:5175"
UCORE_LABEL = "com.udos.ucore-menu"
UCORE_PLIST = os.path.expanduser("~/Library/LaunchAgents/com.udos.ucore-menu.plist")
UCORE_BACKEND_DIR = os.environ.get("UCORE_BACKEND_DIR", str(Path.home() / "Code" / "uCore" / "backend"))


class SystemSnack(SnackPlugin):
    """System services management snack."""

    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate
        self._backend_connected = False
        self._uihub_connected = False
        self._start_at_login = False

    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(
            id="system-services",
            name="Services",
            icon="⚙️",
            kind="multi-action",
            category="system",
            enabled=True,
            actions=[
                "health-check",
                "heal-ui-hub",
                "start-dev-server",
                "stop-dev-server",
                "restart-backend",
                "restart-frontend",
                "toggle-start-at-login",
                "open-s190-diagnostics"
            ],
            metadata={
                "backend": self._backend_connected,
                "uihub": self._uihub_connected,
                "start_at_login": self._start_at_login,
                "description": "System services and health management",
            },
        )

    def is_available(self) -> bool:
        return True  # Always available

    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if action == "health-check":
            return self._health_check()
        elif action == "heal-ui-hub":
            return self._heal_ui_hub()
        elif action == "start-dev-server":
            return self._start_dev_server()
        elif action == "stop-dev-server":
            return self._stop_dev_server()
        elif action == "restart-backend":
            return self._restart_backend()
        elif action == "restart-frontend":
            return self._restart_frontend()
        elif action == "toggle-start-at-login":
            return self._toggle_start_at_login()
        elif action == "open-s190-diagnostics":
            return self._open_s190_diagnostics()
        return False

    def _health_check(self) -> bool:
        """Run health checks and show summary."""
        backend_ok = self._is_backend_alive()
        health = self._api_get("/api/health") if backend_ok else None
        uihub_ok = self._is_uihub_alive()

        lines = [
            f"Backend: {'ok' if backend_ok else 'down'}",
            f"UI Hub: {'ok' if uihub_ok else 'down'}",
        ]
        if health:
            lines.append(f"API status: {health.get('status', 'unknown')}")

        # Show alert (would need menu delegate)
        log.info("Health check: %s", "; ".join(lines))
        return True

    def _heal_ui_hub(self) -> bool:
        """Try repair/restart/start flow for UI Hub."""
        if not self._is_backend_alive():
            log.warning("Heal failed: Backend not running")
            return False

        self._api_post_json("/api/surfaces/ui-hub/repair")
        self._api_post_json("/api/surfaces/ui-hub/restart")
        self._api_post_json("/api/surfaces/ui-hub/start")

        # Wait and check
        deadline = time.time() + 8.0
        while time.time() < deadline:
            if self._is_uihub_alive():
                from AppKit import NSURL, NSWorkspace
                NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(UI_HUB_URL))
                return True
            time.sleep(0.3)

        self._open_s190_diagnostics("uihub-heal-failed")
        return False

    def _restart_backend(self) -> bool:
        """Restart the uCore backend daemon."""
        log.info("Restarting backend...")
        try:
            # Kill existing backend
            subprocess.run(["pkill", "-f", "python.*-m app"], capture_output=True)
            time.sleep(1)

            # Use venv python if available
            venv_python = Path(UCORE_BACKEND_DIR) / ".venv" / "bin" / "python"
            python_bin = str(venv_python) if venv_python.exists() else "/usr/bin/python3"

            # Start new backend
            subprocess.Popen(
                [python_bin, "-m", "app.core.snackbar", "--port", "8484"],
                cwd=UCORE_BACKEND_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            time.sleep(2)
            return True
        except Exception as e:
            log.exception("Failed to restart backend: %s", e)
            return False

    def _restart_frontend(self) -> bool:
        """Restart the frontend dev server."""
        log.info("Restarting frontend dev server...")
        try:
            # Kill existing vite
            subprocess.run(["pkill", "-f", "vite"], capture_output=True)
            time.sleep(1)

            # Start frontend
            subprocess.Popen(
                ["pnpm", "run", "dev"],
                cwd=os.environ.get("UCORE_FRONTEND_DIR", str(Path.home() / "Code" / "uCore" / "frontend")),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except Exception as e:
            log.exception("Failed to restart frontend: %s", e)
            return False

    def _enable_start_at_login(self) -> bool:
        """Install and load the uCore launchd plist (delegates to launchd_manager)."""
        from app.menu.launchd_manager import install as launchd_install
        self._start_at_login = launchd_install()
        return self._start_at_login

    def _toggle_start_at_login(self) -> bool:
        """Toggle start at login."""
        if self._start_at_login:
            return self._disable_start_at_login()
        else:
            return self._enable_start_at_login()

    def _disable_start_at_login(self) -> bool:
        """Unload and remove the launchd plist (delegates to launchd_manager)."""
        from app.menu.launchd_manager import uninstall as launchd_uninstall
        self._start_at_login = not launchd_uninstall()
        return not self._start_at_login

    def _open_s190_diagnostics(self, reason: str = "manual") -> bool:
        """Open local S190 diagnostics fallback page."""
        fallback_path = Path.home() / ".ucore" / "s190-uihub-fallback.html"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)

        safe_reason = reason.replace("<", "<").replace(">", ">")
        retry_url = UI_HUB_URL
        api_health_url = f"{UCORE_URL}/api/health"
        fallback_s190 = f"{UI_HUB_URL}/s190?reason={__import__('urllib.parse').quote(reason)}"

        html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>S190 - UIHub Connectivity Fallback</title>
  <style>
    body {{ font-family: -apple-system, system-ui, sans-serif; margin: 0; background: #0f1115; color: #e6edf3; }}
    main {{ max-width: 780px; margin: 64px auto; padding: 24px; }}
    .card {{ border: 1px solid #30363d; border-radius: 12px; padding: 20px; background: #161b22; }}
    h1 {{ margin: 0 0 8px 0; font-size: 1.5rem; }}
    p {{ color: #9da7b3; line-height: 1.45; }}
    .code {{ font-family: ui-monospace, Menlo, monospace; color: #f0883e; }}
    .row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
    a {{ color: #58a6ff; text-decoration: none; border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; }}
  </style>
</head>
<body>
  <main>
    <div class="card">
      <h1>S190 - System Fallback</h1>
      <p>UI Hub is not reachable. System attempted auto-start and health healing.</p>
      <p>Reason: <span class="code">{safe_reason}</span></p>
      <div class="row">
        <a href="{retry_url}">Retry UI Hub</a>
        <a href="{fallback_s190}">Open S190 in UI Hub</a>
        <a href="{api_health_url}">Open API Health</a>
      </div>
    </div>
  </main
</body>
</html>"""

        fallback_path.write_text(html)
        from AppKit import NSURL, NSWorkspace
        NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(f"file://{fallback_path}"))
        return True

    def _start_dev_server(self) -> bool:
        """Start the frontend dev server via pnpm."""
        log.info("Starting dev server...")
        try:
            if self._is_uihub_alive():
                log.info("Dev server already running")
                return True
            ucore_root = Path.home() / "Code" / "uCore"
            subprocess.Popen(
                ["pnpm", "--filter", "frontend-vue", "run", "dev"],
                cwd=str(ucore_root),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            time.sleep(3)
            return self._is_uihub_alive()
        except Exception as e:
            log.exception("Failed to start dev server: %s", e)
            return False

    def _stop_dev_server(self) -> bool:
        """Stop the frontend dev server by killing vite processes."""
        log.info("Stopping dev server...")
        try:
            subprocess.run(["pkill", "-f", "vite"], capture_output=True)
            time.sleep(1)
            return not self._is_uihub_alive()
        except Exception as e:
            log.exception("Failed to stop dev server: %s", e)
            return False

    def _is_backend_alive(self) -> bool:
        try:
            req = urllib.request.Request(f"{UCORE_URL}/api/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("status") == "ok"
        except Exception:
            return False

    def _is_uihub_alive(self) -> bool:
        try:
            req = urllib.request.Request(UI_HUB_URL)
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _api_get(self, path: str, timeout: float = 3.0):
        try:
            req = urllib.request.Request(f"{UCORE_URL}{path}")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _api_post_json(self, path: str, payload: dict = None, timeout: float = 6.0):
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

    def update_status(self, backend: bool, uihub: bool, start_at_login: bool) -> None:
        """Update status from external refresh."""
        self._backend_connected = backend
        self._uihub_connected = uihub
        self._start_at_login = start_at_login
        update_menu_delegate(self._menu_delegate)


# Register on import
def register(menu_delegate=None):
    """Register the system snack."""
    plugin = SystemSnack(menu_delegate)
    register_snack(plugin)
    return plugin
