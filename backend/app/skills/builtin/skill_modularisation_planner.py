#!/usr/bin/env python3
"""Modularisation Planner Skill — assess large scripts for improvement opportunities.

Analyzes scripts longer than 1000 lines to identify:
- Large functions/methods (>100 lines)
- High cyclomatic complexity candidates
- Multiple responsibility violations
- Missing docstrings
- Import clustering opportunities
- Class extraction candidates
- Module splitting recommendations

Generates:
- Refactoring priority scores
- Module extraction plans
- Complexity metrics
"""
from __future__ import annotations

import ast
import json
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.skills.shared_utils import get_source_files as _get_source_files

log = logging.getLogger("ucore.skills.modularisation_planner")

# Thresholds
MIN_LINES_FOR_ANALYSIS = 1000
MAX_FUNCTION_LINES = 100
MAX_CLASS_LINES = 300
COMPLEXITY_THRESHOLD = 10


class ModularisationPlannerSkill(BaseSkill):
    meta = SkillMeta(
        id="modularisation-planner",
        name="Modularisation Planner",
        description=(
            "Assess large scripts (>1000 lines) for modularization opportunities. "
            "Reports refactoring priorities and extraction plans."
        ),
        category="developer",
        params=[
            SkillParam(
                name="action",
                type="string",
                description="Action: 'scan', 'report', 'plan'",
                required=True,
            ),
            SkillParam(
                name="target",
                type="string",
                description="Optional: specific file or directory",
                required=False,
            ),
            SkillParam(
                name="min_lines",
                type="int",
                description="Minimum lines to consider for analysis",
                required=False,
                default=1000,
            ),
            SkillParam(
                name="output_format",
                type="string",
                description="Output format: 'json', 'markdown'",
                required=False,
                default="json",
            ),
        ],
        timeout=180,
    )

    async def run(self, **kwargs) -> dict:
        action = kwargs.get("action", "scan")
        target = kwargs.get("target", "")
        min_lines = kwargs.get("min_lines", MIN_LINES_FOR_ANALYSIS)
        output_format = kwargs.get("output_format", "json")

        if action == "scan":
            return self._scan_large_scripts(target, min_lines)
        if action == "report":
            scan_result = self._scan_large_scripts(target, min_lines)
            return {
                "success": True,
                "action": "report",
                "report": scan_result,
                "recommendations": self._generate_recommendations(scan_result),
            }
        if action == "plan":
            scan_result = self._scan_large_scripts(target, min_lines)
            return self._generate_plan(scan_result, output_format)
        return {"success": False, "error": f"Unknown action: {action}"}

    def _scan_large_scripts(self, target: str, min_lines: int) -> dict[str, Any]:
        """Scan for large scripts needing modularization."""
        findings: dict[str, list] = {
            "large_files": [],
            "large_functions": [],
            "complex_functions": [],
            "missing_docstrings": [],
            "import_clusters": [],
            "class_extraction_candidates": [],
        }
        stats = {
            "files_scanned": 0,
            "files_over_threshold": 0,
            "total_issues": 0,
        }

        source_files = self._get_source_files(target)
        stats["files_scanned"] = len(source_files)

        for file_path in source_files:
            try:
                line_count = file_path.stat().st_size
                # Quick line count
                with open(file_path, 'r') as f:
                    line_count = sum(1 for _ in f)

                if line_count < min_lines:
                    continue

                stats["files_over_threshold"] += 1
                content = file_path.read_text()

                # Analyze the file
                file_analysis = self._analyze_file(file_path, content, line_count)
                findings["large_files"].append(file_analysis["summary"])

                findings["large_functions"].extend(file_analysis["large_functions"])
                findings["complex_functions"].extend(file_analysis["complex_functions"])
                findings["missing_docstrings"].extend(file_analysis["missing_docstrings"])
                findings["import_clusters"].extend(file_analysis["import_clusters"])
                findings["class_extraction_candidates"].extend(
                    file_analysis["class_extraction_candidates"]
                )

            except Exception as e:
                log.warning(f"Failed to analyze {file_path}: {e}")
                continue

        stats["total_issues"] = sum(len(v) for v in findings.values())

        return {
            "success": True,
            "findings": findings,
            "stats": stats,
        }

    def _get_source_files(self, target: str) -> list[Path]:
        """Get all source files to scan."""
        return _get_source_files(target)

    def _analyze_file(
        self, file_path: Path, content: str, line_count: int
    ) -> dict[str, Any]:
        """Analyze a single file for modularization opportunities."""
        analysis = {
            "summary": {
                "file": str(file_path),
                "lines": line_count,
                "priority_score": 0,
            },
            "large_functions": [],
            "complex_functions": [],
            "missing_docstrings": [],
            "import_clusters": [],
            "class_extraction_candidates": [],
        }

        # Parse Python files
        if file_path.suffix == ".py":
            try:
                tree = ast.parse(content)
                analysis["summary"]["type"] = "python"

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_lines = self._get_node_line_count(node)
                        if func_lines > MAX_FUNCTION_LINES:
                            analysis["large_functions"].append({
                                "file": str(file_path),
                                "function": node.name,
                                "lines": func_lines,
                                "line": node.lineno,
                            })

                        complexity = self._calculate_complexity(node)
                        if complexity > COMPLEXITY_THRESHOLD:
                            analysis["complex_functions"].append({
                                "file": str(file_path),
                                "function": node.name,
                                "complexity": complexity,
                                "line": node.lineno,
                            })

                        if not ast.get_docstring(node):
                            analysis["missing_docstrings"].append({
                                "file": str(file_path),
                                "function": node.name,
                                "line": node.lineno,
                            })

                    elif isinstance(node, ast.ClassDef):
                        class_lines = self._get_node_line_count(node)
                        if class_lines > MAX_CLASS_LINES:
                            analysis["class_extraction_candidates"].append({
                                "file": str(file_path),
                                "class": node.name,
                                "lines": class_lines,
                                "line": node.lineno,
                            })

                # Check import clustering
                analysis["import_clusters"] = self._analyze_imports(tree, file_path)

            except (SyntaxError, ValueError):
                analysis["summary"]["type"] = "parse_error"

        # Calculate priority score
        analysis["summary"]["priority_score"] = self._calculate_priority_score(analysis)

        return analysis

    def _get_node_line_count(self, node: ast.AST) -> int:
        """Get the line count for an AST node."""
        if hasattr(node, "end_lineno") and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return 0

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        return complexity

    def _analyze_imports(self, tree: ast.AST, file_path: Path) -> list[dict]:
        """Analyze import patterns for clustering opportunities."""
        clusters = []
        import_groups: dict[str, list] = defaultdict(list)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split(".")[0]
                    import_groups[top_level].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_level = node.module.split(".")[0]
                    import_groups[top_level].append(node.module)

        # Find modules with many imports (potential extraction candidates)
        for module, imports in import_groups.items():
            if len(imports) > 5:
                clusters.append({
                    "file": str(file_path),
                    "module": module,
                    "imports": imports,
                    "count": len(imports),
                })

        return clusters

    def _calculate_priority_score(self, analysis: dict) -> int:
        """Calculate refactoring priority score (0-100)."""
        score = 0

        # Large functions add 20 points each (max 40)
        score += min(len(analysis["large_functions"]) * 20, 40)

        # Complex functions add 15 points each (max 30)
        score += min(len(analysis["complex_functions"]) * 15, 30)

        # Missing docstrings add 5 points each (max 15)
        score += min(len(analysis["missing_docstrings"]) * 5, 15)

        # Import clusters add 10 points each (max 10)
        score += min(len(analysis["import_clusters"]) * 10, 10)

        # Class extraction candidates add 10 points each (max 10)
        score += min(len(analysis["class_extraction_candidates"]) * 10, 10)

        return min(score, 100)

    def _generate_recommendations(self, scan_result: dict) -> list[str]:
        """Generate recommendations based on scan results."""
        recs = []
        findings = scan_result.get("findings", {})

        large_files = findings.get("large_files", [])
        if large_files:
            sorted_files = sorted(
                large_files, key=lambda x: x.get("priority_score", 0), reverse=True
            )
            top_files = sorted_files[:3]
            recs.append(
                f"Top priority files for modularization: "
                f"{', '.join(f['file'].split('/')[-1] for f in top_files)}"
            )

        large_funcs = findings.get("large_functions", [])
        if large_funcs:
            recs.append(f"Found {len(large_funcs)} large functions (>100 lines) — consider splitting")

        complex_funcs = findings.get("complex_functions", [])
        if complex_funcs:
            recs.append(f"Found {len(complex_funcs)} complex functions — consider refactoring")

        return recs

    def _generate_plan(self, scan_result: dict, output_format: str) -> dict:
        """Generate a modularization plan."""
        findings = scan_result.get("findings", {})
        large_files = findings.get("large_files", [])

        # Sort by priority
        sorted_files = sorted(
            large_files, key=lambda x: x.get("priority_score", 0), reverse=True
        )

        plan = {
            "timestamp": int(time.time()),
            "files_analyzed": len(large_files),
            "priority_order": [],
            "extraction_suggestions": [],
        }

        for file_info in sorted_files:
            plan["priority_order"].append({
                "file": file_info["file"],
                "lines": file_info["lines"],
                "priority_score": file_info["priority_score"],
            })

            # Generate extraction suggestions
            suggestions = self._generate_extraction_suggestions(file_info["file"])
            plan["extraction_suggestions"].extend(suggestions)

        if output_format == "markdown":
            plan["markdown"] = self._to_markdown(plan)

        return {
            "success": True,
            "action": "plan",
            "plan": plan,
        }

    def _generate_extraction_suggestions(self, file_path: str) -> list[dict]:
        """Generate specific extraction suggestions for a file."""
        suggestions = []

        try:
            content = Path(file_path).read_text()
            tree = ast.parse(content)

            # Suggest extracting large functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_lines = self._get_node_line_count(node)
                    if func_lines > MAX_FUNCTION_LINES:
                        suggestions.append({
                            "file": file_path,
                            "type": "function_extraction",
                            "target": node.name,
                            "lines": func_lines,
                            "suggestion": f"Extract '{node.name}' to separate module",
                        })

                elif isinstance(node, ast.ClassDef):
                    class_lines = self._get_node_line_count(node)
                    if class_lines > MAX_CLASS_LINES:
                        suggestions.append({
                            "file": file_path,
                            "type": "class_extraction",
                            "target": node.name,
                            "lines": class_lines,
                            "suggestion": f"Split '{node.name}' class into smaller modules",
                        })

        except Exception:
            pass

        return suggestions

    def _to_markdown(self, plan: dict) -> str:
        """Convert plan to markdown format."""
        md = ["# Modularization Plan\n"]
        md.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append(f"Files analyzed: {plan['files_analyzed']}\n\n")

        md.append("## Priority Order\n")
        for i, file_info in enumerate(plan["priority_order"], 1):
            md.append(
                f"{i}. `{file_info['file'].split('/')[-1]}` "
                f"({file_info['lines']} lines, score: {file_info['priority_score']})\n"
            )

        md.append("\n## Extraction Suggestions\n")
        for suggestion in plan["extraction_suggestions"]:
            md.append(
                f"- **{suggestion['type']}**: {suggestion['suggestion']} "
                f"({suggestion['lines']} lines)\n"
            )

        return "".join(md)