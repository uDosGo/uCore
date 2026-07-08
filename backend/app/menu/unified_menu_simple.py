"""Unified uCore Menu Bar App — Simplified version.

CONSOLIDATED MENU: Only essential actions appear here.
Full snack management is available in the SnackMachine surface.

This is the streamlined menu that focuses on:
- UI Hub status and access
- Quick access to SnackMachine surface
- Clipboard buffer (essential)
- Backend status
- Start at login toggle
"""
from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path

import objc
from AppKit import (
    NSAlert,
    NSApp,
    NSApplication,
    NSMenu,
    NSMenuItem,
)
from Foundation import NSObject

try:
    from AppKit import NSEvent, NSEventMaskKeyDown
except Exception:
    NSEvent = NSEventMaskKeyDown = None
from PyObjCTools import AppHelper
from snackmachine.registry import get_registry

# Import modular components
from app.menu.api_helpers import (
    api_get_sync,
    is_ucore_alive,
    is_uihub_alive,
    open_url,
)

# Import snack registry and plugins
from app.menu.backend_manager import ensure_backend_running
from app.menu.launchd_integration import (
    install_launchd,
    is_launchd_installed,
    uninstall_launchd,
)
from app.menu.lockfile import acquire_lock, release_lock
from app.menu.snacks.clipboard_snack import register as register_clipboard
from app.menu.status_icon import _make_status_icon, update_status_icon

# ─── Config ───────────────────────────────────────────────────────────
UCORE_URL = "http://127.0.0.1:8484"
UI_HUB_URL = "http://localhost:5175"
REFRESH_INTERVAL = 30.0  # seconds

UCORE_LABEL = "com.udos.ucore-menu"
UCORE_PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{UCORE_LABEL}.plist")
UCORE_LOCKFILE = os.path.expanduser("~/.ucore/ucore-menu.pid")
UCORE_BACKEND_DIR = os.environ.get("UCORE_BACKEND_DIR", str(Path.home() / "Code" / "uCore" / "backend"))

