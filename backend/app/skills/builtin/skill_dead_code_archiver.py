#!/usr/bin/env python3
"""Dead Code / Legacy Archiver Skill — identify, archive, and document unused code.

Scans source files to detect:
- Unused functions and methods
- Orphaned imports
- Dead code paths (unreachable code)
- Legacy code patterns (deprecated APIs, old patterns)
- Files with no references

Archives findings to:
- tmp/dead_code_archive/ with timestamped reports
- Generates migration notes for legacy code
"""
from __future__ import annotations

import ast
import json
import logging
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.skills.shared_utils import get_source_files as _get_source_files

log = logging.getLogger("ucore.skills.dead_code_archiver")

# Legacy patterns to detect
LEGACY_PATTERNS = {
    "deprecated_imports": [
        (r"from\s+typing_extensions\s+import", "Use typing instead of typing_extensions"),
        (r"import\s+requests", "Consider using httpx for async HTTP"),
        (r"\.format\(", "Consider using f-strings instead of .format()"),
    ],
    "old_patterns": [
        (r"@asyncio\.coroutine", "Deprecated asyncio.coroutine decorator — use async def"),
        (r"yield from", "Use async/await instead of yield from"),
        (r"super\(.*\)\.__init__\(\)", "Use super().__init__() instead"),
    ],
}


