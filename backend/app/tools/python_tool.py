from __future__ import annotations
import sys, asyncio
from .base import BaseTool, ToolInfo

class PythonTool(BaseTool):
    id = "python"; name = "Python"; description = "Python interpreter"
    async def check(self) -> ToolInfo:
        return ToolInfo(id=self.id, name=self.name, installed=True,
            version=f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
