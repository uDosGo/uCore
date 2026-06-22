"""Tests for Phase 9 workflow and migration API endpoints."""
from __future__ import annotations

from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.workflows import (
    handle_board_health,
    handle_get_task,
    handle_import_status,
    handle_index_coverage,
    handle_update_task,
    record_import_job,
)


class Phase9WorkflowApiTest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get(
            "/api/knowledge/import/status",
            handle_import_status,
        )
        app.router.add_get(
            "/api/knowledge/index/coverage",
            handle_index_coverage,
        )
        app.router.add_get("/api/workflows/task/{task_id}", handle_get_task)
        app.router.add_put(
            "/api/workflows/task/{task_id}",
            handle_update_task,
        )
        app.router.add_get(
            "/api/workflows/board/{board_id}/health",
            handle_board_health,
        )
        return app

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.tasker_dir = Path("/tmp/ucore_phase9_tasker")
        if self.tasker_dir.exists():
            for child in sorted(self.tasker_dir.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
        self.tasker_dir.mkdir(parents=True, exist_ok=True)
        (self.tasker_dir / "backlog").mkdir()
        (self.tasker_dir / "backlog" / "todo-phase9.md").write_text(
            "\n".join(
                [
                    "# Phase 9 Backend Verification",
                    "- status: todo",
                    "- source: ucore-dev",
                    "- source_id: phase-9",
                    "- priority: high",
                    "",
                    "## Summary",
                    "- Verify workflow endpoints",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (self.tasker_dir / "backlog" / "blocked-task.md").write_text(
            "\n".join(
                [
                    "# Blocked Task",
                    "- status: blocked",
                    "- source_id: blocked-task",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        import app.api.workflows as workflows_api
        import app.services.workflow_status as workflow_status

        self._original_api_default_tasker_dir = (
            workflows_api.default_tasker_dir
        )
        self._original_status_default_tasker_dir = (
            workflow_status.default_tasker_dir
        )
        workflows_api.default_tasker_dir = lambda: self.tasker_dir
        workflow_status.default_tasker_dir = lambda: self.tasker_dir

    async def asyncTearDown(self):
        import app.api.workflows as workflows_api
        import app.services.workflow_status as workflow_status

        workflows_api.default_tasker_dir = (
            self._original_api_default_tasker_dir
        )
        workflow_status.default_tasker_dir = (
            self._original_status_default_tasker_dir
        )

        if self.tasker_dir.exists():
            for child in sorted(self.tasker_dir.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
        await super().asyncTearDown()

    async def test_import_status_returns_recorded_jobs(self):
        record_import_job(
            "phase9job",
            status="completed",
            progress=100,
            message="done",
        )

        resp = await self.client.get("/api/knowledge/import/status")

        assert resp.status == 200
        data = await resp.json()
        assert any(job["id"] == "phase9job" for job in data["jobs"])

    async def test_get_task_reads_tasker_markdown(self):
        resp = await self.client.get("/api/workflows/task/phase-9")

        assert resp.status == 200
        data = await resp.json()
        assert data["id"] == "phase-9"
        assert data["title"] == "Phase 9 Backend Verification"
        assert data["status"] == "todo"
        assert data["priority"] == "high"
        assert data["board"] == "backlog"

    async def test_update_task_persists_tasker_markdown(self):
        resp = await self.client.put(
            "/api/workflows/task/phase-9",
            json={
                "title": "Phase 9 Backend Verification",
                "status": "in-progress",
                "priority": "critical",
                "description": "Endpoint verification underway",
                "tags": ["ucore-dev"],
            },
        )

        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "in-progress"
        assert data["priority"] == "critical"

        content = (self.tasker_dir / "backlog" / "todo-phase9.md").read_text(
            encoding="utf-8",
        )
        assert "- status: in-progress" in content
        assert "- priority: critical" in content
        assert "Endpoint verification underway" in content

    async def test_board_health_reports_blocked_tasks(self):
        resp = await self.client.get("/api/workflows/board/backlog/health")

        assert resp.status == 200
        data = await resp.json()
        assert data["board_id"] == "backlog"
        assert data["status"] == "needs-attention"
        assert data["task_count"] == 2
        assert data["warning_count"] == 1
        assert data["issues"] == ["Blocked task: Blocked Task"]

    async def test_index_coverage_response_shape(self):
        resp = await self.client.get("/api/knowledge/index/coverage")

        assert resp.status == 200
        data = await resp.json()
        assert "coverage" in data
        assert "total_docs" in data
        assert "coverage_pct" in data