class DeadCodeArchiverSkill(BaseSkill):
    meta = SkillMeta(
        id="dead-code-archiver",
        name="Dead Code / Legacy Archiver",
        description=(
            "Identify unused code, legacy patterns, and archive findings. "
            "Generates migration notes and removal recommendations."
        ),
        category="developer",
        params=[
            SkillParam(
                name="action",
                type="string",
                description="Action: 'scan', 'archive', 'report'",
                required=True,
            ),
            SkillParam(
                name="target",
                type="string",
                description="Optional: specific directory to scan",
                required=False,
            ),
            SkillParam(
                name="include_legacy",
                type="bool",
                description="Include legacy pattern detection",
                required=False,
                default=True,
            ),
            SkillParam(
                name="dry_run",
                type="bool",
                description="Preview without archiving",
                required=False,
                default=True,
            ),
        ],
        timeout=180,
    )

    async def run(self, **kwargs) -> dict:
        action = kwargs.get("action", "scan")
        target = kwargs.get("target", "")
        include_legacy = kwargs.get("include_legacy", True)
        dry_run = kwargs.get("dry_run", True)

        if action == "scan":
            return self._scan_dead_code(target, include_legacy)
        if action == "report":
            scan_result = self._scan_dead_code(target, include_legacy)
            return {
                "success": True,
                "action": "report",
                "report": scan_result,
                "recommendations": self._generate_recommendations(scan_result),
            }
        if action == "archive":
            scan_result = self._scan_dead_code(target, include_legacy)
            return self._archive_findings(scan_result, dry_run)
        return {"success": False, "error": f"Unknown action: {action}"}

    def _scan_dead_code(self, target: str, include_legacy: bool) -> dict[str, Any]:
        """Scan for dead code and legacy patterns."""
        findings: dict[str, list] = {
            "unused_functions": [],
            "orphaned_imports": [],
            "dead_code_paths": [],
            "legacy_patterns": [],
            "unreferenced_files": [],
        }
        stats = {
            "files_scanned": 0,
            "total_issues": 0,
            "languages": defaultdict(int),
        }

        source_files = self._get_source_files(target)
        stats["files_scanned"] = len(source_files)

        # Build reference map
        all_names: dict[str, list] = defaultdict(list)
        for file_path in source_files:
            try:
                content = file_path.read_text()
                if file_path.suffix == ".py":
                    names = self._extract_python_names(content)
                    for name in names:
                        all_names[name].append(str(file_path))
                    stats["languages"]["python"] += 1
            except Exception:
                continue

        # Check for unused functions
        for file_path in source_files:
            if file_path.suffix != ".py":
                continue
            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_name = node.name
                        # Check if function is used elsewhere
                        if len(all_names.get(func_name, [])) == 1:
                            # Only defined in this file, check if called
                            if not self._is_function_called(content, func_name):
                                findings["unused_functions"].append({
                                    "file": str(file_path),
                                    "function": func_name,
                                    "line": node.lineno,
                                    "lines": len(node.body),
                                })
            except (SyntaxError, ValueError):
                continue

        # Check for orphaned imports
        findings["orphaned_imports"] = self._find_orphaned_imports(source_files)

        # Check for dead code paths
        findings["dead_code_paths"] = self._find_dead_code_paths(source_files)

        # Check for legacy patterns
        if include_legacy:
            findings["legacy_patterns"] = self._find_legacy_patterns(source_files)

        # Check for unreferenced files
        findings["unreferenced_files"] = self._find_unreferenced_files(source_files)

        stats["total_issues"] = sum(len(v) for v in findings.values())

        return {
            "success": True,
            "findings": findings,
            "stats": stats,
        }

    def _get_source_files(self, target: str) -> list[Path]:
        """Get all source files to scan."""
        return _get_source_files(target)

    def _extract_python_names(self, content: str) -> list[str]:
        """Extract all defined names from Python content."""
        names = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    names.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            names.append(target.id)
        except (SyntaxError, ValueError):
            pass
        return names

    def _is_function_called(self, content: str, func_name: str) -> bool:
        """Check if a function is called within its file."""
        # Simple regex check for function calls
        call_pattern = re.compile(rf"\b{re.escape(func_name)}\s*\(")
        return bool(call_pattern.search(content))

    def _find_orphaned_imports(self, files: list[Path]) -> list[dict]:
        """Find imports that are never used."""
        orphaned = []

        for file_path in files:
            if file_path.suffix != ".py":
                continue
            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            name = alias.asname or alias.name
                            if not self._is_name_used(content, name):
                                orphaned.append({
                                    "file": str(file_path),
                                    "import": alias.name,
                                    "line": node.lineno,
                                    "type": "import",
                                })
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for alias in node.names:
                                name = alias.asname or alias.name
                                if not self._is_name_used(content, name):
                                    orphaned.append({
                                        "file": str(file_path),
                                        "import": f"{node.module}.{alias.name}",
                                        "line": node.lineno,
                                        "type": "from_import",
                                    })
            except (SyntaxError, ValueError):
                continue

        return orphaned

    def _is_name_used(self, content: str, name: str) -> bool:
        """Check if a name is used in the content (excluding the import line)."""
        # Remove import lines and check for usage
        lines = content.splitlines()
        code_lines = [ln for ln in lines if not ln.strip().startswith(("import ", "from "))]
        code = "\n".join(code_lines)
        return bool(re.search(rf"\b{re.escape(name)}\b", code))

    def _find_dead_code_paths(self, files: list[Path]) -> list[dict]:
        """Find unreachable code after return/break/continue."""
        dead_paths = []

        for file_path in files:
            if file_path.suffix != ".py":
                continue
            try:
                content = file_path.read_text()
                lines = content.splitlines()

                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped in ("return", "return None", "return 0", "return ''"):
                        # Check if next non-empty line has less indentation
                        j = i + 1
                        while j < len(lines) and not lines[j].strip():
                            j += 1
                        if j < len(lines):
                            current_indent = len(line) - len(line.lstrip())
                            next_indent = len(lines[j]) - len(lines[j].lstrip())
                            if next_indent > current_indent:
                                dead_paths.append({
                                    "file": str(file_path),
                                    "line": j + 1,
                                    "issue": "Code after return statement",
                                    "code": lines[j].strip()[:80],
                                })
            except Exception:
                continue

        return dead_paths

    def _find_legacy_patterns(self, files: list[Path]) -> list[dict]:
        """Find legacy code patterns."""
        legacy = []

        for file_path in files:
            try:
                content = file_path.read_text()
                for category, patterns in LEGACY_PATTERNS.items():
                    for pattern, message in patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            legacy.append({
                                "file": str(file_path),
                                "category": category,
                                "pattern": pattern,
                                "message": message,
                                "count": len(matches),
                            })
            except Exception:
                continue

        return legacy

    def _find_unreferenced_files(self, files: list[Path]) -> list[dict]:
        """Find files that are not imported or referenced."""
        unreferenced = []
        all_content = ""

        for file_path in files:
            try:
                all_content += file_path.read_text() + "\n"
            except Exception:
                continue

        for file_path in files:
            if file_path.suffix != ".py":
                continue
            try:
                stem = file_path.stem
                # Check if module is imported anywhere
                import_pattern = re.compile(rf"(?:import|from)\s+{re.escape(stem)}\b")
                if not import_pattern.search(all_content):
                    # Check if it's a main file or __init__
                    if stem not in ("__init__", "main", "app"):
                        unreferenced.append({
                            "file": str(file_path),
                            "module": stem,
                        })
            except Exception:
                continue

        return unreferenced

    def _generate_recommendations(self, scan_result: dict) -> list[str]:
        """Generate recommendations based on scan results."""
        recs = []
        findings = scan_result.get("findings", {})

        unused = findings.get("unused_functions", [])
        if unused:
            recs.append(f"Found {len(unused)} unused functions — consider removing or documenting")

        orphaned = findings.get("orphaned_imports", [])
        if orphaned:
            recs.append(f"Found {len(orphaned)} orphaned imports — clean up imports")

        dead = findings.get("dead_code_paths", [])
        if dead:
            recs.append(f"Found {len(dead)} dead code paths — review control flow")

        legacy = findings.get("legacy_patterns", [])
        if legacy:
            recs.append(f"Found {len(legacy)} legacy patterns — consider modernization")

        return recs

    def _archive_findings(self, scan_result: dict, dry_run: bool) -> dict:
        """Archive findings to timestamped report file."""
        archive_dir = Path(__file__).parent.parent.parent.parent / "tmp" / "dead_code_archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        report_file = archive_dir / f"dead_code_{timestamp}.json"

        if dry_run:
            return {
                "success": True,
                "action": "archive",
                "dry_run": True,
                "would_write": str(report_file),
                "findings_count": scan_result.get("stats", {}).get("total_issues", 0),
            }

        report_file.write_text(json.dumps(scan_result, indent=2))
        return {
            "success": True,
            "action": "archive",
            "report_file": str(report_file),
            "findings_count": scan_result.get("stats", {}).get("total_issues", 0),
        }
