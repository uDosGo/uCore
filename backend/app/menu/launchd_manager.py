"""Launchd Manager — Single source of truth for macOS auto-start.

This module consolidates all launchd plist management to avoid duplication.
Used by: install_macos_menu.py, unified_menu_simple.py, popcorn_manager.py, system_snack.py
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

log = logging.getLogger("launchd-manager")

# ─── Config ──────────────────────────────────────────────────────────

UCORE_LABEL = "com.udos.ucore-menu"
UCORE_PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{UCORE_LABEL}.plist")
UCORE_LOCKFILE = os.path.expanduser("~/.ucore/ucore-menu.pid")
UCORE_BACKEND_DIR = os.environ.get("UCORE_BACKEND_DIR", str(Path.home() / "Code" / "uCore" / "backend"))

# The canonical module to run - MUST be kept in sync across all callers
CANONICAL_MODULE = "app.menu.unified_menu_simple"


# ─── Plist Generation ────────────────────────────────────────────────

def get_plist_content() -> str:
    """Generate the launchd plist content. Single source of truth."""
    venv_python = Path(UCORE_BACKEND_DIR) / ".venv" / "bin" / "python"
    python_bin = str(venv_python) if venv_python.exists() else "/usr/bin/python3"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{UCORE_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_bin}</string>
    <string>-m</string>
    <string>{CANONICAL_MODULE}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{UCORE_BACKEND_DIR}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>LSUIElement</key>
  <true/>
  <key>LimitLoadToSessionType</key>
  <string>Aqua</string>
  <key>StandardOutPath</key>
  <string>{os.path.expanduser('~/.ucore/logs/ucore-menu-stdout.log')}</string>
  <key>StandardErrorPath</key>
  <string>{os.path.expanduser('~/.ucore/logs/ucore-menu-stderr.log')}</string>
  <key>TimeOut</key>
  <integer>60</integer>
  <key>EnvironmentVariables</key>
  <dict>
    <key>UCORE_DEBUG</key>
    <string>1</string>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
</dict>
</plist>
"""


# ─── Installation ────────────────────────────────────────────────────

def install() -> bool:
    """Install launchd plist for auto-start. Returns True on success."""
    try:
        uid = os.getuid()
        log.info("Installing uCore Menu launchd plist...")

        # Ensure directories exist
        os.makedirs(os.path.expanduser("~/.ucore/logs"), exist_ok=True)
        Path(UCORE_PLIST).parent.mkdir(parents=True, exist_ok=True)

        # Write plist
        Path(UCORE_PLIST).write_text(get_plist_content(), encoding="utf-8")
        log.info(f"Plist written to {UCORE_PLIST}")

        # Bootstrap into launchctl
        result = subprocess.run(
            ["launchctl", "bootstrap", f"gui/{uid}", UCORE_PLIST],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            log.info("uCore Menu installed and loaded")
            return True
        else:
            # May fail if already loaded, which is okay
            log.warning(f"launchctl bootstrap: {result.stderr.strip() or 'already loaded'}")
            return True

    except Exception as e:
        log.error(f"Failed to install launchd: {e}")
        return False


def uninstall() -> bool:
    """Uninstall launchd plist. Returns True on success."""
    try:
        log.info("Uninstalling uCore Menu launchd plist...")
        uid = os.getuid()

        # Bootout from launchctl
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}/{UCORE_LABEL}"],
            capture_output=True, timeout=10
        )

        # Remove plist file
        if Path(UCORE_PLIST).exists():
            Path(UCORE_PLIST).unlink()
            log.info(f"Plist removed from {UCORE_PLIST}")

        # Clean lockfile
        if Path(UCORE_LOCKFILE).exists():
            Path(UCORE_LOCKFILE).unlink()
            log.info("Lockfile cleaned")

        log.info("Launchd uninstalled")
        return True

    except Exception as e:
        log.warning(f"Failed to uninstall launchd: {e}")
        return False


def is_installed() -> bool:
    """Check if launchd plist is installed."""
    return Path(UCORE_PLIST).exists()


