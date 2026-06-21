"""Integration tests for Knowledge (AppFlowy Remote) API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.knowledge import (
    handle_list_workspaces,
    handle_list_documents,
    handle_get_document,
    handle_get_document_content,
    handle_search,
)


class KnowledgeRemoteAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/knowledge/workspaces", handle_list_workspaces)
        app.router.add_get("/api/knowledge/documents", handle_list_documents)
        app.router.add_get("/api/knowledge/documents/{object_id}", handle_get_document)
        app.router.add_get("/api/knowledge/documents/{object_id}/content", handle_get_document_content)
        app.router.add_get("/api/knowledge/search", handle_search)
        return app

    async def test_list_workspaces(self):
        """Should return workspaces list (may be empty if no AppFlowy DB)."""
        resp = await self.client.get("/api/knowledge/workspaces")
        assert resp.status == 200
        data = await resp.json()
        assert "workspaces" in data
        assert "count" in data
        assert isinstance(data["workspaces"], list)

    async def test_list_documents(self):
        """Should return documents list (may be empty)."""
        resp = await self.client.get("/api/knowledge/documents")
        assert resp.status == 200
        data = await resp.json()
        assert "documents" in data
        assert "count" in data
        assert isinstance(data["documents"], list)

    async def test_get_document_nonexistent(self):
        """Should return 404 for unknown document."""
        resp = await self.client.get("/api/knowledge/documents/nonexistent_doc_id_xyz")
        assert resp.status == 404
        data = await resp.json()
        assert "error" in data

    async def test_get_document_content_nonexistent(self):
        """Should return 404 for unknown document content."""
        resp = await self.client.get("/api/knowledge/documents/nonexistent_doc_id_xyz/content")
        assert resp.status == 404
        data = await resp.json()
        assert "error" in data

    async def test_search_missing_query(self):
        """Should return 400 when q parameter is missing."""
        resp = await self.client.get("/api/knowledge/search")
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data

    async def test_search_empty_query(self):
        """Should return 400 when q parameter is empty."""
        resp = await self.client.get("/api/knowledge/search?q=")
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data

    async def test_search_with_query(self):
        """Should return search results (may be empty)."""
        resp = await self.client.get("/api/knowledge/search?q=test+query")
        assert resp.status == 200
        data = await resp.json()
        assert "results" in data
        assert "count" in data
        assert data["query"] == "test query"

    async def test_list_workspaces_structure(self):
        resp = await self.client.get("/api/knowledge/workspaces")
        data = await resp.json()
        if data["count"] > 0:
            ws = data["workspaces"][0]
            assert "id" in ws or "workspace_id" in ws or "name" in ws
