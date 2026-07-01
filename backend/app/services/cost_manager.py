"""Cost Manager — OpenRouter budget tracking and cost-aware routing.

Tracks per-agent spend, enforces daily/weekly budget caps, and
provides cost estimates to the LLM router for cheapest-model selection.

Data persisted to ~/.ucore/cost_state.json for crash recovery.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.services.cost_manager")

STATE_DIR = Path.home() / ".ucore"
STATE_FILE = STATE_DIR / "cost_state.json"

# Known per-1000-token costs for models used in agents.yaml
# Sources: OpenRouter pricing pages (USD per 1K tokens)
MODEL_COST_PER_1K = {
    # OpenRouter models
    "glm-5.1": {"input": 0.0015, "output": 0.0030},       # architecture
    "claude-opus-4.7": {"input": 0.0150, "output": 0.0750}, # reviewer
    "deepseek-v4-flash": {"input": 0.0005, "output": 0.0015}, # debugger
    "qwen3.6-27b": {"input": 0.0010, "output": 0.0020},     # docgen
    # Ollama (free/local)
    "qwen2.5-coder:3b": {"input": 0.0, "output": 0.0},
    "llama3": {"input": 0.0, "output": 0.0},
    "codellama": {"input": 0.0, "output": 0.0},
    "mistral": {"input": 0.0, "output": 0.0},
    # OpenAI fallback
    "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    "gpt-4o": {"input": 0.0025, "output": 0.0100},
    # Generic catch-all (conservative estimate)
    "__default__": {"input": 0.002, "output": 0.008},
}

DEFAULT_DAILY_BUDGET = 2.00   # $2/day default
DEFAULT_WEEKLY_BUDGET = 10.00  # $10/week default
DEFAULT_MONTHLY_BUDGET = 30.00 # $30/month default


@dataclass
class AgentCostRecord:
    """Running cost record for a single agent session."""

    agent_id: str
    model: str
    tasks_completed: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "model": self.model,
            "tasks_completed": self.tasks_completed,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
        }


@dataclass
class CostState:
    """Persistent cost tracking state."""

    daily_spend: float = 0.0
    weekly_spend: float = 0.0
    monthly_spend: float = 0.0
    last_reset_date: str = ""  # ISO date of last daily reset
    agents: dict[str, AgentCostRecord] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "daily_spend": round(self.daily_spend, 6),
            "weekly_spend": round(self.weekly_spend, 6),
            "monthly_spend": round(self.monthly_spend, 6),
            "last_reset_date": self.last_reset_date,
            "agents": {
                aid: rec.to_dict()
                for aid, rec in self.agents.items()
            },
        }


class CostManager:
    """Budget-enforcing cost tracker for the LLM router.

    Features:
    - Per-agent cost tracking with task counts
    - Daily/weekly/monthly budget enforcement
    - Cheapest-model selection among compatible backends
    - Persistent state via ~/.ucore/cost_state.json
    """

    def __init__(
        self,
        daily_budget: float = DEFAULT_DAILY_BUDGET,
        weekly_budget: float = DEFAULT_WEEKLY_BUDGET,
        monthly_budget: float = DEFAULT_MONTHLY_BUDGET,
    ):
        self._daily_budget = daily_budget
        self._weekly_budget = weekly_budget
        self._monthly_budget = monthly_budget
        self._state = CostState()
        self._load()

    # ── Budget Properties ─────────────────────────────────────

    @property
    def daily_budget(self) -> float:
        return self._daily_budget

    @daily_budget.setter
    def daily_budget(self, value: float) -> None:
        self._daily_budget = max(0.0, value)

    @property
    def weekly_budget(self) -> float:
        return self._weekly_budget

    @property
    def monthly_budget(self) -> float:
        return self._monthly_budget

    # ── Spend Tracking ────────────────────────────────────────

    def record_task(
        self,
        agent_id: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float | None = None,
    ) -> float:
        """Record a task completion and compute/add cost.

        Args:
            agent_id: Agent identifier (from agents.yaml)
            model: Model name used
            prompt_tokens: Input tokens (for accurate costing)
            completion_tokens: Output tokens
            cost: Explicit cost (overrides token-based estimate)

        Returns:
            Actual cost incurred
        """
        self._check_reset()

        # Estimate cost from tokens if not provided
        if cost is None:
            cost = self._estimate_cost(model, prompt_tokens, completion_tokens)

        # Update agent record
        if agent_id not in self._state.agents:
            self._state.agents[agent_id] = AgentCostRecord(
                agent_id=agent_id, model=model,
            )
        record = self._state.agents[agent_id]
        record.tasks_completed += 1
        record.total_tokens += prompt_tokens + completion_tokens
        record.total_cost += cost

        # Update global counters
        self._state.daily_spend += cost
        self._state.weekly_spend += cost
        self._state.monthly_spend += cost

        self._save()
        log.debug(
            "Cost recorded: %s/%s = $%.6f "
            "(daily: $%.4f / $%.2f)",
            agent_id, model, cost,
            self._state.daily_spend, self._daily_budget,
        )
        return cost

    def _estimate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Estimate cost for a model given token counts."""
        rates = MODEL_COST_PER_1K.get(
            model, MODEL_COST_PER_1K["__default__"]
        )
        input_cost = (prompt_tokens / 1000) * rates["input"]
        output_cost = (completion_tokens / 1000) * rates["output"]
        return input_cost + output_cost

    def _check_reset(self) -> None:
        """Reset counters if date has changed."""
        today = date.today().isoformat()
        if self._state.last_reset_date == today:
            return

        # New day — reset daily
        self._state.daily_spend = 0.0
        self._state.last_reset_date = today

        # Check weekly reset (ISO week)
        current_week = date.today().isocalendar()[1]
        if self._last_known_week() != current_week:
            self._state.weekly_spend = 0.0

        # Check monthly reset
        current_month = date.today().month
        if self._last_known_month() != current_month:
            self._state.monthly_spend = 0.0

        self._save()

    def _last_known_week(self) -> int:
        """Get the ISO week number from last reset date."""
        try:
            d = date.fromisoformat(self._state.last_reset_date)
            return d.isocalendar()[1]
        except (ValueError, TypeError):
            return 0

    def _last_known_month(self) -> int:
        """Get the month number from last reset date."""
        try:
            d = date.fromisoformat(self._state.last_reset_date)
            return d.month
        except (ValueError, TypeError):
            return 0

    # ── Budget Enforcement ───────────────────────────────────

    def budget_remaining(self) -> dict[str, float]:
        """Return remaining budget across all windows."""
        return {
            "daily": round(
                max(0.0, self._daily_budget - self._state.daily_spend), 4
            ),
            "weekly": round(
                max(0.0, self._weekly_budget - self._state.weekly_spend), 4
            ),
            "monthly": round(
                max(0.0, self._monthly_budget - self._state.monthly_spend), 4
            ),
        }

    def is_within_budget(self, estimated_cost: float = 0.0) -> bool:
        """Check if adding estimated_cost would exceed any budget."""
        remaining = self.budget_remaining()
        return (
            estimated_cost <= remaining["daily"]
            and estimated_cost <= remaining["weekly"]
            and estimated_cost <= remaining["monthly"]
        )

    def cheapest_model(self, models: list[str]) -> str | None:
        """Return the cheapest model from a list by output cost.

        Args:
            models: List of model name strings

        Returns:
            Model name with lowest output cost, or None if empty
        """
        if not models:
            return None

        def _output_cost(m: str) -> float:
            return MODEL_COST_PER_1K.get(
                m, MODEL_COST_PER_1K["__default__"]
            )["output"]

        return min(models, key=_output_cost)

    def cost_tiers(self, models: list[str]) -> dict[str, list[str]]:
        """Categorize models into free/cheap/premium tiers."""
        tiers: dict[str, list[str]] = {
            "free": [], "cheap": [], "premium": [],
        }
        for m in models:
            rates = MODEL_COST_PER_1K.get(
                m, MODEL_COST_PER_1K["__default__"]
            )
            output_cost = rates["output"]
            if output_cost == 0.0:
                tiers["free"].append(m)
            elif output_cost <= 0.002:
                tiers["cheap"].append(m)
            else:
                tiers["premium"].append(m)
        return tiers

    # ── Agent Spend Reports ──────────────────────────────────

    def agent_spend(self, agent_id: str) -> dict | None:
        """Get cost record for a specific agent."""
        record = self._state.agents.get(agent_id)
        if record:
            return record.to_dict()
        return None

    def top_spenders(self, limit: int = 5) -> list[dict]:
        """Get top N costliest agents."""
        sorted_agents = sorted(
            self._state.agents.values(),
            key=lambda r: r.total_cost,
            reverse=True,
        )
        return [r.to_dict() for r in sorted_agents[:limit]]

    def reset_agent(self, agent_id: str) -> bool:
        """Reset cost tracking for a specific agent."""
        if agent_id in self._state.agents:
            del self._state.agents[agent_id]
            self._save()
            return True
        return False

    def reset_all(self) -> None:
        """Reset all cost tracking state."""
        self._state = CostState()
        self._save()

    # ── Summary ──────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """Return full summary for health/status endpoints."""
        remaining = self.budget_remaining()
        return {
            "budgets": {
                "daily": self._daily_budget,
                "weekly": self._weekly_budget,
                "monthly": self._monthly_budget,
            },
            "spend": {
                "daily": round(self._state.daily_spend, 4),
                "weekly": round(self._state.weekly_spend, 4),
                "monthly": round(self._state.monthly_spend, 4),
            },
            "remaining": remaining,
            "total_agents": len(self._state.agents),
            "top_spenders": self.top_spenders(3),
            "free_models": list(
                m for m, r in MODEL_COST_PER_1K.items()
                if r["output"] == 0.0 and not m.startswith("_")
            ),
            "cheap_models": list(
                m for m, r in MODEL_COST_PER_1K.items()
                if 0 < r["output"] <= 0.002 and not m.startswith("_")
            ),
            "premium_models": list(
                m for m, r in MODEL_COST_PER_1K.items()
                if r["output"] > 0.002 and not m.startswith("_")
            ),
        }

    # ── Persistence ──────────────────────────────────────────

    def _load(self) -> None:
        """Load state from disk."""
        if not STATE_FILE.exists():
            return
        try:
            data = json.loads(STATE_FILE.read_text("utf-8"))
            self._state.daily_spend = data.get("daily_spend", 0.0)
            self._state.weekly_spend = data.get("weekly_spend", 0.0)
            self._state.monthly_spend = data.get("monthly_spend", 0.0)
            self._state.last_reset_date = data.get("last_reset_date", "")
            for aid, rec_data in data.get("agents", {}).items():
                self._state.agents[aid] = AgentCostRecord(
                    agent_id=rec_data.get("agent_id", aid),
                    model=rec_data.get("model", ""),
                    tasks_completed=rec_data.get("tasks_completed", 0),
                    total_tokens=rec_data.get("total_tokens", 0),
                    total_cost=rec_data.get("total_cost", 0.0),
                )
        except (json.JSONDecodeError, KeyError) as exc:
            log.warning("Failed to load cost state: %s", exc)

    def _save(self) -> None:
        """Persist state to disk."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            STATE_FILE.write_text(
                json.dumps(self._state.to_dict(), indent=2),
                "utf-8",
            )
        except OSError as exc:
            log.error("Failed to save cost state: %s", exc)


# ─── Singleton ──────────────────────────────────────────────

_manager: CostManager | None = None


def get_cost_manager() -> CostManager:
    global _manager
    if _manager is None:
        _manager = CostManager()
    return _manager


def reset_cost_manager() -> None:
    global _manager
    _manager = None
