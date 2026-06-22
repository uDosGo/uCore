"""Focused tests for workflow surface status helpers."""
from __future__ import annotations

from pathlib import Path

from app.services.workflow_status import (
    build_workflow_status,
    scan_tasker_boards,
)


def test_scan_tasker_boards(tmp_path: Path):
    tasker_dir = tmp_path / ".tasker"
    (tasker_dir / "inbox").mkdir(parents=True)
    (tasker_dir / "doing").mkdir(parents=True)
    (tasker_dir / "inbox" / "todo-first.md").write_text(
        "# First\n",
        encoding="utf-8",
    )
    (tasker_dir / "doing" / "doing-second.md").write_text(
        "# Second\n",
        encoding="utf-8",
    )

    result = scan_tasker_boards(tasker_dir)

    assert result["exists"] is True
    assert result["count"] == 2
    assert result["total_items"] == 2
    assert {board["name"] for board in result["boards"]} == {"doing", "inbox"}


def test_build_workflow_status_includes_guardrails(
    tmp_path: Path,
    monkeypatch,
):
    import app.services.workflow_status as mod

    tasker_dir = tmp_path / ".tasker"
    tasker_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "default_tasker_dir", lambda: tasker_dir)

    result = build_workflow_status(
        maintenance={
            "status": "ok",
            "jobs": [{"skill_id": "brain_sync"}],
            "tray": {"status": "running", "pid": 1234},
        }
    )

    assert result["engine"]["name"] == "Cline Kanban"
    assert result["engine"]["bind"] == "127.0.0.1:3484"
    assert any("localhost" in rule for rule in result["guardrails"])
    assert result["maintenance"]["jobs"][0]["skill_id"] == "brain_sync"
    assert result["maintenance"]["tray"]["status"] == "running"
