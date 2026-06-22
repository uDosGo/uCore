from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.tasker_bridge import render_task_markdown, slugify
from app.services.workflow_status import default_tasker_dir, scan_tasker_boards


def resolve_tasker_dir(tasker_dir: str | None = None) -> Path:
    if tasker_dir:
        return Path(tasker_dir).expanduser()
    return default_tasker_dir()


def _validate_segment(value: str, label: str) -> str:
    segment = value.strip()
    if not segment:
        raise ValueError(f"{label} is required")
    if segment in {".", ".."}:
        raise ValueError(f"Invalid {label}")
    if "/" in segment or "\\" in segment:
        raise ValueError(f"Invalid {label}")
    return segment


def list_tasker_boards(tasker_dir: str | None = None) -> dict[str, Any]:
    base = resolve_tasker_dir(tasker_dir)
    return scan_tasker_boards(base)


def read_task_markdown(
    *,
    board: str,
    task: str,
    tasker_dir: str | None = None,
) -> dict[str, Any]:
    base = resolve_tasker_dir(tasker_dir)
    board_name = _validate_segment(board, "board")
    task_name = _validate_segment(task, "task")
    if not task_name.endswith(".md"):
        task_name = f"{task_name}.md"

    path = (base / board_name / task_name).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError("Task path escapes tasker directory")
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(task_name)

    content = path.read_text(encoding="utf-8")
    return {
        "tasker_dir": str(base),
        "board": board_name,
        "task": path.name,
        "path": str(path),
        "content": content,
    }


def write_task_markdown(
    *,
    title: str,
    board: str = "inbox",
    status: str = "todo",
    body: str = "",
    source: str = "manual",
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    task: str | None = None,
    tasker_dir: str | None = None,
) -> dict[str, Any]:
    base = resolve_tasker_dir(tasker_dir)
    board_name = _validate_segment(board, "board")
    title_text = title.strip()
    if not title_text:
        raise ValueError("title is required")

    status_text = status.strip().lower() or "todo"
    source_text = source.strip() or "manual"
    source_id_text = (
        (source_id or slugify(title_text)).strip()
        or slugify(title_text)
    )

    if task:
        task_name = _validate_segment(task, "task")
        if not task_name.endswith(".md"):
            task_name = f"{task_name}.md"
    else:
        task_name = (
            f"{status_text}-{slugify(title_text)}-"
            f"{slugify(source_id_text)}.md"
        )

    out_dir = base / board_name
    out_dir.mkdir(parents=True, exist_ok=True)
    path = (out_dir / task_name).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError("Task path escapes tasker directory")

    payload = metadata.copy() if metadata else {}
    content = render_task_markdown(
        title=title_text,
        source=source_text,
        source_id=source_id_text,
        status=status_text,
        body=body.strip(),
        metadata=payload,
    )
    path.write_text(content, encoding="utf-8")

    return {
        "tasker_dir": str(base),
        "board": board_name,
        "task": path.name,
        "path": str(path),
        "status": status_text,
        "title": title_text,
        "source": source_text,
        "source_id": source_id_text,
        "written": True,
    }
