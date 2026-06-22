#!/usr/bin/env python3
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
import urllib.request
import urllib.error

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
REFRESH_INTERVAL = 5.0  # seconds

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


def is_ucore_alive() -> bool:
    """Check if snackbar API is responding."""
    result = api_get("/api/health")
    return result is not None and result.get("status") == "ok"


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
                "🥞 Restart Ollama", "restartOllama:", ""
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
        icon = _make_status_icon(False)
        self._status_item.setImage_(icon)
        self._rebuild_menu()

    # ─── Actions ───────────────────────────────────────────────

    def openUIHub_(self, sender):
        """Open UI Hub in browser."""
        log.info("Opening UI Hub")
        subprocess.Popen(["open", UI_HUB_URL])

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