def is_running() -> bool:
    """Check if the menu process is currently running via lockfile."""
    try:
        lockfile = Path(UCORE_LOCKFILE)
        if not lockfile.exists():
            return False
        pid = int(lockfile.read_text().strip())
        os.kill(pid, 0)  # Signal 0 = check if process exists
        return True
    except (ProcessLookupError, ValueError, OSError):
        return False


# ─── Frontend Launchd ────────────────────────────────────────────────

UCORE_FRONTEND_LABEL = "com.udos.ucore-frontend"
UCORE_FRONTEND_PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{UCORE_FRONTEND_LABEL}.plist")
UCORE_FRONTEND_DIR = os.environ.get("UCORE_FRONTEND_DIR", str(Path.home() / "Code" / "uCore" / "frontend"))


def get_frontend_plist_content() -> str:
    """Generate the frontend launchd plist content."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{UCORE_FRONTEND_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>pnpm --filter @udos/ui-hub-vue run dev --host 127.0.0.1 --port 5175</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{os.path.expanduser('~/Code/uCore')}</string>
  <key>RunAtLoad</key>

  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>{os.path.expanduser('~/.ucore/logs/ucore-frontend-stdout.log')}</string>
  <key>StandardErrorPath</key>
  <string>{os.path.expanduser('~/.ucore/logs/ucore-frontend-stderr.log')}</string>
  <key>TimeOut</key>
  <integer>60</integer>
  <key>EnvironmentVariables</key>
  <dict>
    <key>UCORE_DEBUG</key>
    <string>1</string>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
</dict>
</plist>
"""


def install_frontend() -> bool:
    """Install frontend launchd plist for auto-start. Returns True on success."""
    try:
        uid = os.getuid()
        log.info("Installing uCore Frontend launchd plist...")

        os.makedirs(os.path.expanduser("~/.ucore/logs"), exist_ok=True)
        Path(UCORE_FRONTEND_PLIST).parent.mkdir(parents=True, exist_ok=True)

        Path(UCORE_FRONTEND_PLIST).write_text(get_frontend_plist_content(), encoding="utf-8")
        log.info(f"Plist written to {UCORE_FRONTEND_PLIST}")

        result = subprocess.run(
            ["launchctl", "bootstrap", f"gui/{uid}", UCORE_FRONTEND_PLIST],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            log.info("uCore Frontend installed and loaded")
            return True
        else:
            log.warning(f"launchctl bootstrap: {result.stderr.strip() or 'already loaded'}")
            return True

    except Exception as e:
        log.error(f"Failed to install frontend launchd: {e}")
        return False


def uninstall_frontend() -> bool:
    """Uninstall frontend launchd plist. Returns True on success."""
    try:
        log.info("Uninstalling uCore Frontend launchd plist...")
        uid = os.getuid()

        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}/{UCORE_FRONTEND_LABEL}"],
            capture_output=True, timeout=10
        )

        if Path(UCORE_FRONTEND_PLIST).exists():
            Path(UCORE_FRONTEND_PLIST).unlink()
            log.info(f"Plist removed from {UCORE_FRONTEND_PLIST}")

        log.info("Frontend launchd uninstalled")
        return True

    except Exception as e:
        log.warning(f"Failed to uninstall frontend launchd: {e}")
        return False


def is_frontend_installed() -> bool:
    """Check if frontend launchd plist is installed."""
    return Path(UCORE_FRONTEND_PLIST).exists()


def is_frontend_running() -> bool:
    """Check if frontend is running on port 5175."""
    import socket
    try:
        with socket.create_connection(("127.0.0.1", 5175), timeout=0.4):
            return True
    except OSError:
        return False


def get_status() -> dict:
    """Get full status of launchd integration."""
    return {
        "installed": is_installed(),
        "running": is_running(),
        "plist_path": UCORE_PLIST,
        "module": CANONICAL_MODULE,
        "frontend_installed": is_frontend_installed(),
        "frontend_running": is_frontend_running(),
    }