"""Feed API — REST endpoints for the Feed System (Pod/Nugget/Seed/Slate/Spool).

GET  /api/feed/query     — query activities by source, timeframe, importance
POST /api/feed/ingest    — ingest a user activity event
GET  /api/feed/suggest   — generate binder suggestions from feed activity
POST /api/feed/link      — link a .tasker task to a feed activity
"""
from __future__ import annotations

import logging

from aiohttp import web

log = logging.getLogger("ucore.api.feed")

# Lazy singleton
_feed_server = None


def _get_feed_server():
    global _feed_server
    if _feed_server is None:
        from app.mcp.feed.feed_server import FeedServer
        _feed_server = FeedServer()
    return _feed_server


async def handle_feed_ingest(request: web.Request) -> web.Response:
    """POST /api/feed/ingest — ingest an activity event."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON body"}, status=400,
        )

    source = body.get("source", "")
    activity_type = body.get("type", "")
    if not source or not activity_type:
        return web.json_response(
            {"error": "source and type are required"}, status=400,
        )

    server = _get_feed_server()
    result = await server.ingest_activity(
        source=source,
        type=activity_type,
        title=body.get("title", ""),
        content=body.get("content", ""),
        url=body.get("url", ""),
        contact_name=body.get("contact_name", ""),
        importance=float(body.get("importance", 0.5)),
        metadata=body.get("metadata"),
    )

    # Bridge to Spool
    try:
        from app.services.feed_consumer import FeedConsumer
        consumer = FeedConsumer()
        consumer.consume_activity(body)
    except ImportError:
        log.debug("FeedConsumer not available, skipping spool bridge")

    return web.json_response(result)


async def handle_feed_query(request: web.Request) -> web.Response:
    """GET /api/feed/query — query activities."""
    source = request.query.get("source")
    since = request.query.get("since")
    limit = int(request.query.get("limit", "50"))
    importance_min = float(request.query.get("importance_min", "0"))

    server = _get_feed_server()
    activities = await server.query_feed(
        source=source,
        since=since,
        limit=limit,
        importance_min=importance_min,
    )
    return web.json_response({"activities": activities, "count": len(activities)})


async def handle_feed_suggest(request: web.Request) -> web.Response:
    """GET /api/feed/suggest — generate binder suggestions."""
    min_confidence = float(request.query.get("min_confidence", "0.5"))

    server = _get_feed_server()
    suggestions = await server.suggest_binders(
        min_confidence=min_confidence,
    )
    return web.json_response(
        {"suggestions": suggestions, "count": len(suggestions)},
    )


async def handle_feed_link(request: web.Request) -> web.Response:
    """POST /api/feed/link — link a task to an activity."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON body"}, status=400,
        )

    task_id = body.get("task_id", "")
    activity_id = body.get("activity_id")
    if not task_id or activity_id is None:
        return web.json_response(
            {"error": "task_id and activity_id are required"}, status=400,
        )

    server = _get_feed_server()
    result = await server.link_task_to_activity(
        task_id=task_id,
        activity_id=int(activity_id),
        link_type=body.get("link_type", "source"),
    )
    return web.json_response(result)


def register_feed_routes(app: web.Application) -> None:
    """Register Feed API routes."""
    app.router.add_post("/api/feed/ingest", handle_feed_ingest)
    app.router.add_get("/api/feed/query", handle_feed_query)
    app.router.add_get("/api/feed/suggest", handle_feed_suggest)
    app.router.add_post("/api/feed/link", handle_feed_link)
    log.info("Feed API routes registered: ingest, query, suggest, link")