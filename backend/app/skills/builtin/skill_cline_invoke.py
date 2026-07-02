"""Cline Invoke Skill — invoke Cline CLI from uCore skills.

Invokes Cline CLI (VS Code extension's CLI) from within uCore's skill
ecosystem, allowing Dev Mode to use Cline as an agentic executor for
complex multi-step tasks.

Modes:
  - yolo: autonomous execution, no confirmation prompts
  - interactive: human-in-the-loop for sensitive operations

Integrates with: Cline CLI, OpenRouter API, gh CLI.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.cline_invoke")


def _find_cline_binary() -> str | None:
    """Locate the Cline CLI binary."""
    candidates = [
        "cline",
        str(Path.home() / ".local" / "bin" / "cline"),
        str(Path.home() / ".npm-global" / "bin" / "cline"),
        "/usr/local/bin/cline",
    ]
    for c in candidates:
        if Path(c).exists() or _which(c):
            return c
    return None


def _which(cmd: str) -> bool:
    """Check if a command is in PATH."""
    try:
        result = subprocess.run(
            ["which", cmd],
            capture_output=True, text=True, timeout=2, check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


class ClineInvokeSkill(BaseSkill):
    """Invoke Cline CLI for autonomous task execution."""

    meta = SkillMeta(
        id="cline-invoke",
        name="Cline Invoke",
        description=(
            "Invoke Cline CLI from uCore skills."
            " Supports yolo (autonomous) and interactive modes."
            " Uses OpenRouter API key from secret store."
        ),
        category="developer",
        timeout=300,
        params=[
            SkillParam(
                name="task",
                type="string",
                required=True,
                description="Task description for Cline to execute",
            ),
            SkillParam(
                name="mode",
                type="string",
                required=False,
                default="interactive",
                description="Execution mode: 'yolo' or 'interactive'",
            ),
            SkillParam(
                name="cwd",
                type="string",
                required=False,
                default="",
                description="Working directory (default: uCore root)",
            ),
            SkillParam(
                name="timeout",
                type="integer",
                required=False,
                default=120,
                description="Max execution time in seconds",
            ),
            SkillParam(
                name="context",
                type="string",
                required=False,
                default="",
                description="Additional context for Cline",
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        task = kwargs.get("task", "").strip()
        mode = kwargs.get("mode", "interactive").lower()
        cwd = kwargs.get("cwd", str(Path.cwd()))
        timeout = int(kwargs.get("timeout", 120))
        context = kwargs.get("context", "")

        if not task:
            return {"success": False, "error": "task is required"}

        if mode not in ("yolo", "interactive"):
            mode = "interactive"

        # Locate Cline CLI
        cline_bin = _find_cline_binary()
        if not cline_bin:
            return {
                "success": False,
                "error": "Cline CLI not found in PATH",
                "fallback": (
                    "Install Cline CLI: npm install -g @cline/cli"
                    " or use roundtable-dispatch instead"
                ),
            }

        # Verify OpenRouter API key
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            try:
                config_path = (
                    Path.home() / ".config" / "hivemind" / ".env"
                )
                if config_path.exists():
                    content = config_path.read_text()
                    for line in content.splitlines():
                        if line.startswith("OPENROUTER_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"')
                            break
            except Exception:
                pass

        if not api_key and mode != "interactive":
            return {
                "success": False,
                "error": "OpenRouter API key not configured",
                "fallback": "Set OPENROUTER_API_KEY in ~/.config/hivemind/.env",
            }

        # Build command
        cmd = [cline_bin]
        if mode == "yolo":
            cmd.append("--yolo")
        cmd.extend(["--task", task])
        if context:
            cmd.extend(["--context", context])

        # Execute
        try:
            result = await self._run_cline(cmd, cwd, timeout)
            return {
                "success": result.get("success", False),
                "action": "cline-invoke",
                "mode": mode,
                "binary": cline_bin,
                "output": result.get("output", ""),
                "exit_code": result.get("exit_code", -1),
                "duration_ms": result.get("duration_ms", 0),
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Cline task timed out after {timeout}s",
                "mode": mode,
                "binary": cline_bin,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "mode": mode,
                "binary": cline_bin,
            }

    async def _run_cline(
        self, cmd: list[str], cwd: str, timeout: int,
    ) -> dict:
        """Execute Cline CLI and capture output."""
        import time
        t0 = time.perf_counter()

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ},
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        duration = round((time.perf_counter() - t0) * 1000, 1)
        output = (
            stdout.decode("utf-8", errors="replace")
            if stdout else ""
        )
        if stderr:
            err_text = stderr.decode("utf-8", errors="replace")
            if err_text.strip():
                output += f"\n[stderr]\n{err_text}"

        # Try to parse JSON output
        try:
            parsed = json.loads(output)
            return {
                "success": process.returncode == 0,
                "output": parsed.get("response", output),
                "exit_code": process.returncode,
                "duration_ms": duration,
            }
        except (json.JSONDecodeError, ValueError):
            pass

        return {
            "success": process.returncode == 0,
            "output": output[:5000],
            "exit_code": process.returncode,
            "duration_ms": duration,
        }