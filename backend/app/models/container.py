"""Container model — a runtime environment in uCore."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


class ContainerRuntime(str, Enum):
    """Supported container runtimes."""
    PYTHON = "python"
    NODE = "node"
    BASH = "bash"
    DOCKER = "docker"
    WASM = "wasm"
    CUSTOM = "custom"


class ContainerStatus(str, Enum):
    """Lifecycle states for a container."""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    CRASHED = "crashed"


class Container(BaseModel):
    """A runtime container for executing code and running services.

    Containers encapsulate a runtime environment with its own dependencies,
    environment variables, and lifecycle management. They are the execution
    context for snacks, surfaces, and services.
    """
    id: str = Field(default_factory=lambda: f"ctn_{uuid.uuid4().hex[:12]}")
    name: str
    runtime: ContainerRuntime = ContainerRuntime.PYTHON
    status: ContainerStatus = ContainerStatus.CREATED
    image: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)
    env_vars: dict[str, str] = Field(default_factory=dict)
    ports: dict[str, int] = Field(default_factory=dict)
    volumes: list[str] = Field(default_factory=list)
    command: Optional[str] = None
    logs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

    def start(self) -> Container:
        """Transition to running state."""
        self.status = ContainerStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.updated_at = self.started_at
        self.logs.append(f"[{self.started_at.isoformat()}] Started")
        return self

    def stop(self) -> Container:
        """Transition to stopped state."""
        self.status = ContainerStatus.STOPPED
        self.stopped_at = datetime.now(timezone.utc)
        self.updated_at = self.stopped_at
        self.logs.append(f"[{self.stopped_at.isoformat()}] Stopped")
        return self

    def get_logs(self, tail: Optional[int] = None) -> list[str]:
        """Return container logs, optionally only the last N lines."""
        if tail is not None:
            return self.logs[-tail:]
        return self.logs.copy()

    def to_markdown(self) -> str:
        """Render as markdown."""
        lines = [
            f"## Container: {self.name}",
            f"- **ID**: `{self.id}`",
            f"- **Runtime**: `{self.runtime.value}`",
            f"- **Status**: `{self.status.value}`",
            f"- **Created**: {self.created_at.isoformat()}",
        ]
        if self.dependencies:
            lines.append(f"- **Dependencies**: {', '.join(self.dependencies)}")
        if self.env_vars:
            lines.append(f"- **Env vars**: {', '.join(f'{k}={v}' for k, v in self.env_vars.items())}")
        if self.logs:
            lines.append(f"- **Log entries**: {len(self.logs)}")
        return "\n".join(lines)

    model_config = {"frozen": False}
