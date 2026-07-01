"""Roundtable AI Integration -- Multi-model local agent swarm.

Roundtable AI provides a local MCP server that wraps Codex CLI, Claude Code CLI,
Cursor, and Gemini CLI as sub-agents. This module integrates it with Hivemind.

Usage:
    roundtable-mcp-server --agents codex,claude,cursor,gemini

Environment:
    CLI_MCP_SUBAGENTS  - Comma-separated sub-agents
    CLI_MCP_WORKING_DIR - Default working directory
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.mcp.hivemind.roundtable")

ROUNDTABLE_CHECK_FILE = Path.home() / ".roundtable" / "availability_check.json"
ROUNDTABLE_PORT = 4891


@dataclass
class RoundtableAgent:
    """A sub-agent discovered by Roundtable AI."""

    name: str
    available: bool
    version: str | None = None
    model: str | None = None


class RoundtableIntegration:
    """Integration layer between Hivemind and Roundtable AI."""

    def __init__(self, agents: list[str] | None = None):
        self.agents = agents or ["codex", "claude", "cursor", "gemini"]
        self._process: subprocess.Popen | None = None
        self._availability: list[RoundtableAgent] = []

    async def check_availability(self) -> list[RoundtableAgent]:
        """Run availability check -- probes each CLI and caches results."""
        venv_python = self._get_venv_python()
        cmd = [
            venv_python, "-m", "roundtable_mcp_server", "--check",
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30
            )
            if proc.returncode != 0:
                log.warning(
                    "Roundtable check failed: %s", stderr.decode()[:200]
                )
        except (asyncio.TimeoutError, FileNotFoundError) as exc:
            log.warning("Roundtable check error: %s", exc)

        return self._load_availability()

    def _get_venv_python(self) -> str:
        """Resolve python from backend venv or system."""
        project_root = Path(__file__).resolve().parent.parent.parent
        venv = project_root / ".venv" / "bin" / "python"
        if venv.exists():
            return str(venv)
        return "python3"

    def _load_availability(self) -> list[RoundtableAgent]:
        """Load availability check results from cache."""
        if not ROUNDTABLE_CHECK_FILE.exists():
            log.info(
                "No Roundtable availability cache at %s",
                ROUNDTABLE_CHECK_FILE,
            )
            return []

        try:
            data = json.loads(ROUNDTABLE_CHECK_FILE.read_text())
            agents = []
            for cli_name, info in data.items():
                agents.append(RoundtableAgent(
                    name=cli_name,
                    available=info.get("available", False),
                    version=info.get("version"),
                    model=info.get("model"),
                ))
            self._availability = agents
            log.info(
                "Roundtable agents: %d available",
                sum(1 for a in agents if a.available),
            )
            return agents
        except (json.JSONDecodeError, KeyError) as exc:
            log.warning("Failed to parse Roundtable cache: %s", exc)
            return []

    def get_available_agents(self) -> list[RoundtableAgent]:
        """Get cached agent availability (non-blocking)."""
        if not self._availability:
            return self._load_availability()
        return self._availability

    def get_mcp_server_command(self) -> list[str]:
        """Get command to start Roundtable as an MCP server."""
        venv_python = self._get_venv_python()
        agents_str = ",".join(self.agents)
        return [
            venv_python, "-m", "roundtable_mcp_server",
            "--agents", agents_str,
        ]

    def get_env_config(self) -> dict[str, str]:
        """Get environment variables for Roundtable MCP server."""
        return {
            "CLI_MCP_SUBAGENTS": ",".join(self.agents),
            "CLI_MCP_WORKING_DIR": os.getcwd(),
            "ROUNDTABLE_BASE_URL": f"http://localhost:{ROUNDTABLE_PORT}/v1",
        }

    def summary(self) -> dict[str, Any]:
        """Return a summary dict for health/status endpoints."""
        agents = self.get_available_agents()
        available = [a.name for a in agents if a.available]
        unavailable = [a.name for a in agents if not a.available]
        return {
            "installed": True,
            "version": "0.8.0",
            "mcp_server": "roundtable-mcp-server",
            "port": ROUNDTABLE_PORT,
            "requested_agents": self.agents,
            "available": available,
            "unavailable": unavailable,
            "env": self.get_env_config(),
        }


# Singleton
_integration: RoundtableIntegration | None = None


def get_roundtable() -> RoundtableIntegration:
    global _integration
    if _integration is None:
        _integration = RoundtableIntegration()
    return _integration
