from __future__ import annotations

import asyncio
import json
import platform as plat_module
import sys
import time
from contextlib import suppress
from pathlib import Path

from .logging import log
from .settings import settings

try:
    import yaml
except ImportError:
    yaml = None

try:
    from aiohttp import web
except ImportError:
    log.error("aiohttp required: pip install aiohttp")
    sys.exit(1)


# ─── Helpers ──────────────────────────────────────────────────────


def _load_json(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_json(path: str, data: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ─── CORS middleware ──────────────────────────────────────────────


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    if settings.enable_cors:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@web.middleware
async def budget_middleware(request: web.Request, handler):
    """Budget guard for costly API endpoints with usage logging."""
    manager = request.app.get("budget_manager")
    if manager is None:
        return await handler(request)

    path = request.path
    if path not in manager.policy.guarded_endpoints:
        return await handler(request)

    estimated_cost = manager.estimate_for_path(path)

    provider = request.headers.get("X-Provider", "").strip()
    model = request.headers.get("X-Model", "").strip()
    if not provider or not model:
        payload = {}
        if request.can_read_body:
            with suppress(Exception):
                payload = await request.json()
        if isinstance(payload, dict):
            if not provider:
                provider = str(
                    payload.get("provider")
                    or payload.get("vendor")
                    or payload.get("engine")
                    or "",
                ).strip()
            if not model:
                params = payload.get("params")
                if isinstance(params, dict):
                    model = str(
                        params.get("model")
                        or params.get("model_name")
                        or "",
                    ).strip()
                if not model:
                    model = str(
                        payload.get("model")
                        or payload.get("model_name")
                        or "",
                    ).strip()

    allowed, reason, _usage = manager.check_budget(
        estimated_cost,
        model=model,
        provider=provider,
    )

    if not allowed:
        manager.record_usage(
            endpoint=path,
            estimated_cost=estimated_cost,
            actual_cost=0.0,
            status_code=429,
            blocked=True,
            provider=provider,
            model=model,
        )
        return web.json_response(
            {
                "error": reason or "Budget limit reached",
                "hint": "See /api/budget/status for current usage.",
            },
            status=429,
        )

    response = await handler(request)

    actual_cost = estimated_cost
    header_cost = response.headers.get("X-Usage-Cost", "").strip()
    if header_cost:
        with suppress(ValueError):
            actual_cost = float(header_cost)

    manager.record_usage(
        endpoint=path,
        estimated_cost=estimated_cost,
        actual_cost=actual_cost,
        status_code=response.status,
        blocked=False,
        provider=provider,
        model=model,
    )
    return response


# ─── Routes ───────────────────────────────────────────────────────


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "service": "uCore",
        "version": settings.version,
    })


async def version_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "app": settings.app_name,
        "version": settings.version,
        "python": plat_module.python_version(),
        "platform": plat_module.system(),
    })


async def info_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "app": settings.app_name,
        "version": settings.version,
        "host": settings.host,
        "port": settings.port,
        "debug": settings.debug,
        "platform": plat_module.system(),
        "machine": plat_module.machine(),
        "python": plat_module.python_version(),
        "uptime": time.time() - _start_time,
    })


async def shutdown_handler(request: web.Request) -> web.Response:
    asyncio.get_event_loop().stop()
    return web.json_response({"status": "shutting down"})


# ─── MCP Bridge handlers ──────────────────────────────────────────


