"""Tools: GitHub CLI probe."""

from __future__ import annotations

import asyncio
import logging

from app.tools.base import BaseTool, ToolInfo

log = logging.getLogger(__name__)


class GitHubCLITool(BaseTool):
    """Probe for GitHub CLI (`gh`) on PATH."""

    id = "github_cli"
    name = "GitHub CLI"
    description = "GitHub command-line tool"

    async def check(self) -> ToolInfo:
        """Return ToolInfo describing whether `gh` is installed."""
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec(
                "gh",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True
                line = out.decode().strip().split("\n")[0]
                info.version = line.replace("gh version ", "")
        except (TimeoutError, FileNotFoundError, OSError) as exc:
            log.debug("GitHub CLI check failed: %s", exc)
        return info
