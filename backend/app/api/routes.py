"""uCore API — route registration (non-core API endpoints)"""
from __future__ import annotations

import logging

from aiohttp import web

# AppKey instances (avoids NotAppKeyWarning)
CEEFAX_STORE_KEY = web.AppKey("_ceefax_store", object)
DASHBOARD_STORE_KEY = web.AppKey("_dashboard_store", object)

log = logging.getLogger("ucore")


def register_routes(app: web.Application) -> None:
    """Register all non-core API routes and surface extensions."""
    from .agents import handle_agents_stats, handle_list_agents
    from .budget_api import (
        handle_budget_reload,
        handle_budget_status,
        handle_budget_usage,
    )
    from .chat import handle_chat, handle_chat_prompts, handle_models
    from .config_api import handle_get_config
    from .containers import register_container_routes
    from .developer_api import (
        handle_commit_repo_files,
        handle_developer_status,
        handle_get_repo_file_diff,
        handle_get_repo_file_preview,
        handle_list_repo_files,
        handle_list_repo_review,
        handle_list_repos,
        handle_stage_repo_file,
        handle_start_developer,
        handle_stop_developer,
        handle_unstage_repo_file,
        handle_update_repo_file,
    )
    from .docker import handle_docker_ps
    from .exec import handle_exec
    from .flow_router import (
        handle_api_registry_list,
        handle_api_registry_resolve,
        handle_budget_can_spend,
        handle_budget_report,
        handle_budget_status_new,
        handle_cost_estimate,
        handle_cost_models,
        handle_cost_providers,
        handle_cost_stats,
        handle_flow_router_analytics,
        handle_flow_router_history,
        handle_flow_router_route,
        handle_library_ai_search,
        handle_library_ai_suggest,
        handle_quality_rankings,
        handle_quality_score,
        handle_quality_stats,
    )
    from .github import register_github_routes
    from .gridsmith_api import (
        handle_gridsmith_grid_create,
        handle_gridsmith_import_basic,
        handle_gridsmith_latlon_to_ucode,
        handle_gridsmith_status,
        handle_gridsmith_tools,
        handle_gridsmith_ucode_to_latlon,
    )
    from .handlers import (
        handle_agents_spec_capability,
        handle_agents_spec_get,
        handle_agents_spec_list,
        handle_agents_spec_plan,
        handle_agents_spec_route,
        handle_ollama_models_available,
        handle_ollama_performance,
        handle_ollama_status,
    )
    from .knowledge import (
        handle_af_import,
        handle_af_index_status,
        handle_af_status,
        handle_af_sync,
        handle_get_document,
        handle_get_document_content,
        handle_list_documents,
        handle_list_workspaces,
        handle_local_databases,
        handle_local_export,
        handle_local_query,
        handle_local_tables,
        handle_mission_task_binder,
        handle_search,
    )
    from .mcp import (
        handle_mcp_call,
        handle_mcp_diagnostics,
        handle_mcp_discover,
    )
    from .metadata import (
        maintenance_status_handler,
        system_info_handler,
        workflow_status_handler,
    )
    from .secret_store_api import (
        handle_delete_secret,
        handle_export_to_env,
        handle_get_secret,
        handle_import_from_env,
        handle_list_env_vars,
        handle_list_secrets,
        handle_secret_audit,
        handle_set_secret,
        handle_sync_github,
    )
    from .skills import handle_list_skills, handle_run_named_skill, handle_run_skill
    from .snacks import register_snack_routes
    from .surfaces import register_surface_routes
    from .tools import handle_list_tools, handle_tool_status
    from .toon import (
        handle_toon_clear,
        handle_toon_encode,
        handle_toon_stats,
    )
    from .user_workflow import (
        handle_user_workflow_archive,
        handle_user_workflow_reset,
        handle_user_workflow_seed,
        handle_user_workflow_status,
    )
    from .variables_api import (
        handle_get_install_variables,
        handle_get_user_variables,
        handle_get_variables,
        handle_update_user_variables,
    )
    from .workflows import (
        handle_board_health,
        handle_create_workflow,
        handle_get_task,
        handle_import_status,
        handle_index_coverage,
        handle_list_workflows,
        handle_run_workflow,
        handle_update_task,
        handle_workflow_logs,
        handle_workflow_runs,
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
    app.router.add_get("/api/workflows/runs", handle_workflow_runs)
    app.router.add_post("/api/workflows", handle_create_workflow)
    app.router.add_post("/api/workflows/{workflow_id}/run", handle_run_workflow)
    app.router.add_get("/api/workflows/{workflow_id}/logs", handle_workflow_logs)

    # MCP Integration
    app.router.add_get("/api/mcp/tools", handle_mcp_discover)
    app.router.add_post("/api/mcp/call", handle_mcp_call)
    app.router.add_get("/api/mcp/diagnostics", handle_mcp_diagnostics)

    # TOON Context Optimization
    app.router.add_post("/api/toon/encode", handle_toon_encode)
    app.router.add_get("/api/toon/stats", handle_toon_stats)
    app.router.add_post("/api/toon/clear", handle_toon_clear)

    # Flow-LLM Router
    app.router.add_post("/api/flow-router/route", handle_flow_router_route)
    app.router.add_get("/api/flow-router/analytics", handle_flow_router_analytics)
    app.router.add_get("/api/flow-router/history", handle_flow_router_history)

    # Cost-Aware Provider Routing
    app.router.add_get("/api/cost/providers", handle_cost_providers)
    app.router.add_get("/api/cost/models", handle_cost_models)
    app.router.add_post("/api/cost/estimate", handle_cost_estimate)
    app.router.add_get("/api/cost/stats", handle_cost_stats)

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
    # Variables API
    app.router.add_get("/api/variables", handle_get_variables)
    app.router.add_get("/api/variables/user", handle_get_user_variables)
    app.router.add_put("/api/variables/user", handle_update_user_variables)
    app.router.add_get("/api/variables/install", handle_get_install_variables)
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
    # DevMode (internal dev ops) endpoints
    app.router.add_post("/api/developer/start", handle_start_developer)
    app.router.add_post("/api/developer/stop", handle_stop_developer)
    app.router.add_get("/api/developer/status", handle_developer_status)

    app.router.add_get("/api/skills", handle_list_skills)
    app.router.add_get("/api/tools", handle_list_tools)
    app.router.add_get("/api/tools/{tool_id}/status", handle_tool_status)
    app.router.add_get("/api/agents", handle_list_agents)
    app.router.add_get("/api/agents/stats", handle_agents_stats)

    # Ollama Model Management
    app.router.add_get("/api/ollama/status", handle_ollama_status)
    app.router.add_get("/api/ollama/models/available", handle_ollama_models_available)
    app.router.add_get("/api/ollama/performance", handle_ollama_performance)

    # Specialized Agents
    app.router.add_get("/api/agents/spec/list", handle_agents_spec_list)
    app.router.add_get("/api/agents/spec/get/{agent_id}", handle_agents_spec_get)
    app.router.add_post("/api/agents/spec/plan", handle_agents_spec_plan)
    app.router.add_post("/api/agents/spec/route", handle_agents_spec_route)
    app.router.add_get("/api/agents/spec/capability/{capability}", handle_agents_spec_capability)
    app.router.add_get("/api/gridsmith/status", handle_gridsmith_status)
    app.router.add_get("/api/gridsmith/tools", handle_gridsmith_tools)
    app.router.add_post("/api/gridsmith/grid/create", handle_gridsmith_grid_create)
    app.router.add_post("/api/gridsmith/world/import-basic", handle_gridsmith_import_basic)
    app.router.add_post("/api/gridsmith/location/latlon-to-ucode", handle_gridsmith_latlon_to_ucode)
    app.router.add_post("/api/gridsmith/location/ucode-to-latlon", handle_gridsmith_ucode_to_latlon)
    app.router.add_get("/api/system", system_info_handler)
    app.router.add_get("/api/system/maintenance", maintenance_status_handler)
    app.router.add_get("/api/system/workflow", workflow_status_handler)
    app.router.add_get(
        "/api/user/workflow/status",
        handle_user_workflow_status,
    )
    app.router.add_post(
        "/api/user/workflow/archive",
        handle_user_workflow_archive,
    )
    app.router.add_post(
        "/api/user/workflow/reset",
        handle_user_workflow_reset,
    )
    app.router.add_post(
        "/api/user/workflow/seed",
        handle_user_workflow_seed,
    )
    app.router.add_post("/api/exec", handle_exec)
    app.router.add_get("/api/docker/ps", handle_docker_ps)
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_get("/api/chat/prompts", handle_chat_prompts)
    app.router.add_get("/api/models", handle_models)
    app.router.add_post("/api/skills/{skill_id}/run", handle_run_skill)
    app.router.add_post("/api/skills/run", handle_run_named_skill)
    # Health and skill state endpoints
    from .skills import handle_health, handle_skill_state
    app.router.add_get("/api/skills/state", handle_skill_state)
    app.router.add_get("/api/skills/health", handle_health)
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

    # ── uCode Surface extensions: Ceefax Teletext ──────────────────
    try:
        from ..ucode.ceefax import CeefaxStore, register_ceefax_routes
        if not hasattr(app, "_ceefax_store"):
            app[CEEFAX_STORE_KEY] = CeefaxStore()
        register_ceefax_routes(app, app[CEEFAX_STORE_KEY])
        log.debug("Ceefax Teletext (uCode) registered")
    except ImportError as e:
        log.debug("Ceefax not available: %s", e)

    # ── uCode Surface extensions: BBCSDL Bridge ────────────────────
    try:
        from ..ucode.bbcsdl import register_bbcsdl_routes
        if not hasattr(app, "_ceefax_store"):
            from ..ucode.ceefax import CeefaxStore
            app[CEEFAX_STORE_KEY] = CeefaxStore()
        register_bbcsdl_routes(app, app[CEEFAX_STORE_KEY])
        log.debug("BBCSDL (uCode) registered")
    except ImportError as e:
        log.debug("BBCSDL not available: %s", e)

    # ── Terminal Runtime Bridge ────────────────────────────────────
    try:
        from .terminal_runtime import register_terminal_runtime_routes
        register_terminal_runtime_routes(app)
        log.debug("Terminal runtime bridge registered")
    except ImportError as e:
        log.debug("Terminal runtime bridge not available: %s", e)

    # ── Dashboard Surface ──────────────────────────────────────────
    try:
        from ..surfaces.dashboard import DashboardStore, register_dashboard_routes
        if not hasattr(app, "_dashboard_store"):
            app[DASHBOARD_STORE_KEY] = DashboardStore()
        register_dashboard_routes(app, app[DASHBOARD_STORE_KEY])
        log.debug("Dashboard surface registered")
    except ImportError as e:
        log.debug("Dashboard not available: %s", e)

    # ── Documentation Surface ────────────────────────────────────
    try:
        from ..surfaces.documentation_api import register_documentation_routes
        register_documentation_routes(app)
        log.debug("Documentation surface registered")
    except ImportError as e:
        log.debug("Documentation surface not available: %s", e)

    # ── Server Surface ────────────────────────────────────────────
    try:
        from ..surfaces.server import ServerStore, register_server_routes
        if not hasattr(app, "_server_store"):
            app["_server_store"] = ServerStore()
        register_server_routes(app, app["_server_store"])
        log.debug("Server surface registered")
    except ImportError as e:
        log.debug("Server surface not available: %s", e)

    # ── System Surface API ────────────────────────────────────────
    try:
        from ..surfaces.system_api import register_system_api_routes
        register_system_api_routes(app)
        log.debug("System surface API registered")
    except ImportError as e:
        log.debug("System surface API not available: %s", e)

    # ── Library Index (unified vault search) ────────────────────────
    try:
        from .library import register_library_routes
        register_library_routes(app)
        log.debug("Library index routes registered")
    except ImportError as e:
        log.debug("Library routes not available: %s", e)

    # ── Vault Topology (vault layer config for frontend) ────────────
    try:
        from .vault_api import register_vault_routes
        register_vault_routes(app)
        log.debug("Vault topology routes registered")
    except ImportError as e:
        log.debug("Vault topology routes not available: %s", e)

    # ── Catalog Service (skills, MCP servers, LLMs) ──────────────────
    try:
        from .catalog import setup_routes as setup_catalog_routes
        setup_catalog_routes(app)
        log.debug("Catalog API routes registered")
    except ImportError as e:
        log.debug("Catalog routes not available: %s", e)

    # ── Hivemind Knowledge Layer ─────────────────────────────────────
    try:
        from .hivemind_knowledge import setup_routes as setup_hivemind_knowledge_routes
        setup_hivemind_knowledge_routes(app)
        log.debug("Hivemind knowledge layer routes registered")
    except ImportError as e:
        log.debug("Hivemind knowledge routes not available: %s", e)

    # ── Dev Layer API (Dev Mode toggle) ─────────────────────────────
    try:
        from .dev_layer_api import register_dev_layer_routes
        register_dev_layer_routes(app)
        log.debug("Dev Layer API routes registered")
    except ImportError as e:
        log.debug("Dev Layer routes not available: %s", e)

    # ── Tasker API (backend data for Kanban) ─────────────────────────
    try:
        from .tasker_api import handle_workflow_tasks, register_tasker_routes
        register_tasker_routes(app)
        # Workflow-specific filtered task endpoint
        app.router.add_get("/api/workflow/tasks", handle_workflow_tasks)
        log.debug("Tasker API routes registered (incl. /api/workflow/tasks)")
    except ImportError as e:
        log.debug("Tasker API routes not available: %s", e)

    # ── Feed API (unified incoming data layer) ────────────────────────
    try:
        from .feed_api import register_feed_routes
        register_feed_routes(app)
        log.debug("Feed API routes registered")
    except ImportError as e:
        log.debug("Feed API routes not available: %s", e)

    # ── Control Panel API (unified ecosystem status) ──────────────────
    try:
        from .control_api import register_control_routes
        register_control_routes(app)
        log.debug("Control Panel API routes registered")
    except ImportError as e:
        log.debug("Control Panel routes not available: %s", e)

    # ── Surface Registry API ───────────────────────────────────────────
    try:
        from .surface_registry_api import register_surface_routes
        register_surface_routes(app)
        log.debug("Surface Registry API routes registered")
    except ImportError as e:
        log.debug(
            "Surface Registry routes not available: %s", e,
        )

    # ── Template (Slate) API ──────────────────────────────────────────
    try:
        from .template_api import register_template_routes
        register_template_routes(app)
        log.debug("Template (Slate) API routes registered")
    except ImportError as e:
        log.debug("Template API routes not available: %s", e)
