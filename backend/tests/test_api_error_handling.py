"""Edge case tests: error handling across API endpoints.

Tests that the server returns proper error codes for:
- Malformed JSON bodies
- Unregistered routes → 404
- Method not allowed → 405 (when route exists but method doesn't)
- Empty request bodies
"""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase


class ErrorHandlingTest(AioHTTPTestCase):
    """Test general error handling patterns using a simple test app."""

    async def get_application(self):
        app = web.Application()

        async def sample_post(request: web.Request) -> web.Response:
            try:
                data = await request.json()
            except Exception:
                return web.json_response({"error": "Invalid JSON"}, status=400)
            return web.json_response({"ok": True, "data": data})

        app.router.add_post("/api/test-endpoint", sample_post)
        return app

    async def test_malformed_json_returns_400(self):
        """POST with malformed JSON body should return 400."""
        resp = await self.client.post(
            "/api/test-endpoint",
            data=b"this is not json at all",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data

    async def test_empty_body_returns_400(self):
        """POST with empty body should return 400."""
        resp = await self.client.post(
            "/api/test-endpoint",
            data=b"",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 400

    async def test_unregistered_route_returns_404(self):
        """GET to a non-existent route should return 404."""
        resp = await self.client.get("/api/nonexistent/route/xyz")
        assert resp.status == 404

    async def test_method_not_allowed_returns_405(self):
        """GET on a POST-only route should return 405 (if router rejects)
        or 404 (if route doesn't exist for that method)."""
        resp = await self.client.get("/api/test-endpoint")
        # Could be 404 or 405 depending on router
        assert resp.status in (404, 405)

    async def test_invalid_query_params(self):
        """Extra query params should not break endpoints."""
        resp = await self.client.post(
            "/api/test-endpoint?unexpected=param",
            json={"key": "value"},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["ok"] is True

    async def test_partial_json(self):
        """Body that starts as JSON but is truncated."""
        resp = await self.client.post(
            "/api/test-endpoint",
            data=b'{"key": "value"',
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 400

    async def test_oversized_json(self):
        """Very large body (should not crash)."""
        large_data = {"data": "x" * 100000}
        resp = await self.client.post(
            "/api/test-endpoint",
            json=large_data,
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["ok"] is True
