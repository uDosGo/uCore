#!/usr/bin/env python3
"""
uDos Snackbar Menu — macOS menu bar app for Snackbar snacks v1.0.

Shows a hamburger icon in the menu bar:
  🍔 green = snackbar running
  🍔 grey  = snackbar offline

Menu items:
  - List of fruit-themed snacks (click to run)
  - Start at Login (toggle)
  - Restart uCore
  - Quit

Depends on: PyObjC (included with macOS Python)
"""

import os
import sys
import json
import time
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

UCORE_PLIST = os.path.expanduser("~/Library/LaunchAgents/com.udos.snackbar-server.plist")
SNACKBAR_SERVER = os.path.join("/Users/fredbook/Code/uCore/backend", "server.py")
SNACKBAR_WORKDIR = "/Users/fredbook/Code/uCore/backend"

log_dir = os.path.expanduser("~/.ucore/logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] ucore-menu: %(message)s",
    handlers=[logging.FileHandler(os.path.join(log_dir, "ucore-menu.log")), logging.StreamHandler()],
)
log = logging.getLogger("ucore-menu")


# ─── Helpers ──────────────────────────────────────────────────────────

def api_get(path: str, timeout: float = 3.0):
    """Call snackbar API and return parsed JSON, or None."""
    try:
        req = urllib.request.Request(f"{UCORE_URL}{path}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def api_post(path: str, timeout: float = 10.0):
    """POST to snackbar API and return parsed JSON, or None."""
    try:
        req = urllib.request.Request(f"{UCORE_URL}{path}", method="POST")
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


def is_start_at_login_enabled() -> bool:
    """Check if the snackbar launchd plist is loaded."""
    try:
        result = subprocess.run(
            ["launchctl", "list", "com.udos.snackbar-server"],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except Exception:
        return False


def enable_start_at_login():
    """Install and load the snackbar launchd plist."""
    try:
        result = subprocess.run(
            ["/usr/bin/python3", SNACKBAR_SERVER, "--install"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            log.warning(f"Install failed: {result.stderr}")
            return False

        uid = os.getuid()
        subprocess.run(
            ["launchctl", "bootstrap", f"gui/{uid}", UCORE_PLIST],
            capture_output=True, timeout=10
        )
        log.info("Start at login enabled")
        return True
    except Exception as e:
        log.warning(f"Failed to enable start at login: {e}")
        return False


def disable_start_at_login():
    """Unload and remove the snackbar launchd plist."""
    try:
        uid = os.getuid()
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}", UCORE_PLIST],
            capture_output=True, timeout=10
        )
        if os.path.exists(UCORE_PLIST):
            os.remove(UCORE_PLIST)
        log.info("Start at login disabled")
        return True
    except Exception as e:
        log.warning(f"Failed to disable start at login: {e}")
        return False


# ─── Icon ─────────────────────────────────────────────────────────────

def _make_status_icon(connected: bool) -> NSImage:
    """Create a hamburger icon using text."""
    char = "🍔"
    font = NSFont.systemFontOfSize_(16)
    attrs = {
        "NSFontAttributeName": font,
        "NSForegroundColorAttributeName": (
            NSColor.greenColor() if connected else NSColor.grayColor()
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

class SnackbarMenuDelegate(NSObject):
    """Main delegate for the snackbar menu bar app."""

    def init(self):
        self = objc.super(SnackbarMenuDelegate, self).init()
        if self is None:
            return None
        self._connected = False
        self._status_item = None
        self._menu = None
        self._snacks = []
        self._start_at_login = False
        self._refresh_timer = None
        return self

    def setupStatusBar(self):
        """Create the status bar item."""
        bar = NSStatusBar.systemStatusBar()
        self._status_item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        self._status_item.retain()

        # Set initial icon
        icon = _make_status_icon(False)
        self._status_item.setImage_(icon)

        # Create menu
        self._menu = NSMenu.alloc().init()
        self._menu.setAutoenablesItems_(False)
        self._status_item.setMenu_(self._menu)

        # Check initial start-at-login state
        self._start_at_login = is_start_at_login_enabled()

        # Build initial menu
        self._rebuild_menu()

        # Start refresh timer
        self._start_refresh()

    def _rebuild_menu(self):
        """Rebuild the entire menu from current state."""
        self._menu.removeAllItems()

        # ── Header ──────────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍔 Snackbar Menu", None, ""
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

        # ── Snacks (fruit-themed) ──────────────────────────────
        snacks_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "😋 Snacks", None, ""
        )
        snacks_title.setEnabled_(False)
        self._menu.addItem_(snacks_title)

        if self._connected and self._snacks:
            # Fruit emoji order: Analyze→🫐, Code→🍊, Format→🍎, Image→🍌, Summarize→🍓,
            # Translate→🍋, Write→🍑, Mail Bridge→🥝, iCloud→🍇
            fruit_icons = ["🫐", "🍊", "🍎", "🍌", "🍓", "🍋", "🍑", "🥝", "🍇", "🍍", "🥭", "🍈"]
            for i, s in enumerate(self._snacks):
                fruit = fruit_icons[i % len(fruit_icons)]
                label = f"{fruit} {s['name']}"
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    label, "runSnack:", ""
                )
                item.setTarget_(self)
                item.setRepresentedObject_(s["id"])
                self._menu.addItem_(item)
        else:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "(snackbar offline)" if not self._connected else "(no snacks)",
                None, ""
            )
            item.setEnabled_(False)
            self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Start at Login ─────────────────────────────────────
        state = "✓" if self._start_at_login else "  "
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{state} Start at Login", "toggleStartAtLogin:", ""
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Restart uCore ───────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "❄️ Restart uCore", "restartUcore:", ""
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

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
        """Refresh snackbar status and rebuild menu."""
        try:
            self._connected = is_ucore_alive()
            if self._connected:
                snacks_data = api_get("/api/snacks")
                self._snacks = snacks_data.get("snacks", []) if snacks_data else []
            else:
                self._snacks = []
            self._start_at_login = is_start_at_login_enabled()
        except Exception as e:
            log.warning(f"Refresh error: {e}")
            self._connected = False

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
        icon = _make_status_icon(self._connected)
        self._status_item.setImage_(icon)
        self._rebuild_menu()

    # ─── Actions ───────────────────────────────────────────────

    def openUIHub_(self, sender):
        """Open UI Hub in browser."""
        log.info("Opening UI Hub")
        subprocess.Popen(["open", UI_HUB_URL])

    def runSnack_(self, sender):
        """Run a snack."""
        sid = sender.representedObject()
        if not sid:
            return
        log.info(f"Running snack: {sid}")
        result = api_post(f"/api/snacks/{sid}/deliver")
        if result:
            if "error" in result:
                log.warning(f"Snack {sid} failed: {result['error']}")
            else:
                log.info(f"Snack {sid} completed (exit {result.get('returncode', '?')})")

    def toggleStartAtLogin_(self, sender):
        """Toggle the start-at-login setting."""
        if self._start_at_login:
            log.info("Disabling start at login")
            disable_start_at_login()
            self._start_at_login = False
        else:
            log.info("Enabling start at login")
            enable_start_at_login()
            self._start_at_login = True
        self._rebuild_menu()

    def restartUcore_(self, sender):
        """Restart the snackbar server."""
        log.info("Restarting snackbar...")
        subprocess.run(
            ["pkill", "-f", "snackbar/server.py"],
            capture_output=True, timeout=5
        )
        time.sleep(2)
        subprocess.Popen(
            ["/usr/bin/python3", SNACKBAR_SERVER, "--port", "8484", "--auto-start"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
        self._refresh()

    def quitApp_(self, sender):
        """Quit the snackbar menu app."""
        log.info("Quitting ucore-menu")
        if self._refresh_timer:
            self._refresh_timer.cancel()
        NSApplication.sharedApplication().terminate_(self)


# ─── Lockfile ─────────────────────────────────────────────────────────

LOCKFILE = os.path.expanduser("~/.ucore/ucore-menu.pid")


def acquire_lock() -> bool:
    """Acquire a PID lockfile — kills ALL existing ucore-menu instances first."""
    lock_dir = os.path.dirname(LOCKFILE)
    os.makedirs(lock_dir, exist_ok=True)

    # Kill any existing ucore-menu processes by name (handles launchd + manual dups)
    try:
        result = subprocess.run(
            ["pgrep", "-f", "snackbar_menu.py"],
            capture_output=True, text=True, timeout=5
        )
        for pid_str in result.stdout.strip().splitlines():
            pid = pid_str.strip()
            if pid and int(pid) != os.getpid():
                try:
                    log.info(f"Killing existing ucore-menu instance (PID {pid})")
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

    with open(LOCKFILE, "w") as f:
        f.write(str(os.getpid()))
    log.info(f"Lockfile acquired (PID {os.getpid()})")
    return True


def release_lock():
    """Remove the lockfile if it belongs to us."""
    try:
        if os.path.exists(LOCKFILE):
            with open(LOCKFILE) as f:
                stored_pid = int(f.read().strip())
            if stored_pid == os.getpid():
                os.remove(LOCKFILE)
                log.info("Lockfile released")
    except (ValueError, OSError):
        pass


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    acquire_lock()
    log.info("Starting uCore Menu v1.0")

    app = NSApplication.sharedApplication()

    # Hide from Dock — this is a menu bar app only
    app.setActivationPolicy_(1)  # NSApplicationActivationPolicyAccessory

    # Set the process name
    from Foundation import NSProcessInfo
    NSProcessInfo.processInfo().setProcessName_("uCore Menu")

    delegate = SnackbarMenuDelegate.alloc().init()
    delegate.setupStatusBar()
    app.setDelegate_(delegate)
    try:
        AppHelper.runEventLoop()
    finally:
        release_lock()


if __name__ == "__main__":
    main()
