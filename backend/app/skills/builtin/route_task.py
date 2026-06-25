"""route_task — Intelligently route and optionally execute tasks with AI.

Operationalizes the cost strategy:
  simple  → Ollama (free, local)
  medium  → OpenRouter/o3-mini (mid-range, ~$0.01/task)
  complex → Claude/OpenRouter (expensive, intentional)

Features:
  - Auto-detect task complexity from description
  - Budget-aware routing (respects monthly/model limits)
  - Optional execution through provider_router
  - Context size and risk level heuristics
  - Routing decision logging to spool

Usage:
  POST /api/skills/route_task/run
  Body: {
    "task": "fix a typo in README",
    "complexity": "auto",
    "execute": false,
    "context_size": "small",
    "risk_level": "low"
  }
"""
from __future__ import annotations

from app.skills.base import BaseSkill, SkillMeta, SkillParam


class RouteTask(BaseSkill):
    meta = SkillMeta(
        id="route_task",
        name="Route Task",
        description="Route and optionally execute tasks to the best AI provider",
        category="assist",
        timeout=30,
        params=[
            SkillParam(
                name="task",
                type="string",
                required=True,
                description="Task description or query",
            ),
            SkillParam(
                name="complexity",
                type="string",
                required=False,
                default="auto",
                description="Complexity: auto, simple, medium, complex",
            ),
            SkillParam(
                name="context_size",
                type="string",
                required=False,
                default="small",
                description="Context: small (<2K), medium (2K-100K), large (>100K)",
            ),
            SkillParam(
                name="risk_level",
                type="string",
                required=False,
                default="low",
                description="Risk level: low, medium, high (security/safety)",
            ),
            SkillParam(
                name="execute",
                type="boolean",
                required=False,
                default=False,
                description="Execute the task immediately (vs advice-only)",
            ),
        ],
        requires_confirmation=True,
    )

    def _estimate_complexity(self, task: str) -> str:
        """Auto-detect complexity from task description."""
        task_lower = task.lower()

        # Complex indicators
        complex_signals = [
            "security", "vulnerability", "exploit", "race condition",
            "deadlock", "concurrency", "encryption", "cryptography",
            "refactor", "architecture", "design pattern", "distributed",
            "performance optimization", "memory leak", "thread safety",
            "authentication", "authorization", "zero-day",
            "complicated", "intricate", "nuanced", "subtle bug",
        ]
        # Medium indicators
        medium_signals = [
            "implement", "feature", "endpoint", "api", "route",
            "component", "module", "integration", "database",
            "migration", "schema", "query", "test", "coverage",
            "debug", "fix bug", "error handling", "validation",
        ]

        for signal in complex_signals:
            if signal in task_lower:
                return "complex"
        for signal in medium_signals:
            if signal in task_lower:
                return "medium"

        # Check length: longer descriptions are more complex
        if len(task) > 200:
            return "medium"

        return "simple"

    def _estimate_risk(
        self,
        task: str,
        complexity: str,
    ) -> str:
        """Estimate risk level from task description."""
        task_lower = task.lower()

        high_risk_signals = [
            "security", "vulnerability", "exploit", "private key",
            "password", "token", "credential", "hack", "breach",
            "delete", "drop database", "truncate", "production",
            "critical infrastructure", "zero-day", "malware",
        ]
        for signal in high_risk_signals:
            if signal in task_lower:
                return "high"

        if complexity == "complex":
            return "medium"

        return "low"

    def _estimate_context_size(self, task: str) -> str:
        """Estimate required context size from task."""
        if len(task) > 10000:
            return "large"
        if len(task) > 2000:
            return "medium"
        return "small"

    def _build_routing(
        self,
        complexity: str,
        context_size: str,
        risk_level: str,
        budget_remaining: float = 100.0,
    ) -> dict:
        """Build routing decision considering cost, context, risk, budget."""
        cost_table = {
            "simple": {
                "provider": "ollama",
                "model": "qwen2.5-coder:3b",
                "cost": "$0 (local)",
                "reason": "Simple task — use local free model",
                "tokens_per_second": "~40",
            },
            "medium": {
                "provider": "openrouter",
                "model": "deepseek/deepseek-chat",
                "cost": "~$0.01/task (low)",
                "reason": "Medium task — cost-effective cloud model",
                "tokens_per_second": "~60",
            },
            "complex": {
                "provider": "openrouter",
                "model": "anthropic/claude-opus",
                "cost": "~$0.15/task (high)",
                "reason": "Complex task — best reasoning available",
                "tokens_per_second": "~30",
            },
        }

        # Start with base routing
        routing = cost_table.get(complexity, cost_table["simple"])

        # Context size adjustments
        if context_size == "large":
            routing = {
                "provider": "openrouter",
                "model": "google/gemini-2.5-flash-001",
                "cost": "~$0.005/100K tokens (cheap for large context)",
                "reason": f"Large context — use Gemini for 1M token window",
                "tokens_per_second": "~50",
            }

        # Risk level adjustments
        if risk_level == "high":
            routing = {
                "provider": "ollama",
                "model": "qwen2.5-coder:7b",
                "cost": "$0 (local, no data leakage)",
                "reason": "High-risk task — keep local to prevent exposure",
                "tokens_per_second": "~20",
            }

        # Budget-aware fallback
        if budget_remaining < 1.0:
            routing = {
                "provider": "ollama",
                "model": "qwen2.5-coder:3b",
                "cost": "$0 (local, budget constrained)",
                "reason": "Budget exhausted — fall back to local model",
                "tokens_per_second": "~40",
            }

        return routing

    async def run(self, **kwargs) -> dict:
        task = kwargs.get("task", "").strip()
        complexity = kwargs.get("complexity", "auto").strip().lower()
        context_size = kwargs.get("context_size", "").strip().lower()
        risk_level = kwargs.get("risk_level", "low").strip().lower()
        execute = kwargs.get("execute", False)

        if not task:
            return {
                "success": False,
                "error": "task description is required",
            }

        # Auto-detect
        if complexity == "auto":
            complexity = self._estimate_complexity(task)
        if not context_size:
            context_size = self._estimate_context_size(task)
        if risk_level not in ("low", "medium", "high"):
            risk_level = self._estimate_risk(task, complexity)

        # Validate
        valid_complexity = ["simple", "medium", "complex"]
        valid_risk = ["low", "medium", "high"]
        valid_context = ["small", "medium", "large"]
        if complexity not in valid_complexity:
            complexity = "simple"
        if risk_level not in valid_risk:
            risk_level = "low"
        if context_size not in valid_context:
            context_size = "small"

        # Record detected/normalized complexity for observability/tests
        detected_complexity = complexity

        # Check budget (if execute requested)
        budget_remaining = 100.0
        try:
            from app.services.budget_manager import BudgetManager
            budget_mgr = BudgetManager()
            usage = budget_mgr.get_monthly_usage()
            budget_remaining = usage.get("remaining_budget", 100.0)
        except Exception:
            pass

        # Generate routing
        routing = self._build_routing(
            complexity,
            context_size,
            risk_level,
            budget_remaining=budget_remaining,
        )

        result = {
            "success": True,
            "task": task[:100] + ("..." if len(task) > 100 else ""),
            "analysis": {
                "complexity": complexity,
                "detected_complexity": detected_complexity,
                "context_size": context_size,
                "risk_level": risk_level,
                "task_length": len(task),
            },
            "routing": routing,
            "execution": {
                "mode": "execute" if execute else "advice-only",
                "budget_remaining": budget_remaining,
            },
        }

        # Strategy breakdown for multi-tier routing (used by tests)
        def _build_strategy(detected: str) -> dict:
            if detected == "simple":
                tiers = {"simple": 0.8, "medium": 0.15, "complex": 0.05}
            elif detected == "medium":
                tiers = {"simple": 0.2, "medium": 0.7, "complex": 0.1}
            else:
                tiers = {"simple": 0.1, "medium": 0.2, "complex": 0.7}
            return {"tier_allocations": tiers, "notes": f"Strategy for {detected} tasks"}

        result["strategy"] = _build_strategy(detected_complexity)

        # Execute if requested
        if execute:
            result["execution"]["response"] = await self._execute_task(
                task,
                routing,
            )

        return result

    async def _execute_task(
        self,
        task: str,
        routing: dict,
    ) -> dict:
        """Execute the task through the routed provider."""
        try:
            from app.services.provider_router import ProviderRouter
            router = ProviderRouter()
            provider = routing.get("provider", "ollama")
            model = routing.get("model", "")

            response = await router.chat(
                messages=[{"role": "user", "content": task}],
                provider=provider,
                model=model,
                timeout=30,
            )
            return response
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }
