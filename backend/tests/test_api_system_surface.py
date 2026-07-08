"""Integration tests for System Surface API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.surfaces.system_api import register_system_api_routes


class SystemSurfaceAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        register_system_api_routes(app)
        return app

    async def test_list_pages(self):
        resp = await self.client.get("/api/system/pages")
        assert resp.status == 200
        data = await resp.json()
        assert "pages" in data
        assert data["count"] >= 1
        ids = [p["id"] for p in data["pages"]]
        assert "S100" in ids
        assert "S600" in ids

    async def test_list_tools(self):
        resp = await self.client.get("/api/system/tools")
        assert resp.status == 200
        data = await resp.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

    async def test_get_settings(self):
        resp = await self.client.get("/api/system/settings")
        assert resp.status == 200
        data = await resp.json()
        assert "settings" in data
        assert isinstance(data["settings"], dict)

    async def test_update_settings(self):
        resp = await self.client.post(
            "/api/system/settings",
            json={
                "scope": "global",
                "values": {"theme": "dark", "fontSize": 16},
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assert "global" in data["settings"]
        assert data["settings"]["global"]["theme"] == "dark"

    async def test_update_settings_user_scope(self):
        resp = await self.client.post(
            "/api/system/settings",
            json={
                "scope": "user",
                "values": {"displayName": "Test User"},
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert "user" in data["settings"]
        assert data["settings"]["user"]["displayName"] == "Test User"
