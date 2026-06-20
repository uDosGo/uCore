"""GET /api/docker/ps — list Docker containers.

Used by InstallPanel in the frontend to show running containers.
"""
from __future__ import annotations

import asyncio
import json
import logging
from aiohttp import web

log = logging.getLogger("ucore.docker")


async def handle_docker_ps(request: web.Request) -> web.Response:
    """GET /api/docker/ps — list running containers.

    Returns: { "containers": [...], "count": N }
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "ps", "--format", "{{json .}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=10
        )

        if proc.returncode != 0:
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
            return web.json_response({
                "containers": [],
                "count": 0,
                "error": stderr_str.strip(),
            })

        output = stdout.decode("utf-8", errors="replace")
        containers = []
        for line in output.strip().split("\n"):
            if line.strip():
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        return web.json_response({
            "containers": containers,
            "count": len(containers),
        })
    except asyncio.TimeoutError:
        return web.json_response({
            "containers": [],
            "count": 0,
            "error": "Docker command timed out",
        })
    except FileNotFoundError:
        return web.json_response({
            "containers": [],
            "count": 0,
            "error": "Docker not installed",
        })
    except Exception as e:
        log.error("Docker ps error: %s", e)
        return web.json_response({
            "containers": [],
            "count": 0,
            "error": str(e),
        })
