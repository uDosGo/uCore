"""Tasker API — expose .tasker markdown boards as structured data.

Provides:
- GET /api/developer/tasker/boards — list all boards with task counts
- GET /api/developer/tasker/board/{board_name} — list all tasks in a board
- GET /api/developer/tasker/tasks — all tasks across boards (for Kanban)
- GET /api/developer/tasker/summary — aggregate stats by status
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aiohttp import web

from app.services.workflow_status import default_tasker_dir, scan_tasker_boards

log = logging.getLogger("ucore.api.tasker")


def _parse_markdown_task(path: Path) -> dict[str, Any]:
    """Parse a single .tasker markdown file into a structured dict."""
    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    task: dict[str, Any] = {
        "id": path.stem,
        "title": "",
        "description": "",
        "status": "todo",
        "priority": "medium",
        "board": path.parent.name,
        "source": "manual",
        "source_id": "",
        "tags": [],
        "file": str(path),
        "body": "",
    }

    in_summary = False
    summary_parts: list[str] = []
    body_parts: list[str] = []

    for line in lines:
        if line.startswith("# ") and not task["title"]:
            task["title"] = line[2:].strip()
        elif line.startswith("- status:"):
            val = line[len("- status:"):].strip()
            # Normalize "done" to "completed" for Kanban compatibility
            task["status"] = "completed" if val == "done" else val
        elif line.startswith("- source:"):
            task["source"] = line[len("- source:"):].strip()
            val = line[len("- source:"):].strip()
            if val and val not in task["tags"]:
                task["tags"].append(val)
        elif line.startswith("- priority:"):
            task["priority"] = line[len("- priority:"):].strip()
        elif line.startswith("- source_id:"):
            task["source_id"] = line[len("- source_id:"):].strip()
        elif line.startswith("- assignee:"):
            task["assignee"] = line[len("- assignee:"):].strip()
        elif line.startswith("- due:"):
            task["dueDate"] = line[len("- due:"):].strip()
        elif line == "## Summary":
            in_summary = True
        elif in_summary and line.startswith("- "):
            summary_parts.append(line[2:].strip())
        elif in_summary and line.startswith("## "):
            in_summary = False
        elif not line.startswith("#") and not line.startswith("-") and line.strip():
            body_parts.append(line.strip())

    task["description"] = "\n".join(summary_parts) if summary_parts else "\n".join(body_parts)
    task["body"] = "\n".join(body_parts) if body_parts else task["description"]

    # Derive status from filename prefix
    name_lower = path.stem.lower()
    if not task["status"] or task["status"] == "unknown":
        if name_lower.startswith("done-"):
            task["status"] = "completed"
        elif name_lower.startswith("in-progress-"):
            task["status"] = "in-progress"
        elif name_lower.startswith("todo-"):
            task["status"] = "todo"
        elif name_lower.startswith("wip-"):
            task["status"] = "in-progress"
        elif name_lower.startswith("blocked-"):
            task["status"] = "blocked"

    return task


async def handle_list_boards(request: web.Request) -> web.Response:
    """GET /api/developer/tasker/boards — list all tasker boards."""
    tasker = scan_tasker_boards()
    return web.json_response(tasker)


async def handle_list_board_tasks(request: web.Request) -> web.Response:
    """GET /api/developer/tasker/board/{board_name} — list all tasks in a board."""
    board_name = request.match_info.get("board_name", "")
    if not board_name:
        return web.json_response({"error": "board_name required"}, status=400)

    base = default_tasker_dir()
    board_path = base / board_name
    if not board_path.exists() or not board_path.is_dir():
        return web.json_response({"error": f"Board '{board_name}' not found"}, status=404)

    tasks: list[dict[str, Any]] = []
    for md_file in sorted(board_path.glob("*.md")):
        tasks.append(_parse_markdown_task(md_file))

    return web.json_response({
        "board": board_name,
        "path": str(board_path),
        "count": len(tasks),
        "tasks": tasks,
    })


async def handle_all_tasks(request: web.Request) -> web.Response:
    """GET /api/developer/tasker/tasks — all tasks across all boards (for Kanban)."""
    base = default_tasker_dir()
    tasks: list[dict[str, Any]] = []

    if base.exists():
        for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            for md_file in sorted(board_dir.glob("*.md")):
                if md_file.name == "README.md":
                    continue
                tasks.append(_parse_markdown_task(md_file))

    return web.json_response({
        "tasker_dir": str(base),
        "count": len(tasks),
        "tasks": tasks,
    })


async def handle_workflow_tasks(request: web.Request) -> web.Response:
    """GET /api/workflow/tasks — tasks filtered by board/tag (for WorkflowSurface).
    
    Query params:
      - board: filter by board name (substring match)
      - tag: filter by tag (exact match)
    """
    base = default_tasker_dir()
    board_filter = request.query.get("board", "").lower()
    tag_filter = request.query.get("tag", "").lower()
    tasks: list[dict[str, Any]] = []

    if base.exists():
        for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            if board_filter and board_filter not in board_dir.name.lower():
                continue
            for md_file in sorted(board_dir.glob("*.md")):
                if md_file.name == "README.md":
                    continue
                task = _parse_markdown_task(md_file)
                tags = [t.lower() for t in task.get("tags", [])]
                if tag_filter and tag_filter not in tags:
                    continue
                tasks.append(task)

    return web.json_response({
        "tasker_dir": str(base),
        "count": len(tasks),
        "board_filter": board_filter or None,
        "tag_filter": tag_filter or None,
        "tasks": tasks,
    })


async def handle_tasker_summary(request: web.Request) -> web.Response:
    """GET /api/developer/tasker/summary — aggregate stats by status."""
    base = default_tasker_dir()
    status_counts: dict[str, int] = {}
    board_counts: dict[str, int] = {}
    total = 0

    if base.exists():
        for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            count = 0
            for md_file in board_dir.glob("*.md"):
                if md_file.name == "README.md":
                    continue
                task = _parse_markdown_task(md_file)
                status = task.get("status", "todo") or "todo"
                status_counts[status] = status_counts.get(status, 0) + 1
                total += 1
                count += 1
            if count > 0:
                board_counts[board_dir.name] = count

    return web.json_response({
        "tasker_dir": str(base),
        "total": total,
        "by_status": status_counts,
        "by_board": board_counts,
        "status_keys": sorted(status_counts.keys()),
        "board_keys": sorted(board_counts.keys()),
    })


def register_tasker_routes(app: web.Application) -> None:
    """Register tasker API routes under /api/developer/tasker/."""
    app.router.add_get("/api/developer/tasker/boards", handle_list_boards)
    app.router.add_get("/api/developer/tasker/board/{board_name}", handle_list_board_tasks)
    app.router.add_get("/api/developer/tasker/tasks", handle_all_tasks)
    app.router.add_get("/api/developer/tasker/summary", handle_tasker_summary)
