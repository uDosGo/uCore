"""Integration tests for Docker API endpoint."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.api.docker import handle_docker_ps


class DockerAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/docker/ps", handle_docker_ps)
        return app

    async def test_docker_ps_returns_success(self):
        """Should always return a valid JSON response, even if Docker isn't installed."""
        resp = await self.client.get("/api/docker/ps")
        assert resp.status == 200
        data = await resp.json()
        assert "containers" in data
        assert "count" in data
        # containers should be a list (may be empty if Docker unavailable)
        assert isinstance(data["containers"], list)
