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
    from .chat import handle_chat, handle_chat_prompts, handle_models
    from .skills import handle_run_skill, handle_run_named_skill, handle_list_skills
    from .tools import handle_list_tools, handle_tool_status
    from .mcp import (
        handle_mcp_discover, handle_mcp_call,
    )
    from .secret_store_api import (
        handle_list_secrets, handle_get_secret, handle_set_secret,
        handle_delete_secret, handle_list_env_vars, handle_import_from_env,
    )
    from .knowledge import (
        handle_list_workspaces, handle_list_documents,
        handle_get_document, handle_get_document_content, handle_search,
    )

    # Knowledge (AppFlowy bridge)
    app.router.add_get("/api/knowledge/workspaces", handle_list_workspaces)
    app.router.add_get("/api/knowledge/documents", handle_list_documents)
    app.router.add_get("/api/knowledge/documents/{object_id}", handle_get_document)
    app.router.add_get("/api/knowledge/documents/{object_id}/content", handle_get_document_content)
    app.router.add_get("/api/knowledge/search", handle_search)

    # MCP Integration
    app.router.add_get("/api/mcp/tools", handle_mcp_discover)
    app.router.add_post("/api/mcp/call", handle_mcp_call)

    # Secret Store
    app.router.add_get("/api/secrets", handle_list_secrets)
    app.router.add_get("/api/secrets/env", handle_list_env_vars)
    app.router.add_post("/api/secrets/import-env", handle_import_from_env)
    app.router.add_get("/api/secrets/{name}", handle_get_secret)
    app.router.add_post("/api/secrets/{name}", handle_set_secret)
    app.router.add_delete("/api/secrets/{name}", handle_delete_secret)

    app.router.add_get("/api/skills", handle_list_skills)
    app.router.add_get("/api/tools", handle_list_tools)
    app.router.add_get("/api/tools/{tool_id}/status", handle_tool_status)
    app.router.add_get("/api/system", system_info_handler)
    app.router.add_post("/api/exec", handle_exec)
    app.router.add_get("/api/docker/ps", handle_docker_ps)
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_get("/api/chat/prompts", handle_chat_prompts)
    app.router.add_get("/api/models", handle_models)
    app.router.add_post("/api/skills/{skill_id}/run", handle_run_skill)
    app.router.add_post("/api/skills/run", handle_run_named_skill)
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
