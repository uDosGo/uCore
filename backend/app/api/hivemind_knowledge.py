"""Hivemind Knowledge Layer API — Shared memory for multi-agent orchestration.

Endpoints:
    GET  /api/hivemind/knowledge/status — Knowledge layer status
    POST /api/hivemind/knowledge/publish — Publish a knowledge event
    GET  /api/hivemind/knowledge/query — Query knowledge events
    GET  /api/hivemind/knowledge/search — Full-text search
    POST /api/hivemind/knowledge/subscribe — Subscribe an agent
    GET  /api/hivemind/knowledge/subscriptions — List subscriptions
    POST /api/hivemind/knowledge/lock — Acquire a lock
    POST /api/hivemind/knowledge/unlock — Release a lock
    POST /api/hivemind/knowledge/cleanup — Cleanup expired events
"""
from __future__ import annotations

import logging

from aiohttp import web

from app.services.knowledge_layer import KnowledgeLayer

log = logging.getLogger("ucore.api.hivemind_knowledge")


async def handle_status(request: web.Request) -> web.Response:
    """GET /api/hivemind/knowledge/status — Knowledge layer status."""
    kl = KnowledgeLayer()
    status = await kl.status()
    return web.json_response(status)


async def handle_publish(request: web.Request) -> web.Response:
    """POST /api/hivemind/knowledge/publish — Publish a knowledge event.

    Body:
        {
            "agent_id": "agent.coder",
            "event_type": "decision",
            "payload": { ... },
            "ttl_seconds": 86400
        }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    agent_id = body.get("agent_id", "")
    event_type = body.get("event_type", "")
    payload = body.get("payload", {})
    ttl = int(body.get("ttl_seconds", 86400))

    if not agent_id or not event_type:
        return web.json_response(
            {"error": "agent_id and event_type are required"},
            status=400,
        )

    kl = KnowledgeLayer()
    event_id = await kl.publish(agent_id, event_type, payload, ttl)
    return web.json_response({"event_id": event_id, "status": "published"})


async def handle_query(request: web.Request) -> web.Response:
    """GET /api/hivemind/knowledge/query — Query knowledge events.

    Query params:
        event_type: Filter by event type
        agent_id: Filter by agent ID
        limit: Max results (default: 50)
        offset: Pagination offset (default: 0)
    """
    kl = KnowledgeLayer()
    event_type = request.query.get("event_type")
    agent_id = request.query.get("agent_id")
    limit = int(request.query.get("limit", 50))
    offset = int(request.query.get("offset", 0))

    results = await kl.query(
        event_type=event_type,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )
    return web.json_response({
        "events": results,
        "count": len(results),
    })


async def handle_search(request: web.Request) -> web.Response:
    """GET /api/hivemind/knowledge/search — Full-text search.

    Query params:
        q: Search query
        limit: Max results (default: 20)
    """
    query = request.query.get("q", "")
    if not query:
        return web.json_response(
            {"error": "Query parameter 'q' is required"},
            status=400,
        )

    kl = KnowledgeLayer()
    limit = int(request.query.get("limit", 20))
    results = await kl.search(query, limit)
    return web.json_response({
        "events": results,
        "count": len(results),
    })


async def handle_subscribe(request: web.Request) -> web.Response:
    """POST /api/hivemind/knowledge/subscribe — Subscribe an agent.

    Body:
        {
            "agent_id": "agent.coder",
            "event_type": "decision"
        }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    agent_id = body.get("agent_id", "")
    event_type = body.get("event_type")

    if not agent_id:
        return web.json_response(
            {"error": "agent_id is required"},
            status=400,
        )

    kl = KnowledgeLayer()
    sub_id = await kl.subscribe(agent_id, event_type)
    return web.json_response({"subscription_id": sub_id})


async def handle_subscriptions(request: web.Request) -> web.Response:
    """GET /api/hivemind/knowledge/subscriptions — List subscriptions.

    Query params:
        agent_id: Optional filter by agent
    """
    kl = KnowledgeLayer()
    agent_id = request.query.get("agent_id")
    subs = await kl.get_subscriptions(agent_id)
    return web.json_response({
        "subscriptions": subs,
        "count": len(subs),
    })


async def handle_lock(request: web.Request) -> web.Response:
    """POST /api/hivemind/knowledge/lock — Acquire a lock.

    Body:
        {
            "resource_id": "resource-123",
            "agent_id": "agent.coder"
        }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    resource_id = body.get("resource_id", "")
    agent_id = body.get("agent_id", "")

    if not resource_id or not agent_id:
        return web.json_response(
            {"error": "resource_id and agent_id are required"},
            status=400,
        )

    kl = KnowledgeLayer()
    acquired = await kl.lock(resource_id, agent_id)
    if acquired:
        return web.json_response({"status": "locked", "resource_id": resource_id})
    return web.json_response(
        {"error": "Resource already locked", "resource_id": resource_id},
        status=409,
    )


async def handle_unlock(request: web.Request) -> web.Response:
    """POST /api/hivemind/knowledge/unlock — Release a lock.

    Body:
        {
            "resource_id": "resource-123",
            "agent_id": "agent.coder"
        }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    resource_id = body.get("resource_id", "")
    agent_id = body.get("agent_id", "")

    if not resource_id or not agent_id:
        return web.json_response(
            {"error": "resource_id and agent_id are required"},
            status=400,
        )

    kl = KnowledgeLayer()
    released = await kl.unlock(resource_id, agent_id)
    if released:
        return web.json_response({"status": "unlocked", "resource_id": resource_id})
    return web.json_response(
        {"error": "Not locked by this agent", "resource_id": resource_id},
        status=403,
    )


async def handle_cleanup(request: web.Request) -> web.Response:
    """POST /api/hivemind/knowledge/cleanup — Cleanup expired events."""
    kl = KnowledgeLayer()
    removed = await kl.cleanup_expired()
    return web.json_response({"removed": removed})


def setup_routes(app: web.Application) -> None:
    """Setup Hivemind knowledge layer API routes."""
    app.router.add_get(
        "/api/hivemind/knowledge/status", handle_status,
    )
    app.router.add_post(
        "/api/hivemind/knowledge/publish", handle_publish,
    )
    app.router.add_get(
        "/api/hivemind/knowledge/query", handle_query,
    )
    app.router.add_get(
        "/api/hivemind/knowledge/search", handle_search,
    )
    app.router.add_post(
        "/api/hivemind/knowledge/subscribe", handle_subscribe,
    )
    app.router.add_get(
        "/api/hivemind/knowledge/subscriptions", handle_subscriptions,
    )
    app.router.add_post(
        "/api/hivemind/knowledge/lock", handle_lock,
    )
    app.router.add_post(
        "/api/hivemind/knowledge/unlock", handle_unlock,
    )
    app.router.add_post(
        "/api/hivemind/knowledge/cleanup", handle_cleanup,
    )
