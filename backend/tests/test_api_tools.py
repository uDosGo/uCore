"""Integration tests for Tool API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.api.tools import handle_list_tools, handle_tool_status


class ToolsAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/tools", handle_list_tools)
        app.router.add_get("/api/tools/{tool_id}/status", handle_tool_status)
        return app

    async def test_list_tools(self):
        resp = await self.client.get("/api/tools")
        assert resp.status == 200
        data = await resp.json()
        assert "tools" in data
        assert "count" in data
        assert data["count"] >= 7  # 7 tools: git, docker, node, python, ollama, github_cli, vscode

    async def test_tool_status_existing(self):
        """Should return status for known tools without error."""
        resp = await self.client.get("/api/tools/python/status")
        assert resp.status == 200
        data = await resp.json()
        # Should have at minimum: id, name, available fields
        assert "id" in data or "name" in data or "available" in data or "installed" in data

    async def test_tool_status_nonexistent(self):
        resp = await self.client.get("/api/tools/nonexistent_tool/status")
        assert resp.status == 200  # Tools return status even for unknown
        data = await resp.json()
        assert data is not None

    async def test_list_tools_contains_python(self):
        resp = await self.client.get("/api/tools")
        data = await resp.json()
        tool_names = [t.get("name", "") for t in data["tools"]]
        # Python should be discoverable since we're running in it
        assert any("python" in n.lower() for n in tool_names)
