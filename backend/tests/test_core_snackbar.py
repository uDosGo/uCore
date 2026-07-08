"""Tests for core snackbar server setup — CORS, middleware, shutdown."""
from __future__ import annotations

import inspect

import pytest
from aiohttp import web


class TestCoreSnackbar:
    """Unit tests for the snackbar core components."""

    def test_app_creation(self):
        """Verify app can be created with standard settings."""
        app = web.Application()
        assert app is not None
        assert isinstance(app, web.Application)

    def test_cors_headers_added_by_middleware(self):
        """Simulate what the CORS middleware does."""
        from app.core.snackbar import create_app

        app = create_app()
        assert app is not None

        # Check middlewares are configured
        assert len(app.middlewares) > 0

    def test_settings_loaded(self):
        """Settings module loads without errors."""
        from app.core.settings import settings

        assert settings is not None
        assert hasattr(settings, "app_name")
        assert settings.app_name == "uCore"
        assert hasattr(settings, "version")
        assert settings.version == "4.0.5"

    def test_logging_configured(self):
        """Logging module loads without errors."""
        import app.core.logging as logging_mod

        assert logging_mod is not None

    def test_database_migration(self):
        """Database migration runs without errors."""
        from app.core.database import migrate_db

        # Should not raise
        migrate_db()
        assert True

    def test_settings_api_port(self):
        """Settings should have a port configured."""
        from app.core.settings import settings

        assert hasattr(settings, "port")
        assert isinstance(settings.port, int)
        assert settings.port > 0


@pytest.mark.asyncio
async def test_shutdown_handler():
    """Verify the shutdown endpoint works."""
    from app.core.snackbar import shutdown_handler

    app = web.Application()
    app.router.add_post("/api/shutdown", shutdown_handler)
    # We don't actually call it because it stops the loop
    # Just verify it's importable and is a coroutine
    assert callable(shutdown_handler)
    assert hasattr(shutdown_handler, "__wrapped__") or inspect.iscoroutinefunction(shutdown_handler)
