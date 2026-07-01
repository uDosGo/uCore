"""Surface model — a UI workspace/view in uCore."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SurfaceState(str, Enum):
    """Lifecycle states for a Surface."""

    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class SurfaceType(str, Enum):
    """Types of surfaces."""

    PROSE = "prose"           # Markdown editor
    GRID = "grid"             # Grid/cell workspace
    TERMINAL = "terminal"     # Terminal emulator
    TELETEXT = "teletext"     # BBC Teletext/ceefax
    DASHBOARD = "dashboard"   # System dashboard
    MEDIA = "media"           # Media player
    BROWSER = "browser"       # Web browser
    CUSTOM = "custom"         # User-defined


class Surface(BaseModel):
    """A UI surface/workspace in the uCore environment.

    Surfaces are the primary user-facing workspaces — markdown editors,
    grid views, terminals, etc. Each has a lifecycle state and metadata.
    """

    id: str = Field(default_factory=lambda: f"sfc_{uuid.uuid4().hex[:12]}")
    name: str
    type: SurfaceType = SurfaceType.PROSE
    state: SurfaceState = SurfaceState.CREATED
    metadata: dict[str, Any] = Field(default_factory=dict)
    parent_id: str | None = None
    position: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def render(self) -> str:
        """Render the surface as markdown."""
        lines = [
            f"## Surface: {self.name}",
            f"- **ID**: `{self.id}`",
            f"- **Type**: `{self.type.value}`",
            f"- **State**: `{self.state.value}`",
            f"- **Created**: {self.created_at.isoformat()}",
        ]
        if self.metadata:
            lines.append("- **Metadata**:")
            for k, v in self.metadata.items():
                lines.append(f"  - {k}: {v}")
        return "\n".join(lines)

    def update_state(self, new_state: SurfaceState) -> None:
        """Transition the surface to a new state."""
        self.state = new_state
        self.updated_at = datetime.now(UTC)

    def to_markdown(self) -> str:
        """Alias for render()."""
        return self.render()

    model_config = {"frozen": False}
