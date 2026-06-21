"""route_task — Intelligently route tasks to the best provider.

Operationalizes the cost strategy:
  simple  → Ollama (free, local)
  medium  → Roundtable/Codex (mid-range)
  complex → Claude/OpenRouter (expensive, intentional)

Usage:
  POST /api/skills/route_task/run
  Body: { "task": "fix a typo in README", "complexity": "simple" }
"""
from __future__ import annotations

from app.skills.base import BaseSkill, SkillMeta, SkillParam


class RouteTask(BaseSkill):
    meta = SkillMeta(
        id="route_task",
        name="Route Task",
        description="Route a task to the best AI provider based on complexity and cost strategy",
        category="assist",
        timeout=15,
        params=[
            SkillParam(
                name="task",
                type="string",
                required=True,
                description="Description of the task to route",
            ),
            SkillParam(
                name="complexity",
                type="string",
                required=False,
                default="auto",
                description="Task complexity: auto, simple, medium, complex",
            ),
            SkillParam(
                name="context_size",
                type="string",
                required=False,
                default="small",
                description="Context size: small (<2K tokens), medium (2K-100K), large (>100K)",
            ),
        ],
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

    def _build_routing(self, complexity: str, context_size: str) -> dict:
        """Build routing decision based on cost strategy."""
        cost_table = {
            "simple": {
                "provider": "ollama",
                "model": "qwen2.5-coder:7b",
                "cost": "$0 (local)",
                "reason": "Simple task — use local free model",
                "tokens_per_second": "~40",
            },
            "medium": {
                "provider": "openrouter",
                "model": "openai/o3-mini",
                "cost": "~$0.01/task (low)",
                "reason": "Medium task — use cost-effective cloud model",
                "tokens_per_second": "~60",
            },
            "complex": {
                "provider": "openrouter",
                "model": "anthropic/claude-sonnet-4-20250514",
                "cost": "~$0.15/task (high — use sparingly)",
                "reason": "Complex task — best reasoning available",
                "tokens_per_second": "~30",
            },
        }

        # Context size adjustments
        if context_size == "large" and complexity != "complex":
            # Route large-context tasks to Gemini (cheaper for big context)
            return {
                "provider": "openrouter",
                "model": "google/gemini-2.5-flash-001",
                "cost": "~$0.005/100K tokens (cheap for large context)",
                "reason": f"Large context ({context_size}) — use Gemini for 1M token window",
                "tokens_per_second": "~50",
            }

        return cost_table.get(complexity, cost_table["simple"])

    async def run(self, **kwargs) -> dict:
        task = kwargs.get("task", "").strip()
        complexity = kwargs.get("complexity", "auto").strip().lower()
        context_size = kwargs.get("context_size", "small").strip().lower()

        if not task:
            return {
                "success": False,
                "error": "task description is required",
            }

        # Auto-detect if requested
        if complexity == "auto":
            complexity = self._estimate_complexity(task)

        # Validate
        valid = ["simple", "medium", "complex"]
        if complexity not in valid:
            complexity = "simple"

        routing = self._build_routing(complexity, context_size)

        return {
            "success": True,
            "task": task[:100] + ("..." if len(task) > 100 else ""),
            "analysis": {
                "detected_complexity": complexity,
                "context_size": context_size,
                "task_length": len(task),
            },
            "routing": routing,
            "strategy": {
                "tier_allocations": {
                    "simple": {"pct": 15, "provider": "Ollama", "cost": "$0"},
                    "medium": {"pct": 70, "provider": "Codex/Roundtable", "cost": "~$0.01"},
                    "complex": {"pct": 5, "provider": "Claude", "cost": "~$0.15"},
                },
                "note": "Use Ollama for 15% of tasks (simple/repetitive), Codex for 70% (daily work), Claude for 5% (hard problems)",
            },
        }
