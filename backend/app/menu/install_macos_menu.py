#!/usr/bin/env python3
"""Install/uninstall launchd agent for uCore macOS tray menu."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from app.core.settings import settings

LABEL = "com.udos.ucore-menu"
PLIST_PATH = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
PROJECT_DIR = settings.udos_root / "uCore/backend"
MENU_SCRIPT = PROJECT_DIR / "app/menu/snackbar_menu.py"
LOG_DIR = Path.home() / ".ucore/logs"


def plist_text() -> str:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>{MENU_SCRIPT}</string>
  </array>
  <key>WorkingDirectory</key><string>{PROJECT_DIR}</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><false/>
  <key>StandardOutPath</key><string>{LOG_DIR / 'ucore-menu.log'}</string>
  <key>StandardErrorPath</key><string>{LOG_DIR / 'ucore-menu.err.log'}</string>
</dict></plist>
"""


def install() -> int:
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(plist_text(), encoding="utf-8")

    uid = os.getuid()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}/{LABEL}"], capture_output=True)
    result = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(PLIST_PATH)], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr.strip())
        return result.returncode

    print(f"Installed {LABEL} at {PLIST_PATH}")
    return 0


def uninstall() -> int:
    uid = os.getuid()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}/{LABEL}"], capture_output=True)
    if PLIST_PATH.exists():
        PLIST_PATH.unlink()
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
