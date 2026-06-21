"""Integration tests for MCP Protocol API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.mcp import handle_mcp_discover, handle_mcp_call


class MCPAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/mcp/tools", handle_mcp_discover)
        app.router.add_post("/api/mcp/call", handle_mcp_call)
        return app

    async def test_mcp_discover_returns_tools(self):
        resp = await self.client.get("/api/mcp/tools")
        assert resp.status == 200
        data = await resp.json()
        assert "result" in data
        tools = data["result"]["tools"]
        assert len(tools) >= 18  # 15 skills + 3 knowledge tools
        assert all("name" in t for t in tools)
        assert all("description" in t for t in tools)
        assert all("input_schema" in t for t in tools)

    async def test_mcp_discover_has_skill_tools(self):
        resp = await self.client.get("/api/mcp/tools")
        data = await resp.json()
        tools = data["result"]["tools"]
        skill_tools = [t for t in tools if t["name"].startswith("skill_")]
        assert len(skill_tools) >= 14

    async def test_mcp_discover_has_knowledge_tools(self):
        resp = await self.client.get("/api/mcp/tools")
        data = await resp.json()
        tools = data["result"]["tools"]
        knowledge_tools = [t for t in tools if t["name"].startswith("knowledge_")]
        assert len(knowledge_tools) == 3

    async def test_mcp_call_unknown_tool(self):
        resp = await self.client.post("/api/mcp/call", json={
            "name": "nonexistent_tool",
            "arguments": {},
            "id": 1,
        })
        assert resp.status == 404
        data = await resp.json()
        assert "error" in data

    async def test_mcp_call_invalid_json(self):
        resp = await self.client.post("/api/mcp/call", data=b"not json",
                                       headers={"Content-Type": "application/json"})
        assert resp.status == 400

    async def test_mcp_call_skill_hello_world(self):
        resp = await self.client.post("/api/mcp/call", json={
            "name": "skill_hello-world",
            "arguments": {},
            "id": 1,
        })
        assert resp.status == 200
        data = await resp.json()
        assert "result" in data
        assert "content" in data["result"]

    async def test_mcp_discover_protocol_version(self):
        resp = await self.client.get("/api/mcp/tools")
        data = await resp.json()
        assert data["result"]["protocolVersion"] == "2025-03-26"
        assert data["result"]["serverInfo"]["name"] == "uCore MCP"
