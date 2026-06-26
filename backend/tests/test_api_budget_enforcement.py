"""Integration tests for budget middleware enforcement on chat endpoints."""
from __future__ import annotations

from dataclasses import dataclass

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.core.snackbar import budget_middleware


@dataclass
class _Policy:
    guarded_endpoints: list[str]


class _FakeBudgetManager:
    def __init__(self, *, allowed: bool, reason: str | None = None):
        self.policy = _Policy(guarded_endpoints=["/api/chat", "/api/mcp/chat"])
        self.allowed = allowed
        self.reason = reason
        self.calls: list[dict] = []

    def estimate_for_path(self, path: str) -> float:
        return 0.5

    def check_budget(
        self,
        estimated_cost: float,
        model: str = "",
        provider: str = "",
    ):
        usage = {
            "total_cost": 10.0,
            "monthly_limit": 25.0,
            "remaining_budget": 15.0,
            "over_limit": False,
        }
        return (self.allowed, self.reason, usage)

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
        self.calls.append(
            {
                "endpoint": endpoint,
                "estimated_cost": estimated_cost,
                "actual_cost": actual_cost,
                "status_code": status_code,
                "blocked": blocked,
                "provider": provider,
                "model": model,
            },
        )


class BudgetMiddlewareAPITest(AioHTTPTestCase):
    async def get_application(self):
        self.fake_budget = _FakeBudgetManager(allowed=True)
        app = web.Application(middlewares=[budget_middleware])
        app["budget_manager"] = self.fake_budget

        async def _chat_handler(_request: web.Request) -> web.Response:
            response = web.json_response({"ok": True})
            response.headers["X-Usage-Cost"] = "0.75"
            return response

        app.router.add_post("/api/chat", _chat_handler)
        app.router.add_post("/api/mcp/chat", _chat_handler)

        async def _health_handler(_request: web.Request) -> web.Response:
            return web.json_response({"status": "ok"})

        app.router.add_get("/api/health", _health_handler)
        return app

    async def test_budget_blocks_when_denied(self):
        self.fake_budget.allowed = False
        self.fake_budget.reason = "Monthly budget limit reached"

        resp = await self.client.post("/api/chat", json={"message": "hello"})
        assert resp.status == 429
        data = await resp.json()
        assert "error" in data
        assert self.fake_budget.calls[-1]["blocked"] is True
        assert self.fake_budget.calls[-1]["status_code"] == 429

    async def test_budget_allows_and_logs_actual_cost(self):
        self.fake_budget.allowed = True

        resp = await self.client.post(
            "/api/chat",
            json={
                "message": "hello",
                "provider": "openrouter",
                "model": "gpt-4o-mini",
            },
        )
        assert resp.status == 200
        assert self.fake_budget.calls[-1]["blocked"] is False
        assert self.fake_budget.calls[-1]["status_code"] == 200
        assert self.fake_budget.calls[-1]["actual_cost"] == 0.75
        assert self.fake_budget.calls[-1]["provider"] == "openrouter"
        assert self.fake_budget.calls[-1]["model"] == "gpt-4o-mini"

    async def test_budget_extracts_provider_and_model_from_nested_payload(
        self,
    ):
        self.fake_budget.allowed = True

        resp = await self.client.post(
            "/api/mcp/chat",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "vendor": "anthropic",
                "params": {"model_name": "claude-3-haiku"},
            },
        )
        assert resp.status == 200
        assert self.fake_budget.calls[-1]["provider"] == "anthropic"
        assert self.fake_budget.calls[-1]["model"] == "claude-3-haiku"

    async def test_unguarded_endpoint_skips_budget_checks(self):
        self.fake_budget.allowed = False
        self.fake_budget.reason = "should not be used"

        resp = await self.client.get("/api/health")
        assert resp.status == 200
        assert len(self.fake_budget.calls) == 0
