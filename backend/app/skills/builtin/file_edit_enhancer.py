"""file_edit_enhancer — Enhanced file editing with MCP integration.

Provides intelligent file editing capabilities with:
- Multi-file batch operations
- Context-aware replacements
- Spool logging of edits
- Tasker integration for edit tracking

Usage:
  POST /api/skills/file_edit_enhancer/run
  Body: {
    "action": "batch_replace",
    "edits": [
      {"file": "path/to/file.py", "old": "old text", "new": "new text"},
      ...
    ],
    "log_to_spool": true
  }
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.settings import settings
from app.services.spool_writer import write_spool
from app.skills.base import BaseSkill, SkillMeta, SkillParam

PROJECT_ROOT = settings.udos_root / "uCore"


class FileEditEnhancer(BaseSkill):
    meta = SkillMeta(
        id="file_edit_enhancer",
        name="File Edit Enhancer",
        description="Enhanced file editing with MCP integration, batch operations, and spool logging",
        category="maintenance",
        timeout=120,
        params=[
            SkillParam(
                name="action",
                type="string",
                required=True,
                description="Action: batch_replace, smart_replace, or validate",
            ),
            SkillParam(
                name="edits",
                type="array",
                required=False,
                description="List of {file, old, new} edits for batch_replace",
            ),
            SkillParam(
                name="file",
                type="string",
                required=False,
                description="Single file path for smart_replace/validate",
            ),
            SkillParam(
                name="log_to_spool",
                type="boolean",
                required=False,
                default=True,
                description="Log edits to spool for audit trail",
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                required=False,
                default=False,
                description="Preview without writing changes",
            ),
        ],
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        action = str(kwargs.get("action", "batch_replace")).strip().lower()
        log_to_spool = bool(kwargs.get("log_to_spool", True))
        dry_run = bool(kwargs.get("dry_run", False))

        if action == "batch_replace":
            edits = kwargs.get("edits", [])
            return await self._batch_replace(edits, log_to_spool, dry_run)
        elif action == "smart_replace":
            file_path = kwargs.get("file", "")
            old_text = kwargs.get("old", "")
            new_text = kwargs.get("new", "")
            return await self._smart_replace(file_path, old_text, new_text, log_to_spool, dry_run)
        elif action == "validate":
            file_path = kwargs.get("file", "")
            return self._validate(file_path)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def _batch_replace(
        self,
        edits: list[dict[str, str]],
        log_to_spool: bool,
        dry_run: bool,
    ) -> dict:
        """Apply multiple replacements across files efficiently."""
        results = []
        errors = []

        for edit in edits:
            file_path = edit.get("file", "")
            old_text = edit.get("old", "")
            new_text = edit.get("new", "")

            if not file_path or not old_text:
                errors.append(f"Missing file or old_text in edit: {edit}")
                continue

            try:
                path = Path(file_path).expanduser()
                if not path.exists():
                    errors.append(f"File not found: {file_path}")
                    continue

                content = path.read_text(encoding="utf-8")
                if old_text not in content:
                    errors.append(f"Old text not found in {file_path}")
                    continue

                new_content = content.replace(old_text, new_text)

                if not dry_run:
                    path.write_text(new_content, encoding="utf-8")

                results.append({
                    "file": file_path,
                    "replaced": True,
                    "dry_run": dry_run,
                })

                if log_to_spool and not dry_run:
                    write_spool(
                        level="INFO",
                        module="file_edit_enhancer",
                        message=f"Batch replaced in {file_path}",
                    )

            except Exception as exc:
                errors.append(f"Error editing {file_path}: {exc}")

        return {
            "success": len(errors) == 0,
            "action": "batch_replace",
            "results": results,
            "errors": errors,
            "dry_run": dry_run,
        }

    async def _smart_replace(
        self,
        file_path: str,
        old_text: str,
        new_text: str,
        log_to_spool: bool,
        dry_run: bool,
    ) -> dict:
        """Smart replacement with context validation."""
        if not file_path or not old_text:
            return {"success": False, "error": "Missing file or old_text"}

        try:
            path = Path(file_path).expanduser()
            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            content = path.read_text(encoding="utf-8")

            # Validate context exists
            if old_text not in content:
                return {"success": False, "error": f"Old text not found in {file_path}"}

            # Count occurrences
            occurrences = content.count(old_text)

            new_content = content.replace(old_text, new_text)

            if not dry_run:
                path.write_text(new_content, encoding="utf-8")

            if log_to_spool and not dry_run:
                write_spool(
                    level="INFO",
                    module="file_edit_enhancer",
                    message=f"Smart replaced {occurrences} occurrence(s) in {file_path}",
                )

            return {
                "success": True,
                "action": "smart_replace",
                "file": file_path,
                "occurrences": occurrences,
                "dry_run": dry_run,
            }

        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _validate(self, file_path: str) -> dict:
        """Validate file for editing issues."""
        if not file_path:
            return {"success": False, "error": "Missing file path"}

        try:
            path = Path(file_path).expanduser()
            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            content = path.read_text(encoding="utf-8")
            lines = content.split("\n")

            issues = []

            # Check for common issues
            for i, line in enumerate(lines, 1):
                # Check for trailing whitespace
                if line.rstrip() != line and line.strip():
                    issues.append({"line": i, "type": "trailing_whitespace"})

                # Check for tabs
                if "\t" in line:
                    issues.append({"line": i, "type": "tabs"})

            return {
                "success": True,
                "action": "validate",
                "file": file_path,
                "lines": len(lines),
                "issues": issues,
                "valid": len(issues) == 0,
            }

        except Exception as exc:
            return {"success": False, "error": str(exc)}