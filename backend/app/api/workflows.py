"""Workflows API — Task management, board health, and markdown task operations."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aiohttp import web

from app.services.workflow_status import default_tasker_dir, scan_tasker_boards
from app.services.tasker_bridge import slugify

log = logging.getLogger("ucore.api.workflows")

# ─── In-memory import job tracking ──────────────────────────────────
_import_jobs: dict[str, dict[str, Any]] = {}

TRACKED_FIELDS = {"status", "progress", "message", "timestamp", "task_id"}


def record_import_job(
    task_id: str,
    status: str = "queued",
    progress: int = 0,
    message: str = "",
) -> None:
    """Record or update an import job in the in-memory tracker."""
    _import_jobs[task_id] = {
        "id": task_id,
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # Keep only the last 50 jobs
    if len(_import_jobs) > 50:
        oldest = sorted(_import_jobs.keys())[:len(_import_jobs) - 50]
        for k in oldest:
            _import_jobs.pop(k, None)


# ─── Handlers ───────────────────────────────────────────────────────


async def handle_import_status(request: web.Request) -> web.Response:
    """GET /api/knowledge/import/status — return recent import job statuses.

    Returns:
      { "jobs": [{id, status, progress, message, timestamp}] }
    """
    jobs = list(_import_jobs.values())
    # Sort newest first
    jobs.sort(key=lambda j: j.get("timestamp", ""), reverse=True)
    return web.json_response({"jobs": jobs})


async def handle_index_coverage(request: web.Request) -> web.Response:
    """GET /api/knowledge/index/coverage — per-source coverage metrics.

    Returns:
      {
        "coverage": [{source, expected, indexed, coverage_percent}],
        "total_docs": int,
        "coverage_pct": float
      }
    """
    from app.af_manager.config import load_config
    from app.af_manager.sync import get_index_coverage

    config_path = request.query.get("config_path")
    config = load_config(config_path)
    summary = get_index_coverage(config)

    sources = summary.get("sources", [])
    coverage_list = [
        {
            "source": s.get("source", "unknown"),
            "expected": s.get("expected_count", 0),
            "indexed": s.get("indexed_count", 0),
            "coverage_percent": s.get("coverage_pct", 0),
        }
        for s in sources
    ]

    return web.json_response({
        "coverage": coverage_list,
        "total_docs": summary.get("indexed_total", 0),
        "coverage_pct": summary.get("coverage_pct", 0),
    })


# ─── Task operations (markdown-based) ───────────────────────────────


def _find_task_file(task_id: str) -> Path | None:
    """Search .tasker/ boards for a markdown file whose frontmatter/source_id matches task_id."""
    tasker_dir = default_tasker_dir()
    if not tasker_dir.exists():
        return None

    for board_dir in tasker_dir.iterdir():
        if not board_dir.is_dir():
            continue
        for md_file in board_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="replace")
            # Check for source_id metadata line
            if f"source_id: {task_id}" in content:
                return md_file
            # Fallback: check filename slug
            if slugify(task_id) in md_file.stem:
                return md_file

    return None


def _parse_task_markdown(path: Path) -> dict[str, Any] | None:
    """Parse a .tasker markdown file into a TaskDetailData-like dict."""
    if not path or not path.exists():
        return None

    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    task: dict[str, Any] = {
        "id": path.stem,
        "title": "",
        "description": "",
        "status": "todo",
        "priority": "medium",
        "board": path.parent.name,
        "assignee": "",
        "dueDate": "",
        "tags": [],
        "metadata": {},
    }

    # Parse title from first heading
    in_summary = False
    summary_parts: list[str] = []

    for line in lines:
        if line.startswith("# ") and not task["title"]:
            task["title"] = line[2:].strip()
        elif line.startswith("- status:"):
            task["status"] = line[len("- status:"):].strip()
        elif line.startswith("- source:"):
            val = line[len("- source:"):].strip()
            if val not in task.get("tags", []):
                task.setdefault("tags", []).append(val)
        elif line.startswith("- priority:"):
            task["priority"] = line[len("- priority:"):].strip()
        elif line.startswith("- assignee:"):
            task["assignee"] = line[len("- assignee:"):].strip()
        elif line.startswith("- due:"):
            task["dueDate"] = line[len("- due:"):].strip()
        elif line.startswith("- source_id:"):
            task["id"] = line[len("- source_id:"):].strip()
        elif line == "## Summary":
            in_summary = True
        elif in_summary and line.startswith("- "):
            summary_parts.append(line[2:].strip())
        elif in_summary and line.startswith("## "):
            in_summary = False

    task["description"] = "\n".join(summary_parts) if summary_parts else ""
    return task


def _render_task_markdown(task: dict[str, Any]) -> str:
    """Render a task dict back into .tasker markdown format."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tags = task.get("tags", [])
    tags_line = f"- source: {tags[0]}" if tags else ""

    lines = [
        f"# {task.get('title', 'Untitled Task')}",
        "",
        f"- status: {task.get('status', 'todo')}",
        f"- source_id: {task.get('id', 'unknown')}",
        f"- synced_at: {ts}",
        f"- priority: {task.get('priority', 'medium')}",
    ]
    if tags_line:
        lines.append(tags_line)
    if task.get("assignee"):
        lines.append(f"- assignee: {task['assignee']}")
    if task.get("dueDate"):
        lines.append(f"- due: {task['dueDate']}")

    lines.extend([
        "",
        "## Summary",
        task.get("description", ""),
        "",
    ])

    return "\n".join(lines)


