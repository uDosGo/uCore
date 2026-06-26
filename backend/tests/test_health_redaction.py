"""Tests for the safe health clean and truncate functions."""
from __future__ import annotations

from pathlib import Path
from app.services.health import _clean_and_truncate_line, recent_errors_from_logs


def test_clean_and_truncate_line_normal():
    line = "Everything is fine and working nicely here"
    assert _clean_and_truncate_line(line) == line


def test_clean_and_truncate_line_too_long():
    line = "A" * 200
    cleaned = _clean_and_truncate_line(line, max_len=50)
    assert len(cleaned) == 53  # 50 + 3 dots
    assert cleaned.endswith("...")


def test_clean_and_truncate_line_redacts_keys():
    line = "ERROR: Failed to auth, API_KEY: 12ab34cd56eg78ij90klmn-op"
    cleaned = _clean_and_truncate_line(line)
    assert "API_KEY" in cleaned
    assert "12ab34cd" not in cleaned
    assert "[REDACTED]" in cleaned


def test_clean_and_truncate_line_redacts_auth_header():
    line = "CRITICAL: Authorization = Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    cleaned = _clean_and_truncate_line(line)
    assert "Authorization" in cleaned
    assert "Bearer" in cleaned
    assert "eyJhb" not in cleaned
    assert "[REDACTED]" in cleaned
