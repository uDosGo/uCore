from __future__ import annotations
from pydantic import BaseModel

class ToolInfo(BaseModel):
    id: str; name: str; description: str = ""
    installed: bool = False; version: str = ""; running: bool = False

class BaseTool:
    id: str = ""
    name: str = ""
    description: str = ""
    async def check(self) -> ToolInfo:
        raise NotImplementedError