async def handle_get_task(request: web.Request) -> web.Response:
    """GET /api/workflows/task/{task_id} — fetch task details.

    Returns the parsed task from .tasker markdown files.
    """
    task_id = request.match_info.get("task_id", "")
    if not task_id:
        return web.json_response({"error": "task_id is required"}, status=400)

    md_file = _find_task_file(task_id)
    if not md_file:
        # Try scanning all boards
        return web.json_response({"error": "Task not found"}, status=404)

    task = _parse_task_markdown(md_file)
    if not task:
        return web.json_response({"error": "Failed to parse task"}, status=500)

    return web.json_response(task)


async def handle_update_task(request: web.Request) -> web.Response:
    """PUT /api/workflows/task/{task_id} — update task metadata.

    Body: TaskDetailData (id, title, status, priority, assignee, dueDate, description, tags)
    Returns the updated task.
    """
    task_id = request.match_info.get("task_id", "")
    if not task_id:
        return web.json_response({"error": "task_id is required"}, status=400)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    md_file = _find_task_file(task_id)
    if not md_file:
        return web.json_response({"error": "Task not found"}, status=404)

    # Read existing task to merge with updates
    existing = _parse_task_markdown(md_file) or {}
    merged = {**existing, **body}
    merged["id"] = task_id

    # Write updated markdown
    new_content = _render_task_markdown(merged)
    md_file.write_text(new_content, encoding="utf-8")

    log.info("Task %s updated in %s", task_id, md_file)
    return web.json_response(merged)


async def handle_board_health(request: web.Request) -> web.Response:
    """GET /api/workflows/board/{board_id}/health — check board health.

    Returns:
      { status, issues, warning_count, task_count }
    """
    board_id = request.match_info.get("board_id", "")
    if not board_id:
        return web.json_response({"error": "board_id is required"}, status=400)

    tasker = scan_tasker_boards()
    board_data = None
    for board in tasker.get("boards", []):
        if board["name"] == board_id:
            board_data = board
            break

    if not board_data:
        return web.json_response({"error": f"Board '{board_id}' not found"}, status=404)

    board_path = Path(board_data["path"])
    issues: list[str] = []

    # Scan board files for issues
    for item_file in sorted(board_path.glob("*.md")):
        try:
            content = item_file.read_text(encoding="utf-8", errors="replace")
            # Check for blocked tasks
            if "- status: blocked" in content:
                title_line = next(
                    (l for l in content.splitlines() if l.startswith("# ")),
                    item_file.stem,
                )
                issues.append(f"Blocked task: {title_line[2:]}")
            # Check for tasks without title
            if not content.startswith("# "):
                issues.append(f"Missing title in: {item_file.name}")
        except Exception:
            issues.append(f"Unreadable file: {item_file.name}")

    health = {
        "status": "healthy" if len(issues) == 0 else "needs-attention",
        "board_id": board_id,
        "task_count": board_data["count"],
        "issues": issues,
        "warning_count": len(issues),
    }

    return web.json_response(health)