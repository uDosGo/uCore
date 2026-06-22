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
    handle_mission_task_binder,
    handle_af_index_status,
)
import app.api.knowledge as knowledge_api


class KnowledgeRemoteAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/knowledge/workspaces", handle_list_workspaces)
        app.router.add_get("/api/knowledge/documents", handle_list_documents)
        app.router.add_get("/api/knowledge/documents/{object_id}", handle_get_document)
        app.router.add_get("/api/knowledge/documents/{object_id}/content", handle_get_document_content)
        app.router.add_get("/api/knowledge/search", handle_search)
        app.router.add_get(
            "/api/knowledge/adapter/mission-task-binder",
            handle_mission_task_binder,
        )
        app.router.add_get(
            "/api/knowledge/index/status",
            handle_af_index_status,
        )
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

    async def test_mission_task_binder_projection(self):
        old_list_documents = knowledge_api.list_documents

        def fake_list_documents(workspace_id: str | None = None):
            assert workspace_id == "ws_abc"
            return [
                {
                    "id": "doc_1",
                    "workspace_id": "ws_abc",
                    "title": "Mission A: Ship adapter",
                    "type": "task",
                    "updated_at": "2026-06-22T00:00:00Z",
                },
                {
                    "id": "doc_2",
                    "workspace_id": "ws_abc",
                    "title": "General notes",
                    "type": "note",
                    "updated_at": "2026-06-22T00:00:00Z",
                },
            ]

        knowledge_api.list_documents = fake_list_documents
        try:
            resp = await self.client.get(
                (
                    "/api/knowledge/adapter/mission-task-binder"
                    "?workspace_id=ws_abc"
                )
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["count"] == 2
            assert data["mission_count"] == 2
            assert data["binder_count"] == 2
            assert data["rows"][0]["mission"] == "Mission A"
            assert data["rows"][0]["task"] == "Ship adapter"
            assert data["rows"][0]["binder"] == "task"
        finally:
            knowledge_api.list_documents = old_list_documents

    async def test_mission_task_binder_invalid_limit(self):
        resp = await self.client.get(
            "/api/knowledge/adapter/mission-task-binder?limit=bad"
        )
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data

    async def test_mission_task_binder_prefers_metadata(self):
        old_list_documents = knowledge_api.list_documents

        def fake_list_documents(workspace_id: str | None = None):
            assert workspace_id == "ws_meta"
            return [
                {
                    "id": "doc_meta",
                    "workspace_id": "ws_meta",
                    "title": "Fallback Mission: Fallback Task",
                    "type": "note",
                    "metadata": {
                        "mission": "Meta Mission",
                        "task": "Meta Task",
                        "binder": "runbook",
                    },
                    "properties": {
                        "mission": "Properties Mission",
                    },
                }
            ]

        knowledge_api.list_documents = fake_list_documents
        try:
            resp = await self.client.get(
                (
                    "/api/knowledge/adapter/mission-task-binder"
                    "?workspace_id=ws_meta"
                )
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["count"] == 1
            row = data["rows"][0]
            assert row["mission"] == "Meta Mission"
            assert row["task"] == "Meta Task"
            assert row["binder"] == "runbook"
        finally:
            knowledge_api.list_documents = old_list_documents

    async def test_index_status_endpoint(self):
        def fake_load_config(config_path=None):
            return {"sources": []}

        from app.af_manager import config as af_config
        from app.af_manager import sync as af_sync

        old_af_load_config = af_config.load_config
        old_get_index_coverage = af_sync.get_index_coverage

        af_config.load_config = fake_load_config
        af_sync.get_index_coverage = lambda cfg: {
            "status": "ok",
            "source_count": 0,
            "sources": [],
            "indexed_total": 0,
            "expected_total": 0,
            "coverage_pct": 100,
        }
        try:
            resp = await self.client.get("/api/knowledge/index/status")
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "ok"
            assert "coverage_pct" in data
        finally:
            af_config.load_config = old_af_load_config
            af_sync.get_index_coverage = old_get_index_coverage
