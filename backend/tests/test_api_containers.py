"""Integration tests for Container API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.containers import register_container_routes
from app.services.container_manager import ContainerManager


class ContainerAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        import app.api.containers as mod
        mod._mgr = ContainerManager(persist=False)
        register_container_routes(app)
        return app

    async def test_create_container(self):
        resp = await self.client.post("/api/containers", json={
            "name": "Worker", "runtime": "python", "dependencies": ["pydantic"],
        })
        assert resp.status == 201
        data = await resp.json()
        assert data["name"] == "Worker"
        assert data["runtime"] == "python"

    async def test_create_container_no_name(self):
        resp = await self.client.post("/api/containers", json={"runtime": "node"})
        assert resp.status == 400

    async def test_list_containers(self):
        await self.client.post("/api/containers", json={"name": "A", "runtime": "python"})
        await self.client.post("/api/containers", json={"name": "B", "runtime": "node"})
        resp = await self.client.get("/api/containers")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 2

    async def test_get_container(self):
        cr = await self.client.post("/api/containers", json={"name": "Find Me", "runtime": "python"})
        cid = (await cr.json())["id"]
        resp = await self.client.get(f"/api/containers/{cid}")
        assert resp.status == 200
        data = await resp.json()
        assert data["name"] == "Find Me"

    async def test_start_stop_container(self):
        cr = await self.client.post("/api/containers", json={"name": "Cycle", "runtime": "python"})
        cid = (await cr.json())["id"]
        sr = await self.client.post(f"/api/containers/{cid}/start")
        assert sr.status == 200
        assert (await sr.json())["status"] == "running"
        sr2 = await self.client.post(f"/api/containers/{cid}/stop")
        assert sr2.status == 200
        assert (await sr2.json())["status"] == "stopped"

    async def test_get_logs(self):
        cr = await self.client.post("/api/containers", json={"name": "Logger", "runtime": "bash"})
        cid = (await cr.json())["id"]
        await self.client.post(f"/api/containers/{cid}/start")
        await self.client.post(f"/api/containers/{cid}/stop")
        resp = await self.client.get(f"/api/containers/{cid}/logs")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] >= 2

    async def test_delete_container(self):
        cr = await self.client.post("/api/containers", json={"name": "Delete", "runtime": "python"})
        cid = (await cr.json())["id"]
        resp = await self.client.delete(f"/api/containers/{cid}")
        assert resp.status == 200
        get_resp = await self.client.get(f"/api/containers/{cid}")
        assert get_resp.status == 404
