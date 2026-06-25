#!/usr/bin/env python3
from __future__ import annotations
"""
uDos Popcorn — macOS menu bar app for Ollama Management v3.0.

Shows a popcorn icon in the menu bar:
  🍿 green = placeholder (reserved for future features)
  🍿 grey  = default state

Menu items:
  - Open UI Hub
  - Ollama → 🏖️/checking/stopped status + installed models
  - Ollama controls: Start, Stop, Restart
  - Quit

Depends on: PyObjC (included with macOS Python)
"""

import os
import sys
import json
import time
import signal
import subprocess
import threading
import logging
from pathlib import Path
import urllib.request
import urllib.error
import urllib.parse

import objc
from Foundation import NSObject, NSRunLoop, NSDate, NSURL
from AppKit import (
    NSApplication, NSStatusBar, NSVariableStatusItemLength,
    NSMenu, NSMenuItem, NSImage, NSFont, NSColor, NSWorkspace,
    NSAlert, NSApp,
)
from PyObjCTools import AppHelper

# ─── Config ───────────────────────────────────────────────────────────

UCORE_URL = "http://127.0.0.1:8484"
UI_HUB_URL = "http://localhost:5173"
# Polling interval for Ollama status refresh
# Was 5.0s — raised to reduce aggressive polling and log spam
REFRESH_INTERVAL = 30.0
UCORE_BACKEND_DIR = str(Path(__file__).resolve().parents[2])

log_dir = os.path.expanduser("~/.ucore/logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] popcorn: %(message)s",
    handlers=[logging.FileHandler(os.path.join(log_dir, "popcorn.log")), logging.StreamHandler()],
)
log = logging.getLogger("popcorn")


# ─── Helpers ──────────────────────────────────────────────────────────

