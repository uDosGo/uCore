#!/usr/bin/env python3
"""uDos Snackbar Menu — DEPRECATED.

This file has been merged into the unified menu bar app.
Use: backend/app/menu/unified_menu_simple.py instead.
"""
import subprocess
import sys
from pathlib import Path

UNIFIED_MENU = Path(__file__).resolve().parent / "unified_menu_simple.py"

if __name__ == "__main__":
    print("snackbar_menu.py is deprecated. Use unified_menu_simple.py instead.")
    sys.exit(subprocess.run([sys.executable, str(UNIFIED_MENU)]).returncode)