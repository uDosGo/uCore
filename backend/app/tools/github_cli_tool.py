from __future__ import annotations
import asyncio
from app.tools.base import BaseTool, ToolInfo

class GitHubCLITool(BaseTool):
    id = "github_cli"; name = "GitHub CLI"; description = "GitHub command-line tool"
    async def check(self) -> ToolInfo:
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec("gh", "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True
                line = out.decode().strip().split("\n")[0]
                info.version = line.replace("gh version ", "")
        except: pass
        return info
