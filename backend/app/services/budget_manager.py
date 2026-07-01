"""Budget Manager — Session, daily, and monthly budget tracking.

Enforces spending limits with circuit breaker pattern:
- Per-session budget (resets on restart)
- Daily budget (resets at midnight)
- Monthly budget (resets on 1st)
- Per-agent budget caps (reviewer gets more than dev)
- Circuit breaker: when budget < threshold, only free tier

Config: ~/.ucore/config/budget.yaml

Usage:
    bm = BudgetManager.get()
    if bm.can_spend("reviewer", estimated_cost=0.05):
        bm.record_spend("reviewer", cost=0.04)
    status = bm.get_status()
"""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.budget_manager")

DB_PATH = Path.home() / ".ucore" / "indices" / "budget.db"
CONFIG_PATH = Path.home() / ".ucore" / "config" / "budget.yaml"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS spend_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    task_type TEXT,
    model TEXT,
    provider TEXT,
    cost_usd REAL NOT NULL,
    cost_tier TEXT,
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_spend_timestamp
    ON spend_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_spend_agent
    ON spend_log(agent_id);
"""

DEFAULT_CONFIG = {
    "session_budget_usd": 5.0,
    "daily_budget_usd": 10.0,
    "monthly_budget_usd": 50.0,
    "circuit_breaker_threshold": 0.10,
    "per_agent": {
        "dev": {"daily_budget_usd": 2.0, "max_per_task_usd": 0.10},
        "reviewer": {"daily_budget_usd": 3.0, "max_per_task_usd": 0.50},
        "architect": {"daily_budget_usd": 4.0, "max_per_task_usd": 1.00},
        "debugger": {"daily_budget_usd": 1.0, "max_per_task_usd": 0.05},
        "docgen": {"daily_budget_usd": 1.0, "max_per_task_usd": 0.05},
        "gridsmith-dev": {"daily_budget_usd": 1.0, "max_per_task_usd": 0.05},
    },
    "free_tier_only_when_exhausted": True,
}


class BudgetManager:
    """Track and enforce AI spending budgets."""

    _instance: "BudgetManager | None" = None

    def __init__(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(DB_PATH))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._config = self._load_config()

    @classmethod
    def get(cls) -> "BudgetManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_config(self) -> dict[str, Any]:
        if CONFIG_PATH.exists():
            try:
                import yaml
                with open(CONFIG_PATH) as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict):
                    return {**DEFAULT_CONFIG, **data}
            except Exception as e:
                log.warning("Failed to load budget config: %s", e)
        return dict(DEFAULT_CONFIG)

    def can_spend(
        self,
        agent_id: str,
        estimated_cost: float,
        task_type: str | None = None,
    ) -> bool:
        """Check if spending is allowed within budget constraints."""
        if estimated_cost == 0.0:
            return True

        agent_config = self._config.get("per_agent", {}).get(agent_id, {})
        max_per_task = agent_config.get("max_per_task_usd", float("inf"))
        if estimated_cost > max_per_task:
            log.info(
                "Agent %s: cost $%.4f exceeds max_per_task $%.2f",
                agent_id, estimated_cost, max_per_task,
            )
            return False

        session_spend = self._get_period_spend("session")
        session_budget = self._config.get("session_budget_usd", float("inf"))
        if session_spend + estimated_cost > session_budget:
            log.info(
                "Session budget exhausted: $%.2f / $%.2f",
                session_spend, session_budget,
            )
            return False

        daily_spend = self._get_period_spend("day")
        daily_budget = self._config.get("daily_budget_usd", float("inf"))
        if daily_spend + estimated_cost > daily_budget:
            log.info(
                "Daily budget exhausted: $%.2f / $%.2f",
                daily_spend, daily_budget,
            )
            return False

        monthly_spend = self._get_period_spend("month")
        monthly_budget = self._config.get("monthly_budget_usd", float("inf"))
        if monthly_spend + estimated_cost > monthly_budget:
            log.info(
                "Monthly budget exhausted: $%.2f / $%.2f",
                monthly_spend, monthly_budget,
            )
            return False

        agent_daily = agent_config.get("daily_budget_usd", float("inf"))
        if agent_daily < float("inf"):
            agent_spend = self._get_period_spend("day", agent_id=agent_id)
            if agent_spend + estimated_cost > agent_daily:
                log.info(
                    "Agent %s daily exhausted: $%.2f / $%.2f",
                    agent_id, agent_spend, agent_daily,
                )
                return False

        return True

    def record_spend(
        self,
        agent_id: str,
        cost: float,
        model: str = "",
        provider: str = "",
        task_type: str | None = None,
        cost_tier: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a spending event."""
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            """
            INSERT INTO spend_log
            (timestamp, agent_id, task_type, model, provider,
             cost_usd, cost_tier, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now, agent_id, task_type, model, provider,
                cost, cost_tier, json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()

    def get_status(self) -> dict[str, Any]:
        """Get current budget status."""
        session_spend = self._get_period_spend("session")
        daily_spend = self._get_period_spend("day")
        monthly_spend = self._get_period_spend("month")

        session_budget = self._config.get("session_budget_usd", 0)
        daily_budget = self._config.get("daily_budget_usd", 0)
        monthly_budget = self._config.get("monthly_budget_usd", 0)

        threshold = self._config.get("circuit_breaker_threshold", 0.10)
        daily_remaining = daily_budget - daily_spend
        circuit_open = daily_remaining < (daily_budget * threshold)

        return {
            "session": {
                "spend": round(session_spend, 4),
                "budget": session_budget,
                "remaining": round(max(0, session_budget - session_spend), 4),
            },
            "daily": {
                "spend": round(daily_spend, 4),
                "budget": daily_budget,
                "remaining": round(max(0, daily_budget - daily_spend), 4),
            },
            "monthly": {
                "spend": round(monthly_spend, 4),
                "budget": monthly_budget,
                "remaining": round(max(0, monthly_budget - monthly_spend), 4),
            },
            "circuit_breaker_open": circuit_open,
            "free_tier_only": circuit_open,
            "per_agent": self._get_agent_status(),
        }

    def _get_agent_status(self) -> dict[str, Any]:
        result = {}
        for agent_id, agent_config in self._config.get("per_agent", {}).items():
            daily_budget = agent_config.get("daily_budget_usd", 0)
            daily_spend = self._get_period_spend("day", agent_id=agent_id)
            result[agent_id] = {
                "daily_spend": round(daily_spend, 4),
                "daily_budget": daily_budget,
                "daily_remaining": round(max(0, daily_budget - daily_spend), 4),
                "max_per_task": agent_config.get("max_per_task_usd", None),
            }
        return result

    def _get_period_spend(
        self, period: str, agent_id: str | None = None,
    ) -> float:
        now = datetime.now(UTC)

        if period == "session":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "day":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        start_str = start.isoformat()

        if agent_id:
            row = self._conn.execute(
                "SELECT COALESCE(SUM(cost_usd), 0) FROM spend_log "
                "WHERE timestamp >= ? AND agent_id = ?",
                (start_str, agent_id),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT COALESCE(SUM(cost_usd), 0) FROM spend_log "
                "WHERE timestamp >= ?",
                (start_str,),
            ).fetchone()

        return float(row[0]) if row else 0.0

    def get_spend_report(
        self, period: str = "day", limit: int = 50,
    ) -> list[dict[str, Any]]:
        now = datetime.now(UTC)

        if period == "day":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start = now - timedelta(days=7)
        elif period == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        rows = self._conn.execute(
            "SELECT * FROM spend_log WHERE timestamp >= ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (start.isoformat(), limit),
        ).fetchall()

        return [
            {
                "timestamp": r["timestamp"],
                "agent_id": r["agent_id"],
                "task_type": r["task_type"],
                "model": r["model"],
                "provider": r["provider"],
                "cost_usd": r["cost_usd"],
                "cost_tier": r["cost_tier"],
            }
            for r in rows
        ]