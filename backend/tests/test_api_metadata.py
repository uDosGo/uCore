"""Integration tests for System Metadata API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.api.metadata import _get_tray_state, system_info_handler


class MetadataAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/system", system_info_handler)
        return app

    async def test_system_info(self):
        resp = await self.client.get("/api/system")
        assert resp.status == 200
        data = await resp.json()
        assert "platform" in data
        assert "machine" in data
        assert "python" in data
        assert "hostname" in data
        assert "app" in data
        assert "version" in data
        assert data["app"] == "uCore"
        assert data["version"] == "4.0.0"

    async def test_system_info_has_python_version(self):
        resp = await self.client.get("/api/system")
        data = await resp.json()
        # Python version should be a string like "3.14.x"
        assert data["python"].startswith("3")
        assert data["python"].count(".") >= 2


def test_get_tray_state_missing_lock(monkeypatch, tmp_path):
    import app.api.metadata as mod

    monkeypatch.setattr(mod, "POPCORN_PID_FILE", tmp_path / "missing.pid")

    state = _get_tray_state()

    assert state["status"] == "stopped"
    assert state["pid"] is None


def test_get_tray_state_running(monkeypatch, tmp_path):
    import app.api.metadata as mod

    pid_file = tmp_path / "popcorn.pid"
    pid_file.write_text("4321\n", encoding="utf-8")
    monkeypatch.setattr(mod, "POPCORN_PID_FILE", pid_file)

    def fake_kill(pid: int, sig: int):
        assert pid == 4321
        assert sig == 0

    monkeypatch.setattr(mod.os, "kill", fake_kill)

    state = _get_tray_state()

    assert state["status"] == "running"
    assert state["pid"] == 4321


def test_get_tray_state_stale_lock(monkeypatch, tmp_path):
    import app.api.metadata as mod

    pid_file = tmp_path / "popcorn.pid"
    pid_file.write_text("99999\n", encoding="utf-8")
    monkeypatch.setattr(mod, "POPCORN_PID_FILE", pid_file)

    def fake_kill(_pid: int, _sig: int):
        raise ProcessLookupError

    monkeypatch.setattr(mod.os, "kill", fake_kill)

    state = _get_tray_state()

    assert state["status"] == "stale-lock"
    assert state["pid"] is None


def test_get_service_status_includes_ai_runtime(monkeypatch):
    import app.api.metadata as mod

    class FakeRouter:
        def stats(self):
            return {
                "requests": 2,
                "average_latency_ms": 12.5,
                "cache": {"hit_ratio": 0.5},
            }

    monkeypatch.setattr(
        "app.services.provider_router.get_router",
        lambda: FakeRouter(),
    )

    services = mod._get_service_status()

    assert services["ai_runtime"]["requests"] == 2
    assert services["ai_runtime"]["cache"]["hit_ratio"] == 0.5
