"""Integration tests for Snack API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.api.snacks import register_snack_routes
from app.services.snackbar_orchestrator import SnackbarOrchestrator


class SnackAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        import app.api.snacks as mod
        mod._orch = SnackbarOrchestrator(persist=False)
        register_snack_routes(app)
        return app

    async def test_queue_snack(self):
        resp = await self.client.post("/api/snacks", json={
            "type": "task", "priority": "high", "content": {"cmd": "build"}, "source": "test",
        })
        assert resp.status == 201
        data = await resp.json()
        assert data["type"] == "task"
        assert data["priority"] == 1  # HIGH = 1

    async def test_queue_snack_invalid_type(self):
        resp = await self.client.post("/api/snacks", json={"type": "invalid"})
        assert resp.status == 400

    async def test_queue_snack_invalid_priority(self):
        resp = await self.client.post("/api/snacks", json={"type": "task", "priority": "invalid"})
        assert resp.status == 400

    async def test_queue_snack_invalid_json(self):
        resp = await self.client.post("/api/snacks", data=b"not json",
                                       headers={"Content-Type": "application/json"})
        assert resp.status == 400

    async def test_list_queue(self):
        await self.client.post("/api/snacks", json={"type": "message", "content": {"msg": "hi"}})
        await self.client.post("/api/snacks", json={"type": "task", "content": {"cmd": "go"}})
        resp = await self.client.get("/api/snacks")
        assert resp.status == 200
        data = await resp.json()
        assert data["pending"] == 2

    async def test_list_queue_empty(self):
        resp = await self.client.get("/api/snacks")
        assert resp.status == 200
        data = await resp.json()
        assert data["pending"] == 0
        assert data["snacks"] == []

    async def test_deliver_snack(self):
        cr = await self.client.post("/api/snacks", json={"type": "message", "content": {"msg": "go"}})
        cid = (await cr.json())["id"]
        resp = await self.client.post(f"/api/snacks/{cid}/deliver")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "delivered"

    async def test_deliver_nonexistent(self):
        resp = await self.client.post("/api/snacks/nonexistent/deliver")
        assert resp.status == 404

    async def test_deliver_already_delivered(self):
        """Delivering an already delivered snack returns 404 (consumed from queue)."""
        cr = await self.client.post("/api/snacks", json={"type": "message", "content": {}})
        cid = (await cr.json())["id"]
        await self.client.post(f"/api/snacks/{cid}/deliver")
        # After delivery, the snack is consumed and no longer in the pending queue
        resp = await self.client.post(f"/api/snacks/{cid}/deliver")
        assert resp.status == 404

    async def test_fail_snack(self):
        cr = await self.client.post("/api/snacks", json={"type": "task", "content": {}})
        cid = (await cr.json())["id"]
        resp = await self.client.post(f"/api/snacks/{cid}/fail")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "failed"

    async def test_fail_nonexistent(self):
        resp = await self.client.post("/api/snacks/nonexistent/fail")
        assert resp.status == 404

    async def test_retry_snack(self):
        cr = await self.client.post("/api/snacks", json={"type": "task", "content": {}})
        cid = (await cr.json())["id"]
        await self.client.post(f"/api/snacks/{cid}/fail")
        resp = await self.client.post(f"/api/snacks/{cid}/retry")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "queued"
        assert data["retry_count"] == 1

    async def test_retry_nonexistent(self):
        resp = await self.client.post("/api/snacks/nonexistent/retry")
        assert resp.status == 404

    async def test_get_history(self):
        for i in range(3):
            cr = await self.client.post("/api/snacks", json={"type": "message", "content": {"i": i}})
            cid = (await cr.json())["id"]
            await self.client.post(f"/api/snacks/{cid}/deliver")
        resp = await self.client.get("/api/snacks/history")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 3

    async def test_get_history_empty(self):
        resp = await self.client.get("/api/snacks/history")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 0

    async def test_clear_queue(self):
        await self.client.post("/api/snacks", json={"type": "message", "content": {}})
        await self.client.post("/api/snacks", json={"type": "message", "content": {}})
        resp = await self.client.delete("/api/snacks/queue")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 2

    async def test_clear_queue_empty(self):
        resp = await self.client.delete("/api/snacks/queue")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 0
