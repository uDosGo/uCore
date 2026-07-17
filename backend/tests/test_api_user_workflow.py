"""API tests for user workflow endpoints and optional AppFlowy fallback."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

import app.api.user_workflow as mod


class UserWorkflowApiTest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get(
            "/api/user/workflow/status",
            mod.handle_user_workflow_status,
        )
        app.router.add_post(
            "/api/user/workflow/archive",
            mod.handle_user_workflow_archive,
        )
        app.router.add_post(
            "/api/user/workflow/reset",
            mod.handle_user_workflow_reset,
        )
        return app

    async def test_status_degraded_when_appflowy_discovery_fails(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasker_dir = root / ".tasker"
            tasker_dir.mkdir(parents=True, exist_ok=True)

            with (
                patch.object(
                    mod,
                    "default_tasker_dir",
                    return_value=tasker_dir,
                ),
                patch.object(
                    mod,
                    "discover_databases",
                    side_effect=RuntimeError("db unavailable"),
                ),
                patch.object(mod, "list_workspaces", return_value=[]),
            ):
                resp = await self.client.get("/api/user/workflow/status")

            assert resp.status == 200
            payload = await resp.json()
            assert payload["source_of_truth"] == "markdown"
            assert payload["appflowy"]["available"] is False
            assert payload["appflowy"]["status"] == "degraded"
            assert payload["appflowy"]["errors"]

    async def test_archive_succeeds_when_appflowy_discovery_fails(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            logs_dir = root / "logs"
            data_dir = root / "data"
            tasker_dir = root / ".tasker"
            board_dir = tasker_dir / "inbox"
            board_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            (board_dir / "todo-sample.md").write_text(
                "# Sample\n\n- status: todo\n",
                encoding="utf-8",
            )

            with (
                patch.object(mod.settings, "logs_dir", logs_dir),
                patch.object(mod.settings, "data_dir", data_dir),
                patch.object(
                    mod,
                    "default_tasker_dir",
                    return_value=tasker_dir,
                ),
                patch.object(
                    mod,
                    "discover_databases",
                    side_effect=RuntimeError("db unavailable"),
                ),
                patch.object(mod, "list_workspaces", return_value=[]),
            ):
                resp = await self.client.post(
                    "/api/user/workflow/archive",
                    json={"reason": "test"},
                )

            assert resp.status == 200
            payload = await resp.json()
            archive = payload["archive"]
            assert archive["tasker"]["copied_files"] >= 1
            assert archive["appflowy_sidecar"]["errors"]

    async def test_reset_succeeds_and_seeds_when_appflowy_is_degraded(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            logs_dir = root / "logs"
            data_dir = root / "data"
            tasker_dir = root / ".tasker"
            logs_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)

            class _StubManager:
                def create_workflow(self, **kwargs):
                    return {
                        "id": kwargs["workflow_id"],
                        "name": kwargs["name"],
                    }

            with (
                patch.object(mod.settings, "logs_dir", logs_dir),
                patch.object(mod.settings, "data_dir", data_dir),
                patch.object(
                    mod,
                    "default_tasker_dir",
                    return_value=tasker_dir,
                ),
                patch.object(
                    mod,
                    "discover_databases",
                    side_effect=RuntimeError("db unavailable"),
                ),
                patch.object(mod, "list_workspaces", return_value=[]),
                patch(
                    "app.api.workflows.get_workflow_manager",
                    return_value=_StubManager(),
                ),
            ):
                resp = await self.client.post(
                    "/api/user/workflow/reset",
                    json={"reason": "test-reset"},
                )

            assert resp.status == 200
            payload = await resp.json()
            assert payload["seed"]["tasks"]["created_count"] == 4
            assert payload["seed"]["workflows"]["created_count"] == 2
            assert payload["cleared"]["appflowy_sidecar"]["errors"]

            seeded_files = payload["seed"]["tasks"]["created"]
            assert len(seeded_files) == 4
            for path_str in seeded_files:
                text = Path(path_str).read_text(encoding="utf-8")
                assert "- status:" in text
                assert "- priority:" in text
                assert "- mission:" in text
                assert "- task:" in text
                assert "- binder:" in text
                assert "- tags:" in text
