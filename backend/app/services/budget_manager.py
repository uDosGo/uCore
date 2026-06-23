"""Budget management and usage logging for API calls."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.settings import settings

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class BudgetPolicy:
    monthly_usd_limit: float
    default_estimated_cost: float
    guarded_endpoints: list[str]
    per_model_limits: dict[str, float]


class BudgetManager:
    """Tracks API usage and enforces configurable monthly budget limits."""

    def __init__(self):
        self._db_path = settings.data_dir / "budget_usage.db"
        self._policy_path = settings.config_dir / "budget.yaml"
        self._policy = self._load_policy()
        self._init_db()

    def _load_policy(self) -> BudgetPolicy:
        defaults = BudgetPolicy(
            monthly_usd_limit=25.0,
            default_estimated_cost=0.01,
            guarded_endpoints=["/api/chat", "/api/mcp/chat"],
            per_model_limits={},
        )

        if yaml is None or not self._policy_path.exists():
            return defaults

        try:
            parsed = yaml.safe_load(self._policy_path.read_text("utf-8")) or {}
        except Exception:
            return defaults

        monthly = parsed.get("monthly_usd_limit", defaults.monthly_usd_limit)
        default_cost = parsed.get(
            "default_estimated_cost",
            defaults.default_estimated_cost,
        )
        guarded = parsed.get("guarded_endpoints", defaults.guarded_endpoints)
        per_model = parsed.get("per_model_limits", {})

        if not isinstance(guarded, list):
            guarded = defaults.guarded_endpoints
        if not isinstance(per_model, dict):
            per_model = {}

        return BudgetPolicy(
            monthly_usd_limit=float(monthly),
            default_estimated_cost=float(default_cost),
            guarded_endpoints=[str(x) for x in guarded],
            per_model_limits={str(k): float(v) for k, v in per_model.items()},
        )

    def reload_policy(self) -> BudgetPolicy:
        self._policy = self._load_policy()
        return self._policy

    @property
    def policy(self) -> BudgetPolicy:
        return self._policy

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    provider TEXT,
                    model TEXT,
                    estimated_cost REAL NOT NULL,
                    actual_cost REAL NOT NULL,
                    status_code INTEGER NOT NULL,
                    blocked INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    def estimate_for_path(self, path: str) -> float:
        return self._policy.default_estimated_cost

    def _month_bounds(self) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            next_start = now.replace(
                year=now.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            next_start = now.replace(
                month=now.month + 1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        return (start.isoformat(), next_start.isoformat())

    def get_monthly_usage(self) -> dict[str, Any]:
        start_iso, next_iso = self._month_bounds()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(actual_cost), 0) AS total_cost,
                    COUNT(*) AS total_calls,
                    COALESCE(SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END), 0) AS blocked_calls
                FROM usage_logs
                WHERE ts >= ? AND ts < ?
                """,
                (start_iso, next_iso),
            ).fetchone()
        total_cost = float(row["total_cost"] if row else 0.0)
        total_calls = int(row["total_calls"] if row else 0)
        blocked_calls = int(row["blocked_calls"] if row else 0)

        return {
            "period_start": start_iso,
            "period_end": next_iso,
            "total_cost": total_cost,
            "total_calls": total_calls,
            "blocked_calls": blocked_calls,
            "monthly_limit": self._policy.monthly_usd_limit,
            "remaining_budget": max(self._policy.monthly_usd_limit - total_cost, 0.0),
            "over_limit": total_cost >= self._policy.monthly_usd_limit,
        }

    def check_budget(
        self,
        estimated_cost: float,
        model: str = "",
        provider: str = "",
    ) -> tuple[bool, str | None, dict[str, Any]]:
        usage = self.get_monthly_usage()

        if usage["total_cost"] + estimated_cost > self._policy.monthly_usd_limit:
            return (False, "Monthly budget limit reached", usage)

        if model and model in self._policy.per_model_limits:
            model_limit = self._policy.per_model_limits[model]
            model_usage = self.get_model_monthly_usage(model)
            if model_usage + estimated_cost > model_limit:
                return (
                    False,
                    f"Model budget reached for {model}",
                    {
                        **usage,
                        "model": model,
                        "model_limit": model_limit,
                        "model_usage": model_usage,
                    },
                )

        return (True, None, usage)

    def get_model_monthly_usage(self, model: str) -> float:
        start_iso, next_iso = self._month_bounds()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(actual_cost), 0) AS total
                FROM usage_logs
                WHERE ts >= ? AND ts < ? AND model = ?
                """,
                (start_iso, next_iso, model),
            ).fetchone()
        return float(row["total"] if row else 0.0)

    def record_usage(
        self,
        endpoint: str,
        estimated_cost: float,
        actual_cost: float,
        status_code: int,
        blocked: bool,
        provider: str = "",
        model: str = "",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO usage_logs (
                    ts, endpoint, provider, model,
                    estimated_cost, actual_cost, status_code, blocked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    endpoint,
                    provider,
                    model,
                    float(estimated_cost),
                    float(actual_cost),
                    int(status_code),
                    1 if blocked else 0,
                ),
            )
            conn.commit()

    def list_usage(self, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 1000))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ts, endpoint, provider, model,
                       estimated_cost, actual_cost, status_code, blocked
                FROM usage_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [dict(row) for row in rows]
