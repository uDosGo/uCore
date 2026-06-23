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

from dataclasses import dataclass
from typing import Optional
import os
import yaml
import logging

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


class SpecializedAgentRegistry:
    """Load and manage specialized agent configurations."""

    def __init__(self, config_path: Optional[str] = None):
        self.agents: dict[str, AgentSpecialization] = {}
        self.routing_map: dict[tuple[str, str], str] = {}

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
            log.warning(f"Agent config not found at {config_path}, using defaults")
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

    def get_agent(self, agent_id: str) -> Optional[AgentSpecialization]:
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
        """
        Route task to most appropriate agent based on type and complexity.

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

    def get_agents_for_capability(self, capability: str) -> list[AgentSpecialization]:
        """Get all agents that have a specific capability."""
        return [
            agent for agent in self.agents.values()
            if capability in agent.capabilities
        ]
