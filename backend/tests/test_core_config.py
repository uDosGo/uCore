"""Tests for the unified configuration loader."""
from __future__ import annotations

from app.core.config import get_config


def test_config_loads_defaults():
    cfg = get_config()
    assert isinstance(cfg.github.token, str)
    assert isinstance(cfg.mcp.server_port, int)
    assert cfg.mcp.server_port == 8765
    assert isinstance(cfg.database.path, str)
    assert cfg.database.path == "./ucore.db"
    assert isinstance(cfg.logging.level, str)
    assert cfg.logging.level == "INFO"


def test_config_has_cline_principles():
    cfg = get_config()
    principles = cfg.cline.operating_principles if cfg.cline else []
    assert principles
    assert "Prefer safe, reversible changes" in principles[0]