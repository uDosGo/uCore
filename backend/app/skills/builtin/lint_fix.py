"""Lint Fix Skill — find and fix lint errors in Python and TypeScript code.

Supports:
- Finding lint errors with ruff (Python) and oxlint (TypeScript/JavaScript)
- Auto-fixing safe lint errors
- Reporting unsafe fixes that need manual review
- Targeting specific files or entire workspace
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.lint_fix")

# Default paths to scan
BACKEND_ROOT = Path(__file__).parent.parent.parent.parent
FRONTEND_ROOT = BACKEND_ROOT.parent / "frontend"
DEFAULT_SCAN_PATHS = [BACKEND_ROOT]


def _find_ruff() -> str:
    """Find ruff executable, preferring venv."""
    venv_ruff = BACKEND_ROOT / ".venv" / "bin" / "ruff"
    if venv_ruff.exists():
        return str(venv_ruff)
    system_ruff = shutil.which("ruff")
    return system_ruff or "ruff"


def _find_oxlint() -> str | None:
    """Find oxlint executable for TypeScript/JavaScript linting."""
    for loc in [
        BACKEND_ROOT / "node_modules" / "oxlint" / "bin" / "oxlint",
        BACKEND_ROOT / "node_modules" / ".bin" / "oxlint",
        Path.home() / ".npm-global" / "bin" / "oxlint",
    ]:
        if loc.exists():
            return str(loc)
    return shutil.which("oxlint")


def _find_eslint() -> str | None:
    """Find eslint executable for TypeScript/JavaScript linting."""
    for loc in [
        BACKEND_ROOT / "node_modules" / ".bin" / "eslint",
        FRONTEND_ROOT / "node_modules" / ".bin" / "eslint",
        Path.home() / ".npm-global" / "bin" / "eslint",
    ]:
        if loc.exists():
            return str(loc)
    return shutil.which("eslint")


class LintFix(BaseSkill):
    meta = SkillMeta(
        id="lint_fix",
        name="Lint Fix",
        description="Find and fix lint errors in Python and TypeScript code",
        category="developer",
        timeout=120,
        params=[
            SkillParam(
                name="action",
                type="string",
                description="Action: 'check', 'fix', 'report'",
                required=True,
            ),
            SkillParam(
                name="target",
                type="string",
                description="Optional: specific file or directory to target",
                required=False,
            ),
            SkillParam(
                name="language",
                type="string",
                description="Language: 'python', 'typescript', or 'auto' (default)",
                required=False,
                default="auto",
            ),
            SkillParam(
                name="safe_only",
                type="bool",
                description="Only auto-fix safe errors (default: true)",
                required=False,
                default=True,
            ),
        ],
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        action = kwargs.get("action", "check").strip().lower()
        target = kwargs.get("target", "").strip()
        safe_only = kwargs.get("safe_only", True)
        language = kwargs.get("language", "auto").strip().lower()

        # Determine target path and language
        if target:
            target_path = Path(target)
            if not target_path.exists():
                return {"success": False, "error": f"Target path not found: {target}"}
        else:
            target_path = DEFAULT_SCAN_PATHS[0]

        # Auto-detect language from target path
        if language == "auto":
            if str(target_path).endswith((".ts", ".tsx", ".js", ".jsx")) or "frontend" in str(target_path):
                language = "typescript"
            else:
                language = "python"

        if action == "check":
            return await self._check_lint(target_path, language)
        elif action == "fix":
            return await self._fix_lint(target_path, safe_only, language)
        elif action == "report":
            return await self._generate_report(target_path, language)
        else:
            return {"success": False, "error": f"Unknown action: {action}. Use 'check', 'fix', or 'report'."}

    async def _check_lint(self, path: Path, language: str = "python") -> dict:
        """Run lint check and return errors as JSON."""
        if language == "typescript":
            # Try oxlint first, fall back to eslint
            oxlint_path = _find_oxlint()
            if oxlint_path:
                return await self._check_oxlint(path)
            eslint_path = _find_eslint()
            if eslint_path:
                return await self._check_eslint(path)
            return {"success": False, "error": "No TypeScript linter found (oxlint or eslint required)"}
        return await self._check_ruff(path)

    async def _check_ruff(self, path: Path) -> dict:
        """Run ruff check and return errors as JSON."""
        ruff_path = _find_ruff()
        cmd = [ruff_path, "check", str(path), "--output-format=json"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        errors = []
        if stdout:
            try:
                errors = json.loads(stdout.decode("utf-8"))
            except json.JSONDecodeError:
                for line in stdout.decode("utf-8").strip().splitlines():
                    if line:
                        try:
                            errors.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

        by_file: dict[str, list] = {}
        for err in errors:
            fname = err.get("filename", "unknown")
            if fname not in by_file:
                by_file[fname] = []
            by_file[fname].append({
                "code": err.get("code"),
                "message": err.get("message"),
                "line": err.get("location", {}).get("row"),
                "column": err.get("location", {}).get("column"),
                "severity": err.get("severity"),
                "fix_available": err.get("fix") is not None,
                "fix_safe": err.get("fix", {}).get("applicability") == "safe" if err.get("fix") else False,
            })

        return {
            "success": True,
            "action": "check",
            "language": "python",
            "total_errors": len(errors),
            "files_with_errors": len(by_file),
            "errors_by_file": by_file,
            "summary": {
                "safe_fixable": sum(1 for e in errors if (e.get("fix") or {}).get("applicability") == "safe"),
                "unsafe_fixable": sum(1 for e in errors if (e.get("fix") or {}).get("applicability") == "unsafe"),
                "no_fix": sum(1 for e in errors if not e.get("fix")),
            },
        }

    async def _check_oxlint(self, path: Path) -> dict:
        """Run oxlint check for TypeScript/JavaScript."""
        oxlint_path = _find_oxlint()
        if not oxlint_path:
            return {"success": False, "error": "oxlint not found. Install with: npm install -g oxlint"}

        cmd = [oxlint_path, "run", str(path), "--format=json"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        errors = []
        if stdout:
            try:
                errors = json.loads(stdout.decode("utf-8"))
            except json.JSONDecodeError:
                pass

        by_file: dict[str, list] = {}
        for err in errors:
            fname = err.get("filename", "unknown")
            if fname not in by_file:
                by_file[fname] = []
            by_file[fname].append({
                "code": err.get("rule"),
                "message": err.get("message"),
                "line": err.get("location", {}).get("line"),
                "column": err.get("location", {}).get("column"),
                "severity": err.get("severity", "error"),
                "fix_available": False,  # oxlint doesn't auto-fix
                "fix_safe": False,
            })

        return {
            "success": True,
            "action": "check",
            "language": "typescript",
            "total_errors": len(errors),
            "files_with_errors": len(by_file),
            "errors_by_file": by_file,
            "summary": {"safe_fixable": 0, "unsafe_fixable": 0, "no_fix": len(errors)},
        }

    async def _check_eslint(self, path: Path) -> dict:
        """Run eslint check for TypeScript/JavaScript."""
        eslint_path = _find_eslint()
        if not eslint_path:
            return {"success": False, "error": "eslint not found. Install with: npm install -g eslint"}

        cmd = [eslint_path, str(path), "--format", "json"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        errors = []
        if stdout:
            try:
                results = json.loads(stdout.decode("utf-8"))
                for file_result in results:
                    for msg in file_result.get("messages", []):
                        errors.append({
                            "filename": file_result.get("filePath", "unknown"),
                            "code": msg.get("ruleId"),
                            "message": msg.get("message"),
                            "line": msg.get("line"),
                            "column": msg.get("column"),
                            "severity": "error" if msg.get("severity") == 2 else "warning",
                            "fix_available": msg.get("fix") is not None,
                        })
            except json.JSONDecodeError:
                pass

        by_file: dict[str, list] = {}
        for err in errors:
            fname = err.get("filename", "unknown")
            if fname not in by_file:
                by_file[fname] = []
            by_file[fname].append({
                "code": err.get("code"),
                "message": err.get("message"),
                "line": err.get("line"),
                "column": err.get("column"),
                "severity": err.get("severity"),
                "fix_available": err.get("fix_available", False),
                "fix_safe": True,  # eslint fixes are generally safe
            })

        return {
            "success": True,
            "action": "check",
            "language": "typescript",
            "total_errors": len(errors),
            "files_with_errors": len(by_file),
            "errors_by_file": by_file,
            "summary": {
                "safe_fixable": sum(1 for e in errors if e.get("fix_available")),
                "unsafe_fixable": 0,
                "no_fix": sum(1 for e in errors if not e.get("fix_available")),
            },
        }

    async def _fix_lint(self, path: Path, safe_only: bool, language: str = "python") -> dict:
        """Run lint fix to auto-fix errors."""
        if language == "typescript":
            # Try eslint first (supports --fix), then oxlint
            eslint_path = _find_eslint()
            if eslint_path:
                return await self._fix_eslint(path)
            return await self._fix_oxlint(path)
        return await self._fix_ruff(path, safe_only)

    async def _fix_ruff(self, path: Path, safe_only: bool) -> dict:
        """Run ruff check with --fix to auto-fix errors."""
        ruff_path = _find_ruff()
        cmd = [ruff_path, "check", str(path), "--fix"]
        if not safe_only:
            cmd.append("--unsafe-fixes")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        check_result = await self._check_ruff(path)

        return {
            "success": True,
            "action": "fix",
            "language": "python",
            "target": str(path),
            "safe_only": safe_only,
            "output": stdout.decode("utf-8") if stdout else "",
            "stderr": stderr.decode("utf-8") if stderr else "",
            "remaining_errors": check_result.get("total_errors", 0),
            "files_remaining": check_result.get("files_with_errors", 0),
        }

    async def _fix_eslint(self, path: Path) -> dict:
        """Run eslint with --fix to auto-fix TypeScript/JavaScript errors."""
        eslint_path = _find_eslint()
        if not eslint_path:
            return {"success": False, "error": "eslint not found. Install with: npm install -g eslint"}

        cmd = [eslint_path, str(path), "--fix", "--format", "json"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        check_result = await self._check_eslint(path)

        return {
            "success": True,
            "action": "fix",
            "language": "typescript",
            "target": str(path),
            "output": stdout.decode("utf-8") if stdout else "",
            "stderr": stderr.decode("utf-8") if stderr else "",
            "remaining_errors": check_result.get("total_errors", 0),
            "files_remaining": check_result.get("files_with_errors", 0),
        }

    async def _fix_oxlint(self, path: Path) -> dict:
        """oxlint doesn't support auto-fix, return error message."""
        return {
            "success": False,
            "action": "fix",
            "language": "typescript",
            "error": "oxlint does not support auto-fix. Use check action to identify issues.",
        }

    async def _generate_report(self, path: Path, language: str = "python") -> dict:
        """Generate a detailed lint report."""
        check_result = await self._check_lint(path, language)

        errors_by_code: dict[str, int] = {}
        for fname, errs in check_result.get("errors_by_file", {}).items():
            for err in errs:
                code = err.get("code", "unknown")
                errors_by_code[code] = errors_by_code.get(code, 0) + 1

        fixable_files = [
            fname for fname, errs in check_result.get("errors_by_file", {}).items()
            if any(e.get("fix_available") for e in errs)
        ]

        return {
            "success": True,
            "action": "report",
            "language": language,
            "target": str(path),
            "total_errors": check_result.get("total_errors", 0),
            "files_with_errors": check_result.get("files_with_errors", 0),
            "errors_by_code": errors_by_code,
            "fixable_files": fixable_files,
            "summary": check_result.get("summary", {}),
        }
