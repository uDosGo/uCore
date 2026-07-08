#!/usr/bin/env python3
"""Duplicate Code Detector Skill — find and analyze duplicate code patterns.

Scans source files to detect:
- Exact duplicate functions/methods across files
- Similar functions/overlap (AST-based similarity scoring)
- Duplicate import patterns
- Repeated string literals
- Copy-pasted code blocks
- Variable consolidation/sharing/mapping ($VARIABLES)
- Script duplication across snacks, scripts, and docs

Reports: file pairs, similarity scores, line ranges, and removal recommendations.
"""
# ruff: noqa: E501
from __future__ import annotations

import ast
import hashlib
import json
import logging
import re
import time
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.skills.shared_utils import get_source_files as _get_source_files

log = logging.getLogger("ucore.skills.duplicate_detector")

# Thresholds
SIMILARITY_THRESHOLD = 0.85  # 85% similarity for code blocks
MIN_LINES_FOR_DUPLICATE = 5  # Minimum lines to consider for duplication
MAX_LINE_LENGTH = 200  # Ignore very long lines (likely generated)
MIN_SIMILARITY_FOR_FUNCTION = 0.7  # 70% similarity for function overlap


class DuplicateDetectorSkill(BaseSkill):
    meta = SkillMeta(
        id="duplicate-detector",
        name="Duplicate Code Detector",
        description=(
            "Find duplicate code patterns across Python/JS/TS files. "
            "Reports similarity scores and removal recommendations. "
            "Also detects $VARIABLE consolidation and script duplication."
        ),
        category="developer",
        params=[
            SkillParam(
                name="action",
                type="string",
                description="Action: 'scan', 'report', 'archive', 'variables', 'scripts'",
                required=True,
            ),
            SkillParam(
                name="target",
                type="string",
                description="Optional: specific directory or file pattern",
                required=False,
            ),
            SkillParam(
                name="min_lines",
                type="int",
                description="Minimum lines for duplicate detection",
                required=False,
                default=5,
            ),
            SkillParam(
                name="similarity_threshold",
                type="float",
                description="Similarity threshold (0.0-1.0)",
                required=False,
                default=0.85,
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
        min_lines = kwargs.get("min_lines", MIN_LINES_FOR_DUPLICATE)
        threshold = kwargs.get("similarity_threshold", SIMILARITY_THRESHOLD)
        dry_run = kwargs.get("dry_run", True)

        if action == "scan":
            return self._scan_duplicates(target, min_lines, threshold)
        if action == "report":
            scan_result = self._scan_duplicates(target, min_lines, threshold)
            return {
                "success": True,
                "action": "report",
                "report": scan_result,
                "recommendations": self._generate_recommendations(scan_result),
            }
        if action == "archive":
            scan_result = self._scan_duplicates(target, min_lines, threshold)
            return self._archive_duplicates(scan_result, dry_run)
        if action == "variables":
            source_files = self._get_source_files(target)
            return {
                "success": True,
                "action": "variables",
                "findings": self._find_variable_consolidation(source_files),
            }
        if action == "scripts":
            return {
                "success": True,
                "action": "scripts",
                "findings": self._find_script_duplication(target),
            }
        return {"success": False, "error": f"Unknown action: {action}"}

    def _scan_duplicates(
        self, target: str, min_lines: int, threshold: float
    ) -> dict[str, Any]:
        """Scan for duplicate code patterns."""
        findings: dict[str, list] = {
            "exact_duplicates": [],
            "similar_blocks": [],
            "similar_functions": [],
            "duplicate_imports": [],
            "repeated_literals": [],
            "copy_paste_patterns": [],
            "variable_consolidation": [],
            "script_duplication": [],
        }
        stats = {
            "files_scanned": 0,
            "total_issues": 0,
            "languages": defaultdict(int),
        }

        # Get source files
        source_files = self._get_source_files(target)

        # Group by language
        py_files = [f for f in source_files if f.suffix == ".py"]
        js_ts_files = [f for f in source_files if f.suffix in {".js", ".ts", ".jsx", ".tsx"}]

        # Scan Python files for function/method duplicates
        py_findings = self._scan_python_duplicates(py_files, min_lines, threshold)
        findings["exact_duplicates"].extend(py_findings["exact"])
        findings["similar_blocks"].extend(py_findings["similar"])
        stats["languages"]["python"] = len(py_files)

        # Scan JS/TS files for pattern duplicates
        js_findings = self._scan_js_duplicates(js_ts_files, min_lines, threshold)
        findings["exact_duplicates"].extend(js_findings["exact"])
        findings["similar_blocks"].extend(js_findings["similar"])
        stats["languages"]["javascript"] = len(js_ts_files)

        # Find similar functions (overlapping logic)
        findings["similar_functions"] = self._find_similar_functions(py_files + js_ts_files, MIN_SIMILARITY_FOR_FUNCTION)

        # Find duplicate import patterns
        findings["duplicate_imports"] = self._find_duplicate_imports(source_files)

        # Find repeated string literals
        findings["repeated_literals"] = self._find_repeated_literals(source_files)

        # Find variable consolidation opportunities
        findings["variable_consolidation"] = self._find_variable_consolidation(source_files)

        # Find script duplication across snacks/scripts/docs
        findings["script_duplication"] = self._find_script_duplication(target)

        # Find large files that need modularization (>1000 lines)
        findings["large_files"] = self._find_large_files(source_files)

        # Find duplicate functions within the same file
        findings["duplicate_functions_in_file"] = self._find_duplicate_functions_in_file(py_files)

        # Find circular imports
        findings["circular_imports"] = self._find_circular_imports(source_files)

        # Calculate stats
        stats["files_scanned"] = len(source_files)
        stats["total_issues"] = sum(len(v) for v in findings.values())

        return {
            "success": True,
            "findings": findings,
            "stats": stats,
        }

    def _get_source_files(self, target: str) -> list[Path]:
        """Get all source files to scan."""
        return _get_source_files(target)

    def _scan_python_duplicates(
        self, files: list[Path], min_lines: int, threshold: float
    ) -> dict[str, list]:
        """Scan Python files for duplicate functions and code blocks."""
        exact_duplicates = []
        similar_blocks = []

        # Hash-based exact duplicate detection
        hash_to_files: dict[str, list] = defaultdict(list)

        for file_path in files:
            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_code = ast.unparse(node)
                        if len(func_code.splitlines()) >= min_lines:
                            func_hash = hashlib.sha256(func_code.encode()).hexdigest()
                            hash_to_files[func_hash].append({
                                "file": str(file_path),
                                "name": node.name,
                                "lines": len(func_code.splitlines()),
                                "start_line": node.lineno,
                            })
            except (SyntaxError, ValueError):
                continue

        # Report exact duplicates
        for func_hash, locations in hash_to_files.items():
            if len(locations) > 1:
                exact_duplicates.append({
                    "type": "exact_function_duplicate",
                    "locations": locations,
                    "hash": func_hash[:12],
                })

        # Similar block detection (simplified - based on normalized structure)
        similar_blocks = self._find_similar_blocks(files, min_lines, threshold)

        return {"exact": exact_duplicates, "similar": similar_blocks}

    def _scan_js_duplicates(
        self, files: list[Path], min_lines: int, threshold: float
    ) -> dict[str, list]:
        """Scan JS/TS files for duplicate functions and code blocks."""
        exact_duplicates = []
        similar_blocks = []

        # Simple regex-based function extraction for JS/TS
        func_pattern = re.compile(
            r"(?:function\s+(\w+)|(\w+)\s*=\s*(?:async\s+)?\(|(\w+)\s*\([^)]*\)\s*=>)"
            r"[\s\S]{0,5000}",
            re.MULTILINE
        )

        hash_to_files: dict[str, list] = defaultdict(list)

        for file_path in files:
            try:
                content = file_path.read_text()
                for match in func_pattern.finditer(content):
                    func_name = match.group(1) or match.group(2) or match.group(3)
                    if not func_name:
                        continue
                    func_code = match.group(0)
                    if len(func_code.splitlines()) >= min_lines:
                        func_hash = hashlib.sha256(func_code.encode()).hexdigest()
                        hash_to_files[func_hash].append({
                            "file": str(file_path),
                            "name": func_name,
                            "lines": len(func_code.splitlines()),
                        })
            except Exception:
                continue

        for func_hash, locations in hash_to_files.items():
            if len(locations) > 1:
                exact_duplicates.append({
                    "type": "exact_function_duplicate",
                    "locations": locations,
                    "hash": func_hash[:12],
                })

        similar_blocks = self._find_similar_blocks(files, min_lines, threshold)
        return {"exact": exact_duplicates, "similar": similar_blocks}

    def _find_similar_blocks(
        self, files: list[Path], min_lines: int, threshold: float
    ) -> list[dict]:
        """Find similar code blocks using normalized comparison."""
        similar = []
        block_hashes: dict[str, list] = defaultdict(list)

        for file_path in files:
            try:
                content = file_path.read_text()
                lines = content.splitlines()

                # Extract blocks of consecutive non-empty lines
                i = 0
                while i < len(lines):
                    if lines[i].strip() and not lines[i].strip().startswith("#"):
                        # Find block end
                        block_lines = []
                        j = i
                        while j < len(lines) and lines[j].strip():
                            if len(lines[j]) < MAX_LINE_LENGTH:
                                block_lines.append(lines[j])
                            j += 1

                        if len(block_lines) >= min_lines:
                            # Normalize whitespace
                            normalized = "\n".join(
                                line.strip() for line in block_lines
                            )
                            block_hash = hashlib.sha256(
                                normalized.encode()
                            ).hexdigest()
                            block_hashes[block_hash].append({
                                "file": str(file_path),
                                "start_line": i + 1,
                                "end_line": j,
                                "lines": len(block_lines),
                            })
                        i = j
                    else:
                        i += 1
            except Exception:
                continue

        # Report similar blocks (same hash = identical after normalization)
        for block_hash, locations in block_hashes.items():
            if len(locations) > 1:
                similar.append({
                    "type": "similar_block",
                    "locations": locations,
                    "hash": block_hash[:12],
                })

        return similar

    def _find_similar_functions(
        self, files: list[Path], threshold: float
    ) -> list[dict]:
        """Find similar (overlapping) functions using AST-based similarity scoring."""
        function_signatures: list[dict] = []

        for file_path in files:
            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_code = ast.unparse(node)
                        if len(func_code.splitlines()) >= MIN_LINES_FOR_DUPLICATE:
                            # Extract signature info
                            args = [arg.arg for arg in node.args.args]
                            returns = ast.unparse(node.returns) if node.returns else None
                            function_signatures.append({
                                "file": str(file_path),
                                "name": node.name,
                                "start_line": node.lineno,
                                "lines": len(func_code.splitlines()),
                                "args": args,
                                "returns": returns,
                                "normalized": self._normalize_function(func_code),
                            })
            except (SyntaxError, ValueError):
                continue

        # Compare all function pairs for similarity
        similar_functions = []
        for i, func_a in enumerate(function_signatures):
            for func_b in function_signatures[i + 1:]:
                # Skip if same file
                if func_a["file"] == func_b["file"]:
                    continue

                # Compare normalized code
                similarity = SequenceMatcher(
                    None, func_a["normalized"], func_b["normalized"]
                ).ratio()

                if similarity >= threshold and similarity < 1.0:
                    similar_functions.append({
                        "type": "similar_function",
                        "similarity": round(similarity, 3),
                        "functions": [
                            {"file": func_a["file"], "name": func_a["name"], "start_line": func_a["start_line"]},
                            {"file": func_b["file"], "name": func_b["name"], "start_line": func_b["start_line"]},
                        ],
                    })

        # Sort by similarity descending
        similar_functions.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_functions[:50]  # Limit to top 50

    def _normalize_function(self, code: str) -> str:
        """Normalize function code for similarity comparison."""
        # Remove variable names, keep structure
        normalized = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', 'VAR', code)
        # Remove string literals
        normalized = re.sub(r'["\'][^"\']*["\']', 'STR', normalized)
        # Remove numbers
        normalized = re.sub(r'\b\d+\b', 'NUM', normalized)
        # Normalize whitespace
        return ' '.join(normalized.split())

    def _find_variable_consolidation(
        self, files: list[Path]
    ) -> list[dict]:
        """Find $VARIABLE patterns and consolidation opportunities."""
        var_to_files: dict[str, list] = defaultdict(list)
        env_var_patterns = [
            re.compile(r'\$\{?([A-Z_][A-Z0-9_]*)\}?'),  # ${VAR} or $VAR
            re.compile(r'os\.environ\.get\(["\']([A-Z_][A-Z0-9_]*)["\']'),  # os.environ.get('VAR')
            re.compile(r'os\.getenv\(["\']([A-Z_][A-Z0-9_]*)["\']'),  # os.getenv('VAR')
            re.compile(r'process\.env\.([A-Z_][A-Z0-9_]*)'),  # process.env.VAR (JS)
        ]

        for file_path in files:
            try:
                content = file_path.read_text()
                for pattern in env_var_patterns:
                    for match in pattern.finditer(content):
                        var_name = match.group(1)
                        var_to_files[var_name].append(str(file_path))
            except Exception:
                continue

        # Find variables used in multiple places
        consolidation = []
        for var_name, locations in var_to_files.items():
            if len(locations) > 2:  # Used in more than 2 files
                # Determine scope based on usage patterns
                scope = "global" if len(locations) > 5 else "user"
                consolidation.append({
                    "variable": var_name,
                    "locations": list(set(locations)),  # Unique files
                    "count": len(locations),
                    "scope": scope,
                    "recommendation": f"Consider centralizing ${var_name} in shared config",
                })

        return sorted(consolidation, key=lambda x: x["count"], reverse=True)[:30]

    def _find_script_duplication(
        self, target: str
    ) -> list[dict]:
        """Find duplicated scripts across snacks, scripts, and docs directories."""
        root = Path(__file__).parent.parent.parent.parent
        script_patterns = [
            "scripts/**/*.py",
            "scripts/**/*.sh",
            "backend/tools/**/*.py",
            "docs/**/*.md",
            "backend/app/menu/snacks/**/*.py",
        ]

        all_files = []
        for pattern in script_patterns:
            all_files.extend((root / pattern.replace("**", "")).parent.rglob(pattern.split("/")[-1]))

        # Filter out excluded dirs
        exclude_dirs = {"node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build"}
        all_files = [f for f in all_files if not any(ex in f.parts for ex in exclude_dirs)]

        # Hash-based detection for scripts
        hash_to_files: dict[str, list] = defaultdict(list)
        for file_path in all_files:
            try:
                content = file_path.read_text()
                # Normalize for comparison
                normalized = '\n'.join(
                    line.strip() for line in content.splitlines()
                    if line.strip() and not line.strip().startswith('#')
                )
                file_hash = hashlib.sha256(normalized.encode()).hexdigest()
                hash_to_files[file_hash].append({
                    "file": str(file_path),
                    "category": self._get_category(file_path),
                })
            except Exception:
                continue

        # Report duplicates
        script_duplicates = []
        for file_hash, locations in hash_to_files.items():
            if len(locations) > 1:
                script_duplicates.append({
                    "type": "script_duplication",
                    "locations": locations,
                    "hash": file_hash[:12],
                })

        return script_duplicates

    def _get_category(self, file_path: Path) -> str:
        """Determine category for a file path."""
        path_str = str(file_path)
        if "/scripts/" in path_str:
            return "script"
        if "/snacks/" in path_str:
            return "snack"
        if "/docs/" in path_str:
            return "doc"
        if "/tools/" in path_str:
            return "tool"
        return "other"

    def _find_duplicate_imports(self, files: list[Path]) -> list[dict]:
        """Find duplicate import patterns across files."""
        import_to_files: dict[str, list] = defaultdict(list)

        for file_path in files:
            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_to_files[alias.name].append(str(file_path))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            import_to_files[node.module].append(str(file_path))
            except (SyntaxError, ValueError):
                continue

        duplicates = []
        for imp, locations in import_to_files.items():
            if len(locations) > 3:  # Appears in more than 3 files
                duplicates.append({
                    "import": imp,
                    "locations": locations,
                    "count": len(locations),
                })

        return duplicates

    def _find_repeated_literals(self, files: list[Path]) -> list[dict]:
        """Find repeated string literals across files."""
        literal_to_files: dict[str, list] = defaultdict(list)

        for file_path in files:
            try:
                content = file_path.read_text()
                # Find string literals (simple approach)
                literals = re.findall(r'["\']([^"\']{10,50})["\']', content)
                for lit in literals:
                    literal_to_files[lit].append(str(file_path))
            except Exception:
                continue

        repeated = []
        for lit, locations in literal_to_files.items():
            if len(locations) > 3:
                repeated.append({
                    "literal": lit[:50] + "..." if len(lit) > 50 else lit,
                    "locations": locations[:5],  # Limit to 5 files
                    "count": len(locations),
                })

        return sorted(repeated, key=lambda x: x["count"], reverse=True)[:20]

    def _generate_recommendations(self, scan_result: dict) -> list[str]:
        """Generate recommendations based on scan results."""
        recs = []
        findings = scan_result.get("findings", {})

        exact = findings.get("exact_duplicates", [])
        if exact:
            recs.append(f"Found {len(exact)} exact duplicate functions — consider extracting to shared module")

        similar = findings.get("similar_blocks", [])
        if similar:
            recs.append(f"Found {len(similar)} similar code blocks — review for consolidation")

        func_similar = findings.get("similar_functions", [])
        if func_similar:
            recs.append(f"Found {len(func_similar)} similar functions with overlapping logic — consider merging")

        imports = findings.get("duplicate_imports", [])
        if imports:
            top_imports = sorted(imports, key=lambda x: x["count"], reverse=True)[:5]
            recs.append(f"Top repeated imports: {', '.join(i['import'] for i in top_imports)}")

        vars_consolidation = findings.get("variable_consolidation", [])
        if vars_consolidation:
            top_vars = sorted(vars_consolidation, key=lambda x: x["count"], reverse=True)[:5]
            recs.append(f"Variables needing consolidation: {', '.join(v['variable'] for v in top_vars)}")

        script_dups = findings.get("script_duplication", [])
        if script_dups:
            recs.append(f"Found {len(script_dups)} duplicated scripts across snacks/scripts/docs")

        large_files = findings.get("large_files", [])
        if large_files:
            top_large = sorted(large_files, key=lambda x: x["lines"], reverse=True)[:5]
            large_list = [f"{f['file']} ({f['lines']} lines)" for f in top_large]
            recs.append(f"Large files needing modularization: {', '.join(large_list)}")

        dup_funcs = findings.get("duplicate_functions_in_file", [])
        if dup_funcs:
            recs.append(f"Found {len(dup_funcs)} duplicate functions within files — consolidate")

        circular = findings.get("circular_imports", [])
        if circular:
            recs.append(f"Found {len(circular)} potential circular imports — review imports")

        return recs

    def _archive_duplicates(self, scan_result: dict, dry_run: bool) -> dict:
        """Archive duplicate code findings to a report file."""
        archive_dir = Path(__file__).parent.parent.parent.parent / "tmp" / "duplicate_reports"
        archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        report_file = archive_dir / f"duplicates_{timestamp}.json"

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

    def _find_large_files(self, files: list[Path]) -> list[dict]:
        """Find files that need modularization (>1000 lines)."""
        large_files = []
        for file_path in files:
            try:
                line_count = len(file_path.read_text().splitlines())
                if line_count > 1000:
                    large_files.append({
                        "file": str(file_path),
                        "lines": line_count,
                        "recommendation": "Split into smaller modules (target: <500 lines per module)",
                    })
            except Exception:
                continue

        return sorted(large_files, key=lambda x: x["lines"], reverse=True)[:20]

    def _find_duplicate_functions_in_file(self, files: list[Path]) -> list[dict]:
        """Find duplicate functions within the same file."""
        duplicates = []
        for file_path in files:
            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                functions = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        func_start = node.lineno
                        func_end = node.end_lineno
                        func_code = "\n".join(content.splitlines()[func_start-1:func_end])
                        functions.append({
                            "name": func_name,
                            "start": func_start,
                            "end": func_end,
                            "code": func_code,
                        })

                # Find exact duplicates within the same file
                seen = {}
                for func in functions:
                    func_hash = hashlib.md5(func["code"].encode()).hexdigest()
                    if func_hash in seen:
                        duplicates.append({
                            "file": str(file_path),
                            "function_1": seen[func_hash]["name"],
                            "line_1": seen[func_hash]["start"],
                            "function_2": func["name"],
                            "line_2": func["start"],
                            "reason": "Exact duplicate function within same file",
                        })
                    else:
                        seen[func_hash] = func

            except (SyntaxError, ValueError):
                continue

        return duplicates

    def _find_circular_imports(self, files: list[Path]) -> list[dict]:
        """Find potential circular import patterns."""
        circular = []
        import_graph = defaultdict(set)

        for file_path in files:
            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module:
                            import_graph[str(file_path)].add(node.module)
            except (SyntaxError, ValueError):
                continue

        # Simple circular import detection (not exhaustive)
        for file_a, imports in import_graph.items():
            for file_b in imports:
                if file_b in import_graph and file_a in import_graph[file_b]:
                    circular.append({
                        "file_a": file_a,
                        "file_b": file_b,
                        "reason": "Potential circular import detected",
                    })

        return circular

    def _find_duplicate_install_patterns(self, files: list[Path]) -> list[dict]:
        """Find duplicate installation/launchd patterns across files."""
        install_patterns: dict[str, list] = defaultdict(list)

        # Pattern for launchd plist generation
        launchd_pattern = re.compile(
            r'launchctl\s+(?:bootstrap|load).*com\.udos\.ucore',
            re.IGNORECASE
        )

        # Pattern for plist content generation
        plist_pattern = re.compile(
            r'<\?xml version="1\.0".*plist.*</plist>',
            re.DOTALL
        )

        for file_path in files:
            try:
                content = file_path.read_text()

                # Check for launchd bootstrap calls
                for match in launchd_pattern.finditer(content):
                    install_patterns["launchd_bootstrap"].append({
                        "file": str(file_path),
                        "line": content[:match.start()].count('\n') + 1,
                    })

                # Check for inline plist generation
                for match in plist_pattern.finditer(content):
                    # Extract the module being installed
                    module_match = re.search(r'<string>-m</string>\s*<string>([^<]+)</string>', match.group(0))
                    module = module_match.group(1) if module_match else "unknown"
                    install_patterns["plist_generation"].append({
                        "file": str(file_path),
                        "module": module,
                        "line": content[:match.start()].count('\n') + 1,
                    })
            except Exception:
                continue

        # Report patterns found in multiple files
        duplicates = []
        for pattern_type, locations in install_patterns.items():
            if len(locations) > 1:
                duplicates.append({
                    "type": f"duplicate_{pattern_type}",
                    "locations": locations,
                    "count": len(locations),
                    "recommendation": f"Consider consolidating {pattern_type} into single module",
                })

        return duplicates

    def _remove_duplicate_files(self, duplicates: list[dict], dry_run: bool = True) -> dict:
        """Remove or archive duplicate files that have been consolidated."""
        removed = []
        errors = []

        for dup in duplicates:
            if dup.get("type") == "duplicate_plist_generation":
                # These are now handled by launchd_manager.py
                for loc in dup.get("locations", []):
                    file_path = Path(loc["file"])
                    if "launchd_manager.py" in str(file_path):
                        continue  # Skip the canonical file

                    if dry_run:
                        removed.append({"file": str(file_path), "action": "would_remove"})
                    else:
                        # Move to archive instead of delete
                        archive_dir = Path(__file__).parent.parent.parent.parent / "tmp" / "archived_duplicates"
                        archive_dir.mkdir(parents=True, exist_ok=True)
                        try:
                            # Just rename with .archived suffix for safety
                            archived = archive_dir / f"{file_path.stem}.archived{file_path.suffix}"
                            file_path.rename(archived)
                            removed.append({"file": str(file_path), "action": "archived", "to": str(archived)})
                        except Exception as e:
                            errors.append({"file": str(file_path), "error": str(e)})

        return {"removed": removed, "errors": errors}
