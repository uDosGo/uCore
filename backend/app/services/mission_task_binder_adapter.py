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


def _pick_alias(mapping: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = _clean(mapping.get(key))
        if value:
            return value
    return ""


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
        _pick_alias(metadata, ("mission", "project", "objective"))
        or _pick_alias(properties, ("mission", "project", "objective"))
        or _pick_alias(doc, ("mission", "project", "objective"))
    )
    task = (
        _pick_alias(metadata, ("task", "work_item", "todo"))
        or _pick_alias(properties, ("task", "work_item", "todo"))
        or _pick_alias(doc, ("task", "work_item", "todo"))
    )
    binder = (
        _pick_alias(metadata, ("binder", "notebook", "collection"))
        or _pick_alias(properties, ("binder", "notebook", "collection"))
        or _pick_alias(doc, ("binder", "notebook", "collection"))
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
