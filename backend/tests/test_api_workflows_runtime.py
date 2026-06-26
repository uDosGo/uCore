"""Tests for workflow runtime endpoints: create/list/run/logs."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.api.workflows import (
    handle_create_workflow,
    handle_list_workflows,
    handle_run_workflow,
    handle_workflow_logs,
)


class WorkflowRuntimeApiTest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/workflows", handle_list_workflows)
        app.router.add_post("/api/workflows", handle_create_workflow)
        app.router.add_post(
            "/api/workflows/{workflow_id}/run",
            handle_run_workflow,
        )
        app.router.add_get(
            "/api/workflows/{workflow_id}/logs",
            handle_workflow_logs,
        )
        return app

    async def test_create_and_list_workflow(self):
        create_resp = await self.client.post(
            "/api/workflows",
            json={
                "name": "runtime-smoke",
                "steps": [
                    {"type": "skill", "skill_id": "nonexistent"},
                ],
            },
        )
        assert create_resp.status == 201
        created = await create_resp.json()
        assert created["id"].startswith("wf-runtime-smoke-")
        assert created["step_count"] == 1

        list_resp = await self.client.get("/api/workflows")
        assert list_resp.status == 200
        listed = await list_resp.json()
        assert listed["count"] >= 1
        assert any(w["id"] == created["id"] for w in listed["workflows"])

    async def test_run_and_logs(self):
        create_resp = await self.client.post(
            "/api/workflows",
            json={
                "name": "runtime-run",
                "steps": [
                    {"type": "skill", "skill_id": "nonexistent"},
                ],
            },
        )
        created = await create_resp.json()
        workflow_id = created["id"]

        run_resp = await self.client.post(f"/api/workflows/{workflow_id}/run")
        assert run_resp.status == 200
        run_data = await run_resp.json()
        assert run_data["workflow_id"] == workflow_id
        assert run_data["status"] in ("failed", "completed")
        assert len(run_data["steps"]) == 1

        logs_resp = await self.client.get(f"/api/workflows/{workflow_id}/logs")
        assert logs_resp.status == 200
        logs_data = await logs_resp.json()
        assert logs_data["workflow_id"] == workflow_id
        assert logs_data["run_count"] >= 1
        assert logs_data["log_count"] >= 1
