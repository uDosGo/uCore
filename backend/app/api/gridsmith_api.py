"""GridSmith API — expose the live uCode GridSmith scaffold via uCore."""
from __future__ import annotations

from aiohttp import web

from app.services.gridsmith_bridge import get_gridsmith_bridge


async def handle_gridsmith_status(request: web.Request) -> web.Response:
    bridge = get_gridsmith_bridge()
    return web.json_response(bridge.status())


async def handle_gridsmith_tools(request: web.Request) -> web.Response:
    bridge = get_gridsmith_bridge()
    return web.json_response(await bridge.run("tools", "list"))


async def handle_gridsmith_grid_create(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}

    cols = int(body.get("cols", 80))
    rows = int(body.get("rows", 24))
    bridge = get_gridsmith_bridge()
    return web.json_response(
        await bridge.run("grid", "create", "--cols", str(cols), "--rows", str(rows)),
    )


async def handle_gridsmith_latlon_to_ucode(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}

    lat = body.get("lat")
    lon = body.get("lon")
    if lat is None or lon is None:
        return web.json_response({"error": "lat and lon are required"}, status=400)

    level = int(body.get("level", 340))
    bridge = get_gridsmith_bridge()
    return web.json_response(
        await bridge.run(
            "location",
            "latlon-to-ucode",
            "--lat",
            str(lat),
            "--lon",
            str(lon),
            "--level",
            str(level),
        ),
    )


async def handle_gridsmith_ucode_to_latlon(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}

    coord = str(body.get("coord", "")).strip()
    if not coord:
        return web.json_response({"error": "coord is required"}, status=400)

    bridge = get_gridsmith_bridge()
    return web.json_response(
        await bridge.run("location", "ucode-to-latlon", "--coord", coord),
    )


async def handle_gridsmith_import_basic(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}

    program = str(body.get("program", "")).strip()
    world_name = str(body.get("world_name", "Imported BASIC World")).strip()
    if not program:
        return web.json_response({"error": "program is required"}, status=400)

    bridge = get_gridsmith_bridge()
    return web.json_response(
        await bridge.run(
            "world",
            "import-basic",
            "--program",
            program,
            "--world-name",
            world_name,
        ),
    )
