"""Specialized Agents API — Agent configuration and routing endpoints."""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException

log = logging.getLogger(__name__)

from app.services.agent_specialization import SpecializedAgentRegistry
from app.services.provider_router import ProviderRouter

router = APIRouter(prefix="/api/agents/spec", tags=["agents-specialized"])


@router.get("/list")
async def list_specialized_agents():
    """Get all configured specialized agents."""
    try:
        registry = SpecializedAgentRegistry()
        agents = registry.list_agents()

        return {
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
        }
    except Exception as e:
        log.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific agent's configuration."""
    try:
        registry = SpecializedAgentRegistry()
        agent = registry.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        return {
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
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route")
async def route_to_specialized_agent(
    task_type: str,
    complexity: str = "medium",
    messages: list[dict] = None,
):
    """
    Route a task to the best specialized agent and execute it.

    Args:
        task_type: Type of task (design, implement, review, debug, document)
        complexity: Task complexity (low, medium, high)
        messages: Chat messages to send to the agent

    Returns:
        Agent response with routing metadata
    """
    try:
        if not messages:
            messages = []

        registry = SpecializedAgentRegistry()
        agent = registry.get_best_agent_for_task(task_type, complexity)

        log.info(
            f"Routing task (type={task_type}, complexity={complexity}) to agent {agent.id}"
        )

        # Use provider router to execute through the agent's configured provider/model
        provider_router = ProviderRouter()
        response = await provider_router.chat(
            messages=messages,
            provider=agent.provider,
            model=agent.model,
            timeout=agent.timeout,
        )

        return {
            "success": True,
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "model": agent.model,
                "provider": agent.provider,
            },
            "routing": {
                "task_type": task_type,
                "complexity": complexity,
            },
            "response": response,
            "cost": agent.cost_per_task,
        }
    except Exception as e:
        log.error(f"Failed to route task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capability/{capability}")
async def agents_with_capability(capability: str):
    """Get all agents that have a specific capability."""
    try:
        registry = SpecializedAgentRegistry()
        agents = registry.get_agents_for_capability(capability)

        return {
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
        }
    except Exception as e:
        log.error(f"Failed to get agents for capability {capability}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
