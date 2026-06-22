"""Mission/task/binder adapter projection helpers."""
from __future__ import annotations

from typing import Any


DEFAULT_MISSION = "General"
DEFAULT_BINDER = "note"
DEFAULT_TITLE = "(untitled)"


def _clean(value: Any) -> str:
    """Normalize adapter string values."""
    return str(value or "").strip()


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _title_parts(title: str) -> tuple[str, str]:
    """Split title into mission/task when possible.

    Supports forms like:
    - "Mission: Task"
    - "Mission - Task"
    - "Mission | Task"
    """
    for sep in (":", " - ", " | "):
        if sep in title:
            left, right = title.split(sep, 1)
            mission = _clean(left) or DEFAULT_MISSION
            task = _clean(right) or title
            return mission, task
    return DEFAULT_MISSION, title


def project_mission_task_binder(doc: dict[str, Any]) -> dict[str, Any]:
    """Project an AppFlowy document into mission/task/binder fields.

    Field precedence:
    1) metadata/properties mission/task/binder values
    2) title split into mission/task
    3) defaults
    """
    metadata = _as_mapping(doc.get("metadata"))
    properties = _as_mapping(doc.get("properties"))

    title = _clean(doc.get("title")) or DEFAULT_TITLE

    mission = (
        _clean(metadata.get("mission"))
        or _clean(properties.get("mission"))
    )
    task = (
        _clean(metadata.get("task"))
        or _clean(properties.get("task"))
    )
    binder = (
        _clean(metadata.get("binder"))
        or _clean(properties.get("binder"))
        or _clean(doc.get("type"))
        or DEFAULT_BINDER
    )

    if not mission or not task:
        title_mission, title_task = _title_parts(title)
        if not mission:
            mission = title_mission
        if not task:
            task = title_task

    return {
        "id": doc.get("id"),
        "workspace_id": doc.get("workspace_id"),
        "mission": mission,
        "task": task,
        "binder": binder,
        "title": title,
        "updated_at": doc.get("updated_at"),
        "source": "appflowy",
    }
