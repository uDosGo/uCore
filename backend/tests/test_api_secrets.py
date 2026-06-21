"""Integration tests for Secret Store API endpoints."""
from __future__ import annotations

import os
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.secret.store import SecretStore


class SecretsAPITest(AioHTTPTestCase):
    async def get_application(self):
        # Create a fresh in-memory secret store for tests
        self._store = SecretStore()
        self._store._secrets = {}
        self._store._dirty = False
        import app.api.secret_store_api as mod
        import app.secret.store as store_mod
        store_mod._store = self._store

        from app.api.secret_store_api import (
            handle_list_secrets, handle_get_secret, handle_set_secret,
            handle_delete_secret, handle_list_env_vars, handle_import_from_env,
        )

        app = web.Application()
        app.router.add_get("/api/secrets", handle_list_secrets)
        app.router.add_get("/api/secrets/env", handle_list_env_vars)
        app.router.add_post("/api/secrets/import-env", handle_import_from_env)
        app.router.add_get("/api/secrets/{name}", handle_get_secret)
        app.router.add_post("/api/secrets/{name}", handle_set_secret)
        app.router.add_delete("/api/secrets/{name}", handle_delete_secret)
        return app

    async def asyncTearDown(self):
        self._store._secrets = {}
        await super().asyncTearDown()

    async def test_list_secrets_empty(self):
        resp = await self.client.get("/api/secrets")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 0
        assert data["secrets"] == []

    async def test_set_and_get_secret(self):
        resp = await self.client.post("/api/secrets/TEST_KEY", json={"value": "test_value_123"})
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "saved"
        assert data["name"] == "TEST_KEY"

        # Verify via GET
        resp = await self.client.get("/api/secrets/TEST_KEY")
        assert resp.status == 200
        data = await resp.json()
        assert data["name"] == "TEST_KEY"
        assert data["value"] == "test_value_123"

    async def test_get_nonexistent_secret(self):
        resp = await self.client.get("/api/secrets/DOES_NOT_EXIST")
        assert resp.status == 404
        data = await resp.json()
        assert "error" in data

    async def test_delete_secret(self):
        # Set first
        await self.client.post("/api/secrets/DELETE_ME", json={"value": "to_delete"})
        # Delete
        resp = await self.client.delete("/api/secrets/DELETE_ME")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "deleted"

        # Verify gone
        resp = await self.client.get("/api/secrets/DELETE_ME")
        assert resp.status == 404

    async def test_delete_nonexistent(self):
        resp = await self.client.delete("/api/secrets/ALREADY_GONE")
        assert resp.status == 404

    async def test_set_secret_invalid_json(self):
        resp = await self.client.post("/api/secrets/BAD", data=b"not json",
                                       headers={"Content-Type": "application/json"})
        assert resp.status == 400

    async def test_set_secret_empty_value(self):
        resp = await self.client.post("/api/secrets/EMPTY", json={"value": ""})
        assert resp.status == 400

    async def test_list_env_vars(self):
        resp = await self.client.get("/api/secrets/env")
        assert resp.status == 200
        data = await resp.json()
        assert "env_vars" in data
        assert "count" in data

    async def test_import_from_env(self):
        resp = await self.client.post("/api/secrets/import-env")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "imported"

    async def test_list_after_set(self):
        await self.client.post("/api/secrets/KEY_A", json={"value": "val_a"})
        await self.client.post("/api/secrets/KEY_B", json={"value": "val_b"})
        resp = await self.client.get("/api/secrets")
        data = await resp.json()
        assert data["count"] == 2
        names = [s["name"] for s in data["secrets"]]
        assert "KEY_A" in names
        assert "KEY_B" in names
