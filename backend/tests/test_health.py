"""Test the uCore health endpoint."""
from __future__ import annotations


def test_settings_import():
    """Smoke test — settings module imports correctly."""
    from app.core.settings import Settings
    s = Settings()
    assert s.app_name == "uCore"
    assert s.version == "4.0.0"


def test_logging_import():
    """Smoke test — logging module imports correctly."""
    from app.core.logging import setup_logging
    logger = setup_logging()
    assert logger.name == "ucore"


def test_snackbar_import():
    """Smoke test — snackbar creates app without errors."""
    from app.core.snackbar import create_app
    app = create_app()
    assert app is not None
    routes = list(app.router.routes())
    assert len(routes) >= 4  # health, version, info, shutdown + system

