"""Integration tests for MCP Protocol API endpoints."""
from __future__ import annotations

from typing import Any, cast

import app.api.mcp as mcp_api
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.api.mcp import handle_mcp_call, handle_mcp_discover


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
        knowledge_tools = [
            t for t in tools if t["name"].startswith("knowledge_")
        ]
        assert len(knowledge_tools) == 3

    async def test_mcp_discover_has_clipboard_tools(self):
        resp = await self.client.get("/api/mcp/tools")
        data = await resp.json()
        tools = data["result"]["tools"]
        names = {tool["name"] for tool in tools}
        assert "clipboard_capture" in names
        assert "clipboard_get" in names
        assert "clipboard_delete" in names

    async def test_mcp_discover_has_tasker_tools(self):
        resp = await self.client.get("/api/mcp/tools")
        data = await resp.json()
        tools = data["result"]["tools"]
        names = {tool["name"] for tool in tools}
        assert "tasker_list_boards" in names
        assert "tasker_read_task" in names
        assert "tasker_write_task" in names
        assert "tasker_sync_export" in names

    async def test_mcp_discover_has_gridsmith_tools(self):
        resp = await self.client.get("/api/mcp/tools")
        data = await resp.json()
        tools = data["result"]["tools"]
        names = {tool["name"] for tool in tools}
        assert "gridsmith_tools_list" in names
        assert "gridsmith_create_grid" in names
        assert "gridsmith_import_basic_program" in names

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
        resp = await self.client.post(
            "/api/mcp/call",
            data=b"not json",
            headers={"Content-Type": "application/json"},
        )
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

    async def test_mcp_call_clipboard_capture(self):
        def fake_capture_current_clipboard(source: str, metadata: dict):
            assert source == "user_copy"
            assert metadata == {"origin": "mcp"}
            return {"id": "clip_abc", "content": "hello"}

        old_capture = mcp_api.capture_current_clipboard
        mcp_api.capture_current_clipboard = fake_capture_current_clipboard
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "clipboard_capture",
                "arguments": {
                    "source": "user_copy",
                    "metadata": {"origin": "mcp"},
                },
                "id": 12,
            })
            assert resp.status == 200
            data = await resp.json()
            assert "result" in data
            assert "clip_abc" in data["result"]["content"][0]["text"]
        finally:
            mcp_api.capture_current_clipboard = old_capture

    async def test_mcp_call_clipboard_get_recent(self):
        def fake_get_recent_items(limit: int, include_pinned: bool):
            assert limit == 2
            assert include_pinned is True
            return [{"id": "clip_1"}, {"id": "clip_2"}]

        old_get_recent = mcp_api.get_recent_items
        mcp_api.get_recent_items = fake_get_recent_items
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "clipboard_get",
                "arguments": {"limit": 2, "include_pinned": True},
                "id": 13,
            })
            assert resp.status == 200
            data = await resp.json()
            text = data["result"]["content"][0]["text"]
            assert '"count": 2' in text
            assert "clip_1" in text
        finally:
            mcp_api.get_recent_items = old_get_recent

    async def test_mcp_call_clipboard_delete(self):
        def fake_delete_item(item_id: str):
            assert item_id == "clip_del"
            return True

        old_delete = mcp_api.delete_item
        mcp_api.delete_item = fake_delete_item
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "clipboard_delete",
                "arguments": {"item_id": "clip_del"},
                "id": 14,
            })
            assert resp.status == 200
            data = await resp.json()
            assert "deleted" in data["result"]["content"][0]["text"]
        finally:
            mcp_api.delete_item = old_delete

    async def test_mcp_call_knowledge_list_workspaces(self):
        from app.knowledge import appflowy

        def fake_list_workspaces():
            return [{"id": "ws_1", "name": "Workspace 1"}]

        old_list_workspaces = appflowy.list_workspaces
        appflowy.list_workspaces = fake_list_workspaces
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "knowledge_list_workspaces",
                "arguments": {},
                "id": 15,
            })
            assert resp.status == 200
            data = await resp.json()
            text = data["result"]["content"][0]["text"]
            assert "ws_1" in text
        finally:
            appflowy.list_workspaces = old_list_workspaces

    async def test_mcp_call_knowledge_list_documents(self):
        from app.knowledge import appflowy

        def fake_list_documents(workspace_id: str | None = None):
            assert workspace_id == "ws_abc"
            return [{"id": "doc_1", "title": "Doc One"}]

        old_list_documents = appflowy.list_documents
        appflowy.list_documents = fake_list_documents
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "knowledge_list_documents",
                "arguments": {"workspace_id": "ws_abc"},
                "id": 16,
            })
            assert resp.status == 200
            data = await resp.json()
            text = data["result"]["content"][0]["text"]
            assert "doc_1" in text
        finally:
            appflowy.list_documents = old_list_documents

    async def test_mcp_call_knowledge_search(self):
        from app.knowledge import appflowy

        def fake_semantic_search(
            query: str,
            workspace_id: str | None,
            limit: int,
        ):
            assert query == "vector search"
            assert workspace_id == "ws_abc"
            assert limit == 5
            return [{"id": "row_1", "content": "match"}]

        old_semantic_search = appflowy.semantic_search
        appflowy.semantic_search = fake_semantic_search
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "knowledge_search",
                "arguments": {
                    "query": "vector search",
                    "workspace_id": "ws_abc",
                    "limit": 5,
                },
                "id": 17,
            })
            assert resp.status == 200
            data = await resp.json()
            text = data["result"]["content"][0]["text"]
            assert "row_1" in text
        finally:
            appflowy.semantic_search = old_semantic_search

    async def test_mcp_call_knowledge_search_missing_query(self):
        resp = await self.client.post("/api/mcp/call", json={
            "name": "knowledge_search",
            "arguments": {},
            "id": 18,
        })
        assert resp.status == 400
        data = await resp.json()
        assert data["error"]["code"] == -32602

    async def test_mcp_call_knowledge_search_invalid_limit(self):
        resp = await self.client.post("/api/mcp/call", json={
            "name": "knowledge_search",
            "arguments": {"query": "abc", "limit": "bad"},
            "id": 19,
        })
        assert resp.status == 400
        data = await resp.json()
        assert data["error"]["code"] == -32602

    async def test_mcp_call_tasker_list_boards(self):
        def fake_list_tasker_boards(tasker_dir=None):
            assert tasker_dir == "/tmp/tasker"
            return {"boards": [{"name": "inbox", "count": 2}], "count": 1}

        old_list_tasker_boards = mcp_api.list_tasker_boards
        mcp_api.list_tasker_boards = fake_list_tasker_boards
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "tasker_list_boards",
                "arguments": {"tasker_dir": "/tmp/tasker"},
                "id": 20,
            })
            assert resp.status == 200
            data = await resp.json()
            assert "inbox" in data["result"]["content"][0]["text"]
        finally:
            mcp_api.list_tasker_boards = old_list_tasker_boards

    async def test_mcp_call_tasker_read_task(self):
        def fake_read_task_markdown(*, board: str, task: str, tasker_dir=None):
            assert board == "inbox"
            assert task == "todo-card.md"
            assert tasker_dir == "/tmp/tasker"
            return {"task": task, "content": "# Card\n"}

        old_read_task_markdown = mcp_api.read_task_markdown
        mcp_api.read_task_markdown = fake_read_task_markdown
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "tasker_read_task",
                "arguments": {
                    "board": "inbox",
                    "task": "todo-card.md",
                    "tasker_dir": "/tmp/tasker",
                },
                "id": 21,
            })
            assert resp.status == 200
            data = await resp.json()
            assert "todo-card.md" in data["result"]["content"][0]["text"]
        finally:
            mcp_api.read_task_markdown = old_read_task_markdown

    async def test_mcp_call_tasker_write_task(self):
        def fake_write_task_markdown(
            *,
            title: str,
            board: str,
            status: str,
            body: str,
            source: str,
            source_id,
            metadata,
            task,
            tasker_dir,
        ):
            assert title == "Write MCP card"
            assert board == "doing"
            assert status == "todo"
            assert body == "Body"
            assert source == "manual"
            assert source_id == "abc"
            assert metadata == {"priority": "P1"}
            assert task is None
            assert tasker_dir == "/tmp/tasker"
            return {"task": "todo-write-mcp-card-abc.md", "written": True}

        old_write_task_markdown = mcp_api.write_task_markdown
        mcp_api.write_task_markdown = fake_write_task_markdown
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "tasker_write_task",
                "arguments": {
                    "title": "Write MCP card",
                    "board": "doing",
                    "status": "todo",
                    "body": "Body",
                    "source": "manual",
                    "source_id": "abc",
                    "metadata": {"priority": "P1"},
                    "tasker_dir": "/tmp/tasker",
                },
                "id": 22,
            })
            assert resp.status == 200
            data = await resp.json()
            assert "written" in data["result"]["content"][0]["text"]
        finally:
            mcp_api.write_task_markdown = old_write_task_markdown

    async def test_mcp_call_tasker_write_task_invalid_metadata(self):
        resp = await self.client.post("/api/mcp/call", json={
            "name": "tasker_write_task",
            "arguments": {"title": "Bad", "metadata": "wrong"},
            "id": 23,
        })
        assert resp.status == 400
        data = await resp.json()
        assert data["error"]["code"] == -32602

    async def test_mcp_call_tasker_sync_export(self):
        class FakeSkill:
            async def run(self, **kwargs):
                assert kwargs["db"] == "database"
                assert kwargs["board"] == "inbox"
                return {"success": True, "count": 1}

        def fake_get_skill(skill_id: str):
            if skill_id == "tasker_sync":
                return cast("Any", FakeSkill())
            return None

        old_get_skill = mcp_api.get_skill
        mcp_api.get_skill = fake_get_skill
        try:
            resp = await self.client.post("/api/mcp/call", json={
                "name": "tasker_sync_export",
                "arguments": {"db": "database", "board": "inbox"},
                "id": 24,
            })
            assert resp.status == 200
            data = await resp.json()
            text = data["result"]["content"][0]["text"].lower()
            assert '"success": true' in text
        finally:
            mcp_api.get_skill = old_get_skill
