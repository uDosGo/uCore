"""uCore API — route registration (non-core API endpoints)"""
from __future__ import annotations

import logging
from aiohttp import web

log = logging.getLogger("ucore")


def register_routes(app: web.Application) -> None:
    """Register all non-core API routes and surface extensions."""
    from .metadata import system_info_handler, maintenance_status_handler, workflow_status_handler
    from .surfaces import register_surface_routes
    from .snacks import register_snack_routes
    from .containers import register_container_routes
    from .github import register_github_routes
    from .exec import handle_exec
    from .docker import handle_docker_ps
    from .chat import handle_chat, handle_chat_prompts, handle_models
    from .skills import handle_run_skill, handle_run_named_skill, handle_list_skills
    from .tools import handle_list_tools, handle_tool_status
    from .agents import handle_list_agents, handle_agents_stats
    from .mcp import (
        handle_mcp_discover, handle_mcp_call,
    )
    from .secret_store_api import (
        handle_list_secrets, handle_get_secret, handle_set_secret,
        handle_delete_secret, handle_list_env_vars, handle_import_from_env,
        handle_export_to_env, handle_secret_audit, handle_sync_github,
    )
    from .config_api import handle_get_config
    from .budget_api import (
        handle_budget_status,
        handle_budget_usage,
        handle_budget_reload,
    )
    from .developer_api import (
        handle_list_repos,
        handle_list_repo_files,
        handle_get_repo_file_preview,
        handle_update_repo_file,
        handle_get_repo_file_diff,
        handle_list_repo_review,
        handle_stage_repo_file,
        handle_unstage_repo_file,
        handle_commit_repo_files,
    )
    from .knowledge import (
        handle_list_workspaces, handle_list_documents,
        handle_get_document, handle_get_document_content, handle_search,
        handle_mission_task_binder,
        handle_local_databases, handle_local_tables, handle_local_query,
        handle_local_export,
        handle_af_import, handle_af_sync, handle_af_status,
        handle_af_index_status,
    )
    from .workflows import (
        handle_import_status, handle_index_coverage,
        handle_get_task, handle_update_task,
        handle_board_health,
        handle_create_workflow,
        handle_list_workflows,
        handle_run_workflow,
        handle_workflow_logs,
    )

    # Knowledge (AppFlowy bridge)
    app.router.add_get("/api/knowledge/workspaces", handle_list_workspaces)
    app.router.add_get("/api/knowledge/documents", handle_list_documents)
    app.router.add_get("/api/knowledge/documents/{object_id}", handle_get_document)
    app.router.add_get("/api/knowledge/documents/{object_id}/content", handle_get_document_content)
    app.router.add_get("/api/knowledge/search", handle_search)
    app.router.add_get(
        "/api/knowledge/adapter/mission-task-binder",
        handle_mission_task_binder,
    )
    app.router.add_get("/api/knowledge/local/databases", handle_local_databases)
    app.router.add_get("/api/knowledge/local/tables", handle_local_tables)
    app.router.add_post("/api/knowledge/local/query", handle_local_query)
    app.router.add_post("/api/knowledge/local/export", handle_local_export)
    # AF Manager (vault import/sync)
    app.router.add_post("/api/knowledge/import", handle_af_import)
    app.router.add_post("/api/knowledge/sync", handle_af_sync)
    app.router.add_get("/api/knowledge/status", handle_af_status)
    app.router.add_get("/api/knowledge/index/status", handle_af_index_status)
    # Phase 9 new endpoints
    app.router.add_get("/api/knowledge/import/status", handle_import_status)
    app.router.add_get("/api/knowledge/index/coverage", handle_index_coverage)
    app.router.add_get("/api/workflows/task/{task_id}", handle_get_task)
    app.router.add_put("/api/workflows/task/{task_id}", handle_update_task)
    app.router.add_get("/api/workflows/board/{board_id}/health", handle_board_health)
    app.router.add_get("/api/workflows", handle_list_workflows)
    app.router.add_post("/api/workflows", handle_create_workflow)
    app.router.add_post("/api/workflows/{workflow_id}/run", handle_run_workflow)
    app.router.add_get("/api/workflows/{workflow_id}/logs", handle_workflow_logs)

    # MCP Integration
    app.router.add_get("/api/mcp/tools", handle_mcp_discover)
    app.router.add_post("/api/mcp/call", handle_mcp_call)

    # Secret Store
    app.router.add_get("/api/secrets", handle_list_secrets)
    app.router.add_get("/api/secrets/env", handle_list_env_vars)
    app.router.add_get("/api/secrets/audit", handle_secret_audit)
    app.router.add_post("/api/secrets/import-env", handle_import_from_env)
    app.router.add_post("/api/secrets/export-env", handle_export_to_env)
    app.router.add_post("/api/secrets/sync-github", handle_sync_github)
    app.router.add_get("/api/secrets/{name}", handle_get_secret)
    app.router.add_post("/api/secrets/{name}", handle_set_secret)
    app.router.add_delete("/api/secrets/{name}", handle_delete_secret)

    # Central config
    app.router.add_get("/api/config", handle_get_config)
    app.router.add_get("/api/budget/status", handle_budget_status)
    app.router.add_get("/api/budget/usage", handle_budget_usage)
    app.router.add_post("/api/budget/reload", handle_budget_reload)
    app.router.add_get("/api/developer/repos", handle_list_repos)
    app.router.add_get("/api/developer/repos/{repo_name}/files", handle_list_repo_files)
    app.router.add_get("/api/developer/repos/{repo_name}/file-preview", handle_get_repo_file_preview)
    app.router.add_put("/api/developer/repos/{repo_name}/file-preview", handle_update_repo_file)
    app.router.add_get("/api/developer/repos/{repo_name}/diff", handle_get_repo_file_diff)
    app.router.add_get("/api/developer/repos/{repo_name}/review", handle_list_repo_review)
    app.router.add_post("/api/developer/repos/{repo_name}/stage", handle_stage_repo_file)
    app.router.add_post("/api/developer/repos/{repo_name}/unstage", handle_unstage_repo_file)
    app.router.add_post("/api/developer/repos/{repo_name}/commit", handle_commit_repo_files)

    app.router.add_get("/api/skills", handle_list_skills)
    app.router.add_get("/api/tools", handle_list_tools)
    app.router.add_get("/api/tools/{tool_id}/status", handle_tool_status)
    app.router.add_get("/api/agents", handle_list_agents)
    app.router.add_get("/api/agents/stats", handle_agents_stats)
    app.router.add_get("/api/system", system_info_handler)
    app.router.add_get("/api/system/maintenance", maintenance_status_handler)
    app.router.add_get("/api/system/workflow", workflow_status_handler)
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

    # ── Spool / Activity Feed ───────────────────────────────────────
    try:
        from .spool import register_spool_routes
        register_spool_routes(app)
        log.debug("Spool activity feed routes registered")
    except ImportError as e:
        log.debug("Spool routes not available: %s", e)

    # ── Identity (UDN-IDENTITY-API-001) ─────────────────────────────
    try:
        from .identity_api import register_identity_routes
        register_identity_routes(app)
        log.debug("Identity routes registered")
    except ImportError as e:
        log.debug("Identity routes not available: %s", e)

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
