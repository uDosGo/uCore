from __future__ import annotations

import logging

from aiohttp import web

from app.services.flow_router import FlowLLMRouter

log = logging.getLogger("ucore.api.flow_router")

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
        return web.json_response(
            {"error": "Invalid JSON", "status": "error"}, status=400)

    task_description = body.get("task", "")
    complexity = body.get("complexity", "auto")
    context_size = body.get("context_size", "small")
    risk_level = body.get("risk_level", "low")
    task_id = body.get("task_id")
    budget_remaining = body.get("budget_remaining", 100.0)
    max_price = body.get("max_price")

    if not task_description:
        return web.json_response(
            {"error": "task is required", "status": "error"}, status=400)

    try:
        flow_router = get_flow_router()
        result = await flow_router.route_task(
            task_description=task_description,
            complexity=complexity,
            context_size=context_size,
            risk_level=risk_level,
            task_id=task_id,
            budget_remaining=budget_remaining,
            max_price=max_price,
        )
        return web.json_response({"status": "routed", "result": result})
    except Exception as e:
        log.error(f"Flow router route error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_flow_router_analytics(request: web.Request) -> web.Response:
    """GET /api/flow-router/analytics — Get routing analytics."""
    try:
        flow_router = get_flow_router()
        analytics = flow_router.get_analytics()
        return web.json_response({"status": "ok", "analytics": analytics})
    except Exception as e:
        log.error(f"Flow router analytics error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_flow_router_history(request: web.Request) -> web.Response:
    """GET /api/flow-router/history — Get routing history."""
    try:
        flow_router = get_flow_router()
        limit = int(request.query.get("limit", "100"))
        history = flow_router.get_routing_history(limit=limit)
        return web.json_response(
            {"status": "ok", "history": history, "count": len(history)})
    except Exception as e:
        log.error(f"Flow router history error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_cost_providers(request: web.Request) -> web.Response:
    """GET /api/cost/providers — List providers with cost tiers."""
    try:
        from app.services.provider_router import get_router
        router = get_router()
        providers = router.list_providers()
        return web.json_response({"status": "ok", "providers": providers})
    except Exception as e:
        log.error(f"Cost providers error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_cost_models(request: web.Request) -> web.Response:
    """GET /api/cost/models — List all models with cost metadata."""
    try:
        from app.services.provider_router import get_router
        router = get_router()
        models = router.list_models()
        return web.json_response(
            {"status": "ok", "models": models, "count": len(models)})
    except Exception as e:
        log.error(f"Cost models error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_cost_estimate(request: web.Request) -> web.Response:
    """POST /api/cost/estimate — Estimate cost for a chat request."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON", "status": "error"}, status=400)
    messages = body.get("messages", [])
    provider_name = body.get("provider")
    model_id = body.get("model")
    if not messages:
        return web.json_response(
            {"error": "messages is required", "status": "error"}, status=400)
    try:
        from app.services.provider_router import get_router
        router = get_router()
        prov = router.get_provider(provider_name)
        cost_per_token = prov.cost_per_token
        estimated_cost = len(messages) * cost_per_token
        if cost_per_token <= 0:
            estimated_cost = 0.0
        return web.json_response({
            "status": "ok",
            "estimate": {
                "provider": prov.name,
                "model": model_id or prov.default_model,
                "cost_tier": prov.cost_tier,
                "cost_per_token": cost_per_token,
                "message_count": len(messages),
                "estimated_cost": round(estimated_cost, 6),
            },
        })
    except Exception as e:
        log.error(f"Cost estimate error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_cost_stats(request: web.Request) -> web.Response:
    """GET /api/cost/stats — Get provider router stats."""
    try:
        from app.services.provider_router import get_router
        router = get_router()
        stats = router.stats()
        return web.json_response({"status": "ok", "stats": stats})
    except Exception as e:
        log.error(f"Cost stats error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_api_registry_resolve(request):
    """GET /api/registry/resolve?variable=${primary:coder}"""
    variable = request.query.get("variable", "")
    if not variable:
        return web.json_response(
            {"error": "variable query param required"}, status=400)
    try:
        from app.services.api_registry import ApiRegistry
        registry = ApiRegistry.get()
        resolved = registry.resolve(variable)
        if resolved is None:
            return web.json_response(
                {"status": "unresolved", "variable": variable})
        return web.json_response({
            "status": "ok", "variable": variable,
            "resolved": resolved.to_dict()})
    except Exception as e:
        log.error(f"Registry resolve error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_api_registry_list(request):
    """GET /api/registry/list — List all resolvable variables."""
    try:
        from app.services.api_registry import ApiRegistry
        registry = ApiRegistry.get()
        resolved = registry.list_resolved()
        return web.json_response({
            "status": "ok", "variables": resolved,
            "count": len(resolved)})
    except Exception as e:
        log.error(f"Registry list error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_quality_score(request):
    """POST /api/quality/score — Score a model response."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON", "status": "error"}, status=400)
    try:
        from app.services.quality_scorer import QualityScorer
        scorer = QualityScorer.get()
        score = scorer.score_response(
            task_type=body.get("task_type", "any"),
            model=body.get("model", ""),
            provider=body.get("provider", ""),
            prompt=body.get("prompt", ""),
            response=body.get("response", ""),
            latency_ms=body.get("latency_ms", 0),
            cost_usd=body.get("cost_usd", 0.0),
            cost_tier=body.get("cost_tier", "unknown"),
            had_error=body.get("had_error", False))
        return web.json_response({"status": "ok", "score": score})
    except Exception as e:
        log.error(f"Quality score error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_quality_rankings(request):
    """GET /api/quality/rankings?task_type=implement"""
    task_type = request.query.get("task_type")
    limit = int(request.query.get("limit", "20"))
    try:
        from app.services.quality_scorer import QualityScorer
        scorer = QualityScorer.get()
        rankings = scorer.get_model_rankings(task_type, limit)
        return web.json_response(
            {"status": "ok", "rankings": rankings})
    except Exception as e:
        log.error(f"Quality rankings error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_quality_stats(request):
    """GET /api/quality/stats — Overall quality statistics."""
    try:
        from app.services.quality_scorer import QualityScorer
        scorer = QualityScorer.get()
        stats = scorer.get_stats()
        return web.json_response({"status": "ok", "stats": stats})
    except Exception as e:
        log.error(f"Quality stats error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_budget_status_new(request):
    """GET /api/budget/status — Get current budget status."""
    try:
        from app.services.budget_manager import BudgetManager
        bm = BudgetManager.get()
        status = bm.get_status()
        return web.json_response(
            {"status": "ok", "budget": status})
    except Exception as e:
        log.error(f"Budget status error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_budget_can_spend(request):
    """POST /api/budget/can-spend — Check if spending is allowed."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON", "status": "error"}, status=400)
    agent_id = body.get("agent_id", "dev")
    estimated_cost = body.get("estimated_cost", 0.0)
    task_type = body.get("task_type")
    try:
        from app.services.budget_manager import BudgetManager
        bm = BudgetManager.get()
        allowed = bm.can_spend(agent_id, estimated_cost, task_type)
        return web.json_response({
            "status": "ok", "allowed": allowed,
            "agent_id": agent_id,
            "estimated_cost": estimated_cost})
    except Exception as e:
        log.error(f"Budget can-spend error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_budget_report(request):
    """GET /api/budget/report?period=day — Get spending report."""
    period = request.query.get("period", "day")
    limit = int(request.query.get("limit", "50"))
    try:
        from app.services.budget_manager import BudgetManager
        bm = BudgetManager.get()
        report = bm.get_spend_report(period, limit)
        return web.json_response({
            "status": "ok", "period": period, "records": report})
    except Exception as e:
        log.error(f"Budget report error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_library_ai_search(request):
    """GET /api/library/ai/search?q=auth+module&agent_id=reviewer"""
    query = request.query.get("q", "")
    agent_id = request.query.get("agent_id")
    limit = int(request.query.get("limit", "10"))
    if not query:
        return web.json_response(
            {"error": "q query param required"}, status=400)
    try:
        from app.services.library_ai_bridge import LibraryAIBridge
        bridge = LibraryAIBridge()
        results = bridge.search(
            query, agent_id=agent_id, limit=limit)
        return web.json_response({"status": "ok", **results})
    except Exception as e:
        log.error(f"Library AI search error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)


async def handle_library_ai_suggest(request):
    """POST /api/library/ai/suggest — Get AI-suggested files."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON", "status": "error"}, status=400)
    task_summary = body.get("task_summary", "")
    agent_id = body.get("agent_id", "dev")
    limit = body.get("limit", 5)
    if not task_summary:
        return web.json_response(
            {"error": "task_summary is required"}, status=400)
    try:
        from app.services.library_ai_bridge import LibraryAIBridge
        bridge = LibraryAIBridge()
        results = await bridge.suggest_for_task(
            task_summary, agent_id=agent_id, limit=limit)
        return web.json_response({"status": "ok", **results})
    except Exception as e:
        log.error(f"Library AI suggest error: {e}")
        return web.json_response(
            {"error": str(e), "status": "error"}, status=500)
