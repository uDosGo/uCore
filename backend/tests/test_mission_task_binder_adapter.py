from __future__ import annotations

from app.services.mission_task_binder_adapter import (
    project_mission_task_binder,
)


def test_projection_prefers_metadata_over_other_sources():
    row = project_mission_task_binder(
        {
            "id": "doc-1",
            "workspace_id": "ws-1",
            "title": "Fallback Mission: Fallback Task",
            "type": "note",
            "metadata": {
                "mission": "Meta Mission",
                "task": "Meta Task",
                "binder": "runbook",
            },
            "properties": {
                "mission": "Property Mission",
                "task": "Property Task",
                "binder": "checklist",
            },
        },
    )

    assert row["mission"] == "Meta Mission"
    assert row["task"] == "Meta Task"
    assert row["binder"] == "runbook"


def test_projection_uses_properties_when_metadata_missing():
    row = project_mission_task_binder(
        {
            "id": "doc-2",
            "workspace_id": "ws-1",
            "title": "Fallback Mission - Fallback Task",
            "properties": {
                "mission": "Ops",
                "task": "Rotate Keys",
                "binder": "security",
            },
        },
    )

    assert row["mission"] == "Ops"
    assert row["task"] == "Rotate Keys"
    assert row["binder"] == "security"


def test_projection_splits_title_when_structured_fields_absent():
    row = project_mission_task_binder(
        {
            "id": "doc-3",
            "workspace_id": "ws-2",
            "title": "Mission A: Ship Adapter",
            "type": "task",
        },
    )

    assert row["mission"] == "Mission A"
    assert row["task"] == "Ship Adapter"
    assert row["binder"] == "task"


def test_projection_uses_defaults_for_sparse_documents():
    row = project_mission_task_binder({"id": "doc-4"})

    assert row["title"] == "(untitled)"
    assert row["mission"] == "General"
    assert row["task"] == "(untitled)"
    assert row["binder"] == "note"
