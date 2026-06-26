from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

from app.services.flow_router import FlowLLMRouter

log = logging.getLogger("ucore.api.flow_router")

# Global Flow Router instance
_flow_router = None


def get_flow_router() -> FlowLLMRouter:
    global _flow_router
    if _flow_router is None:
        from app.services.provider_router import ProviderRouter
        _flow_router = FlowLLMRouter(ProviderRouter())
    return _flow_router


async def handle_flow_router_route(request: web.Request) -> web.Response:
    """POST /api/flow-router/route — Route a task to optimal provider/model."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({
            "error": "Invalid JSON",
            "status": "error",
        }, status=400)
    
    task_description = body.get("task", "")
    complexity = body.get("complexity", "auto")
    context_size = body.get("context_size", "small")
    risk_level = body.get("risk_level", "low")
    task_id = body.get("task_id")
    budget_remaining = body.get("budget_remaining", 100.0)
    
    if not task_description:
        return web.json_response({
            "error": "task is required",
            "status": "error",
        }, status=400)
    
    try:
        flow_router = get_flow_router()
        result = await flow_router.route_task(
            task_description=task_description,
            complexity=complexity,
            context_size=context_size,
            risk_level=risk_level,
            task_id=task_id,
            budget_remaining=budget_remaining,
        )
        
        return web.json_response({
            "status": "routed",
            "result": result,
        })
        
    except Exception as e:
        log.error(f"Flow router route error: {e}")
        return web.json_response({
            "error": str(e),
            "status": "error",
        }, status=500)


async def handle_flow_router_analytics(request: web.Request) -> web.Response:
    """GET /api/flow-router/analytics — Get routing analytics."""
    try:
        flow_router = get_flow_router()
        analytics = flow_router.get_analytics()
        
        return web.json_response({
            "status": "ok",
            "analytics": analytics,
        })
        
    except Exception as e:
        log.error(f"Flow router analytics error: {e}")
        return web.json_response({
            "error": str(e),
            "status": "error",
        }, status=500)


async def handle_flow_router_history(request: web.Request) -> web.Response:
    """GET /api/flow-router/history — Get routing history."""
    try:
        flow_router = get_flow_router()
        limit = int(request.query.get("limit", "100"))
        history = flow_router.get_routing_history(limit=limit)
        
        return web.json_response({
            "status": "ok",
            "history": history,
            "count": len(history),
        })
        
    except Exception as e:
        log.error(f"Flow router history error: {e}")
        return web.json_response({
            "error": str(e),
            "status": "error",
        }, status=500)
