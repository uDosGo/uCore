"""MCP handlers: Autostart domain (health check)."""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.mcp_handlers.autostart")


async def handle_autostart_health_check(arguments: dict, request_id: Any) -> web.Response:
    """Handle autostart_health_check tool."""
    from app.skills.builtin.skill_autostart import run_health_check

    result = run_health_check()
    return web.json_response({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
        },
        "id": request_id,
    })
