#!/usr/bin/env python3
"""Install/uninstall launchd agent for uCore macOS tray menu.

This is a thin wrapper around launchd_manager.py - the single source of truth.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from app.menu.launchd_manager import UCORE_PLIST
from app.menu.launchd_manager import install as launchd_install
from app.menu.launchd_manager import uninstall as launchd_uninstall

LABEL = "com.udos.ucore-menu"


def install() -> int:
    """Install menu launchd plist using the canonical launchd_manager."""
    launchd_install()

    # Also bootstrap server plist if it exists
    server_plist = Path.home() / "Library/LaunchAgents/com.udos.ucore-server.plist"
    if server_plist.exists():
        uid = os.getuid()
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}/com.udos.ucore-server"],
            capture_output=True,
        )
        subprocess.run(
            ["launchctl", "bootstrap", f"gui/{uid}", str(server_plist)],
            capture_output=True, text=True,
        )

    print(f"Installed {LABEL} at {UCORE_PLIST}")
    return 0


def uninstall() -> int:
    """Uninstall menu launchd plist using the canonical launchd_manager."""
    launchd_uninstall()

    # Also uninstall server plist
    server_plist = Path.home() / "Library/LaunchAgents/com.udos.ucore-server.plist"
    if server_plist.exists():
        uid = os.getuid()
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}/com.udos.ucore-server"],
            capture_output=True,
        )
        server_plist.unlink()

    print(f"Removed {LABEL}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()

    if args.uninstall:
        return uninstall()
    return install()


if __name__ == "__main__":
    raise SystemExit(main())
