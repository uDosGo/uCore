"""Skills API — run skills/scripts via the DevStudio surface.

POST /api/skills/{skill_id}/run — execute a skill by ID
POST /api/skills/run — run a skill by directory path
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from aiohttp import web

log = logging.getLogger("ucore.skills")

# Default skill paths
SKILL_PATHS = [
    Path.home() / "Code/DevStudio/skills",
    Path.home() / "Code/uCore/skills",
    Path("/usr/local/share/udos/skills"),
]


async def handle_run_skill(request: web.Request) -> web.Response:
    """POST /api/skills/{skill_id}/run — execute a skill by ID.

    Body (optional): { "args": [...], "env": {...}, "timeout": 60 }
    Returns: { "stdout": "...", "stderr": "...", "exit_code": 0 }
    """
    skill_id = request.match_info.get("skill_id", "")
    return await _run_skill_by_id(skill_id, request)


async def handle_run_named_skill(request: web.Request) -> web.Response:
    """POST /api/skills/run — run a skill by path/name.

    Body: { "skill": "skill-name", "args": [...], "timeout": 60 }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    skill_name = body.get("skill", "").strip()
    if not skill_name:
        return web.json_response({"error": "skill name is required"}, status=400)

    return await _run_skill_by_id(skill_name, request, body)


async def _run_skill_by_id(
    skill_id: str, request: web.Request, body: dict | None = None
) -> web.Response:
    """Internal: find and execute a skill script."""
    if body is None:
        try:
            body = await request.json() if request.body_exists else {}
        except Exception:
            body = {}

    # Find the skill directory
    skill_dir = _find_skill(skill_id)
    if not skill_dir:
        return web.json_response({
            "error": f"Skill '{skill_id}' not found",
            "searched": [str(p) for p in SKILL_PATHS],
        }, status=404)

    # Find executable to run
    script = _find_script(skill_dir)
    if not script:
        return web.json_response({
            "error": f"No runnable script found in {skill_dir}",
            "expected": ["run.sh", "run.py", "index.js", "main.py"],
        }, status=404)

    # Build command
    args = body.get("args", [])
    timeout = min(float(body.get("timeout", 60)), 300)  # Max 5 min
    env = os.environ.copy()
    env.update(body.get("env", {}))

    cmd = [str(script)] + args
    log.info("Running skill: %s (cmd=%s, timeout=%ss)", skill_id, cmd, timeout)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(skill_dir),
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
        stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
        exit_code = proc.returncode or 0

        log.info("Skill result: exit_code=%d, stdout_len=%d", exit_code, len(stdout_str))

        return web.json_response({
            "stdout": stdout_str,
            "stderr": stderr_str,
            "exit_code": exit_code,
            "skill_id": skill_id,
            "script": str(script),
        })
    except asyncio.TimeoutError:
        log.warning("Skill timed out: %s", skill_id)
        return web.json_response({
            "error": f"Skill timed out after {timeout}s",
            "skill_id": skill_id,
        }, status=408)
    except Exception as e:
        log.error("Skill error: %s", e)
        return web.json_response({
            "error": str(e),
            "skill_id": skill_id,
        }, status=500)


def _find_skill(skill_id: str) -> Path | None:
    """Find a skill directory by ID across all skill paths."""
    for base in SKILL_PATHS:
        candidate = base / skill_id
        if candidate.exists() and candidate.is_dir():
            return candidate
        # Also check if it's a direct path
        path = Path(skill_id)
        if path.exists() and path.is_dir():
            return path
    return None


def _find_script(skill_dir: Path) -> Path | None:
    """Find the first executable script in a skill directory."""
    preferred_order = ["run.sh", "run.py", "index.js", "main.py", "run"]
    for name in preferred_order:
        candidate = skill_dir / name
        if candidate.exists():
            return candidate
    # Fallback: find any executable
    for f in skill_dir.iterdir():
        if f.is_file() and os.access(f, os.X_OK):
            return f
    return None


async def handle_list_skills(request: web.Request) -> web.Response:
    """GET /api/skills — list all available skills."""
    from app.skills.registry import list_skills as ls
    skills = ls()
    return web.json_response({"skills": skills, "count": len(skills)})
