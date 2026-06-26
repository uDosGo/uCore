"""GridSmith bridge — invoke the live uCode GridSmith CLI from uCore.

This keeps GridSmith development inside the uCode monorepo while exposing
its functionality through uCore REST and MCP surfaces.
"""
from __future__ import annotations

import asyncio
import json

from app.core.settings import settings


class GridSmithBridge:
    """Thin bridge to the live GridSmith CLI build."""

    def __init__(self) -> None:
        self.ucode_root = settings.udos_root / "uCode"
        self.agent_root = self.ucode_root / "agents" / "gridsmith"
        self.cli_path = self.agent_root / "dist" / "cli.js"

    def status(self) -> dict:
        return {
            "ucode_root": str(self.ucode_root),
            "agent_root": str(self.agent_root),
            "cli_path": str(self.cli_path),
            "exists": self.cli_path.exists(),
        }

    async def run(self, *args: str) -> dict:
        if not self.cli_path.exists():
            raise FileNotFoundError(
                f"GridSmith CLI not built: {self.cli_path}. Run npm build in uCode/agents/gridsmith.",
            )

        proc = await asyncio.create_subprocess_exec(
            "node",
            str(self.cli_path),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.ucode_root),
        )
        stdout, stderr = await proc.communicate()
        stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
        stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""

        if proc.returncode != 0:
            raise RuntimeError(stderr_text or stdout_text or f"GridSmith exited {proc.returncode}")

        payload = stdout_text.strip()
        if not payload:
            return {"ok": True}

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {"stdout": payload}


_bridge: GridSmithBridge | None = None


def get_gridsmith_bridge() -> GridSmithBridge:
    global _bridge
    if _bridge is None:
        _bridge = GridSmithBridge()
    return _bridge
