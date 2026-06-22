"""Integration tests for Knowledge import endpoint ingest context."""
from __future__ import annotations

import asyncio

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.knowledge import handle_af_import


class KnowledgeImportAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_post("/api/knowledge/import", handle_af_import)
        return app

    async def test_import_accepts_ingest_context(self):
        from app.af_manager import config as af_config
        from app.af_manager import sync as af_sync

        old_load_config = af_config.load_config
        old_run_import = af_sync.run_import
        old_ensure_future = asyncio.ensure_future

        captured: dict[str, object] = {}

        def fake_load_config(config_path=None):
            return {
                "sources": [
                    {
                        "name": "Vault",
                        "local_path": "~/Vault",
                        "enabled": True,
                        "tags": [],
                    }
                ]
            }

        def fake_run_import(config, progress_callback=None, ingest_context=None):
            captured["ingest_context"] = ingest_context
            return {"status": "completed"}

        def run_immediately(coro):
            return asyncio.get_event_loop().create_task(coro)

        af_config.load_config = fake_load_config
        af_sync.run_import = fake_run_import
        asyncio.ensure_future = run_immediately

        try:
            payload = {
                "source": "Vault",
                "mission": "Vault Consolidation",
                "binder": "runbook",
                "files": ["README.md", "notes.md"],
            }
            resp = await self.client.post("/api/knowledge/import", json=payload)
            assert resp.status == 200
            data = await resp.json()

            assert data["status"] == "started"
            assert data["ingest_context"]["mission"] == "Vault Consolidation"
            assert data["ingest_context"]["binder"] == "runbook"
            assert data["ingest_context"]["files"] == ["README.md", "notes.md"]

            await asyncio.sleep(0)
            assert captured["ingest_context"] == {
                "mission": "Vault Consolidation",
                "binder": "runbook",
                "files": ["README.md", "notes.md"],
            }
        finally:
            af_config.load_config = old_load_config
            af_sync.run_import = old_run_import
            asyncio.ensure_future = old_ensure_future

    async def test_import_uses_empty_ingest_context_when_not_provided(self):
        from app.af_manager import config as af_config
        from app.af_manager import sync as af_sync

        old_load_config = af_config.load_config
        old_run_import = af_sync.run_import
        old_ensure_future = asyncio.ensure_future

        captured: dict[str, object] = {}

        def fake_load_config(config_path=None):
            return {
                "sources": [
                    {
                        "name": "Vault",
                        "local_path": "~/Vault",
                        "enabled": True,
                        "tags": [],
                    }
                ]
            }

        def fake_run_import(config, progress_callback=None, ingest_context=None):
            captured["ingest_context"] = ingest_context
            return {"status": "completed"}

        def run_immediately(coro):
            return asyncio.get_event_loop().create_task(coro)

        af_config.load_config = fake_load_config
        af_sync.run_import = fake_run_import
        asyncio.ensure_future = run_immediately

        try:
            resp = await self.client.post("/api/knowledge/import", json={"source": "Vault"})
            assert resp.status == 200
            data = await resp.json()

            assert data["status"] == "started"
            assert data["ingest_context"] == {}

            await asyncio.sleep(0)
            assert captured["ingest_context"] == {}
        finally:
            af_config.load_config = old_load_config
            af_sync.run_import = old_run_import
            asyncio.ensure_future = old_ensure_future
