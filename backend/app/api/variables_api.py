"""
Variables API — user, installation, and system variable store.
Extends /api/config with editable user variables and installation metadata.

Endpoints:
  GET  /api/variables          — all variables (user + installation)
  GET  /api/variables/user     — user variables only
  PUT  /api/variables/user     — update user variables
  GET  /api/variables/install  — installation variables (read-only)
"""
from __future__ import annotations

import json
import os
import platform
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web

# ─── Variable Store Path ─────────────────────────────────────────────
_VARIABLE_STORE_DIR = Path(
    os.environ.get(
        "UCORE_DATA_DIR",
        os.path.expanduser("~/.ucore/data"),
    )
)
_VARIABLE_STORE_FILE = _VARIABLE_STORE_DIR / "variables.json"
_INSTALL_META_FILE = _VARIABLE_STORE_DIR / "install_meta.json"


def _ensure_store() -> None:
    """Ensure the data directory and default variable store exist."""
    _VARIABLE_STORE_DIR.mkdir(parents=True, exist_ok=True)
    if not _VARIABLE_STORE_FILE.exists():
        default_vars = {
            "username": os.environ.get("USER", "user"),
            "role": "developer",
            "location": "unknown",
            "timezone": str(
                datetime.now(timezone.utc).astimezone().tzinfo
            ) or "UTC",
            "uid": str(uuid.uuid4()),
        }
        _VARIABLE_STORE_FILE.write_text(json.dumps(default_vars, indent=2))

    # Installation meta — written once on first start
    if not _INSTALL_META_FILE.exists():
        install_meta = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "install_date": datetime.now(timezone.utc).isoformat(),
            "udos_root": str(
                Path(
                    os.environ.get(
                        "UDOS_ROOT",
                        os.path.expanduser("~/Code"),
                    )
                ).resolve()
            ),
        }
        _INSTALL_META_FILE.write_text(json.dumps(install_meta, indent=2))


def _load_variables() -> dict:
    """Load user variables from store."""
    _ensure_store()
    try:
        return json.loads(_VARIABLE_STORE_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_variables(vars: dict) -> None:
    """Save user variables to store."""
    _ensure_store()
    _VARIABLE_STORE_FILE.write_text(json.dumps(vars, indent=2))


def _load_install_meta() -> dict:
    """Load installation metadata (read-only)."""
    _ensure_store()
    try:
        return json.loads(_INSTALL_META_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


# ─── Handlers ────────────────────────────────────────────────────────

async def handle_get_variables(request: web.Request) -> web.Response:
    """GET /api/variables — return all variables (user + install)."""
    user_vars = _load_variables()
    install_vars = _load_install_meta()
    return web.json_response({
        "user": user_vars,
        "installation": install_vars,
    })


async def handle_get_user_variables(request: web.Request) -> web.Response:
    """GET /api/variables/user — return user variables."""
    return web.json_response(_load_variables())


async def handle_update_user_variables(request: web.Request) -> web.Response:
    """PUT /api/variables/user — update user variables (merge)."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    if not isinstance(body, dict):
        return web.json_response({"error": "Body must be a JSON object"}, status=400)

    current = _load_variables()
    # Only allow known user variable keys
    allowed_keys = {
        "username", "role", "location",
        "timezone", "uid", "email",
    }
    for key, value in body.items():
        if key in allowed_keys:
            current[key] = str(value)

    _save_variables(current)
    return web.json_response({"status": "ok", "variables": current})


async def handle_get_install_variables(
    request: web.Request,
) -> web.Response:
    """GET /api/variables/install — return installation (read-only)."""
    return web.json_response(_load_install_meta())


# ─── Route Registration ─────────────────────────────────────────────

def register_variable_routes(app: web.Application) -> None:
    """Register variable API routes."""
    app.router.add_get("/api/variables", handle_get_variables)
    app.router.add_get("/api/variables/user", handle_get_user_variables)
    app.router.add_put("/api/variables/user", handle_update_user_variables)
    app.router.add_get("/api/variables/install", handle_get_install_variables)