def api_get(path: str, timeout: float = 3.0):
    """Call snackbar API and return parsed JSON, or None."""
    try:
        req = urllib.request.Request(f"{UCORE_URL}{path}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def api_post_json(path: str, payload: dict | None = None, timeout: float = 6.0):
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


def is_ucore_alive() -> bool:
    """Check if snackbar API is responding."""
    result = api_get("/api/health")
    return result is not None and result.get("status") == "ok"


def is_uihub_alive() -> bool:
    """Check if UI Hub frontend is reachable."""
    try:
        req = urllib.request.Request(UI_HUB_URL)
        with urllib.request.urlopen(req, timeout=1.2) as resp:
            return int(getattr(resp, "status", 200)) < 500
    except Exception:
        return False


def _backend_python_cmd() -> list[str]:
    """Build a backend launch command, preferring the repo virtualenv."""
    venv_python = Path(UCORE_BACKEND_DIR) / ".venv" / "bin" / "python"
    python_bin = str(venv_python) if venv_python.exists() else sys.executable
    return [python_bin, "-m", "app", "--port", "8484", "--auto-start"]


def ensure_ucore_running(timeout_s: float = 8.0) -> bool:
    """Ensure backend is running; launch it if needed."""
    if is_ucore_alive():
        return True

    try:
        subprocess.Popen(
            _backend_python_cmd(),
            cwd=UCORE_BACKEND_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as e:
        log.warning(f"Failed to start backend: {e}")
        return False

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if is_ucore_alive():
            return True
        time.sleep(0.25)
    return False


def ensure_uihub_running(timeout_s: float = 12.0) -> bool:
    """Ensure UI Hub is running using surface runtime APIs."""
    if is_uihub_alive():
        return True
    if not ensure_ucore_running():
        return False

    _ = api_post_json("/api/surfaces/ui-hub/start")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if is_uihub_alive():
            return True
        time.sleep(0.3)

    _ = api_post_json("/api/surfaces/ui-hub/restart")
    deadline = time.time() + 6.0
    while time.time() < deadline:
        if is_uihub_alive():
            return True
        time.sleep(0.3)
    return False


def open_s190_fallback(reason: str) -> None:
    """Open a local S190-style fallback page when UI Hub is unreachable."""
    fallback_path = Path.home() / ".ucore" / "s190-uihub-fallback.html"
    fallback_path.parent.mkdir(parents=True, exist_ok=True)

    safe_reason = reason.replace("<", "&lt;").replace(">", "&gt;")
    retry_url = UI_HUB_URL
    api_health_url = f"{UCORE_URL}/api/health"
    fallback_s190 = f"{UI_HUB_URL}/s190?reason={urllib.parse.quote(reason)}"
    html = f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
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
    <div class=\"card\">
      <h1>S190 - System Fallback</h1>
      <p>UI Hub is not reachable yet. Popcorn attempted auto-start and health healing.</p>
      <p>Reason: <span class=\"code\">{safe_reason}</span></p>
      <div class=\"row\">
        <a href=\"{retry_url}\">Retry UI Hub</a>
        <a href=\"{fallback_s190}\">Open S190 in UI Hub</a>
        <a href=\"{api_health_url}\">Open API Health</a>
      </div>
    </div>
  </main>
</body>
</html>
"""
    fallback_path.write_text(html, encoding="utf-8")
    subprocess.Popen(["open", str(fallback_path)])


def open_url(url: str):
    """Open a URL in the default browser."""
    NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(url))


def check_ollama():
    """Check Ollama status and return (status, models_list).

    Returns 'stopped' if ~/.ucore/ollama_disabled exists, even if
    Ollama is technically running (prevents watchdog re-launch).
    """
    # If we explicitly disabled it, always report stopped
    disable_file = os.path.expanduser("~/.ucore/ollama_disabled")
    explicitly_disabled = os.path.exists(disable_file)

    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            if explicitly_disabled:
                return ("stopped", models)
            return ("running", models)
    except Exception:
        pass
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/")
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if explicitly_disabled:
                return ("stopped", [])
            return ("installed", [])
    except Exception:
        return ("stopped", [])


# ─── Popcorn Icon ─────────────────────────────────────────────────────

POPCORN_ICON_DIR = os.path.join(os.path.dirname(__file__), "popcorn.iconset")
POPCORN_ICNS = os.path.join(os.path.dirname(__file__), "popcorn.icns")

def _ensure_icon():
    """Generate a proper .icns icon from the 🍿 emoji if it doesn't exist."""
    icns_path = POPCORN_ICNS
    if os.path.isfile(icns_path):
        return icns_path

    log.info("Generating Popcorn .icns icon from emoji...")
    os.makedirs(POPCORN_ICON_DIR, exist_ok=True)

    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }

    from AppKit import NSAttributedString, NSBitmapImageRep

    for name, px in sizes.items():
        path = os.path.join(POPCORN_ICON_DIR, name)
        font = NSFont.systemFontOfSize_(px * 0.85)
        attrs = {
            "NSFontAttributeName": font,
            "NSForegroundColorAttributeName": NSColor.whiteColor(),
        }
        attr_str = NSAttributedString.alloc().initWithString_attributes_("🍿", attrs)
        text_size = attr_str.size()

        image = NSImage.alloc().initWithSize_((px, px))
        image.lockFocus()
        cx = (px - text_size.width) / 2
        cy = (px - text_size.height) / 2
        attr_str.drawAtPoint_((cx, cy))
        image.unlockFocus()

        tiff_data = image.TIFFRepresentation()
        bitmap = NSBitmapImageRep.alloc().initWithData_(tiff_data)
        png_data = bitmap.representationUsingType_properties_(4, None)  # NSPNGFileType
        png_data.writeToFile_atomically_(path, True)

    try:
        subprocess.run(
            ["iconutil", "-c", "icns", POPCORN_ICON_DIR, "-o", icns_path],
            capture_output=True, timeout=30, check=True
        )
        log.info(f"Popcorn .icns created at {icns_path}")
    except Exception as e:
        log.warning(f"Failed to create .icns (iconutil may not be available): {e}")
        return None

    return icns_path


def _make_status_icon(any_running: bool) -> NSImage:
    """Create a popcorn icon using text."""
    char = "🍿"
    font = NSFont.systemFontOfSize_(16)
    attrs = {
        "NSFontAttributeName": font,
        "NSForegroundColorAttributeName": (
            NSColor.greenColor() if any_running else NSColor.grayColor()
        ),
    }
    from AppKit import NSAttributedString
    attr_str = NSAttributedString.alloc().initWithString_attributes_(char, attrs)
    text_size = attr_str.size()
    image = NSImage.alloc().initWithSize_(text_size)
    image.lockFocus()
    attr_str.drawAtPoint_((0, 0))
    image.unlockFocus()
    return image


# ─── App Delegate ─────────────────────────────────────────────────────

class PopcornDelegate(NSObject):
    """Main delegate for the popcorn menu bar app."""

    def init(self):
        self = objc.super(PopcornDelegate, self).init()
        if self is None:
            return None
        self._connected = False
        self._status_item = None
        self._menu = None
        self._surfaces = []
        self._any_running = False
        self._refresh_timer = None
        self._ollama_status = 'checking'
        self._ollama_models = []
        return self

    def setupStatusBar(self):
        """Create the status bar item."""
        bar = NSStatusBar.systemStatusBar()
        self._status_item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        self._status_item.retain()

        icon = _make_status_icon(False)
        self._status_item.setImage_(icon)

        self._menu = NSMenu.alloc().init()
        self._menu.setAutoenablesItems_(False)
        self._status_item.setMenu_(self._menu)

        self._rebuild_menu()
        self._start_refresh()

    def _rebuild_menu(self):
        """Rebuild the entire menu from current state."""
        self._menu.removeAllItems()

        # ── Header ──────────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍿 Popcorn — Ollama Manager", None, ""
        )
        item.setEnabled_(False)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Open UI Hub ─────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍒 Open UI Hub", "openUIHub:", "o"
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🩺 Health Check", "checkHealth:", "h"
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🛠 Heal UI Hub", "healUIHub:", "r"
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🧭 Open S190 Diagnostics", "openS190Diagnostics:", "d"
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Backend Daemon ───────────────────────────────────────
        backend_alive = is_ucore_alive()
        backend_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{'🟢' if backend_alive else '🔴'} Backend (uCore on :8484)", None, ""
        )
        backend_item.setEnabled_(False)
        self._menu.addItem_(backend_item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⟳ Restart Backend", "restartBackend:", ""
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⟳ Restart UI Hub", "restartUIHub:", ""
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Ollama ─────────────────────────────────────────────
        ollama_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Ollama", None, ""
        )
        self._menu.addItem_(ollama_title)

        ollama_status = self._ollama_status
        ollama_models = self._ollama_models

        if ollama_status == "running":
            status_dot = "🏖️"
            status_label = "Ollama Running"
        elif ollama_status == "installed":
            status_dot = "🏖️"
            status_label = "Ollama Installed (idle)"
        elif ollama_status == "checking":
            status_dot = ""
            status_label = "Checking Ollama..."
        else:
            status_dot = ""
            disable_file = os.path.expanduser("~/.ucore/ollama_disabled")
            if os.path.exists(disable_file):
                status_label = "○ Stopped (disabled)"
            else:
                status_label = "Stopped"

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{status_dot} {status_label}", None, ""
        )
        self._menu.addItem_(item)

        # Ollama start/stop controls
        if ollama_status == "running":
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "○ Stop Ollama", "stopOllama:", ""
            )
            item.setTarget_(self)
            self._menu.addItem_(item)
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "○ Restart Ollama", "restartOllama:", ""
            )
            item.setTarget_(self)
            self._menu.addItem_(item)
        else:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "🥞 Start Ollama", "startOllama:", ""
            )
            item.setTarget_(self)
            self._menu.addItem_(item)

        if ollama_models:
            for model in ollama_models:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    f"🌀 {model}", None, ""
                )
                self._menu.addItem_(item)
        elif ollama_status == "running":
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "🌀 (no models installed)", None, ""
            )
            self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Quit ───────────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🔥 Quit", "quitApp:", "q"
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

    def _start_refresh(self):
        """Start the periodic refresh timer."""
        self._refresh()

    def _refresh(self):
        """Refresh Ollama status and rebuild menu."""

        # Check Ollama status
        try:
            status, models = check_ollama()
            self._ollama_status = status
            self._ollama_models = models
            log.info(f"Ollama status: {status}, models: {models}")
        except Exception as e:
            log.warning(f"Ollama check error: {e}")
            self._ollama_status = 'stopped'
            self._ollama_models = []

        # Schedule next refresh
        if self._refresh_timer is None:
            self._refresh_timer = threading.Timer(REFRESH_INTERVAL, self._refresh)
            self._refresh_timer.daemon = True
            self._refresh_timer.start()
        else:
            self._refresh_timer.cancel()
            self._refresh_timer = threading.Timer(REFRESH_INTERVAL, self._refresh)
            self._refresh_timer.daemon = True
            self._refresh_timer.start()

        # Update UI on main thread
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False
        )

    def updateUI_(self, sender):
        """Called on main thread to update icon and menu."""
        self._connected = is_ucore_alive()
        icon = _make_status_icon(self._connected)
        self._status_item.setImage_(icon)
        self._rebuild_menu()

    # ─── Actions ───────────────────────────────────────────────

    def openUIHub_(self, sender):
        """Open UI Hub in browser."""
        log.info("Opening UI Hub (with auto-start)")
        if ensure_uihub_running():
            subprocess.Popen(["open", UI_HUB_URL])
            return

        open_s190_fallback("uihub-cant-connect")
        alert = NSAlert.alloc().init()
        alert.setMessageText_("UIHub not reachable")
        alert.setInformativeText_(
            "Popcorn tried auto-start + heal, but localhost:5173 is still down."
        )
        alert.runModal()

    def checkHealth_(self, sender):
        """Run basic health checks and show a quick summary."""
        backend_ok = ensure_ucore_running()
        health = api_get("/api/health") if backend_ok else None
        uihub_ok = is_uihub_alive()
        debug = api_post_json("/api/surfaces/ui-hub/debug") if backend_ok else None

        lines = [
            f"Backend: {'ok' if backend_ok else 'down'}",
            f"UI Hub: {'ok' if uihub_ok else 'down'}",
        ]
        if health:
            lines.append(f"API status: {health.get('status', 'unknown')}")
        if isinstance(debug, dict) and "healthy" in debug:
            lines.append(f"ui-hub debug healthy: {debug.get('healthy')}")

        alert = NSAlert.alloc().init()
        alert.setMessageText_("uCore Health Check")
        alert.setInformativeText_("\n".join(lines))
        alert.runModal()

    def restartBackend_(self, sender):
        """Restart the uCore backend daemon."""
        log.info("Restarting backend daemon from popcorn menu...")
        try:
            result = subprocess.run(
                ["pgrep", "-f", "python -m app"],
                capture_output=True, text=True, timeout=5
            )
            pids = []
            for pid_str in result.stdout.strip().splitlines():
                pid = pid_str.strip()
                if pid and int(pid) != os.getpid():
                    pids.append(int(pid))
            if pids:
                for pid in pids:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except (ProcessLookupError, OSError):
                        pass
                log.info(f"Killed backend PIDs: {pids}")
                time.sleep(1)

            # Restart via ensure_ucore_running
            if ensure_ucore_running(timeout_s=10.0):
                log.info("Backend restarted successfully")
            else:
                log.warning("Backend failed to restart")
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Backend restart failed")
                alert.setInformativeText_("Could not restart uCore backend on :8484")
                alert.runModal()
        except Exception as e:
            log.error(f"Backend restart error: {e}")

    def restartUIHub_(self, sender):
        """Restart the UI Hub frontend."""
        log.info("Restarting UI Hub from popcorn menu...")
        if not ensure_ucore_running():
            alert = NSAlert.alloc().init()
            alert.setMessageText_("UI Hub restart failed")
            alert.setInformativeText_("Backend is not running. Start it first.")
            alert.runModal()
            return

        _ = api_post_json("/api/surfaces/ui-hub/restart")
        log.info("UI Hub restart requested")

    def healUIHub_(self, sender):
        """Try repair/restart/start flow for UI Hub and open it on success."""
        if not ensure_ucore_running():
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Heal failed")
            alert.setInformativeText_("Backend could not be started.")
            alert.runModal()
            return

        _ = api_post_json("/api/surfaces/ui-hub/repair")
        _ = api_post_json("/api/surfaces/ui-hub/restart")
        _ = api_post_json("/api/surfaces/ui-hub/start")

        if ensure_uihub_running(timeout_s=8.0):
            subprocess.Popen(["open", UI_HUB_URL])
            return

        open_s190_fallback("uihub-heal-failed")

    def openS190Diagnostics_(self, sender):
        """Open local S190 diagnostics fallback page immediately."""
        open_s190_fallback("manual-s190-diagnostics")

    def openSurface_(self, sender):
        """Open a surface URL in the browser."""
        url = sender.representedObject()
        if url and url != "#":
            log.info(f"Opening surface: {url}")
            subprocess.Popen(["open", url])

    def quitApp_(self, sender):
        """Quit the popcorn menu app."""
        log.info("Quitting popcorn")
        if self._refresh_timer:
            self._refresh_timer.cancel()
        NSApplication.sharedApplication().terminate_(self)

    # ── Ollama Actions ─────────────────────────────────────────────

    def startOllama_(self, sender):
        """Start Ollama server explicitly (only called from popcorn menu)."""
        log.info("Starting Ollama from popcorn menu...")
        try:
            # Remove disable flag so watchdog doesn't kill it
            disable_file = os.path.expanduser("~/.ucore/ollama_disabled")
            if os.path.exists(disable_file):
                os.remove(disable_file)

            # Start ollama serve as a standalone process (not via launchd)
            proc = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            log.info(f"Ollama started (PID {proc.pid})")
            time.sleep(2)
            self._ollama_status = 'checking'
            self._refresh()
        except Exception as e:
            log.error(f"Failed to start Ollama: {e}")
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Failed to Start Ollama")
            alert.setInformativeText_(str(e))
            alert.runModal()

    def stopOllama_(self, sender):
        """Stop Ollama server — kills it AND prevents auto-restart.

        Sets a disable flag so no watchdog re-launches it.
        Only startOllama_ (popcorn menu) can revive it.
        """
        log.info("Stopping Ollama permanently (until explicitly started)...")
        try:
            # 1. Kill all ollama processes with extreme prejudice
            result = subprocess.run(
                ["pgrep", "-f", "ollama"],
                capture_output=True, text=True, timeout=5
            )
            pids = [int(p) for p in result.stdout.strip().splitlines() if p.strip()]
            # Filter out our own pgrep command
            pids = [p for p in pids if p != os.getpid()]

            if pids:
                # SIGKILL immediately — no graceful shutdown needed for resource reclaim
                for pid in pids:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except (ProcessLookupError, OSError):
                        pass
                log.info(f"Killed Ollama PIDs: {pids}")
                time.sleep(0.5)

            # 2. Unload any launchd agent that might respawn Ollama
            for plist in ["homebrew.mxcl.ollama", "ollama", "com.ollama.ollama"]:
                try:
                    subprocess.run(
                        ["launchctl", "unload", f"/Library/LaunchAgents/{plist}.plist"],
                        capture_output=True, timeout=5,
                    )
                except Exception:
                    pass
                try:
                    subprocess.run(
                        ["launchctl", "unload", f"~/Library/LaunchAgents/{plist}.plist"],
                        capture_output=True, timeout=5,
                    )
                except Exception:
                    pass

            # 3. Set disable flag so no auto-restart
            disable_file = os.path.expanduser("~/.ucore/ollama_disabled")
            os.makedirs(os.path.dirname(disable_file), exist_ok=True)
            with open(disable_file, "w") as f:
                f.write(f"disabled by popcorn at {time.time()}")

            # 4. Also kill any leftover ollama runner processes
            for leftover in ["ollama_llama_server", "ollama-runner"]:
                try:
                    subprocess.run(["pkill", "-9", leftover], capture_output=True, timeout=3)
                except Exception:
                    pass

            self._ollama_status = 'stopped'
            self._ollama_models = []
            self._refresh()
            log.info("Ollama fully stopped and disabled. Only popcorn menu can restart.")
        except Exception as e:
            log.error(f"Failed to stop Ollama: {e}")
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Failed to Stop Ollama")
            alert.setInformativeText_(str(e))
            alert.runModal()

    def restartOllama_(self, sender):
        """Restart Ollama (stop then start)."""
        log.info("Restarting Ollama...")
        self.stopOllama_(sender)
        time.sleep(2)
        self.startOllama_(sender)


