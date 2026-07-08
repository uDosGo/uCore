"""Roundtable Dispatch Skill — parallel specialized agent execution.

Takes a task, determines which specialized agents are needed based on
the agents.yaml routing matrix, dispatches to them concurrently via
the Roundtable integration, and collects/aggregates results.

Agent mapping (from agents.yaml):
  architect    — system design, high-level planning
  dev          — implementation, coding
  reviewer     — code review, quality analysis
  debugger     — bug fixing, troubleshooting
  docgen       — documentation generation
  gridsmith-dev — grid-based UI development

Integrates with: Roundtable integration, agents.yaml, Hivemind server.
"""
from __future__ import annotations

import asyncio
import json
import logging
import urllib.request
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.roundtable_dispatch")

ROUNDTABLE_URL = "http://localhost:8490/api/hivemind/roundtable"
AGENT_CONFIG = {
    "architect": {
        "model": "glm-5.1",
        "provider": "openrouter",
        "capabilities": ["design", "architecture", "planning"],
    },
    "dev": {
        "model": "qwen2.5-coder:7b",
        "provider": "ollama",
        "capabilities": ["implementation", "coding", "testing"],
    },
    "reviewer": {
        "model": "claude-opus-4.7",
        "provider": "openrouter",
        "capabilities": ["review", "security", "quality"],
    },
    "debugger": {
        "model": "deepseek-v4-flash",
        "provider": "openrouter",
        "capabilities": ["debugging", "analysis", "troubleshooting"],
    },
    "docgen": {
        "model": "qwen3.6-27b",
        "provider": "openrouter",
        "capabilities": ["documentation", "writing", "clarity"],
    },
    "gridsmith-dev": {
        "model": "qwen2.5-coder:3b",
        "provider": "ollama",
        "capabilities": ["worldbuild", "grid", "spatial"],
    },
}


class RoundtableDispatchSkill(BaseSkill):
    """Dispatch tasks to parallel specialized agents via Roundtable."""

    meta = SkillMeta(
        id="roundtable-dispatch",
        name="Roundtable Dispatch",
        description=(
            "Dispatch tasks to parallel specialized agents"
            " via Roundtable. Collects and aggregates results."
        ),
        category="assist",
        timeout=180,
        params=[
            SkillParam(
                name="task",
                type="string",
                required=True,
                description="Task description to dispatch",
            ),
            SkillParam(
                name="agents",
                type="string",
                required=False,
                default="auto",
                description=(
                    "Comma-separated agent list or 'auto' for routing."
                    " Options: architect, dev, reviewer, debugger,"
                    " docgen, gridsmith-dev"
                ),
            ),
            SkillParam(
                name="mode",
                type="string",
                required=False,
                default="parallel",
                description=(
                    "Execution mode: 'parallel' (concurrent) or"
                    " 'sequential' (chain: design → implement → review)"
                ),
            ),
            SkillParam(
                name="context",
                type="string",
                required=False,
                default="",
                description="Additional context for the task",
            ),
        ],
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        task = kwargs.get("task", "").strip()
        agents_str = kwargs.get("agents", "auto")
        mode = kwargs.get("mode", "parallel")
        context = kwargs.get("context", "")

        if not task:
            return {"success": False, "error": "task is required"}

        # Resolve agents
        if agents_str == "auto":
            agent_list = self._auto_select_agents(task)
        else:
            agent_list = [
                a.strip() for a in agents_str.split(",")
                if a.strip() in AGENT_CONFIG
            ]

        if not agent_list:
            agent_list = ["dev"]  # fallback

        # Check Roundtable health
        if not await self._roundtable_available():
            return {
                "success": False,
                "error": "Roundtable not available on port 8490",
                "agents_resolved": agent_list,
                "fallback": "Use hivemind-consensus or route_task instead",
            }

        if mode == "sequential":
            result = await self._dispatch_sequential(
                task, agent_list, context
            )
        else:
            result = await self._dispatch_parallel(
                task, agent_list, context
            )

        return {
            "success": True,
            "action": "roundtable-dispatch",
            "mode": mode,
            "agents_dispatched": agent_list,
            "results": result,
        }

    def _auto_select_agents(self, task: str) -> list[str]:
        """Auto-select agents based on task content."""
        task_lower = task.lower()
        agents = []

        # Architecture signals
        if any(w in task_lower for w in [
            "architect", "design", "refactor", "restructure",
            "plan", "system", "module boundary", "pattern",
        ]):
            agents.append("architect")

        # Implementation signals
        if any(w in task_lower for w in [
            "implement", "build", "create", "add", "feature",
            "code", "function", "component", "write",
        ]):
            agents.append("dev")

        # Review signals
        if any(w in task_lower for w in [
            "review", "audit", "check", "validate", "verify",
            "security", "quality", "standard",
        ]):
            agents.append("reviewer")

        # Debug signals
        if any(w in task_lower for w in [
            "bug", "fix", "debug", "error", "crash", "trace",
            "broken", "failed", "exception",
        ]):
            agents.append("debugger")

        # Documentation signals
        if any(w in task_lower for w in [
            "document", "doc", "readme", "comment", "guide",
            "explain", "describe",
        ]):
            agents.append("docgen")

        # Default to dev if nothing matched
        if not agents:
            agents = ["dev"]

        return agents[:3]  # max 3 agents for auto-select

    async def _roundtable_available(self) -> bool:
        """Check if Roundtable is reachable."""
        try:
            req = urllib.request.Request(
                ROUNDTABLE_URL, method="GET",
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status < 400
        except Exception:
            return False

    async def _dispatch_parallel(
        self, task: str, agents: list[str], context: str,
    ) -> dict[str, Any]:
        """Dispatch task to all agents concurrently."""
        async_tasks = []
        for agent_id in agents:
            async_tasks.append(
                self._call_agent(agent_id, task, context)
            )
        results_list = await asyncio.gather(*async_tasks, return_exceptions=True)

        results: dict[str, Any] = {}
        for agent_id, res in zip(agents, results_list):
            if isinstance(res, Exception):
                results[agent_id] = {
                    "success": False,
                    "error": str(res),
                }
            else:
                results[agent_id] = res

        return results

    async def _dispatch_sequential(
        self, task: str, agents: list[str], context: str,
    ) -> dict[str, Any]:
        """Dispatch task sequentially, each agent builds on previous."""
        results: dict[str, Any] = {}
        accumulated = context

        for agent_id in agents:
            res = await self._call_agent(
                agent_id, task, accumulated,
            )
            results[agent_id] = res
            if isinstance(res, dict) and res.get("output"):
                accumulated += f"\n\n[{agent_id}] {res.get('output', '')}"

        return results

    async def _call_agent(
        self, agent_id: str, task: str, context: str,
    ) -> dict:
        """Call a single agent through Roundtable."""
        config = AGENT_CONFIG.get(agent_id, {})
        payload = {
            "agent": agent_id,
            "task": task,
            "context": context,
            "model": config.get("model", ""),
            "provider": config.get("provider", ""),
        }
        body = json.dumps(payload).encode("utf-8")

        # Try Roundtable dispatch endpoint
        try:
            req = urllib.request.Request(
                f"{ROUNDTABLE_URL}/dispatch",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "agent": agent_id,
                "note": "Roundtable dispatch failed — agent may be offline",
            }
