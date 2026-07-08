"""Unified uCore Menu Bar App — Single modular menu bar application.

Combines: Ollama management, UI Hub health, Clipboard buffer, Snacks,
Surfaces, System services.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import objc
from AppKit import (
    NSAlert,
    NSApp,
    NSApplication,
    NSAttributedString,
    NSBackingStoreBuffered,
    NSButton,
    NSColor,
    NSFont,
    NSImage,
    NSMenu,
    NSMenuItem,
    NSPanel,
    NSScrollView,
    NSStatusBar,
    NSTableColumn,
    NSTableView,
    NSTextField,
    NSVariableStatusItemLength,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskUtilityWindow,
    NSWorkspace,
)
from Foundation import NSURL, NSObject

try:
    from AppKit import NSEvent, NSEventMaskKeyDown
except Exception:
    NSEvent = NSEventMaskKeyDown = None
from PyObjCTools import AppHelper
from snackmachine.registry import get_registry

# Import snack registry and plugins
from app.menu.backend_manager import ensure_backend_running
from app.menu.snacks.appflowy_sync_snack import (
    register as register_appflowy_sync,
)
from app.menu.snacks.clipboard_snack import register as register_clipboard
from app.menu.snacks.ollama_snack import register as register_ollama
from app.menu.snacks.surface_snack import register as register_surface
from app.menu.snacks.system_snack import register as register_system

# ─── Config ───────────────────────────────────────────────────────────

UCORE_URL = "http://127.0.0.1:8484"
UI_HUB_URL = "http://localhost:5173"
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


# ─── Helpers ──────────────────────────────────────────────────────────

def api_get(path: str, timeout: float = 3.0):
    """Call snackbar API and return parsed JSON, or None."""
    try:
        req = urllib.request.Request(f"{UCORE_URL}{path}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def api_post_json(
    path: str, payload: dict | None = None, timeout: float = 6.0
):
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
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def open_url(url: str):
    """Open a URL in the default browser."""
    NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(url))


def _run_osascript(script: str, timeout: int = 8) -> str:
    """Run an osascript command and return output."""
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "osascript failed")
    return proc.stdout.strip()


def _make_status_icon(connected: bool) -> NSImage:
    """Create a status icon (popcorn emoji)."""
    char = "🍿"
    font = NSFont.systemFontOfSize_(16)
    attrs = {
        "NSFontAttributeName": font,
        "NSForegroundColorAttributeName": (
            NSColor.greenColor() if connected else NSColor.grayColor()
        ),
    }
    attr_str = NSAttributedString.alloc().initWithString_attributes_(
        char, attrs
    )
    text_size = attr_str.size()
    image = NSImage.alloc().initWithSize_(text_size)
    image.lockFocus()
    attr_str.drawAtPoint_((0, 0))
    image.unlockFocus()
    return image


# ─── Lockfile Management ──────────────────────────────────────────────

def acquire_lock() -> bool:
    """Acquire a PID lockfile — gracefully handle existing instances."""
    lock_dir = Path(UCORE_LOCKFILE).parent
    lock_dir.mkdir(parents=True, exist_ok=True)

    # Check if lockfile exists and process is still alive
    lock_path = Path(UCORE_LOCKFILE)
    if lock_path.exists():
        try:
            stored_pid = int(lock_path.read_text().strip())
            # Check if process exists
            os.kill(stored_pid, 0)
            # Process exists, try to terminate gracefully
            log.info(
                "Existing menu instance found (PID %s), terminating...",
                stored_pid,
            )
            os.kill(stored_pid, 15)  # SIGTERM
            time.sleep(1)
            # Force kill if still alive
            try:
                os.kill(stored_pid, 0)
                os.kill(stored_pid, 9)  # SIGKILL
            except (ProcessLookupError, OSError):
                pass
        except (ValueError, ProcessLookupError, OSError):
            pass  # Lockfile stale or invalid

    # Write our PID
    lock_path.write_text(str(os.getpid()))
    log.info("Lockfile acquired (PID %s)", os.getpid())
    return True


def release_lock():
    """Remove the lockfile if it belongs to us."""
    try:
        lock_path = Path(UCORE_LOCKFILE)
        if lock_path.exists():
            stored_pid = int(lock_path.read_text().strip())
            if stored_pid == os.getpid():
                lock_path.unlink()
                log.info("Lockfile released")
    except (ValueError, OSError):
        pass


# ─── Launchd Integration (delegates to launchd_manager) ──────────────

def install_launchd() -> bool:
    """Install launchd plist for auto-start (delegates to launchd_manager)."""
    from app.menu.launchd_manager import install as launchd_install
    return launchd_install()


def uninstall_launchd() -> bool:
    """Uninstall launchd plist (delegates to launchd_manager)."""
    from app.menu.launchd_manager import uninstall as launchd_uninstall
    return launchd_uninstall()


def is_launchd_installed() -> bool:
    """Check if launchd plist is installed (delegates to launchd_manager)."""
    from app.menu.launchd_manager import is_installed
    return is_installed()


# ─── App Delegate ─────────────────────────────────────────────────────

class UnifiedMenuDelegate(NSObject):
    """Main delegate for the unified uCore menu bar app."""

    def init(self):
        self = objc.super(UnifiedMenuDelegate, self).init()
        if self is None:
            return None

        # State
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

        # Snack registry
        self._registry = get_registry()

        # Register built-in snacks
        self._clipboard_snack = register_clipboard(self)
        self._ollama_snack = register_ollama(self)
        self._surface_snack = register_surface(self)
        self._system_snack = register_system(self)
        self._appflowy_sync_snack = register_appflowy_sync(self)

        return self

    def setupStatusBar(self):
        """Create the status bar item."""
        bar = NSStatusBar.systemStatusBar()
        self._status_item = bar.statusItemWithLength_(
            NSVariableStatusItemLength
        )
        self._status_item.retain()

        # Set initial icon
        icon = _make_status_icon(False)
        self._status_item.setImage_(icon)

        # Create menu
        self._menu = NSMenu.alloc().init()
        self._menu.setAutoenablesItems_(False)
        self._status_item.setMenu_(self._menu)

        # Check initial start-at-login state
        self._start_at_login = is_launchd_installed()

        # Build initial menu
        self._rebuild_menu()

        # Register global shortcut for clipboard
        self._register_global_shortcut()

        # Start refresh timer
        self._start_refresh()

    def _register_global_shortcut(self):
        """Register global shortcut for clipboard panel (Ctrl+Cmd+V)."""
        try:
            from AppKit import NSEvent, NSEventMaskKeyDown

            # Use shortcut_utils constants instead of Foundation imports
            from app.menu.shortcut_utils import (
                MOD_ALL,
                MOD_COMMAND,
                MOD_CONTROL,
            )

            wanted_mods = MOD_CONTROL | MOD_COMMAND
            wanted_key = 9  # 'v' key code

            def _handler(event):
                try:
                    actual = int(event.modifierFlags()) & MOD_ALL
                    if (
                        actual == wanted_mods
                        and int(event.keyCode()) == wanted_key
                    ):
                        self.performSelectorOnMainThread_withObject_waitUntilDone_(
                            "showClipboardPopover:",
                            None,
                            False,
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
        """Rebuild the entire menu from current state and snack registry."""
        self._menu.removeAllItems()

        # ── Header ──────────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍿 uCore Menu", None, "",
        )
        item.setEnabled_(False)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── UI Hub Section ──────────────────────────────────────
        uihub_status = "🟢" if self._uihub_connected else "🔴"
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{uihub_status} UI Hub", None, "",
        )
        item.setEnabled_(False)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍒 Open UI Hub", "openUIHub:", "o",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🩺 Health Check", "healthCheck:", "h",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🛠 Heal UI Hub", "healUIHub:", "r",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🧭 Open S190 Diagnostics", "openS190Diagnostics:", "d",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Ollama Section ──────────────────────────────────────
        ollama_snack = self._registry.get("ollama-manager")
        if ollama_snack:
            spec = ollama_snack.spec
            status_icon = spec.icon
            status_label = spec.metadata.get("status", "unknown").capitalize()
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"{status_icon} Ollama ({status_label})", None, "",
            )
            item.setEnabled_(False)
            self._menu.addItem_(item)

            models = spec.metadata.get("models", [])
            if models:
                for model in models[:5]:  # Limit to 5 models
                    item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                        f"  📦 {model}", None, "",
                    )
                    item.setEnabled_(False)
                    self._menu.addItem_(item)

            # Ollama controls
            if spec.metadata.get("status") == "running":
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "○ Stop Ollama", "ollamaAction:", "",
                )
                item.setTarget_(self)
                item.setRepresentedObject_(json.dumps({"action": "stop"}))
                self._menu.addItem_(item)

                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "○ Restart Ollama", "ollamaAction:", "",
                )
                item.setTarget_(self)
                item.setRepresentedObject_(json.dumps({"action": "restart"}))
                self._menu.addItem_(item)
            else:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "🥞 Start Ollama", "ollamaAction:", "",
                )
                item.setTarget_(self)
                item.setRepresentedObject_(json.dumps({"action": "start"}))
                self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Clipboard Buffer ───────────────────────────────────
        clipboard_snack = self._registry.get("clipboard-buffer")
        if clipboard_snack:
            recent, saved = clipboard_snack.get_items()
            total_clip = len(recent) + len(saved)
            clip_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"📋 Clipboard Buffer ({total_clip})", None, "",
            )
            clip_title.setEnabled_(False)
            self._menu.addItem_(clip_title)

            from app.menu.shortcut_utils import shortcut_display
            clip_hint = shortcut_display("ctrl+cmd+v")
            search_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"📋 Open Clipboard Panel  {clip_hint}",
                "showClipboardPopover:",
                "",
            )
            search_item.setTarget_(self)
            self._menu.addItem_(search_item)

            search_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "🔍 Search...", "searchClipboard:", "f",
            )
            search_item.setTarget_(self)
            self._menu.addItem_(search_item)

            capture_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "➕ Capture Current Clipboard", "captureClipboard:", "",
            )
            capture_item.setTarget_(self)
            self._menu.addItem_(capture_item)

            if saved:
                saved_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    f"📌 Saved Items ({len(saved)})", None, "",
                )
                saved_title.setEnabled_(False)
                self._menu.addItem_(saved_title)
                for item_data in saved[:5]:
                    preview = (item_data.get("content") or "").replace("\n", " ").strip()
                    if len(preview) > 50:
                        preview = preview[:47] + "..."
                    item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                        f"📌 {preview or '(empty)'}", "pasteClipboardItem:", "",
                    )
                    item.setTarget_(self)
                    item.setRepresentedObject_(item_data.get("id"))
                    self._menu.addItem_(item)

            if recent:
                recent_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "📄 Recent", None, "",
                )
                recent_title.setEnabled_(False)
                self._menu.addItem_(recent_title)
                for item_data in recent[:8]:
                    preview = (item_data.get("content") or "").replace("\n", " ").strip()
                    if len(preview) > 54:
                        preview = preview[:51] + "..."
                    item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                        f"📄 {preview or '(empty)'}", "pasteClipboardItem:", "",
                    )
                    item.setTarget_(self)
                    item.setRepresentedObject_(item_data.get("id"))
                    self._menu.addItem_(item)

            self._menu.addItem_(NSMenuItem.separatorItem())

            clear_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "🗑️ Clear History", "clearClipboardHistory:", "",
            )
            clear_item.setTarget_(self)
            self._menu.addItem_(clear_item)

            clear_all_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "🧨 Clear All (Including Saved)", "clearClipboardAll:", "",
            )
            clear_all_item.setTarget_(self)
            self._menu.addItem_(clear_all_item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Snacks (from registry) ──────────────────────────────
        snacks_by_category = self._registry.get_by_category()
        for category, snacks in snacks_by_category.items():
            if category in ["clipboard", "surface", "system"]:
                continue  # Handled separately

            cat_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"😋 {category.capitalize()}", None, "",
            )
            cat_title.setEnabled_(False)
            self._menu.addItem_(cat_title)

            for snack in snacks:
                spec = snack.spec
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    f"{spec.icon} {spec.name}", "runSnack:", "",
                )
                item.setTarget_(self)
                item.setRepresentedObject_(json.dumps({
                    "id": spec.id,
                    "kind": spec.kind,
                    "actions": spec.actions,
                }))
                self._menu.addItem_(item)

                if spec.kind == "multi-action":
                    for action_name in spec.actions:
                        sub = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                            f"   ↳ {action_name}", "runSnack:", "",
                        )
                        sub.setTarget_(self)
                        sub.setRepresentedObject_(json.dumps({
                            "id": spec.id,
                            "kind": "multi-action",
                            "action": action_name,
                            "actions": spec.actions,
                        }))
                        self._menu.addItem_(sub)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Surfaces (Dynamic from API) ─────────────────────────
        surfaces_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🖥️ Surfaces", None, "",
        )
        surfaces_title.setEnabled_(False)
        self._menu.addItem_(surfaces_title)

        surface_snack = self._registry.get("surface-manager")
        if surface_snack and surface_snack._surfaces:
            for surface in surface_snack._surfaces:
                name = surface.get("name", surface.get("id", "Unknown"))
                icon = surface.get("metadata", {}).get("icon", "🖥️")
                surface_id = surface.get("id", "")
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    f"{icon} {name}", "openSurface:", "",
                )
                item.setTarget_(self)
                item.setRepresentedObject_(surface_id)
                self._menu.addItem_(item)
        else:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "(no surfaces - click to refresh)", "refreshSurfaces:", "",
            )
            item.setTarget_(self)
            self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── System Services ────────────────────────────────────
        services_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⚙️ Services", None, "",
        )
        services_title.setEnabled_(False)
        self._menu.addItem_(services_title)

        backend_status = "🟢" if self._connected else "🔴"
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{backend_status} Backend (uCore on :8484)", None, "",
        )
        item.setEnabled_(False)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "↻ Restart Backend", "restartBackend:", "",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🌐 Restart Frontend Dev Server", "restartFrontend:", "",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

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
            # Check backend
            self._connected = is_ucore_alive()

            # Check UI Hub
            self._uihub_connected = is_uihub_alive()

            # Check start at login
            self._start_at_login = is_launchd_installed()

            # Refresh snacks from backend
            if self._connected:
                snacks_data = api_get("/api/snacks/system")
                if snacks_data:
                    self._registry.update_from_backend(snacks_data.get("snacks", []))

                # Refresh clipboard
                clip_data = api_get("/api/snacks/clipboard?limit=24")
                if clip_data:
                    clip_items = clip_data.get("items", [])
                    recent = [c for c in clip_items if not c.get("pinned")]
                    saved = [c for c in clip_items if c.get("pinned")]
                    if self._clipboard_snack:
                        self._clipboard_snack.update_items(recent, saved)

                # Refresh surfaces
                surfaces_data = api_get("/api/surfaces/list")
                if surfaces_data:
                    surfaces = surfaces_data.get("surfaces", [])
                    if self._surface_snack:
                        self._surface_snack.update_surfaces(surfaces, self._connected)

                # Refresh Ollama status
                if self._ollama_snack:
                    self._ollama_snack._refresh_status()

            # Update system snack status
            if self._system_snack:
                self._system_snack.update_status(
                    self._connected, self._uihub_connected, self._start_at_login
                )

        except Exception as e:
            log.warning(f"Refresh error: {e}")
            self._connected = False

        # Schedule next refresh
        if self._refresh_timer:
            self._refresh_timer.cancel()
        self._refresh_timer = threading.Timer(REFRESH_INTERVAL, self._refresh)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()

        # Update UI on main thread
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False,
        )

    def updateUI_(self, sender):
        """Called on main thread to update icon and menu."""
        icon = _make_status_icon(self._connected)
        self._status_item.setImage_(icon)
        self._rebuild_menu()
        self._refresh_clipboard_panel_content()

    # ─── Actions ───────────────────────────────────────────────────

    def openUIHub_(self, _sender):
        """Open UI Hub in browser with auto-start."""
        log.info("Opening UI Hub (with auto-start)")
        if self._ensure_uihub_running():
            open_url(UI_HUB_URL)
            return

        self._open_s190_fallback("uihub-cant-connect")
        alert = NSAlert.alloc().init()
        alert.setMessageText_("UIHub not reachable")
        alert.setInformativeText_(
            "Menu tried auto-start + heal, but localhost:5173 is still down."
        )
        alert.runModal()

    def _ensure_uihub_running(self, timeout_s: float = 12.0) -> bool:
        """Ensure UI Hub is running using surface runtime APIs."""
        if is_uihub_alive():
            return True
        if not ensure_backend_running():
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

    def healthCheck_(self, _sender):
        """Run health checks and show summary."""
        backend_ok = ensure_backend_running()
        health = api_get("/api/health") if backend_ok else None
        uihub_ok = is_uihub_alive()

        lines = [
            f"Backend: {'ok' if backend_ok else 'down'}",
            f"UI Hub: {'ok' if uihub_ok else 'down'}",
        ]
        if health:
            lines.append(f"API status: {health.get('status', 'unknown')}")

        alert = NSAlert.alloc().init()
        alert.setMessageText_("uCore Health Check")
        alert.setInformativeText_("\n".join(lines))
        alert.runModal()

    def healUIHub_(self, _sender):
        """Try repair/restart/start flow for UI Hub."""
        if not ensure_backend_running():
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Heal failed")
            alert.setInformativeText_("Backend could not be started.")
            alert.runModal()
            return

        _ = api_post_json("/api/surfaces/ui-hub/repair")
        _ = api_post_json("/api/surfaces/ui-hub/restart")
        _ = api_post_json("/api/surfaces/ui-hub/start")

        if self._ensure_uihub_running(timeout_s=8.0):
            open_url(UI_HUB_URL)
            return

        self._open_s190_fallback("uihub-heal-failed")

    def openS190Diagnostics_(self, _sender):
        """Open local S190 diagnostics fallback page."""
        self._open_s190_fallback("manual-s190-diagnostics")

    def _open_s190_fallback(self, reason: str):
        """Open a local S190-style fallback page."""
        fallback_path = Path.home() / ".ucore" / "s190-uihub-fallback.html"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)

        safe_reason = reason.replace("<", "<").replace(">", ">")
        retry_url = UI_HUB_URL
        api_health_url = f"{UCORE_URL}/api/health"
        fallback_s190 = f"{UI_HUB_URL}/s190?reason={urllib.parse.quote(reason)}"
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
      <p>UI Hub is not reachable. Menu attempted auto-start and health healing.</p>
      <p>Reason: <span class="code">{safe_reason}</span></p>
      <div class="row">
        <a href="{retry_url}">Retry UI Hub</a>
        <a href="{fallback_s190}">Open S190 in UI Hub</a>
        <a href="{api_health_url}">Open API Health</a>
      </div>
    </div>
  </main>
</body>
</html>"""
        fallback_path.write_text(html)
        open_url(f"file://{fallback_path}")

    def ollamaAction_(self, sender):
        """Handle Ollama actions (start/stop/restart)."""
        import json
        data = json.loads(sender.representedObject())
        action = data.get("action")
        if self._ollama_snack:
            self._ollama_snack.execute(action)

    def openSurface_(self, sender):
        """Open a surface URL in the browser."""
        surface_id = sender.representedObject()
        if self._surface_snack:
            self._surface_snack.execute(f"open-{surface_id}")

    def refreshSurfaces_(self, sender):
        """Refresh surfaces from API."""
        if self._surface_snack:
            self._surface_snack._refresh_surfaces()

    def runSnack_(self, sender):
        """Execute a snack action."""
        import json
        data = json.loads(sender.representedObject())
        snack_id = data.get("id")
        action = data.get("action")
        self._registry.execute(snack_id, action)

    def restartBackend_(self, _sender):
        """Restart the uCore backend daemon."""
        log.info("Restarting backend...")
        try:
            subprocess.run(["pkill", "-f", "python.*-m app"], capture_output=True)
            time.sleep(1)
            venv_python = Path(UCORE_BACKEND_DIR) / ".venv" / "bin" / "python"
            python_bin = str(venv_python) if venv_python.exists() else "/usr/bin/python3"
            subprocess.Popen(
                [python_bin, "-m", "app.core.snackbar", "--port", "8484", "--auto-start"],
                cwd=UCORE_BACKEND_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            time.sleep(2)
        except Exception as e:
            log.exception("Failed to restart backend: %s", e)

    def restartFrontend_(self, _sender):
        """Restart the frontend dev server."""
        log.info("Restarting frontend dev server...")
        try:
            subprocess.run(["pkill", "-f", "vite"], capture_output=True)
            time.sleep(1)
            subprocess.Popen(
                ["pnpm", "run", "dev"],
                cwd=os.environ.get("UCORE_FRONTEND_DIR", str(Path.home() / "Code" / "uCore" / "frontend")),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as e:
            log.exception("Failed to restart frontend: %s", e)

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

    # ─── Clipboard Panel (from snackbar_menu.py) ──────────────────

    def showClipboardPopover_(self, _sender):
        """Show the clipboard popover panel."""
        self._ensure_clipboard_panel()
        self._position_clipboard_panel()
        self._refresh_clipboard_panel_content()
        self._clipboard_panel.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        if self._clipboard_search_field is not None:
            self._clipboard_panel.makeFirstResponder_(self._clipboard_search_field)

    def hideClipboardPopover_(self, _sender):
        """Close the floating clipboard panel."""
        if self._clipboard_panel is not None:
            self._clipboard_panel.orderOut_(None)

    def refreshClipboardPopover_(self, _sender):
        """Reload clipboard items inside the floating panel."""
        self._refresh_clipboard_panel_content()

    def searchClipboard_(self, _sender):
        """Prompt for a query and paste a selected search result."""
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Search Clipboard Buffer")
        alert.setInformativeText_("Type a query to find past copies")
        field = NSTextField.alloc().initWithFrame_(((0, 0), (280, 24)))
        alert.setAccessoryView_(field)
        alert.addButtonWithTitle_("Search")
        alert.addButtonWithTitle_("Cancel")
        choice = alert.runModal()
        if choice != 1000:
            return
        query = field.stringValue().strip()
        if not query:
            return

        result = api_get(f"/api/snacks/clipboard/search?q={urllib.parse.quote(query)}&limit=10")
        items = result.get("items", []) if result else []
        if not items:
            log.info("Clipboard search returned no matches")
            return

        # macOS-native quick chooser for search results.
        options = []
        mapping = {}
        for item_data in items:
            preview = (item_data.get("content") or "").replace("\n", " ").strip()
            if len(preview) > 80:
                preview = preview[:77] + "..."
            key = f"{item_data.get('timestamp', '')}  {preview}"
            options.append(key)
            mapping[key] = item_data.get("id")

        script = (
            "set theItems to {"
            + ", ".join([json.dumps(x) for x in options])
            + "}\n"
            + 'set chosen to choose from list theItems with prompt "Select clipboard item"\n'
            + 'if chosen is false then return ""\n'
            + "return item 1 of chosen\n"
        )
        try:
            selected = _run_osascript(script)
        except Exception as exc:
            log.warning(f"Clipboard chooser failed: {exc}")
            return

        item_id = mapping.get(selected)
        if item_id:
            api_post_json(f"/api/snacks/clipboard/{item_id}/paste", {})

    def captureClipboard_(self, _sender):
        """Capture current macOS clipboard into Snackbar clipboard buffer."""
        result = api_post_json("/api/snacks/clipboard/capture", {"source": "user_copy"})
        if result and not result.get("error"):
            log.info("Captured clipboard item")
        else:
            log.warning(f"Clipboard capture failed: {result}")
        self._refresh()

    def pasteClipboardItem_(self, sender):
        """Copy selected clipboard item back to system clipboard for paste."""
        item_id = sender.representedObject()
        if not item_id:
            return
        result = api_post_json(f"/api/snacks/clipboard/{item_id}/paste", {})
        if result and result.get("status") == "ok":
            log.info(f"Clipboard item {item_id} copied to clipboard")
        else:
            log.warning(f"Failed to paste clipboard item {item_id}: {result}")

    def pasteSelectedClipboardItem_(self, sender):
        """Paste the currently selected clipboard panel item without closing the panel."""
        item = self._selected_clipboard_item()
        if not item:
            return
        result = api_post_json(f"/api/snacks/clipboard/{item.get('id')}/paste", {})
        if result and result.get("status") == "ok":
            log.info(f"Clipboard item {item.get('id')} copied to clipboard")
        else:
            log.warning(f"Failed to paste selected clipboard item: {result}")

    def pinSelectedClipboardItem_(self, sender):
        """Toggle pin state for the selected clipboard panel item."""
        item = self._selected_clipboard_item()
        if not item:
            return
        desired = not bool(item.get("pinned"))
        result = api_post_json(
            f"/api/snacks/clipboard/{item.get('id')}/pin",
            {"pinned": desired},
        )
        if result and result.get("status") == "ok":
            log.info(f"Clipboard item {item.get('id')} pin set to {desired}")
            self._refresh()

    def deleteSelectedClipboardItem_(self, sender):
        """Delete the selected clipboard panel item."""
        item = self._selected_clipboard_item()
        if not item:
            return
        result = api_post_json(f"/api/snacks/clipboard/{item.get('id')}/delete", {})
        if result and result.get("status") in ("ok", "deleted"):
            log.info(f"Deleted clipboard item {item.get('id')}")
            self._refresh()

    def clearClipboardHistory_(self, _sender):
        """Clear non-pinned clipboard history."""
        result = api_post_json("/api/snacks/clipboard/clear", {"include_pinned": False})
        if result and result.get("status") == "ok":
            log.info(f"Cleared clipboard history: {result.get('cleared', 0)}")
        self._refresh()

    def clearClipboardAll_(self, _sender):
        """Clear all clipboard entries including saved items."""
        result = api_post_json("/api/snacks/clipboard/clear", {"include_pinned": True})
        if result and result.get("status") == "ok":
            log.info(f"Cleared clipboard all: {result.get('cleared', 0)}")
        self._refresh()

    def _ensure_clipboard_panel(self):
        """Create the floating clipboard panel if not exists."""
        if self._clipboard_panel is not None:
            return

        from AppKit import (
            NSFloatingWindowLevel,
        )

        style_mask = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskUtilityWindow
        )
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0.0, 0.0), (440.0, 360.0)),
            style_mask,
            NSBackingStoreBuffered,
            False,
        )
        panel.setTitle_("Clipboard Buffer")
        panel.setFloatingPanel_(True)
        panel.setLevel_(NSFloatingWindowLevel)
        panel.setReleasedWhenClosed_(False)

        content_view = panel.contentView()

        search_field = NSTextField.alloc().initWithFrame_(((16.0, 324.0), (250.0, 24.0)))
        search_field.setPlaceholderString_("Search clipboard...")
        search_field.setDelegate_(self)
        content_view.addSubview_(search_field)
        self._clipboard_search_field = search_field

        refresh_button = NSButton.alloc().initWithFrame_(((278.0, 322.0), (68.0, 28.0)))
        refresh_button.setTitle_("Refresh")
        refresh_button.setTarget_(self)
        refresh_button.setAction_("refreshClipboardPopover:")
        content_view.addSubview_(refresh_button)

        capture_button = NSButton.alloc().initWithFrame_(((352.0, 322.0), (72.0), (28.0)))
        capture_button.setTitle_("Capture")
        capture_button.setTarget_(self)
        capture_button.setAction_("captureClipboard:")
        content_view.addSubview_(capture_button)

        scroll_view = NSScrollView.alloc().initWithFrame_(((16.0, 68.0), (408.0, 244.0)))
        scroll_view.setHasVerticalScroller_(True)

        table_view = NSTableView.alloc().initWithFrame_(((0.0, 0.0), (408.0, 244.0)))
        column = NSTableColumn.alloc().initWithIdentifier_("content")
        column.setTitle_("Clipboard")
        column.setWidth_(396.0)
        table_view.addTableColumn_(column)
        table_view.setHeaderView_(None)
        table_view.setDataSource_(self)
        table_view.setDelegate_(self)
        table_view.setTarget_(self)
        table_view.setDoubleAction_("pasteSelectedClipboardItem:")
        scroll_view.setDocumentView_(table_view)
        content_view.addSubview_(scroll_view)
        self._clipboard_table = table_view

        paste_button = NSButton.alloc().initWithFrame_(((16.0, 18.0), (74.0, 30.0)))
        paste_button.setTitle_("Paste")
        paste_button.setTarget_(self)
        paste_button.setAction_("pasteSelectedClipboardItem:")
        content_view.addSubview_(paste_button)

        pin_button = NSButton.alloc().initWithFrame_(((96.0, 18.0), (74.0, 30.0)))
        pin_button.setTitle_("Pin")
        pin_button.setTarget_(self)
        pin_button.setAction_("pinSelectedClipboardItem:")
        content_view.addSubview_(pin_button)

        delete_button = NSButton.alloc().initWithFrame_(((176.0, 18.0), (74.0, 30.0)))
        delete_button.setTitle_("Delete")
        delete_button.setTarget_(self)
        delete_button.setAction_("deleteSelectedClipboardItem:")
        content_view.addSubview_(delete_button)

        close_button = NSButton.alloc().initWithFrame_(((350.0, 18.0), (74.0, 30.0)))
        close_button.setTitle_("Close")
        close_button.setTarget_(self)
        close_button.setAction_("hideClipboardPopover:")
        content_view.addSubview_(close_button)

        self._clipboard_panel = panel
        self._refresh_clipboard_panel_content()

    def _position_clipboard_panel(self):
        """Position panel near status item."""
        if self._clipboard_panel is None:
            return
        try:
            button = self._status_item.button()
            window = button.window() if button is not None else None
            frame = window.frame() if window is not None else None
            panel_frame = self._clipboard_panel.frame()
            if frame is not None:
                x = frame.origin.x + frame.size.width - panel_frame.size.width
                y = frame.origin.y - 8
                self._clipboard_panel.setFrameTopLeftPoint_((x, y))
                return
        except Exception:
            pass
        self._clipboard_panel.center()

    def _refresh_clipboard_panel_content(self):
        """Refresh clipboard items inside the floating panel."""
        if self._clipboard_panel is None or self._clipboard_table is None:
            return
        query = ""
        if self._clipboard_search_field is not None:
            query = self._clipboard_search_field.stringValue().strip()
        self._load_clipboard_panel_items(query)
        self._clipboard_table.reloadData()
        if self._clipboard_panel_items:
            from Foundation import NSIndexSet
            self._clipboard_table.selectRowIndexes_byExtendingSelection_(
                NSIndexSet.indexSetWithIndex_(0), False,
            )

    def _load_clipboard_panel_items(self, query: str = ""):
        """Load clipboard items for panel display."""
        if query:
            result = api_get(f"/api/snacks/clipboard/search?q={urllib.parse.quote(query)}&limit=100")
            self._clipboard_panel_items = result.get("items", []) if result else []
        else:
            result = api_get("/api/snacks/clipboard?limit=100")
            self._clipboard_panel_items = result.get("items", []) if result else []

    def _selected_clipboard_item(self):
        """Get the currently selected clipboard item."""
        if self._clipboard_table is None:
            return None
        row = self._clipboard_table.selectedRow()
        if row < 0 or row >= len(self._clipboard_panel_items):
            return None
        return self._clipboard_panel_items[row]

    def numberOfRowsInTableView_(self, table_view):
        """NSTableView dataSource method."""
        return len(self._clipboard_panel_items)

    def tableView_objectValueForTableColumn_row_(self, table_view, table_column, row):
        """NSTableView dataSource method."""
        if row < 0 or row >= len(self._clipboard_panel_items):
            return ""
        item = self._clipboard_panel_items[row]
        preview = (item.get("content") or "").replace("\n", " ").strip()
        if len(preview) > 88:
            preview = preview[:85] + "..."
        prefix = "📌" if item.get("pinned") else "📄"
        source = item.get("source") or "clipboard"
        return f"{prefix} [{source}] {preview or '(empty)'}"

    def controlTextDidChange_(self, notification):
        """NSTextField delegate method for search field."""
        if self._clipboard_search_field is None:
            return
        if notification.object() == self._clipboard_search_field:
            self._refresh_clipboard_panel_content()


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    acquire_lock()
    log.info("Starting uCore Menu v1.0 — Unified Menu Bar App")

    # Auto-start backend if not running
    if not is_ucore_alive():
        log.info("Backend not running, attempting auto-start...")
        ensure_backend_running()

    app = NSApplication.sharedApplication()

    # Hide from Dock — this is a menu bar app only
    app.setActivationPolicy_(1)  # NSApplicationActivationPolicyAccessory

    # Set the process name
    from Foundation import NSProcessInfo
    NSProcessInfo.processInfo().setProcessName_("uCore Menu")

    delegate = UnifiedMenuDelegate.alloc().init()
    delegate.setupStatusBar()

    # Handle signals for graceful shutdown
    def signal_handler(signum, frame):
        log.info(f"Received signal {signum}, shutting down...")
        release_lock()
        NSApp().terminate_(None)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Run the app
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
