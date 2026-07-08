"""server — modular uCore snackbar entry point.

Snackbar Server — v4.1 (modular daemon)
========================================

Route handlers live in ``snackbar/modules/`` and are loaded dynamically.
Each module exposes a ``register(app: web.Application) -> None`` function.

To add a new module:
  1. Create ``snackbar/modules/your_module.py``
  2. Define ``async def register(app: web.Application) -> None: ...``
  3. The loader picks it up automatically on next start.

Usage:
    python3 -m app.snackbar --port 8484
    python3 -m app.snackbar --port 8484 --auto-start
"""
from __future__ import annotations

import importlib
import json
import pkgutil
import time
from pathlib import Path

from aiohttp import web

from app.core.logging import log
from app.core.settings import settings

# ─── Shared helpers (re-exported for modules) ──────────────────────


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


# ─── Middleware ────────────────────────────────────────────────────


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    if settings.enable_cors:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization"
        )
    return response


@web.middleware
async def budget_middleware(request: web.Request, handler):
    """Budget guard for costly API endpoints with usage logging."""
    manager = request.app.get("budget_manager")
    if manager is None:
        return await handler(request)

    from contextlib import suppress

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
                        params.get("model") or params.get("model_name") or "",
                    ).strip()
                if not model:
                    model = str(
                        payload.get("model") or payload.get("model_name") or "",
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


# ─── Dynamic module loader ─────────────────────────────────────────

_MODULES_PACKAGE = "app.snackbar.modules"


def _load_modules(app: web.Application) -> list[str]:
    """Dynamically import and register all route modules.

    Each module in ``app/snackbar/modules/`` must expose a ``register(app)``
    callable.  Modules are loaded in alphabetical order for determinism.
    """
    loaded: list[str] = []

    try:
        pkg = importlib.import_module(_MODULES_PACKAGE)
    except ImportError as exc:
        log.warning("Snackbar modules package not found: %s", exc)
        return loaded

    for mod_info in pkgutil.iter_modules(pkg.__path__):
        mod_name = mod_info.name
        if mod_name.startswith("_"):
            continue
        full_name = f"{_MODULES_PACKAGE}.{mod_name}"
        try:
            module = importlib.import_module(full_name)
            register_fn = getattr(module, "register", None)
            if register_fn is None:
                log.debug("Skipping %s (no register function)", full_name)
                continue
            register_fn(app)
            loaded.append(mod_name)
            log.debug("Loaded snackbar module: %s", mod_name)
        except Exception as exc:
            log.error("Failed to load snackbar module %s: %s", full_name, exc)

    log.info("Loaded %d snackbar modules: %s", len(loaded), ", ".join(loaded))
    return loaded


# ─── Cleanup context ───────────────────────────────────────────────


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


# ─── App factory ───────────────────────────────────────────────────

_start_time: float = time.time()


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

    # Run database migration on startup
    from app.core.database import migrate_db

    migration = migrate_db()
    log.info(
        "Database migration: v%s (%s tables)",
        migration["version"],
        "surfaces, snacks, containers",
    )

    # Load all modular route handlers
    _load_modules(app)

    # Register API module routes (non-overlapping with core)
    try:
        from ..api.routes import register_routes

        register_routes(app)
        log.debug("API module routes registered")
    except ImportError as e:
        log.debug("API module not yet available: %s", e)

    # Register catalog routes
    try:
        from ..api.catalog import setup_routes

        setup_routes(app)
        log.debug("Catalog routes registered")
    except ImportError as e:
        log.debug("Catalog API not yet available: %s", e)

    return app


# ─── Main entry ────────────────────────────────────────────────────


def main():
    """Start the uCore snackbar daemon."""
    log.info("Starting uCore snackbar on %s:%d", settings.host, settings.port)

    app = create_app()
    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
