"""Lint Fix Skill — Auto-fix common Python lint errors.

Provides:
- Fix trailing whitespace on blank lines
- Add missing newlines at end of files
- Report line length violations
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill

log = logging.getLogger("skill_lint_fix")


def fix_trailing_whitespace(content: str) -> str:
    """Remove trailing whitespace from all lines."""
    lines = content.splitlines(keepends=True)
    fixed_lines = []
    for line in lines:
        # Remove trailing whitespace but preserve line endings
        fixed = line.rstrip() + "\n" if line.endswith("\n") else line.rstrip()
        fixed_lines.append(fixed)
    return "".join(fixed_lines)


def ensure_final_newline(content: str) -> str:
    """Ensure file ends with a newline."""
    if content and not content.endswith("\n"):
        return content + "\n"
    return content


def check_line_lengths(content: str, max_length: int = 79) -> list[dict]:
    """Check for lines exceeding max length."""
    violations = []
    for i, line in enumerate(content.splitlines(), 1):
        if len(line) > max_length:
            violations.append({
                "line": i,
                "length": len(line),
                "preview": line[:60] + "..." if len(line) > 60 else line,
            })
    return violations


def fix_file(filepath: Path) -> dict[str, Any]:
    """Fix lint issues in a single file."""
    if not filepath.exists():
        return {"error": f"File not found: {filepath}"}

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    original = content
    fixes_applied = []

    # Fix trailing whitespace
    content = fix_trailing_whitespace(content)
    if content != original:
        fixes_applied.append("trailing_whitespace")

    # Ensure final newline
    content = ensure_final_newline(content)
    if content != original:
        fixes_applied.append("final_newline")

    if fixes_applied:
        try:
            filepath.write_text(content, encoding="utf-8")
            return {"fixed": True, "fixes": fixes_applied}
        except Exception as e:
            return {"error": f"Failed to write file: {e}"}

    return {"fixed": False, "fixes": []}


def fix_directory(directory: Path, pattern: str = "*.py") -> dict[str, Any]:
    """Fix lint issues in all matching files in a directory."""
    results = {
        "files_processed": 0,
        "files_fixed": 0,
        "errors": [],
        "line_violations": [],
    }

    for filepath in directory.rglob(pattern):
        if filepath.name.startswith("_"):
            continue

        result = fix_file(filepath)
        results["files_processed"] += 1

        if "error" in result:
            results["errors"].append({
                "file": str(filepath),
                "error": result["error"],
            })
        elif result.get("fixed"):
            results["files_fixed"] += 1
            log.info(f"Fixed {filepath}: {result['fixes']}")

        # Check line lengths
        try:
            content = filepath.read_text(encoding="utf-8")
            violations = check_line_lengths(content)
            if violations:
                results["line_violations"].append({
                    "file": str(filepath),
                    "violations": violations,
                })
        except Exception:
            pass

    return results


class LintFixSkill(BaseSkill):
    """Skill for auto-fixing Python lint errors."""

    @property
    def meta(self):
        return type("Meta", (), {
            "id": "lint_fix",
            "name": "Lint Fix",
            "description": "Auto-fix trailing whitespace and missing newlines",
            "category": "system",
            "timeout": 60,
        })()

    def validate(self, **kwargs) -> list[str]:
        return []

    async def run(self, **kwargs) -> dict[str, Any]:
        target = kwargs.get("target", "backend")
        max_length = kwargs.get("max_length", 79)

        if target == "backend":
            directory = Path(__file__).parent.parent.parent
        elif target == "all":
            directory = Path(__file__).parent.parent.parent.parent
        else:
            directory = Path(target)

        results = fix_directory(directory)
        results["target"] = str(directory)
        results["max_length"] = max_length

        return {
            "success": True,
            "action": "lint_fix",
            "results": results,
        }


# Register on import
def register():
    """Register the lint fix skill."""
    from app.skills.registry import register_skill
    register_skill(LintFixSkill())
    return LintFixSkill()


if __name__ == "__main__":
    result = asyncio.run(LintFixSkill().run())
    import json
    print(json.dumps(result, indent=2, default=str))