# ─── Lockfile (prevent duplicate instances) ──────────────────────────

POPCORN_LOCKFILE = os.path.expanduser("~/.ucore/ucore-popcorn.pid")


def acquire_lock() -> bool:
    """Acquire a PID lockfile — kills ALL existing popcorn instances first."""
    lock_dir = os.path.dirname(POPCORN_LOCKFILE)
    os.makedirs(lock_dir, exist_ok=True)

    # Kill any existing popcorn processes by name (handles launchd + manual dups)
    try:
        result = subprocess.run(
            ["pgrep", "-f", "popcorn.py"],
            capture_output=True, text=True, timeout=5
        )
        for pid_str in result.stdout.strip().splitlines():
            pid = pid_str.strip()
            if pid and int(pid) != os.getpid():
                try:
                    log.info(f"Killing existing Popcorn instance (PID {pid})")
                    os.kill(int(pid), 15)
                except (ProcessLookupError, OSError):
                    pass
        time.sleep(1)
        # Force kill any survivors
        for pid_str in result.stdout.strip().splitlines():
            pid = pid_str.strip()
            if pid and int(pid) != os.getpid():
                try:
                    os.kill(int(pid), 0)
                    os.kill(int(pid), 9)
                except (ProcessLookupError, OSError):
                    pass
        time.sleep(0.5)
    except Exception:
        pass

    with open(POPCORN_LOCKFILE, "w") as f:
        f.write(str(os.getpid()))
    log.info(f"Lockfile acquired (PID {os.getpid()})")
    return True


def release_lock():
    """Remove the lockfile if it belongs to us."""
    try:
        if os.path.exists(POPCORN_LOCKFILE):
            with open(POPCORN_LOCKFILE) as f:
                stored_pid = int(f.read().strip())
            if stored_pid == os.getpid():
                os.remove(POPCORN_LOCKFILE)
                log.info("Lockfile released")
    except (ValueError, OSError):
        pass


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    acquire_lock()
    log.info("Starting uDos Popcorn v3.0 — Surface Manager")

    app = NSApplication.sharedApplication()

    # Hide from Dock — this is a menu bar app only
    app.setActivationPolicy_(1)  # NSApplicationActivationPolicyAccessory

    # Set the process name so the menu bar shows "Popcorn" instead of "Python"
    from Foundation import NSProcessInfo
    NSProcessInfo.processInfo().setProcessName_("Popcorn")

    delegate = PopcornDelegate.alloc().init()
    delegate.setupStatusBar()
    app.setDelegate_(delegate)
    try:
        AppHelper.runEventLoop()
    finally:
        release_lock()


if __name__ == "__main__":
    main()
