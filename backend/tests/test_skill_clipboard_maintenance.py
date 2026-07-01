from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_clipboard_maintenance_captures_and_cleans(monkeypatch):
    from app.skills.builtin.clipboard_maintenance import ClipboardMaintenance

    def fake_capture_current_clipboard(*, source: str, metadata: dict):
        assert source == "maintenance"
        assert metadata.get("trigger") == "maintenance_scheduler"
        return {"id": "clip_1", "source": source}

    def fake_cleanup_history(*, max_items: int, max_days: int):
        assert max_items == 123
        assert max_days == 7
        return {"removed_age": 2, "removed_overflow": 1}

    monkeypatch.setattr(
        "app.skills.builtin.clipboard_maintenance.capture_current_clipboard",
        fake_capture_current_clipboard,
    )
    monkeypatch.setattr(
        "app.skills.builtin.clipboard_maintenance.cleanup_history",
        fake_cleanup_history,
    )

    result = await ClipboardMaintenance().run(max_items=123, max_days=7)

    assert result["success"] is True
    assert result["capture"]["status"] == "captured"
    assert result["capture"]["item_id"] == "clip_1"
    assert result["cleanup"] == {"removed_age": 2, "removed_overflow": 1}


@pytest.mark.asyncio
async def test_clipboard_maintenance_skips_empty_clipboard(monkeypatch):
    from app.skills.builtin.clipboard_maintenance import ClipboardMaintenance

    def fake_capture_current_clipboard(*, source: str, metadata: dict):
        raise ValueError("Clipboard is empty")

    def fake_cleanup_history(*, max_items: int, max_days: int):
        return {"removed_age": 0, "removed_overflow": 0}

    monkeypatch.setattr(
        "app.skills.builtin.clipboard_maintenance.capture_current_clipboard",
        fake_capture_current_clipboard,
    )
    monkeypatch.setattr(
        "app.skills.builtin.clipboard_maintenance.cleanup_history",
        fake_cleanup_history,
    )

    result = await ClipboardMaintenance().run()

    assert result["success"] is True
    assert result["capture"]["status"] == "skipped"
    assert "empty" in result["capture"]["reason"].lower()
