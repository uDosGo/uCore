from __future__ import annotations
import asyncio
from app.tools.base import BaseTool, ToolInfo

class DockerTool(BaseTool):
    id = "docker"; name = "Docker"; description = "Container runtime"
    async def check(self) -> ToolInfo:
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec("docker", "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True
                info.version = out.decode().strip()
            proc2 = await asyncio.create_subprocess_exec("docker", "info", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await asyncio.wait_for(proc2.communicate(), timeout=5)
            info.running = proc2.returncode == 0
        except: pass
        return info
