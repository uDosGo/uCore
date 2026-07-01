from __future__ import annotations

from pathlib import Path

import pytest
from app.services.tasker_ops import (
    list_tasker_boards,
    read_task_markdown,
    write_task_markdown,
)


def test_write_task_markdown_creates_file(tmp_path: Path):
    result = write_task_markdown(
        title="Ship Tasker MCP",
        board="doing",
        status="in-progress",
        body="Expose read and write operations.",
        tasker_dir=str(tmp_path / ".tasker"),
        source="manual",
        source_id="udw-006",
        metadata={"priority": "P1"},
    )

    output = Path(result["path"])
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "# Ship Tasker MCP" in text
    assert "status: in-progress" in text
    assert "priority: P1" in text


def test_read_task_markdown_returns_content(tmp_path: Path):
    task_dir = tmp_path / ".tasker" / "inbox"
    task_dir.mkdir(parents=True)
    task_file = task_dir / "todo-sample-1.md"
    task_file.write_text("# Sample\n", encoding="utf-8")

    result = read_task_markdown(
        board="inbox",
        task="todo-sample-1.md",
        tasker_dir=str(tmp_path / ".tasker"),
    )

    assert result["task"] == "todo-sample-1.md"
    assert result["content"] == "# Sample\n"


def test_list_tasker_boards_counts_items(tmp_path: Path):
    inbox = tmp_path / ".tasker" / "inbox"
    doing = tmp_path / ".tasker" / "doing"
    inbox.mkdir(parents=True)
    doing.mkdir(parents=True)
    (inbox / "todo-a.md").write_text("# A\n", encoding="utf-8")
    (doing / "doing-b.md").write_text("# B\n", encoding="utf-8")

    result = list_tasker_boards(str(tmp_path / ".tasker"))

    assert result["count"] == 2
    assert result["total_items"] == 2


def test_read_task_markdown_rejects_path_escape(tmp_path: Path):
    with pytest.raises(ValueError):
        read_task_markdown(
            board="../escape",
            task="task.md",
            tasker_dir=str(tmp_path / ".tasker"),
        )
