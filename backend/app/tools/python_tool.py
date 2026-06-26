"""Tools: Python probe."""

from __future__ import annotations

import sys

from app.tools.base import BaseTool, ToolInfo


class PythonTool(BaseTool):
    """Report the current running Python interpreter."""

    id = "python"
    name = "Python"
    description = "Python interpreter"

    async def check(self) -> ToolInfo:
        version = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        return ToolInfo(id=self.id, name=self.name, installed=True, version=version)
