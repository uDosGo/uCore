"""server — unified uCore snackbar entry point"""
from __future__ import annotations

"""
Snackbar Server — v4.0 (uCore unified daemon)
===============================================
Unified daemon for uDos surface lifecycle, scheduled snacks, container management,
UDO installation, cross-platform operation, SVG processing, vault sync, and MCP bridge.

Features:
  - Surface lifecycle management (start/stop/restart/repair/debug)
  - Scheduled snack execution (cron-like periodic tasks)
  - Container management (Docker lifecycle via API)
  - UDO package management (install, list, update)
  - Cross-platform awareness (mac/linux/vm device detection)
  - Snack/skill execution with timeout and logging
  - SVG processing (convert, generate, describe)
  - Vault sync bridge
  - MCP protocol gateway
  - CORS-enabled HTTP API for Popcorn and UI Hub

Depends on: aiohttp, PyYAML (optional)

Usage:
    python3 server.py --port 8484
    python3 server.py --port 8484 --auto-start
    python3 server.py --install
    python3 server.py --uninstall
"""

import os
import sys
import json
import time
import signal
import shutil
import uuid
import asyncio
import subprocess
import logging
import platform
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

# ─── Provider Router ──────────────────────────────────────────────
from provider_router import ProviderRouter, get_router
from svg_bridge import convert_svg, generate_svg, describe_svg

try:
    import yaml
except ImportError:
    yaml = None

try:
    from aiohttp import web
except ImportError:
    print("aiohttp required: pip install aiohttp")
    sys.exit(1)

# ─── Submodule imports (split by file-splitter) ───────────────────

from server_identity import *  # identity
from server_surfaces import *  # surfaces
from server_other import *  # other
from server_snacks import *  # snacks
from server_skills import *  # skills
from server_scheduler import *  # scheduler
from server_containers import *  # containers
from server_udos import *  # udos
from server_ceefax import *  # ceefax
from server_pages import *  # pages
from server_maintenance import *  # maintenance
from server_health import *  # health
from server_chat import *  # chat
from server_bbcsdl import *  # bbcsdl
from server_events import *  # events
from server_dashboard import *  # dashboard
from server_peers import *  # peers
from server_ingest import *  # ingest
from server_vibe import *  # vibe
from server_map import *  # map
from server_approval import *  # approval
from server_mission_control import *  # mission_control
from server_developer import *  # devstudio
from server_vault import *  # vault
from server_process import *  # process
from server_bridge import *  # bridge
from server_mcp import *  # mcp
from server_svg import *  # svg
