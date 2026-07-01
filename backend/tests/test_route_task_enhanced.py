"""Tests for route_task skill with execution, budget, and risk heuristics."""
from __future__ import annotations

import asyncio
import unittest
from unittest import mock

from app.skills.builtin.route_task import RouteTask


class RouteTaskSkillTest(unittest.TestCase):
    def setUp(self):
        self.skill = RouteTask()

    def test_estimate_complexity_medium(self):
        """Test medium complexity detection."""
        medium_tasks = [
            "implement a REST API endpoint",
            "debug a query performance issue",
            "add database migration",
            "write unit tests for the module",
        ]
        for task in medium_tasks:
            result = self.skill._estimate_complexity(task)
            self.assertEqual(result, "medium")

    def test_run_missing_task(self):
        """Test run rejects empty task."""
        async def _run():
            return await self.skill.run(task="")
        result = asyncio.run(_run())
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_run_complexity_auto_detect(self):
        """Test auto complexity detection in run."""
        async def _run():
            return await self.skill.run(
                task="implement a new API endpoint",
                complexity="auto",
            )
        result = asyncio.run(_run())
        self.assertTrue(result["success"])
        self.assertEqual(result["analysis"]["complexity"], "medium")

    def test_run_context_size_auto_detect(self):
        """Test auto context size detection."""
        async def _run():
            long_task = "x" * 5000
            return await self.skill.run(task=long_task)
        result = asyncio.run(_run())
        self.assertTrue(result["success"])
        self.assertEqual(result["analysis"]["context_size"], "medium")

    def test_run_advice_only_mode(self):
        """Test advice-only (non-execution) mode."""
        async def _run():
            return await self.skill.run(
                task="write a function",
                execute=False,
            )
        result = asyncio.run(_run())
        self.assertTrue(result["success"])
        self.assertEqual(
            result["execution"]["mode"],
            "advice-only",
        )
        self.assertNotIn("response", result["execution"])

    @mock.patch("app.services.budget_manager.BudgetManager")
    def test_run_includes_budget_remaining(self, mock_budget_class):
        """Test budget remaining is included in result."""
        mock_budget = mock.Mock()
        mock_budget.get_monthly_usage.return_value = {
            "remaining_budget": 12.50,
        }
        mock_budget_class.return_value = mock_budget

        async def _run():
            return await self.skill.run(task="test task")
        result = asyncio.run(_run())
        self.assertTrue(result["success"])
        self.assertEqual(
            result["execution"]["budget_remaining"],
            12.50,
        )
