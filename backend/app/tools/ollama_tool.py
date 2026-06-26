"""Probe for the local Ollama LLM runtime.

Provides a lightweight check that detects the `ollama` binary and optionally
probes the local HTTP admin endpoint if `aiohttp` is available.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Final

from app.tools.base import BaseTool, ToolInfo

log = logging.getLogger(__name__)
_OLLAMA_HEALTH_URL: Final[str] = "http://localhost:11434/api/tags"
_HTTP_OK: Final[int] = 200


class OllamaTool(BaseTool):
    """Probe for a local Ollama installation and runtime."""

    id = "ollama"
    name = "Ollama"
    description = "Local LLM runtime"

    async def check(self) -> ToolInfo:
        """Check whether Ollama runtime is installed and running."""
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True
                info.version = out.decode().strip()


            # Check if running: perform an HTTP probe if aiohttp is available.
            try:
                import aiohttp  # local import; optional dependency  # noqa: PLC0415

                async with aiohttp.ClientSession() as s:
                    r = await s.get(_OLLAMA_HEALTH_URL, timeout=2)
                    info.running = r.status == _HTTP_OK
            except ModuleNotFoundError:
                log.debug("aiohttp not installed; skipping Ollama HTTP check")
            except Exception as exc:  # network / protocol errors
                log.debug("Ollama running check failed: %s", exc)
        except (TimeoutError, FileNotFoundError, OSError) as exc:
            log.debug("Ollama check failed: %s", exc)
        return info
