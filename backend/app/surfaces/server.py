"""Server Surface — unified service health, logs, models, agents, budget.

Provides aggregated endpoints consumed by the Server Surface frontend tabs:
  - Dashboard (health aggregate)
  - Services (registry)
  - Logs (spool-backed)
  - Models (Ollama proxy)
  - Agents (skill/tool aggregate)
  - Budget (cost tracking)
"""

from __future__ import annotations

import asyncio
import logging

from aiohttp import ClientSession, ClientTimeout, web

log = logging.getLogger("ucore")

# ─── Service Registry ──────────────────────────────────────────────


class ServerStore:
    """In-memory store for registered services with default seed."""

    def __init__(self) -> None:
        self._services: dict[str, dict] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        for svc in [
            {
                "name": "snackbar",
                "port": 8484,
                "type": "system",
                "description": "Container orchestrator & workflow runner",
            },
            {
                "name": "hivemind",
                "port": 8490,
                "type": "system",
                "description": "AI agent routing",
            },
            {
                "name": "vault-mcp",
                "port": 8765,
                "type": "user",
                "description": "Vault MCP bridge",
            },
            {
                "name": "ollama",
                "port": 11434,
                "type": "system",
                "description": "Local LLM runtime",
            },
            {
                "name": "feed-spool",
                "port": 8486,
                "type": "system",
                "description": "Feed spooler & transport",
            },
            {
                "name": "secret-server",
                "port": 30001,
                "type": "user",
                "description": "AES-256-GCM encrypted secret vault",
            },
        ]:
            self._services[svc["name"]] = svc

    def list_services(self) -> list[dict]:
        return list(self._services.values())

    def get_service(self, name: str) -> dict | None:
        return self._services.get(name)

    def add_service(self, svc: dict) -> dict:
        self._services[svc["name"]] = svc
        return svc


# ─── Health Probe ──────────────────────────────────────────────────


async def _probe_service(svc: dict) -> dict:
    """Probe a single service's /health endpoint."""
    port = svc.get("port", 0)
    if not port:
        return {**svc, "status": "down", "uptime": 0}
    url = f"http://localhost:{port}/health"
    try:
        async with ClientSession(
            timeout=ClientTimeout(total=2)
        ) as session:
            async with session.get(url) as resp:
                return {
                    **svc,
                    "status": "up" if resp.status == 200 else "degraded",
                    "uptime": 99.0,
                }
    except Exception:
        return {**svc, "status": "down", "uptime": 0}


async def _probe_all(store: ServerStore) -> list[dict]:
    svcs = store.list_services()
    tasks = [_probe_service(s) for s in svcs]
    return list(await asyncio.gather(*tasks))


# ─── Route Registration ────────────────────────────────────────────


