from __future__ import annotations
import asyncio
from .base import BaseTool, ToolInfo

class NodeTool(BaseTool):
    id = "node"; name = "Node.js"; description = "JavaScript runtime"
    async def check(self) -> ToolInfo:
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec("node", "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True; info.version = out.decode().strip()
        except: pass
        return info
