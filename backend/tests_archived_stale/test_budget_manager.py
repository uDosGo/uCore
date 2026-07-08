"""Unit tests for budget manager limit semantics."""
from __future__ import annotations

import unittest

from app.services.budget_manager import BudgetManager, BudgetPolicy


def _manager_for_test() -> BudgetManager:
    manager = BudgetManager.__new__(BudgetManager)
    manager._policy = BudgetPolicy(
        monthly_usd_limit=1.0,
        default_estimated_cost=0.1,
        guarded_endpoints=["/api/chat", "/api/mcp/chat"],
        per_model_limits={"gpt-4o-mini": 0.5},
    )
    return manager


class BudgetManagerLimitTest(unittest.TestCase):
    def test_monthly_limit_blocks_at_threshold(self):
        manager = _manager_for_test()
        manager.get_monthly_usage = lambda: {
            "total_cost": 0.9,
            "monthly_limit": 1.0,
            "remaining_budget": 0.1,
            "over_limit": False,
        }
        manager.get_model_monthly_usage = lambda _model: 0.0

        allowed, reason, _usage = manager.check_budget(estimated_cost=0.1)
        self.assertFalse(allowed)
        self.assertEqual(reason, "Monthly budget limit reached")

    def test_model_limit_blocks_at_threshold(self):
        manager = _manager_for_test()
        manager.get_monthly_usage = lambda: {
            "total_cost": 0.1,
            "monthly_limit": 1.0,
            "remaining_budget": 0.9,
            "over_limit": False,
        }
        manager.get_model_monthly_usage = lambda _model: 0.4

        allowed, reason, usage = manager.check_budget(
            estimated_cost=0.1,
            model="gpt-4o-mini",
            provider="openrouter",
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "Model budget reached for gpt-4o-mini")
        self.assertEqual(usage["model_limit"], 0.5)
        self.assertEqual(usage["model_usage"], 0.4)