def register_server_routes(app: web.Application, store: ServerStore) -> None:  # noqa: C901
    """Register aiohttp routes for the Server surface."""

    # ── Health ────────────────────────────────────────────────
    async def handle_health(_request: web.Request) -> web.Response:
        services = await _probe_all(store)
        up = sum(1 for s in services if s["status"] == "up")
        degraded = sum(1 for s in services if s["status"] == "degraded")
        down = sum(1 for s in services if s["status"] == "down")
        pct = round((up / max(len(services), 1)) * 100)
        return web.json_response({
            "services": services,
            "count": len(services),
            "up": up,
            "degraded": degraded,
            "down": down,
            "health_pct": pct,
        })

    # ── Services ──────────────────────────────────────────────
    async def handle_list_services(_request: web.Request) -> web.Response:
        services = await _probe_all(store)
        return web.json_response({"services": services, "count": len(services)})

    async def handle_get_service(request: web.Request) -> web.Response:
        name = request.match_info["name"]
        svc = store.get_service(name)
        if not svc:
            return web.json_response({"error": "Service not found"}, status=404)
        probed = await _probe_service(svc)
        return web.json_response({"service": probed})

    async def handle_add_service(request: web.Request) -> web.Response:
        try:
            body = await request.json()
            svc = store.add_service(body)
            return web.json_response({"status": "ok", "service": svc}, status=201)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    # ── Logs ──────────────────────────────────────────────────
    async def handle_logs(request: web.Request) -> web.Response:
        raw_limit = request.query.get("limit", "20")
        limit = int(raw_limit)
        try:
            from app.services.spool_reader import read_spool  # noqa: PLC0415
            entries = read_spool(max_entries=limit)
            logs = [
                {
                    "timestamp": e.timestamp,
                    "service": e.module or "system",
                    "level": (e.level or "info").lower(),
                    "message": e.message,
                }
                for e in entries[:limit]
            ]
        except ImportError:
            logs = []
        return web.json_response(
            {"logs": logs, "count": len(logs)},
        )

    # ── Models (Ollama proxy) ─────────────────────────────────
    async def handle_models(_request: web.Request) -> web.Response:
        models = []
        error = None
        try:
            from app.api.handlers import (  # noqa: PLC0415
                handle_ollama_models_available,
            )
            models = handle_ollama_models_available
        except ImportError:
            pass
        if not models or callable(models):
            try:
                async with ClientSession(
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as session:
                    async with session.get(
                        "http://localhost:11434/api/tags"
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            raw = data.get("models") or []
                            total = max(len(raw), 1)
                            models = [
                                {
                                    "id": m.get("name", ""),
                                    "name": m.get("name", ""),
                                    "pct": round(
                                        ((len(raw) - i) / total) * 100
                                    ),
                                    "calls": 0,
                                }
                                for i, m in enumerate(raw[:10])
                            ]
                        else:
                            error = f"Ollama returned {resp.status}"
            except Exception as exc:
                error = str(exc)
        return web.json_response({
            "models": models if isinstance(models, list) else [],
            "count": len(models) if isinstance(models, list) else 0,
            "error": error,
        })

    # ── Agent list (mirrors /api/agents but flat) ─────────────
    async def handle_server_agents(_request: web.Request) -> web.Response:
        try:
            from app.api.agents import handle_list_agents
            resp = await handle_list_agents(_request)
            data = json.loads(resp.body) if hasattr(resp, "body") else {}
            agents = data.get("agents", [])
            mapped = [
                {
                    "id": a.get("id", "unknown"),
                    "name": a.get("name", "Agent"),
                    "icon": a.get("icon", "smart_toy"),
                    "active": a.get("status", "offline") != "offline",
                    "description": ", ".join(
                        a.get("capabilities", []) or ["general"]
                    ),
                }
                for a in agents
            ]
            return web.json_response({"agents": mapped, "count": len(mapped)})
        except Exception as exc:
            log.warning("Server agents aggregation failed: %s", exc)
            return web.json_response({"agents": [], "count": 0, "error": str(exc)})

    # ── Budget (flat schema) ──────────────────────────────────
    async def handle_server_budget(request: web.Request) -> web.Response:
        try:
            from app.api.budget_api import handle_budget_status as _budget
            resp = await _budget(request)
            import json as _json
            if hasattr(resp, "body"):
                data = _json.loads(resp.body)
            else:
                data = {}
            usage = data.get("usage", {})
            policy = data.get("policy", {})
            limit = float(policy.get("monthly_usd_limit", 50))
            used = float(usage.get("total_cost", 0))
            remaining = max(0, limit - used)
            return web.json_response({
                "remaining": round(remaining, 2),
                "used": round(used, 2),
                "limit": round(limit, 2),
                "over_limit": used >= limit,
            })
        except Exception as exc:
            log.warning("Server budget aggregation failed: %s", exc)
            return web.json_response({
                "remaining": 50.00,
                "used": 0.00,
                "limit": 50.00,
                "over_limit": False,
                "error": str(exc),
            })

    # ── Register routes ───────────────────────────────────────
    app.router.add_get("/api/server/health", handle_health)
    app.router.add_get("/api/server/services", handle_list_services)
    app.router.add_get("/api/server/services/{name}", handle_get_service)
    app.router.add_post("/api/server/services", handle_add_service)
    app.router.add_get("/api/server/logs", handle_logs)
    app.router.add_get("/api/server/models", handle_models)
    app.router.add_get("/api/server/agents", handle_server_agents)
    app.router.add_get("/api/server/budget", handle_server_budget)


# Needed for json import in handler closures
import json  # noqa: E402

import aiohttp  # noqa: E402
