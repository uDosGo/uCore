"""Integration tests for Server Surface API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.surfaces.server import ServerStore, register_server_routes


class ServerSurfaceAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        store = ServerStore()
        register_server_routes(app, store)
        return app

    async def test_health_endpoint(self):
        resp = await self.client.get("/api/server/health")
        assert resp.status == 200
        data = await resp.json()
        assert "services" in data
        assert "count" in data
        assert "up" in data
        assert "down" in data
        assert "health_pct" in data
        assert data["count"] >= 1

    async def test_list_services(self):
        resp = await self.client.get("/api/server/services")
        assert resp.status == 200
        data = await resp.json()
        assert "services" in data
        assert data["count"] >= 1
        names = [s["name"] for s in data["services"]]
        assert "snackbar" in names
        assert "ollama" in names

    async def test_get_service_found(self):
        resp = await self.client.get("/api/server/services/snackbar")
        assert resp.status == 200
        data = await resp.json()
        assert "service" in data
        svc = data["service"]
        assert svc["name"] == "snackbar"
        assert svc["port"] == 8484

    async def test_get_service_not_found(self):
        resp = await self.client.get("/api/server/services/nonexistent")
        assert resp.status == 404

    async def test_add_service(self):
        resp = await self.client.post(
            "/api/server/services",
            json={
                "name": "test-svc",
                "port": 9999,
                "type": "user",
                "description": "Test service",
            },
        )
        assert resp.status == 201
        data = await resp.json()
        assert data["status"] == "ok"

    async def test_logs_endpoint(self):
        resp = await self.client.get("/api/server/logs")
        assert resp.status == 200
        data = await resp.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)

    async def test_logs_with_limit(self):
        resp = await self.client.get("/api/server/logs?limit=5")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] <= 5

    async def test_models_endpoint(self):
        resp = await self.client.get("/api/server/models")
        assert resp.status == 200
        data = await resp.json()
        assert "models" in data

    async def test_agents_endpoint(self):
        resp = await self.client.get("/api/server/agents")
        assert resp.status == 200
        data = await resp.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)

    async def test_budget_endpoint(self):
        resp = await self.client.get("/api/server/budget")
        assert resp.status == 200
        data = await resp.json()
        assert "remaining" in data
        assert "used" in data
        assert "limit" in data
        assert "over_limit" in data