async def mcp_query_handler(request: web.Request) -> web.Response:
    """POST /api/mcp/query — proxy a query to MCP bridge"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    try:
        from app.services.mcp import get_bridge
        bridge = get_bridge()
        peer = data.get("peer", "forge")
        tool = data.get("tool", "")
        params = data.get("params", {})
        result = await bridge.call_tool(peer, tool, params)
        return web.json_response({"result": result})
    except ImportError as e:
        return web.json_response({"error": f"MCP bridge not available: {e}"}, status=501)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def mcp_status_handler(request: web.Request) -> web.Response:
    """GET /api/mcp/status — get MCP mesh status"""
    try:
        from app.services.mcp import get_bridge
        bridge = get_bridge()
        status = await bridge.get_mesh_status()
        return web.json_response(status)
    except ImportError:
        return web.json_response({"status": "unavailable", "message": "MCP bridge not loaded"})


async def mcp_providers_handler(request: web.Request) -> web.Response:
    """GET /api/mcp/providers — list AI providers"""
    try:
        from app.services.provider_router import get_router
        router = get_router()
        return web.json_response({
            "providers": router.list_providers(),
            "models": router.list_models(),
        })
    except ImportError as e:
        return web.json_response({"error": f"Provider router not available: {e}"}, status=501)


async def mcp_chat_handler(request: web.Request) -> web.Response:
    """POST /api/mcp/chat — chat with AI provider"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    messages = data.get("messages", [])
    provider = data.get("provider")
    model = data.get("model")
    if not messages:
        return web.json_response({"error": "messages are required"}, status=400)
    try:
        from app.services.provider_router import get_router
        router = get_router()
        result = await router.chat(messages, provider=provider, model=model)
        return web.json_response(result)
    except ImportError as e:
        return web.json_response({"error": f"Provider router not available: {e}"}, status=501)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def migrate_admin_handler(request: web.Request) -> web.Response:
    """GET /api/admin/migrate — run database migration"""
    try:
        from app.core.database import migrate_db
        result = migrate_db()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ─── App factory ──────────────────────────────────────────────────


_start_time: float = time.time()


async def maintenance_scheduler_ctx(app: web.Application):
    """Run the lightweight overnight maintenance scheduler in the background."""
    from app.services.maintenance_scheduler import (
        MaintenanceScheduler,
        set_maintenance_scheduler,
    )

    scheduler = MaintenanceScheduler()
    set_maintenance_scheduler(scheduler)
    app["maintenance_scheduler"] = scheduler
    await scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()
        set_maintenance_scheduler(None)


def create_app() -> web.Application:
    """Build and return a configured aiohttp application."""
    app = web.Application(middlewares=[budget_middleware, cors_middleware])
    app.cleanup_ctx.append(maintenance_scheduler_ctx)

    # Budget manager (usage logging + enforcement scaffold)
    try:
        from app.services.budget_manager import BudgetManager

        app["budget_manager"] = BudgetManager()
        log.debug("Budget manager initialized")
    except Exception as e:
        app["budget_manager"] = None
        log.warning("Budget manager unavailable: %s", e)

    # Core routes (these are the canonical ones)
    app.router.add_get("/api/health", health_handler)
    app.router.add_get("/api/version", version_handler)
    app.router.add_get("/api/info", info_handler)
    app.router.add_post("/api/shutdown", shutdown_handler)

    # MCP / AI routes
    app.router.add_post("/api/mcp/query", mcp_query_handler)
    app.router.add_get("/api/mcp/status", mcp_status_handler)
    app.router.add_get("/api/mcp/providers", mcp_providers_handler)
    app.router.add_post("/api/mcp/chat", mcp_chat_handler)

    # Database / Admin routes
    app.router.add_get("/api/admin/migrate", migrate_admin_handler)

    # Run database migration on startup
    from app.core.database import migrate_db
    migration = migrate_db()
    log.info("Database migration: v%s (%s tables)", migration["version"], "surfaces, snacks, containers")

    # Register API module routes (non-overlapping with core)
    try:
        from ..api.routes import register_routes
        register_routes(app)
        log.debug("API module routes registered")
    except ImportError as e:
        log.debug("API module not yet available: %s", e)

    return app


# ─── Main entry ──────────────────────────────────────────────────


def main():
    """Start the uCore snackbar daemon."""
    log.info("Starting uCore snackbar on %s:%d", settings.host, settings.port)

    app = create_app()
    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()

