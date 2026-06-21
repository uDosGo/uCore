"""Integration tests for System Metadata API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.metadata import system_info_handler


class MetadataAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/system", system_info_handler)
        return app

    async def test_system_info(self):
        resp = await self.client.get("/api/system")
        assert resp.status == 200
        data = await resp.json()
        assert "platform" in data
        assert "machine" in data
        assert "python" in data
        assert "hostname" in data
        assert "app" in data
        assert "version" in data
        assert data["app"] == "uCore"
        assert data["version"] == "4.0.0"

    async def test_system_info_has_python_version(self):
        resp = await self.client.get("/api/system")
        data = await resp.json()
        # Python version should be a string like "3.14.x"
        assert data["python"].startswith("3")
        assert data["python"].count(".") >= 2
