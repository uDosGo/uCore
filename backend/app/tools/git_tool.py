from __future__ import annotations
import asyncio
from app.tools.base import BaseTool, ToolInfo

class GitTool(BaseTool):
    id = "git"; name = "Git"; description = "Version control"
    async def check(self) -> ToolInfo:
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec("git", "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True; info.version = out.decode().strip()
        except: pass
        return info
