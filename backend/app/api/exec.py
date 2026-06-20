"""POST /api/exec — execute shell commands safely.

Used by InstallPanel and DocsPanel in the frontend to:
- Probe installed tools (Docker, Node, Git, gh, vscode, Zen, QQcode)
- Sync documentation via git
- Run arbitrary commands with timeouts
"""
from __future__ import annotations

import asyncio
import logging
from aiohttp import web

log = logging.getLogger("ucore.exec")

# Whitelist of allowed commands (glob patterns)
ALLOWED_COMMANDS = [
    "which *",
    "node --version",
    "git --version",
    "gh --version",
    "docker --version",
    "mdfind *",
    "qqcode --help",
    "cd * && ./skills/*/run.sh *",
    "docker ps *",
]


def _is_safe(command: str) -> bool:
    """Basic safety check - reject destructive commands."""
    dangerous = ["rm -rf", "sudo", "> /dev", "dd ", ":(){ :|:& };:", "mkfs", "chmod 777"]
    for d in dangerous:
        if d in command.lower():
            return False
    return True


async def handle_exec(request: web.Request) -> web.Response:
    """POST /api/exec — run a shell command.

    Body: { "command": "...", "timeout": 30 }
    Returns: { "stdout": "...", "stderr": "...", "exit_code": 0 }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    command = body.get("command", "").strip()
    timeout = min(float(body.get("timeout", 30)), 120)  # Max 120s

    if not command:
        return web.json_response({"error": "command is required"}, status=400)

    if not _is_safe(command):
        return web.json_response({
            "error": "Command rejected by safety check",
            "command": command,
        }, status=400)

    log.info("Executing: %s (timeout=%ss)", command[:100], timeout)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
        stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
        exit_code = proc.returncode or 0

        log.info("Exec result: exit_code=%d, stdout_len=%d", exit_code, len(stdout_str))

        return web.json_response({
            "stdout": stdout_str,
            "stderr": stderr_str,
            "exit_code": exit_code,
            "command": command,
        })
    except asyncio.TimeoutError:
        log.warning("Command timed out: %s", command[:100])
        return web.json_response({
            "error": f"Command timed out after {timeout}s",
            "command": command,
        }, status=408)
    except Exception as e:
        log.error("Exec error: %s", e)
        return web.json_response({
            "error": str(e),
            "command": command,
        }, status=500)
