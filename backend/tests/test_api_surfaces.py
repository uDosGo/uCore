"""Integration tests for Surface API endpoints using aiohttp test utils."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.api.surfaces import register_surface_routes
from app.services.surface_manager import SurfaceManager


class SurfaceAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        import app.api.surfaces as mod
        mod._surfaces = SurfaceManager(persist=False)
        register_surface_routes(app)
        return app

    async def test_create_surface(self):
        resp = await self.client.post("/api/surfaces", json={
            "name": "Test Surface", "type": "prose", "metadata": {"theme": "dark"},
        })
        assert resp.status == 201
        data = await resp.json()
        assert data["name"] == "Test Surface"
        assert data["type"] == "prose"

    async def test_create_surface_no_name(self):
        resp = await self.client.post("/api/surfaces", json={"type": "grid"})
        assert resp.status == 400

    async def test_create_surface_invalid_json(self):
        resp = await self.client.post("/api/surfaces", data=b"not json",
                                       headers={"Content-Type": "application/json"})
        assert resp.status == 400

    async def test_create_surface_invalid_type(self):
        resp = await self.client.post("/api/surfaces", json={"name": "Bad", "type": "invalid_type_xyz"})
        assert resp.status == 400

    async def test_list_surfaces(self):
        await self.client.post("/api/surfaces", json={"name": "A", "type": "prose"})
        await self.client.post("/api/surfaces", json={"name": "B", "type": "grid"})
        resp = await self.client.get("/api/surfaces")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 2

    async def test_list_surfaces_empty(self):
        resp = await self.client.get("/api/surfaces")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 0
        assert data["surfaces"] == []

    async def test_get_surface(self):
        cr = await self.client.post("/api/surfaces", json={"name": "Find Me", "type": "dashboard"})
        cid = (await cr.json())["id"]
        resp = await self.client.get(f"/api/surfaces/{cid}")
        assert resp.status == 200
        data = await resp.json()
        assert data["name"] == "Find Me"

    async def test_get_surface_not_found(self):
        resp = await self.client.get("/api/surfaces/nonexistent")
        assert resp.status == 404

    async def test_delete_surface(self):
        cr = await self.client.post("/api/surfaces", json={"name": "Delete Me", "type": "terminal"})
        cid = (await cr.json())["id"]
        resp = await self.client.delete(f"/api/surfaces/{cid}")
        assert resp.status == 200
        get_resp = await self.client.get(f"/api/surfaces/{cid}")
        assert get_resp.status == 404

    async def test_delete_nonexistent(self):
        resp = await self.client.delete("/api/surfaces/nonexistent")
        assert resp.status == 404

    async def test_start_surface(self):
        cr = await self.client.post("/api/surfaces", json={"name": "Start", "type": "prose"})
        cid = (await cr.json())["id"]
        resp = await self.client.post(f"/api/surfaces/{cid}/start")
        assert resp.status == 200
        data = await resp.json()
        assert data["state"] == "running"

    async def test_stop_surface(self):
        cr = await self.client.post("/api/surfaces", json={"name": "Stop", "type": "prose"})
        cid = (await cr.json())["id"]
        await self.client.post(f"/api/surfaces/{cid}/start")
        resp = await self.client.post(f"/api/surfaces/{cid}/stop")
        assert resp.status == 200
        data = await resp.json()
        assert data["state"] == "stopped"

    async def test_start_nonexistent(self):
        resp = await self.client.post("/api/surfaces/nonexistent/start")
        assert resp.status == 404

    async def test_start_runtime_alias_ui_hub(self):
        import app.api.surfaces as mod

        class FakeRuntime:
            def start(self, surface_id: str):
                if surface_id == "ui-hub":
                    return {
                        "success": True,
                        "surface_id": "ui-hub",
                        "status": "running",
                        "port": 5173,
                    }
                return None

            def stop(self, surface_id: str):
                if surface_id == "ui-hub":
                    return {
                        "success": True,
                        "surface_id": "ui-hub",
                        "status": "stopped",
                        "port": 5173,
                    }
                return None

            def restart(self, surface_id: str):
                return None

        old_runtime = mod.get_surface_runtime_manager
        mod.get_surface_runtime_manager = lambda: FakeRuntime()
        try:
            resp = await self.client.post("/api/surfaces/ui-hub/start")
            assert resp.status == 200
            data = await resp.json()
            assert data["surface_id"] == "ui-hub"
            assert data["port"] == 5173

            stop_resp = await self.client.post("/api/surfaces/ui-hub/stop")
            assert stop_resp.status == 200
            stop_data = await stop_resp.json()
            assert stop_data["status"] == "stopped"
        finally:
            mod.get_surface_runtime_manager = old_runtime

    async def test_start_surface_with_runtime_metadata(self):
        import app.api.surfaces as mod

        class FakeRuntime:
            def start(self, surface_id: str):
                if surface_id == "ui-hub":
                    return {
                        "success": True,
                        "surface_id": "ui-hub",
                        "status": "running",
                        "port": 5173,
                    }
                return None

            def stop(self, surface_id: str):
                return None

            def restart(self, surface_id: str):
                return None

        old_runtime = mod.get_surface_runtime_manager
        mod.get_surface_runtime_manager = lambda: FakeRuntime()
        try:
            create_resp = await self.client.post(
                "/api/surfaces",
                json={
                    "name": "Frontend",
                    "type": "dashboard",
                    "metadata": {"runtime_id": "ui-hub"},
                },
            )
            assert create_resp.status == 201
            cid = (await create_resp.json())["id"]

            start_resp = await self.client.post(f"/api/surfaces/{cid}/start")
            assert start_resp.status == 200
            payload = await start_resp.json()
            assert payload["state"] == "running"
            assert payload["runtime"]["surface_id"] == "ui-hub"
        finally:
            mod.get_surface_runtime_manager = old_runtime

    async def test_stop_nonexistent(self):
        resp = await self.client.post("/api/surfaces/nonexistent/stop")
        assert resp.status == 404

    async def test_stop_already_stopped(self):
        """Stopping an already stopped surface should be idempotent."""
        cr = await self.client.post("/api/surfaces", json={"name": "Idempotent", "type": "prose"})
        cid = (await cr.json())["id"]
        resp = await self.client.post(f"/api/surfaces/{cid}/stop")
        assert resp.status == 200
        data = await resp.json()
        assert data["state"] == "stopped"
