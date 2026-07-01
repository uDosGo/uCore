"""Integration tests for specialized agents workflow planning API."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.api.handlers import handle_agents_spec_plan, handle_agents_spec_route


class AgentsSpecAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_post("/api/agents/spec/plan", handle_agents_spec_plan)
        app.router.add_post("/api/agents/spec/route", handle_agents_spec_route)
        return app

    async def test_plan_surface_ownership_workflow(self):
        resp = await self.client.post(
            "/api/agents/spec/plan",
            json={
                "task_type": "surface-restructure",
                "complexity": "high",
                "task": (
                    "Refactor Developer, Server, and "
                    "System Tools ownership"
                ),
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["workflow"]["workflow_id"] == "surface-ownership-refactor"
        assert data["workflow"]["active_stage"]["agent"]["id"] == "architect"
        assert "developer" in data["surface_taxonomy"]

    async def test_route_plan_only_uses_requested_stage(self):
        resp = await self.client.post(
            "/api/agents/spec/route",
            json={
                "task_type": "surface-taxonomy",
                "complexity": "medium",
                "task": "Apply the approved taxonomy",
                "workflow_stage": "dev",
                "plan_only": True,
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["workflow"]["active_stage"]["agent"]["id"] == "dev"
