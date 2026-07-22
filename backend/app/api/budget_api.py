"""Budget API endpoints."""
from __future__ import annotations

from aiohttp import web

from app.core.snackbar import BUDGET_MANAGER_KEY


def _get_manager(request: web.Request):
    manager = request.app.get(BUDGET_MANAGER_KEY)
    if manager is None:
        raise web.HTTPServiceUnavailable(
            text='{"error":"budget manager unavailable"}',
            content_type="application/json",
        )
    return manager


async def handle_budget_status(request: web.Request) -> web.Response:
    manager = _get_manager(request)
    usage = manager.get_monthly_usage()
    policy = manager.policy
    return web.json_response(
        {
            "usage": usage,
            "policy": {
                "monthly_usd_limit": policy.monthly_usd_limit,
                "default_estimated_cost": policy.default_estimated_cost,
                "guarded_endpoints": policy.guarded_endpoints,
                "per_model_limits": policy.per_model_limits,
            },
        },
    )


async def handle_budget_usage(request: web.Request) -> web.Response:
    manager = _get_manager(request)
    raw_limit = request.query.get("limit", "100")
    try:
        limit = int(raw_limit)
    except ValueError:
        limit = 100
    rows = manager.list_usage(limit=limit)
    return web.json_response({"entries": rows, "count": len(rows)})


async def handle_budget_reload(request: web.Request) -> web.Response:
    manager = _get_manager(request)
    policy = manager.reload_policy()
    return web.json_response(
        {
            "status": "reloaded",
            "policy": {
                "monthly_usd_limit": policy.monthly_usd_limit,
                "default_estimated_cost": policy.default_estimated_cost,
                "guarded_endpoints": policy.guarded_endpoints,
                "per_model_limits": policy.per_model_limits,
            },
        },
    )
