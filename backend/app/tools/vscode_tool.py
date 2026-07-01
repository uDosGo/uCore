"""Tools: VS Code probe."""

from __future__ import annotations

import asyncio
import logging

from app.tools.base import BaseTool, ToolInfo

log = logging.getLogger(__name__)


class VSCodeTool(BaseTool):
    id = "vscode"
    name = "VS Code"
    description = "Visual Studio Code editor"

    async def check(self) -> ToolInfo:
        """Check whether VS Code is installed and return ToolInfo."""
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec(
                "code",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True
                lines = out.decode().strip().split("\n")
                info.version = lines[0] if lines else ""
        except Exception as exc:
            log.debug("VSCode check failed: %s", exc)
        return info
