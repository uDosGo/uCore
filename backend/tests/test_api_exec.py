"""Integration tests for Exec API endpoint."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.exec import handle_exec


class ExecAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_post("/api/exec", handle_exec)
        return app

    async def test_exec_echo(self):
        resp = await self.client.post("/api/exec", json={"command": "echo hello ucore"})
        assert resp.status == 200
        data = await resp.json()
        assert "stdout" in data
        assert data["exit_code"] == 0
        assert "hello ucore" in data["stdout"]

    async def test_exec_no_command(self):
        resp = await self.client.post("/api/exec", json={})
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data

    async def test_exec_empty_command(self):
        resp = await self.client.post("/api/exec", json={"command": ""})
        assert resp.status == 400

    async def test_exec_invalid_json(self):
        resp = await self.client.post("/api/exec", data=b"not json",
                                       headers={"Content-Type": "application/json"})
        assert resp.status == 400

    async def test_exec_unsafe_command_rejected(self):
        resp = await self.client.post("/api/exec", json={"command": "rm -rf /"})
        assert resp.status == 400
        data = await resp.json()
        assert "safety" in data.get("error", "").lower() or "rejected" in data.get("error", "").lower()

    async def test_exec_which_python(self):
        resp = await self.client.post("/api/exec", json={"command": "which python3"})
        assert resp.status == 200
        data = await resp.json()
        assert data["exit_code"] == 0
        assert "python" in data["stdout"].lower()

    async def test_exec_with_timeout(self):
        resp = await self.client.post("/api/exec", json={"command": "echo timeout_test", "timeout": 5})
        assert resp.status == 200
        data = await resp.json()
        assert "timeout_test" in data["stdout"]
