"""Enhanced Flow Router — Mission-aware multi-stage routing.

Integrates API Registry, Quality Scorer, Budget Manager,
Agent Specialization, and Secret Store.

Usage:
    router = EnhancedFlowRouter()
    result = await router.execute(
        task_type="review",
        task_summary="Review the new auth module",
    )
"""
from __future__ import annotations

import logging
import time
from typing import Any

log = logging.getLogger("ucore.enhanced_router")


class EnhancedFlowRouter:
    """Mission-aware multi-stage AI flow router."""

    QUALITY_THRESHOLD = 0.6
    MAX_RETRIES = 2

    def __init__(self) -> None:
        self._api_registry = None
        self._quality_scorer = None
        self._budget_manager = None
        self._agent_registry = None
        self._provider_router = None

    def _get_api_registry(self):
        if self._api_registry is None:
            from app.services.api_registry import ApiRegistry
            self._api_registry = ApiRegistry.get()
        return self._api_registry

    def _get_quality_scorer(self):
        if self._quality_scorer is None:
            from app.services.quality_scorer import QualityScorer
            self._quality_scorer = QualityScorer.get()
        return self._quality_scorer

    def _get_budget_manager(self):
        if self._budget_manager is None:
            from app.services.budget_manager import BudgetManager
            self._budget_manager = BudgetManager.get()
        return self._budget_manager

    def _get_agent_registry(self):
        if self._agent_registry is None:
            from app.services.agent_specialization import SpecializedAgentRegistry
            self._agent_registry = SpecializedAgentRegistry()
        return self._agent_registry

    def _get_provider_router(self):
        if self._provider_router is None:
            from app.services.provider_router import get_router
            self._provider_router = get_router()
        return self._provider_router

    async def execute(
        self,
        task_type: str,
        task_summary: str = "",
        context: dict[str, Any] | None = None,
        complexity: str = "medium",
    ) -> dict[str, Any]:
        """Execute a multi-stage flow for the given task."""
        context = context or {}
        registry = self._get_agent_registry()
        workflow = registry.plan_workflow(task_type, complexity, task_summary)
        stages = workflow.get("stages", [])

        if not stages:
            return {"status": "error", "error": "No workflow stages found"}

        results: list[dict[str, Any]] = []
        final_output = ""

        for stage in stages:
            stage_role = stage.get("role", "dev")
            stage_title = stage.get("title", stage_role)
            agent_info = stage.get("agent", {})
            agent_id = agent_info.get("id", stage_role)

            log.info("Flow stage: %s (agent=%s)", stage_title, agent_id)

            stage_result = await self._execute_stage(
                agent_id=agent_id,
                task_type=task_type,
                task_summary=task_summary,
                context=context,
                stage_title=stage_title,
            )
            results.append(stage_result)

            if stage_result.get("status") == "error":
                return {
                    "status": "error",
                    "stage": stage_title,
                    "error": stage_result.get("error"),
                    "stages_completed": len(results) - 1,
                    "results": results,
                }
            final_output = stage_result.get("output", "")

        return {
            "status": "completed",
            "workflow_id": workflow.get("workflow_id"),
            "workflow_name": workflow.get("name"),
            "stages_completed": len(results),
            "results": results,
            "output": final_output,
        }

    async def _execute_stage(
        self,
        agent_id: str,
        task_type: str,
        task_summary: str,
        context: dict[str, Any],
        stage_title: str,
    ) -> dict[str, Any]:
        """Execute a single flow stage with retry logic."""
        registry = self._get_agent_registry()
        agent = registry.get_agent(agent_id)

        if agent is None:
            return {"status": "error", "error": f"Agent '{agent_id}' not found"}

        model_var = self._get_model_variable(agent)
        api_registry = self._get_api_registry()
        resolved = api_registry.resolve(model_var, timeout=agent.timeout)

        if resolved is None:
            return {
                "status": "error",
                "error": f"Could not resolve: {model_var}",
            }

        budget = self._get_budget_manager()
        estimated_cost = agent.cost_per_task
        if not budget.can_spend(agent_id, estimated_cost, task_type):
            resolved_free = api_registry.resolve("${local:any}")
            if resolved_free is None:
                return {
                    "status": "error",
                    "error": "Budget exhausted, no free tier",
                }
            resolved = resolved_free
            estimated_cost = 0.0

        prompt = self._build_prompt(agent, task_summary, context, stage_title)
        last_error = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                result = await self._call_provider(
                    resolved, prompt, agent.timeout,
                )

                if result.get("error"):
                    last_error = result["error"]
                    if attempt < self.MAX_RETRIES:
                        premium = api_registry.resolve("${premium:any}")
                        if premium:
                            resolved = premium
                    continue

                scorer = self._get_quality_scorer()
                score = scorer.score_response(
                    task_type=task_type,
                    model=resolved.model,
                    provider=resolved.provider,
                    prompt=prompt,
                    response=result.get("content", ""),
                    latency_ms=result.get("latency_ms", 0),
                    cost_usd=estimated_cost,
                    cost_tier=resolved.cost_tier,
                )

                budget.record_spend(
                    agent_id=agent_id,
                    cost=estimated_cost,
                    model=resolved.model,
                    provider=resolved.provider,
                    task_type=task_type,
                    cost_tier=resolved.cost_tier,
                )

                return {
                    "status": "ok",
                    "stage": stage_title,
                    "agent": agent_id,
                    "model": resolved.model,
                    "provider": resolved.provider,
                    "cost_tier": resolved.cost_tier,
                    "cost_usd": estimated_cost,
                    "quality_score": score,
                    "output": result.get("content", ""),
                }
            except Exception as e:
                last_error = str(e)
                log.error("Stage %s error: %s", stage_title, last_error)

        return {"status": "error", "error": f"Retries exhausted: {last_error}"}

    def _get_model_variable(self, agent) -> str:
        registry = self._get_api_registry()
        if registry.is_variable(agent.model):
            return agent.model
        cost = agent.cost_per_task
        if cost == 0.0:
            return "${local:any}"
        elif cost <= 0.01:
            return "${ultra-cheap:any}"
        elif cost <= 0.05:
            return "${budget:any}"
        elif cost <= 0.10:
            return "${primary:any}"
        else:
            return "${premium:any}"

    def _build_prompt(self, agent, task_summary, context, stage_title):
        parts = [
            f"<system>{agent.system_prompt}</system>",
            f"<task>{task_summary}</task>",
            f"<stage>{stage_title}</stage>",
        ]
        if context.get("files"):
            files_str = "\n".join(f"  - {f}" for f in context["files"])
            parts.append(f"<files>\n{files_str}\n</files>")
        if context.get("previous_output"):
            prev = context["previous_output"]
            parts.append(f"<previous_output>{prev}</previous_output>")
        return "\n\n".join(parts)

    async def _call_provider(self, resolved, prompt, timeout):
        router = self._get_provider_router()
        messages = [{"role": "user", "content": prompt}]
        started = time.perf_counter()
        result = await router.chat(
            messages=messages,
            provider=resolved.provider,
            model=resolved.model,
            timeout=timeout,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        result["latency_ms"] = round(elapsed_ms, 1)
        return result
