"""API routes for Snack queue and delivery."""
from __future__ import annotations

from aiohttp import web
from app.models.snack import SnackType, SnackPriority
from app.services.snackbar_orchestrator import SnackbarOrchestrator
from app.menu.system_snacks import (
    list_system_snacks,
    read_system_badges,
    run_system_snack,
)

# Shared service instance
_orch = SnackbarOrchestrator()


def register_snack_routes(app: web.Application) -> None:
    app.router.add_get("/api/snacks", list_queue)
    app.router.add_post("/api/snacks", queue_snack)
    app.router.add_get("/api/snacks/history", get_history)
    app.router.add_post("/api/snacks/{snack_id}/deliver", deliver_snack)
    app.router.add_post("/api/snacks/{snack_id}/fail", fail_snack)
    app.router.add_post("/api/snacks/{snack_id}/retry", retry_snack)
    app.router.add_delete("/api/snacks/queue", clear_queue)
    app.router.add_get("/api/snacks/system", list_system)
    app.router.add_get("/api/snacks/system/badges", list_system_badges)
    app.router.add_post("/api/snacks/system/{snack_id}/run", run_system)


async def list_queue(request: web.Request) -> web.Response:
    """GET /api/snacks — list pending snacks in priority order"""
    queue = _orch.get_queue()
    return web.json_response({
        "snacks": [s.model_dump(mode="json") for s in queue],
        "pending": len(queue),
    })


async def queue_snack(request: web.Request) -> web.Response:
    """POST /api/snacks — add a snack to the queue"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    type_str = data.get("type", "message")
    priority_str = data.get("priority", "normal")

    try:
        st = SnackType(type_str)
    except ValueError:
        return web.json_response({"error": f"Invalid type: {type_str}"}, status=400)

    try:
        pr = SnackPriority[priority_str.upper()]
    except KeyError:
        return web.json_response({"error": f"Invalid priority: {priority_str}"}, status=400)

    snack = _orch.queue_snack(
        type=st,
        content=data.get("content", {}),
        priority=pr,
        source=data.get("source", "api"),
        target=data.get("target"),
        timeout_seconds=data.get("timeout_seconds"),
    )
    return web.json_response(snack.model_dump(mode="json"), status=201)


async def get_history(request: web.Request) -> web.Response:
    """GET /api/snacks/history — list delivered/failed snacks"""
    limit = request.query.get("limit")
    try:
        limit = int(limit) if limit else None
    except ValueError:
        limit = None
    history = _orch.get_history(limit=limit)
    return web.json_response({
        "snacks": [s.model_dump(mode="json") for s in history],
        "count": len(history),
    })


async def deliver_snack(request: web.Request) -> web.Response:
    """POST /api/snacks/{snack_id}/deliver"""
    snack_id = request.match_info.get("snack_id")
    snack = _orch.deliver_snack(snack_id)
    if snack is None:
        return web.json_response({"error": "Snack not found"}, status=404)
    return web.json_response(snack.model_dump(mode="json"))


async def fail_snack(request: web.Request) -> web.Response:
    """POST /api/snacks/{snack_id}/fail"""
    snack_id = request.match_info.get("snack_id")
    snack = _orch.fail_snack(snack_id)
    if snack is None:
        return web.json_response({"error": "Snack not found"}, status=404)
    return web.json_response(snack.model_dump(mode="json"))


async def retry_snack(request: web.Request) -> web.Response:
    """POST /api/snacks/{snack_id}/retry"""
    snack_id = request.match_info.get("snack_id")
    snack = _orch.retry_snack(snack_id)
    if snack is None:
        return web.json_response({"error": "Snack not found or max retries reached"}, status=404)
    return web.json_response(snack.model_dump(mode="json"))


async def clear_queue(request: web.Request) -> web.Response:
    """DELETE /api/snacks/queue — clear all pending"""
    cleared = _orch.clear_queue()
    return web.json_response({"status": "cleared", "count": cleared})


async def list_system(request: web.Request) -> web.Response:
    """GET /api/snacks/system — list built-in macOS system snacks."""
    snacks = list_system_snacks()
    return web.json_response({"snacks": snacks, "count": len(snacks)})


async def list_system_badges(request: web.Request) -> web.Response:
    """GET /api/snacks/system/badges — fetch live badge values."""
    badges = read_system_badges()
    return web.json_response({"badges": badges, "count": len(badges)})


async def run_system(request: web.Request) -> web.Response:
    """POST /api/snacks/system/{snack_id}/run — execute a built-in system snack.

    Body (optional):
      {
        "action": "summarise|rewrite-professional|compose|format|to-html|validate",
        "text": "optional input"
      }
    """
    snack_id = request.match_info.get("snack_id", "")
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    result = run_system_snack(
        snack_id,
        action=body.get("action"),
        text=body.get("text"),
    )
    status = 200 if result.get("status") == "success" else 400
    return web.json_response(result, status=status)
