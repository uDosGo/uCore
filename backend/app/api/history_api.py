"""History API — snapshot, undo, and action log endpoints.

GET  /api/history/actions?lane=&limit=50  — list recent actions
POST /api/history/snapshot               — create a git snapshot
POST /api/history/undo                   — undo the last reversible action
POST /api/history/restore/{action_id}    — restore a previous snapshot
GET  /api/history/stats?lane=            — history statistics
"""
from __future__ import annotations

import logging

from aiohttp import web

from app.services.history_service import get_history

log = logging.getLogger("ucore.api.history")


async def handle_list_actions(request: web.Request) -> web.Response:
    """GET /api/history/actions"""
    lane = request.query.get("lane")
    raw_limit = request.query.get("limit", "50")
    try:
        limit = int(raw_limit)
    except ValueError:
        limit = 50
    try:
        history = get_history()
        actions = history.list_actions(limit=limit, lane=lane or None)
        return web.json_response({"actions": actions, "count": len(actions)})
    except Exception as exc:
        log.error("List actions failed: %s", exc)
        return web.json_response({"error": str(exc)}, status=500)


async def handle_create_snapshot(request: web.Request) -> web.Response:
    """POST /api/history/snapshot"""
    try:
        body = await request.json()
    except Exception:
        body = {}
    label = body.get("label", body.get("description", "Manual snapshot"))
    lane = body.get("lane", "ecosystem")
    try:
        history = get_history()
        result = history.create_snapshot(label, lane=lane)
        return web.json_response(result)
    except Exception as exc:
        log.error("Snapshot failed: %s", exc)
        return web.json_response({"error": str(exc)}, status=500)


async def handle_undo_last(request: web.Request) -> web.Response:
    """POST /api/history/undo"""
    try:
        body = await request.json()
    except Exception:
        body = {}
    lane = body.get("lane", "ecosystem")
    try:
        history = get_history()
        result = history.undo_last(lane=lane)
        return web.json_response(result)
    except Exception as exc:
        log.error("Undo failed: %s", exc)
        return web.json_response({"error": str(exc)}, status=500)


async def handle_restore_snapshot(request: web.Request) -> web.Response:
    """POST /api/history/restore/{action_id}"""
    raw_id = request.match_info.get("action_id", "0")
    try:
        action_id = int(raw_id)
    except ValueError:
        return web.json_response(
            {"error": "action_id must be an integer"}, status=400,
        )
    try:
        history = get_history()
        result = history.restore_snapshot(action_id)
        return web.json_response(result)
    except Exception as exc:
        log.error("Restore failed: %s", exc)
        return web.json_response({"error": str(exc)}, status=500)


async def handle_history_stats(request: web.Request) -> web.Response:
    """GET /api/history/stats"""
    lane = request.query.get("lane")
    try:
        history = get_history()
        stats = history.get_stats(lane=lane or None)
        return web.json_response(stats)
    except Exception as exc:
        log.error("Stats failed: %s", exc)
        return web.json_response({"error": str(exc)}, status=500)


def register_history_routes(app: web.Application) -> None:
    """Register history API routes."""
    app.router.add_get("/api/history/actions", handle_list_actions)
    app.router.add_get("/api/history/stats", handle_history_stats)
    app.router.add_post("/api/history/snapshot", handle_create_snapshot)
    app.router.add_post("/api/history/undo", handle_undo_last)
    app.router.add_post(
        "/api/history/restore/{action_id}", handle_restore_snapshot,
    )
    log.info("History API routes registered")