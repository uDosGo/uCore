from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def default_tasker_dir() -> Path:
    return Path(os.getenv("UCORE_TASKER_DIR", str(Path.home() / "Code/uCore/.tasker"))).expanduser()


def scan_tasker_boards(tasker_dir: Path | None = None) -> dict[str, Any]:
    base = tasker_dir or default_tasker_dir()
    boards: list[dict[str, Any]] = []

    if base.exists():
        for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            files = sorted(board_dir.glob("*.md"))
            boards.append(
                {
                    "name": board_dir.name,
                    "path": str(board_dir),
                    "count": len(files),
                    "items": [f.name for f in files[:10]],
                }
            )

    return {
        "tasker_dir": str(base),
        "exists": base.exists(),
        "boards": boards,
        "count": len(boards),
        "total_items": sum(board["count"] for board in boards),
    }


def build_workflow_status(maintenance: dict[str, Any] | None = None) -> dict[str, Any]:
    tasker = scan_tasker_boards()
    maintenance_jobs = []
    if maintenance and maintenance.get("status") == "ok":
        maintenance_jobs = maintenance.get("jobs", [])

    return {
        "engine": {
            "name": "Cline Kanban",
            "role": "Primary DevStudio workflow engine",
            "command": "npx kanban",
            "bind": "127.0.0.1:3484",
            "access": "localhost-only",
            "isolation": "ephemeral git worktrees per card",
            "review_loop": "diff + inline feedback per task",
            "automation": [
                "linked cards",
                "auto-commit",
                "auto-pr",
            ],
        },
        "guardrails": [
            "Keep the Kanban server bound to localhost only.",
            "Do not expose via public host, tunnel, or 0.0.0.0 in the default dev workflow.",
            "Use ephemeral worktrees to isolate agent changes from the main workspace.",
            "Prefer SSH tunnel or Tailscale only if remote access is ever required.",
        ],
        "task_markdown": tasker,
        "maintenance": {
            "status": "ok" if maintenance_jobs else "unknown",
            "jobs": maintenance_jobs,
            "endpoint": "/api/system/maintenance",
        },
        "next_actions": [
            "Expose .tasker board actions in the Workflow Builder UI.",
            "Add sync controls for tasker_sync and vault_sync.",
            "Integrate richer agent orchestration only after the local workflow substrate is stable.",
        ],
    }
