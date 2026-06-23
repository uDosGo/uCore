"""Ollama and Specialized Agents aiohttp handlers."""
from __future__ import annotations

import logging
from aiohttp import web

log = logging.getLogger("ucore")


async def handle_ollama_status(request: web.Request) -> web.Response:
    """GET /api/ollama/status — Get Ollama instance status and model list."""
    try:
        from app.api.ollama import get_ollama_status
        status = await get_ollama_status()
        return web.json_response(status)
    except Exception as e:
        log.error(f"Failed to get Ollama status: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_ollama_models_available(request: web.Request) -> web.Response:
    """GET /api/ollama/models/available — List models available to pull."""
    try:
        from app.api.ollama import get_available_models
        models = await get_available_models()
        return web.json_response(models)
    except Exception as e:
        log.error(f"Failed to get available models: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_ollama_performance(request: web.Request) -> web.Response:
    """GET /api/ollama/performance — Get model performance stats."""
    try:
        from app.api.ollama import get_ollama_model_performance
        stats = await get_ollama_model_performance()
        return web.json_response(stats)
    except Exception as e:
        log.error(f"Failed to get model performance: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_agents_spec_list(request: web.Request) -> web.Response:
    """GET /api/agents/spec/list — List all specialized agents."""
    try:
        from app.services.agent_specialization import SpecializedAgentRegistry
        registry = SpecializedAgentRegistry()
        agents = registry.list_agents()

        return web.json_response({
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "model": agent.model,
                    "provider": agent.provider,
                    "capabilities": agent.capabilities,
                    "cost_per_task": agent.cost_per_task,
                    "timeout": agent.timeout,
                    "priority": agent.priority,
                }
                for agent in agents
            ]
        })
    except Exception as e:
        log.error(f"Failed to list agents: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_agents_spec_get(request: web.Request) -> web.Response:
    """GET /api/agents/spec/get/{agent_id} — Get specific agent config."""
    try:
        agent_id = request.match_info.get("agent_id", "")
        if not agent_id:
            return web.json_response(
                {"error": "agent_id required"},
                status=400,
            )

        from app.services.agent_specialization import SpecializedAgentRegistry
        registry = SpecializedAgentRegistry()
        agent = registry.get_agent(agent_id)

        if not agent:
            return web.json_response(
                {"error": f"Agent {agent_id} not found"},
                status=404,
            )

        return web.json_response({
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "model": agent.model,
            "provider": agent.provider,
            "system_prompt": agent.system_prompt,
            "capabilities": agent.capabilities,
            "cost_per_task": agent.cost_per_task,
            "timeout": agent.timeout,
            "priority": agent.priority,
        })
    except Exception as e:
        log.error(f"Failed to get agent: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_agents_spec_route(request: web.Request) -> web.Response:
    """POST /api/agents/spec/route — Route task to specialized agent."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    try:
        task_type = body.get("task_type", "implement")
        complexity = body.get("complexity", "medium")
        messages = body.get("messages", [])
        task = body.get("task", "")
        workflow_stage = body.get("workflow_stage")
        plan_only = bool(body.get("plan_only", False))

        from app.services.agent_specialization import SpecializedAgentRegistry
        from app.services.provider_router import get_router

        registry = SpecializedAgentRegistry()
        workflow = registry.plan_workflow(
            task_type=task_type,
            complexity=complexity,
            task_summary=task,
            requested_stage=workflow_stage,
        )
        active_agent = registry.get_agent(
            workflow["active_stage"]["agent"]["id"]
        )
        if active_agent is None:
            active_agent = registry.get_best_agent_for_task(
                task_type,
                complexity,
            )

        if plan_only:
            return web.json_response({
                "success": True,
                "workflow": workflow,
            })

        log.info(
            f"Routing task (type={task_type}, complexity={complexity}) "
            f"to agent {active_agent.id}"
        )

        router = get_router()
        response = await router.chat(
            messages=messages,
            provider=active_agent.provider,
            model=active_agent.model,
            timeout=active_agent.timeout,
        )

        return web.json_response({
            "success": True,
            "agent": {
                "id": active_agent.id,
                "name": active_agent.name,
                "model": active_agent.model,
                "provider": active_agent.provider,
            },
            "routing": {
                "task_type": task_type,
                "complexity": complexity,
            },
            "workflow": workflow,
            "response": response,
            "cost": active_agent.cost_per_task,
        })
    except Exception as e:
        log.error(f"Failed to route task: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_agents_spec_plan(request: web.Request) -> web.Response:
    """POST /api/agents/spec/plan — Build a workflow plan only."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    try:
        task_type = body.get("task_type", "implement")
        complexity = body.get("complexity", "medium")
        task = body.get("task", "")
        workflow_stage = body.get("workflow_stage")

        from app.services.agent_specialization import SpecializedAgentRegistry

        registry = SpecializedAgentRegistry()
        workflow = registry.plan_workflow(
            task_type=task_type,
            complexity=complexity,
            task_summary=task,
            requested_stage=workflow_stage,
        )

        return web.json_response({
            "success": True,
            "workflow": workflow,
            "surface_taxonomy": registry.get_surface_taxonomy(),
        })
    except Exception as e:
        log.error(f"Failed to plan workflow: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_agents_spec_capability(request: web.Request) -> web.Response:
    """GET /api/agents/spec/capability/{capability}.

    Return agents matching the requested capability.
    """
    try:
        capability = request.match_info.get("capability", "")
        if not capability:
            return web.json_response(
                {"error": "capability required"},
                status=400,
            )

        from app.services.agent_specialization import SpecializedAgentRegistry
        registry = SpecializedAgentRegistry()
        agents = registry.get_agents_for_capability(capability)

        return web.json_response({
            "capability": capability,
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "model": agent.model,
                    "provider": agent.provider,
                }
                for agent in agents
            ],
        })
    except Exception as e:
        log.error(f"Failed to get agents for capability: {e}")
        return web.json_response({"error": str(e)}, status=500)
