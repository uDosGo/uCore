from __future__ import annotations
import asyncio
from .base import BaseTool, ToolInfo

class OllamaTool(BaseTool):
    id = "ollama"; name = "Ollama"; description = "Local LLM runtime"
    async def check(self) -> ToolInfo:
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec("ollama", "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True; info.version = out.decode().strip()
            # Check if running
            import aiohttp
            try:
                async with aiohttp.ClientSession() as s:
                    r = await s.get("http://localhost:11434/api/tags", timeout=2)
                    info.running = r.status == 200
            except: pass
        except: pass
        return info
