"""Agent Specialization Registry — Maps tasks to specialized AI agents.

This service loads agent configurations from agents.yaml and provides
intelligent task routing to the most appropriate agent based on task type,
complexity, and required capabilities.

Each agent has:
- Specialized model selection (Ollama, OpenRouter, etc.)
- Custom system prompt optimized for the task type
- Cost tracking and timeout configuration
- Capability tags for skill matching
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import yaml  # type: ignore[import-untyped]

log = logging.getLogger(__name__)


@dataclass
class AgentSpecialization:
    """Configuration for a specialized agent."""

    id: str
    name: str
    description: str
    model: str
    provider: str
    system_prompt: str
    capabilities: list[str]
    cost_per_task: float
    timeout: int
    priority: int = 99


@dataclass
class WorkflowStageTemplate:
    """Configuration for a workflow stage."""

    role: str
    title: str
    description: str = ""
    capabilities: list[str] = field(default_factory=list)


@dataclass
class WorkflowTemplate:
    """Configuration for a multi-stage task workflow."""

    id: str
    name: str
    description: str
    task_types: list[str] = field(default_factory=list)
    match_any: list[str] = field(default_factory=list)
    ownership_model: str | None = None
    stages: list[WorkflowStageTemplate] = field(default_factory=list)


class SpecializedAgentRegistry:
    """Load and manage specialized agent configurations."""

    def __init__(self, config_path: str | None = None):
        self.agents: dict[str, AgentSpecialization] = {}
        self.routing_map: dict[tuple[str, str], str] = {}
        self.surface_taxonomy: dict[str, dict[str, Any]] = {}
        self.workflow_templates: dict[str, WorkflowTemplate] = {}

        if config_path is None:
            config_path = os.path.expanduser("~/.ucore/config/agents.yaml")
            if not os.path.exists(config_path):
                # Fallback to repo config
                config_path = os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "config",
                    "agents.yaml",
                )

        if os.path.exists(config_path):
            self.load_config(config_path)
        else:
            log.warning(
                "Agent config not found at %s, using defaults",
                config_path,
            )
            self._load_defaults()

    def load_config(self, config_path: str) -> None:
        """Load agent configurations from YAML file."""
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}

            for agent_id, agent_data in data.get("agents", {}).items():
                try:
                    self.agents[agent_id] = AgentSpecialization(**agent_data)
                except Exception as e:
                    log.error(f"Failed to load agent {agent_id}: {e}")

            # Load routing map: (task_type, complexity) → agent_id
            for task_type, complexity_map in data.get("routing", {}).items():
                for complexity, agent_id in complexity_map.items():
                    self.routing_map[(task_type, complexity)] = agent_id

            self.surface_taxonomy = data.get("surface_taxonomy", {}) or {}

            workflows = data.get("workflows", {}) or {}
            for workflow_id, workflow_data in workflows.items():
                try:
                    stage_templates = [
                        WorkflowStageTemplate(**stage)
                        for stage in workflow_data.get("stages", [])
                    ]
                    self.workflow_templates[workflow_id] = WorkflowTemplate(
                        id=workflow_id,
                        name=workflow_data.get("name", workflow_id),
                        description=workflow_data.get("description", ""),
                        task_types=workflow_data.get("task_types", []) or [],
                        match_any=workflow_data.get("match_any", []) or [],
                        ownership_model=workflow_data.get("ownership_model"),
                        stages=stage_templates,
                    )
                except Exception as e:
                    log.error(f"Failed to load workflow {workflow_id}: {e}")

            log.info(f"Loaded {len(self.agents)} agents from {config_path}")
        except Exception as e:
            log.error(f"Failed to load agent config: {e}")
            self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default agent configuration (fallback)."""
        self.agents = {
            "dev": AgentSpecialization(
                id="dev",
                name="Developer Agent",
                description="General-purpose development",
                model="qwen2.5-coder:3b",
                provider="ollama",
                system_prompt="You are a helpful AI developer assistant.",
                capabilities=["implementation", "debugging"],
                cost_per_task=0.0,
                timeout=60,
                priority=2,
            ),
            "reviewer": AgentSpecialization(
                id="reviewer",
                name="Code Reviewer Agent",
                description="Code review and quality assurance",
                model="claude-opus-4.7",
                provider="openrouter",
                system_prompt="You are an expert code reviewer.",
                capabilities=["review", "security"],
                cost_per_task=0.05,
                timeout=90,
                priority=3,
            ),
        }

        self.routing_map = {
            ("implement", "high"): "dev",
            ("implement", "medium"): "dev",
            ("implement", "low"): "dev",
            ("review", "high"): "reviewer",
            ("review", "medium"): "reviewer",
            ("debug", "high"): "dev",
        }
        self.surface_taxonomy = {}
        self.workflow_templates = {}

    def get_agent(self, agent_id: str) -> AgentSpecialization | None:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> list[AgentSpecialization]:
        """List all configured agents, sorted by priority."""
        return sorted(self.agents.values(), key=lambda a: a.priority)

    def get_best_agent_for_task(
        self,
        task_type: str,
        complexity: str = "medium",
    ) -> AgentSpecialization:
        """Route task to most appropriate agent based on type and complexity.

        Args:
            task_type: Task type (e.g., 'implement', 'review', 'design')
            complexity: Task complexity ('low', 'medium', 'high')

        Returns:
            Best-matching AgentSpecialization

        """
        # Try exact routing match
        agent_id = self.routing_map.get((task_type, complexity))
        if agent_id and agent_id in self.agents:
            return self.agents[agent_id]

        # Fall back to task type + medium
        agent_id = self.routing_map.get((task_type, "medium"))
        if agent_id and agent_id in self.agents:
            return self.agents[agent_id]

        # Fall back to 'dev' agent (always available)
        if "dev" in self.agents:
            return self.agents["dev"]

        # Last resort: return first available agent
        if self.agents:
            return list(self.agents.values())[0]

        raise RuntimeError("No agents configured")

    def get_agents_for_capability(
        self,
        capability: str,
    ) -> list[AgentSpecialization]:
        """Get all agents that have a specific capability."""
        return [
            agent for agent in self.agents.values()
            if capability in agent.capabilities
        ]

    def get_surface_taxonomy(self) -> dict[str, dict[str, Any]]:
        """Return the configured canonical surface ownership model."""
        return self.surface_taxonomy

    def get_workflow_template(
        self,
        task_type: str,
        task_summary: str = "",
    ) -> WorkflowTemplate | None:
        """Find the best workflow template for a task."""
        summary = task_summary.lower()
        for workflow in self.workflow_templates.values():
            if task_type in workflow.task_types:
                return workflow
            if summary and any(
                token.lower() in summary for token in workflow.match_any
            ):
                return workflow
        return None

    def plan_workflow(
        self,
        task_type: str,
        complexity: str = "medium",
        task_summary: str = "",
        requested_stage: str | None = None,
    ) -> dict[str, Any]:
        """Build a stage-by-stage workflow plan for the task."""
        workflow = self.get_workflow_template(task_type, task_summary)

        if workflow is None:
            agent = self.get_best_agent_for_task(task_type, complexity)
            stage = {
                "index": 0,
                "role": agent.id,
                "title": f"Execute with {agent.name}",
                "description": "Single-agent route",
                "capabilities": agent.capabilities,
                "agent": self._serialize_agent(agent),
            }
            return {
                "workflow_id": "single-agent",
                "name": "Single Agent Route",
                "description": "No multi-stage workflow matched this task.",
                "task_type": task_type,
                "complexity": complexity,
                "ownership_model": None,
                "stages": [stage],
                "active_stage_index": 0,
                "active_stage": stage,
            }

        stages: list[dict[str, Any]] = []
        active_stage_index = 0
        normalized_stage = (requested_stage or "").strip().lower()

        for index, stage_template in enumerate(workflow.stages):
            resolved_agent = self.get_agent(stage_template.role)
            if resolved_agent is None:
                resolved_agent = self.get_best_agent_for_task(
                    task_type,
                    complexity,
                )
            stage = {
                "index": index,
                "role": stage_template.role,
                "title": stage_template.title,
                "description": stage_template.description,
                "capabilities": stage_template.capabilities,
                "agent": self._serialize_agent(resolved_agent),
            }
            stages.append(stage)
            if normalized_stage in {stage_template.role.lower(), str(index)}:
                active_stage_index = index

        ownership_model = None
        if workflow.ownership_model == "surface_taxonomy":
            ownership_model = self.get_surface_taxonomy()

        return {
            "workflow_id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "task_type": task_type,
            "complexity": complexity,
            "ownership_model": ownership_model,
            "stages": stages,
            "active_stage_index": active_stage_index,
            "active_stage": stages[active_stage_index],
        }

    def _serialize_agent(self, agent: AgentSpecialization) -> dict[str, Any]:
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "model": agent.model,
            "provider": agent.provider,
            "capabilities": agent.capabilities,
            "timeout": agent.timeout,
            "cost_per_task": agent.cost_per_task,
            "priority": agent.priority,
        }
