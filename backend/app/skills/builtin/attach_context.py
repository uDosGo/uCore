"""attach_context — Inject CONTEXT.md into AI sessions.

Reads the project CONTEXT.md and returns it as a system prompt
or context block for injection into Continue/Cline sessions.

Usage:
  POST /api/skills/attach_context/run
  Body: { "project": "uCore" }  — optional, defaults to uCore
"""
from __future__ import annotations

from pathlib import Path
from app.skills.base import BaseSkill, SkillMeta, SkillParam

PROJECT_CONTEXT_FILES = {
    "ucore": Path.home() / "Code/uCore/CONTEXT.md",
    "default": Path.home() / "Code/uCore/CONTEXT.md",
}


class AttachContext(BaseSkill):
    meta = SkillMeta(
        id="attach_context",
        name="Attach Context",
        description="Inject CONTEXT.md as a system prompt for AI sessions",
        category="assist",
        timeout=10,
        params=[
            SkillParam(
                name="project",
                type="string",
                required=False,
                default="ucore",
                description="Project name (ucore)",
            ),
            SkillParam(
                name="format",
                type="string",
                required=False,
                default="system_prompt",
                description="Output format: system_prompt, raw, or markdown_block",
            ),
        ],
    )

    async def run(self, **kwargs) -> dict:
        project = kwargs.get("project", "ucore").lower().strip()
        fmt = kwargs.get("format", "system_prompt").strip()
        context_path = PROJECT_CONTEXT_FILES.get(project) or PROJECT_CONTEXT_FILES["default"]

        if not context_path.exists():
            return {
                "success": False,
                "error": f"CONTEXT.md not found for '{project}' at {context_path}",
            }

        context_text = context_path.read_text()

        if fmt == "raw":
            return {
                "success": True,
                "project": project,
                "content": context_text,
                "length": len(context_text),
            }

        if fmt == "markdown_block":
            return {
                "success": True,
                "project": project,
                "content": f"```markdown\n{context_text}\n```",
                "length": len(context_text),
            }

        # Default: system_prompt format
        system_prompt = f"""You are working on the {project.upper()} project.

CONTEXT:
{context_text}

Use this context to understand the project architecture, API endpoints,
and coding conventions before responding."""
        return {
            "success": True,
            "project": project,
            "content": system_prompt,
            "format": "system_prompt",
            "length": len(system_prompt),
            "instructions": "Prepend this system prompt to the current AI session for full project context.",
        }
