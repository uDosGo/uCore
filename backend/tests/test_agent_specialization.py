"""Tests for specialized agent workflow planning."""
from __future__ import annotations

from app.services.agent_specialization import SpecializedAgentRegistry


def test_surface_ownership_workflow_uses_architect_dev_reviewer():
    registry = SpecializedAgentRegistry()

    workflow = registry.plan_workflow(
        task_type="surface-restructure",
        complexity="high",
        task_summary=(
            "Define the Developer, Server, and System Tools "
            "ownership taxonomy"
        ),
    )

    assert workflow["workflow_id"] == "surface-ownership-refactor"
    assert [stage["agent"]["id"] for stage in workflow["stages"]] == [
        "architect",
        "dev",
        "reviewer",
    ]
    assert workflow["active_stage"]["agent"]["id"] == "architect"
    assert set(workflow["ownership_model"].keys()) == {
        "developer",
        "server",
        "system-tools",
    }


def test_surface_ownership_workflow_can_select_dev_stage():
    registry = SpecializedAgentRegistry()

    workflow = registry.plan_workflow(
        task_type="surface-taxonomy",
        complexity="medium",
        task_summary="Implement the approved taxonomy",
        requested_stage="dev",
    )

    assert workflow["active_stage_index"] == 1
    assert workflow["active_stage"]["agent"]["id"] == "dev"


def test_non_taxonomy_task_falls_back_to_single_agent_route():
    registry = SpecializedAgentRegistry()

    workflow = registry.plan_workflow(
        task_type="implement",
        complexity="medium",
        task_summary="Build a small endpoint",
    )

    assert workflow["workflow_id"] == "single-agent"
    assert len(workflow["stages"]) == 1
    assert workflow["active_stage"]["agent"]["id"] == "dev"
