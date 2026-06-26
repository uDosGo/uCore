"""Tools: Node.js probe."""

from __future__ import annotations

import asyncio
import logging

from app.tools.base import BaseTool, ToolInfo

log = logging.getLogger(__name__)


class NodeTool(BaseTool):
    """Probe for Node.js on PATH."""

    id = "node"
    name = "Node.js"
    description = "JavaScript runtime"

    async def check(self) -> ToolInfo:
        """Return ToolInfo describing whether `node` is installed."""
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec(
                "node",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True
                info.version = out.decode().strip()
        except (TimeoutError, FileNotFoundError, OSError) as exc:
            log.debug("Node check failed: %s", exc)
        return info
