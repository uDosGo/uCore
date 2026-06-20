"""uCore API — route registration (non-core API endpoints)"""
from __future__ import annotations

import logging
from aiohttp import web

log = logging.getLogger("ucore")


def register_routes(app: web.Application) -> None:
    """Register all non-core API routes and surface extensions."""
    from .metadata import system_info_handler
    from .surfaces import register_surface_routes
    from .snacks import register_snack_routes
    from .containers import register_container_routes
    from .github import register_github_routes
    from .exec import handle_exec
    from .docker import handle_docker_ps

    app.router.add_get("/api/system", system_info_handler)
    app.router.add_post("/api/exec", handle_exec)
    app.router.add_get("/api/docker/ps", handle_docker_ps)
    register_surface_routes(app)
    register_snack_routes(app)
    register_container_routes(app)
    register_github_routes(app)

    # ── Surface extensions: Ceefax Teletext ─────────────────────────
    try:
        from ..surfaces.ceefax import CeefaxStore, register_ceefax_routes
        if not hasattr(app, "_ceefax_store"):
            app["_ceefax_store"] = CeefaxStore()
        register_ceefax_routes(app, app["_ceefax_store"])
        log.debug("Ceefax Teletext surface registered")
    except ImportError as e:
        log.debug("Ceefax not available: %s", e)

    # ── Surface extensions: BBCSDL Bridge ──────────────────────────
    try:
        from ..surfaces.bbcsdl import register_bbcsdl_routes
        if not hasattr(app, "_ceefax_store"):
            from ..surfaces.ceefax import CeefaxStore
            app["_ceefax_store"] = CeefaxStore()
        register_bbcsdl_routes(app, app["_ceefax_store"])
        log.debug("BBCSDL surface registered")
    except ImportError as e:
        log.debug("BBCSDL not available: %s", e)

    # ── Dashboard Surface ──────────────────────────────────────────
    try:
        from ..surfaces.dashboard import DashboardStore, register_dashboard_routes
        if not hasattr(app, "_dashboard_store"):
            app["_dashboard_store"] = DashboardStore()
        register_dashboard_routes(app, app["_dashboard_store"])
        log.debug("Dashboard surface registered")
    except ImportError as e:
        log.debug("Dashboard not available: %s", e)
