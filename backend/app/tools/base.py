"""Base classes for tool probes.

Defines `ToolInfo` (pydantic model) used to report probe results and the
`BaseTool` abstract class that probes implement.
"""

from __future__ import annotations

from pydantic import BaseModel


class ToolInfo(BaseModel):
    """Model describing the result of a local tool probe.

    Attributes:
        id: tool identifier (e.g. "git")
        name: human friendly name
        description: optional short description
        installed: whether the tool binary was detected
        version: detected version string
        running: whether the tool is currently running/responding

    """

    id: str
    name: str
    description: str = ""
    installed: bool = False
    version: str = ""
    running: bool = False


class BaseTool:
    """Abstract base for a local tool probe.

    Subclasses should implement `check()` and set class attributes like
    `id`, `name`, and `description`.
    """

    id: str = ""
    name: str = ""
    description: str = ""

    async def check(self) -> ToolInfo:
        """Perform the probe and return a `ToolInfo` instance."""
        raise NotImplementedError
