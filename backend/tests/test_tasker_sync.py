"""Focused tests for the Markdown-first Tasker workflow bridge."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.tasker_bridge import export_rows_to_tasker


def test_export_rows_to_tasker_writes_markdown(tmp_path: Path):
    rows = [
        {
            "id": 42,
            "title": "Ship workflow bridge",
            "status": "todo",
            "description": "Export markdown tasks from AppFlowy.",
            "notes": "Keep it local-first.",
        },
    ]
    result = export_rows_to_tasker(
        rows,
        tasker_dir=str(tmp_path / ".tasker"),
        board="inbox",
    )

    assert result["count"] == 1
    output = Path(result["exports"][0]["file"])
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "# Ship workflow bridge" in text
    assert "status: todo" in text
    assert "Export markdown tasks from AppFlowy." in text


def test_export_rows_to_tasker_normalizes_aliases(tmp_path: Path):
    rows = [
        {
            "id": "abc-123",
            "title": "Normalize metadata",
            "status": "done",
            "project": "Core Stability",
            "work_item": "Normalize metadata",
            "notebook": "ops",
            "urgency": "urgent",
            "labels": "ops, weekly, ops",
            "description": "Ensure canonical markdown output.",
        },
    ]

    result = export_rows_to_tasker(
        rows,
        tasker_dir=str(tmp_path / ".tasker"),
        board="inbox",
    )

    output = Path(result["exports"][0]["file"])
    text = output.read_text(encoding="utf-8")
    assert "status: completed" in text
    assert "priority: high" in text
    assert "mission: Core Stability" in text
    assert "task: Normalize metadata" in text
    assert "binder: ops" in text
    assert "tags: ops, weekly" in text


@pytest.mark.asyncio
async def test_tasker_sync_skill_exports_query_rows(
    tmp_path: Path,
    monkeypatch,
):
    import app.skills.builtin.tasker_sync as mod

    monkeypatch.setattr(
        mod,
        "discover_databases",
        lambda: {"database": "/tmp/fake.db"},
    )
    monkeypatch.setattr(
        mod,
        "run_query",
        lambda db_path, sql, params, write: {
            "rows": [
                {
                    "id": "abc",
                    "title": "Wire workflow UI",
                    "status": "doing",
                    "description": "Connect S300.",
                },
            ],
            "count": 1,
        },
    )

    result = await mod.TaskerSync().run(
        db="database",
        sql="SELECT * FROM row_table LIMIT 1",
        tasker_dir=str(tmp_path / ".tasker"),
        board="doing",
    )

    assert result["success"] is True
    assert result["count"] == 1
    out_file = Path(result["exports"][0]["file"])
    assert out_file.exists()
    assert "doing" in out_file.name