log_dir = os.path.expanduser("~/.ucore/logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] ucore-menu: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "ucore-menu.log")),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("ucore-menu")


# ─── Frontend helpers ─────────────────────────────────────────────────


def _ensure_frontend_running() -> bool:
    """Ensure both backend and frontend are running.

    Returns True if frontend is reachable after this call.
    Extracted from duplicated blocks in openUIHub_, openSnackMachine_,
    and showClipboardPopover_.
    """
    if is_uihub_alive():
        return True

    if not is_ucore_alive():
        ensure_backend_running()
        time.sleep(2)

    log.info("Starting frontend via launchd...")
    try:
        from app.menu.launchd_manager import (
            install_frontend,
            is_frontend_installed,
        )
        if not is_frontend_installed():
            install_frontend()
        for _ in range(20):
            time.sleep(0.5)
            if is_uihub_alive():
                log.info("Frontend started successfully")
                return True
    except Exception as e:
        log.error(f"Failed to start frontend: {e}")

    return is_uihub_alive()


# ─── App Delegate ─────────────────────────────────────────────────────

class UnifiedMenuDelegate(NSObject):
    """Main delegate for the unified uCore menu bar app."""

    def init(self):
        self = objc.super(UnifiedMenuDelegate, self).init()
        if self is None:
            return None

        self._connected = False
        self._uihub_connected = False
        self._start_at_login = False
        self._status_item = None
        self._menu = None
        self._refresh_timer = None
        self._clipboard_panel = None
        self._clipboard_search_field = None
        self._clipboard_table = None
        self._clipboard_panel_items = []
        self._global_shortcut_monitor = None

        self._registry = get_registry()
        self._clipboard_snack = register_clipboard(self)

        return self

    def setupStatusBar(self):
        """Create the status bar item."""
        # Create status item with emoji title directly
        self._status_item = _make_status_icon(False)
        self._status_item.retain()

        self._menu = NSMenu.alloc().init()
        self._menu.setAutoenablesItems_(False)
        self._status_item.setMenu_(self._menu)

        self._start_at_login = is_launchd_installed()
        self._rebuild_menu()
        self._register_global_shortcut()
        self._start_refresh()

    def _register_global_shortcut(self):
        """Register global shortcut for clipboard panel (Ctrl+Cmd+V)."""
        try:
            from AppKit import NSEvent, NSEventMaskKeyDown

            from app.menu.shortcut_utils import MOD_ALL, MOD_COMMAND, MOD_CONTROL

            wanted_mods = MOD_CONTROL | MOD_COMMAND
            wanted_key = 9  # 'v' key code

            def _handler(event):
                try:
                    actual = int(event.modifierFlags()) & MOD_ALL
                    if actual == wanted_mods and int(event.keyCode()) == wanted_key:
                        self.performSelectorOnMainThread_withObject_waitUntilDone_(
                            "showClipboardPopover:", None, False,
                        )
                except Exception as exc:
                    log.debug("Global shortcut handler error: %s", exc)

            self._global_shortcut_monitor = (
                NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                    NSEventMaskKeyDown, _handler
                )
            )
            log.info("Global clipboard shortcut registered: Ctrl+Cmd+V")
        except Exception as exc:
            log.warning("Failed to register global shortcut: %s", exc)

    def _rebuild_menu(self):
        """Rebuild the menu - CONSOLIDATED to essential items only."""
        self._menu.removeAllItems()

        # ── Header ──────────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍔 SnackShack", None, "h",
        )
        item.setEnabled_(True)
        item.setTarget_(self)
        item.setAction_("openSnackMachine:")
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── UI Hub Section ──────────────────────────────────────
        uihub_status = "😊" if self._uihub_connected else "😢"
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{uihub_status} Frontend", None, "",
        )
        item.setEnabled_(False)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍒 Open UI Hub", "openUIHub:", "o",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Quick Actions ────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍟 SnackMachine", "openSnackMachine:", "s",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🏝️ Clipboard", "showClipboardPopover:", "v",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Status ───────────────────────────────────────────────
        backend_status = "😊" if self._connected else "😢"
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{backend_status} Backend", None, "",
        )
        item.setEnabled_(False)
        self._menu.addItem_(item)

        state = "✓" if self._start_at_login else "  "
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{state} Start at Login", "toggleStartAtLogin:", "",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Quit ───────────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🔥 Quit", "quitApp:", "q",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

    def _start_refresh(self):
        """Start the periodic refresh timer."""
        self._refresh()

    def _refresh(self):
        """Refresh all status and rebuild menu."""
        try:
            self._connected = is_ucore_alive()
            self._uihub_connected = is_uihub_alive()
            self._start_at_login = is_launchd_installed()

            if self._connected:
                clip_data = api_get_sync("/api/snacks/clipboard?limit=24")
                if clip_data:
                    clip_items = clip_data.get("items", [])
                    recent = [c for c in clip_items if not c.get("pinned")]
                    saved = [c for c in clip_items if c.get("pinned")]
                    if self._clipboard_snack:
                        self._clipboard_snack.update_items(recent, saved)
        except Exception as e:
            log.warning(f"Refresh error: {e}")
            self._connected = False

        if self._refresh_timer:
            self._refresh_timer.cancel()
        self._refresh_timer = threading.Timer(REFRESH_INTERVAL, self._refresh)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()

        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False,
        )

    def updateUI_(self, sender):
        """Called on main thread to update icon and menu."""
        update_status_icon(self._status_item, self._connected)
        self._rebuild_menu()

    # ─── Actions ───────────────────────────────────────────────────

    def openUIHub_(self, _sender):
        """Open UI Hub in browser with auto-start."""
        log.info("Opening UI Hub")
        if _ensure_frontend_running():
            open_url(UI_HUB_URL)
        else:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("UIHub not reachable")
            alert.setInformativeText_(
                "Backend is running but UI Hub is still down."
            )
            alert.runModal()

    def openSnackMachine_(self, _sender):
        """Open SnackMachine surface in browser with auto-start."""
        log.info("Opening SnackMachine")
        _ensure_frontend_running()
        open_url("http://localhost:5175/snackmachine")

    def showClipboardPopover_(self, _sender):
        """Show the clipboard popover panel."""
        _ensure_frontend_running()
        # Simplified: just open the S310 clipboard page
        open_url("http://localhost:5175/s310")

    def toggleStartAtLogin_(self, _sender):
        """Toggle start at login."""
        if self._start_at_login:
            uninstall_launchd()
        else:
            install_launchd()
        self._start_at_login = is_launchd_installed()
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False,
        )

    def quitApp_(self, _sender):
        """Quit the menu app."""
        log.info("Quitting uCore Menu")
        if self._refresh_timer:
            self._refresh_timer.cancel()
        if self._global_shortcut_monitor:
            from AppKit import NSEvent
            NSEvent.removeMonitor_(self._global_shortcut_monitor)
        release_lock()
        NSApplication.sharedApplication().terminate_(self)


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    if not acquire_lock():
        print("Failed to acquire lock")
        return

    # Auto-start backend if not running
    if not is_ucore_alive():
        log.info("Backend not running, attempting auto-start...")
        ensure_backend_running()

    app = NSApplication.sharedApplication()

    # Hide from Dock — this is a menu bar app only
    app.setActivationPolicy_(1)  # NSApplicationActivationPolicyAccessory
    app.activateIgnoringOtherApps_(True)

    # Set the process name for Activity Monitor
    from Foundation import NSProcessInfo
    NSProcessInfo.processInfo().setProcessName_("uCore Menu")

    delegate = UnifiedMenuDelegate.alloc().init()
    delegate.setupStatusBar()

    NSApp().setDelegate_(delegate)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
