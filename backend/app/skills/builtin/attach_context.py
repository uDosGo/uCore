"""attach_context — Inject CONTEXT.md into AI sessions.

Reads the project CONTEXT.md and returns it as a system prompt
or context block for injection into Continue/Cline sessions.

Usage:
  POST /api/skills/attach_context/run
  Body: { "project": "uCore" }  — optional, defaults to uCore
"""
from __future__ import annotations

from app.core.settings import settings
from app.services.wisdom_paths import readable_wisdom_path
from app.skills.base import BaseSkill, SkillMeta, SkillParam

PROJECT_CONTEXT_FILES = {
    "ucore": settings.udos_root / "uCore/CONTEXT.md",
    "default": settings.udos_root / "uCore/CONTEXT.md",
}
PROJECT_WISDOM_FILES = {
    "ucore": readable_wisdom_path(),
    "default": readable_wisdom_path(),
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
                description=(
                    "Output format: system_prompt, raw, "
                    "or markdown_block"
                ),
            ),
            SkillParam(
                name="include_wisdom",
                type="boolean",
                required=False,
                default=True,
                description=(
                    "Include private project wisdom alongside CONTEXT.md "
                    "when available"
                ),
            ),
        ],
    )

    async def run(self, **kwargs) -> dict:
        project = kwargs.get("project", "ucore").lower().strip()
        fmt = kwargs.get("format", "system_prompt").strip()
        include_wisdom = bool(kwargs.get("include_wisdom", True))
        context_path = (
            PROJECT_CONTEXT_FILES.get(project)
            or PROJECT_CONTEXT_FILES["default"]
        )
        wisdom_path = (
            PROJECT_WISDOM_FILES.get(project)
            or PROJECT_WISDOM_FILES["default"]
        )

        if not context_path.exists():
            return {
                "success": False,
                "error": (
                    f"CONTEXT.md not found for '{project}' "
                    f"at {context_path}"
                ),
            }

        context_text = context_path.read_text(encoding="utf-8")
        wisdom_text = None
        if include_wisdom and wisdom_path.exists():
            wisdom_text = wisdom_path.read_text(encoding="utf-8")

        combined_text = context_text
        if wisdom_text:
            combined_text = (
                f"{context_text}\n\n---\n\n"
                f"# Project Wisdom\n\n{wisdom_text}"
            )

        if fmt == "raw":
            return {
                "success": True,
                "project": project,
                "content": combined_text,
                "length": len(combined_text),
                "has_wisdom": wisdom_text is not None,
            }

        if fmt == "markdown_block":
            return {
                "success": True,
                "project": project,
                "content": f"```markdown\n{combined_text}\n```",
                "length": len(combined_text),
                "has_wisdom": wisdom_text is not None,
            }

        # Default: system_prompt format
        system_prompt = f"""You are working on the {project.upper()} project.

CONTEXT:
{combined_text}

Use this context to understand the project architecture, API endpoints,
and coding conventions before responding."""
        return {
            "success": True,
            "project": project,
            "content": system_prompt,
            "format": "system_prompt",
            "length": len(system_prompt),
            "has_wisdom": wisdom_text is not None,
            "instructions": (
                "Prepend this system prompt to the current AI "
                "session for full project context."
            ),
        }
