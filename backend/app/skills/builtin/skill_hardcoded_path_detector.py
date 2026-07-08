#!/usr/bin/env python3
"""Hardcoded Path Detector Skill — find and report hardcoded paths.

Scans source files to detect:
- Absolute paths hardcoded in code
- Environment variable references that should be used instead
- Platform-specific paths that should be configurable
- UDOS_CODE, UDOS_VAULT, HOME references

Reports: file locations, line numbers, path types, and recommendations.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.hardcoded_path_detector")

# Hardcoded path patterns to detect
HARDCODED_PATH_PATTERNS = [
    # Absolute paths
    (r'/Users/[a-zA-Z0-9_]+', 'Absolute macOS user path'),
    (r'/Users/[a-zA-Z0-9_]+', 'Absolute Linux user path'),
    (r'/home/[a-zA-Z0-9_]+', 'Absolute Linux user path'),
    (r'/tmp/', 'Temporary directory'),
    (r'/var/', 'System directory'),
    (r'/etc/', 'Configuration directory'),

    # Project-specific hardcoded paths
    (r'/Users/fredbook/Code', 'Hardcoded UDOS_CODE path'),
    (r'/Users/fredbook/Vault', 'Hardcoded UDOS_VAULT path'),

    # Common directories without env vars
    (r'~/Library/', 'Home directory (should use os.path.expanduser)'),
    (r'~/.', 'Home directory (should use os.path.expanduser)'),
    (r'node_modules/', 'Node modules (should be in .gitignore)'),
    (r'__pycache__/', 'Python cache (should be in .gitignore)'),
    (r'\.venv/', 'Virtual environment (should be in .gitignore)'),
]

# Environment variables that should be used instead of hardcoded paths
ENV_VAR_REPLACEMENTS = {
    'UDOS_CODE': 'Code repository root',
    'UDOS_VAULT': 'Vault directory',
    'UDOS_DATA_HOME': 'Data home directory',
    'UDOS_STATE_HOME': 'State home directory',
    'UDOS_CONFIG_HOME': 'Config home directory',
    'HOME': 'Home directory',
    'USER': 'Username',
    'TMPDIR': 'Temporary directory',
}


class HardcodedPathDetectorSkill(BaseSkill):
    meta = SkillMeta(
        id="hardcoded-path-detector",
        name="Hardcoded Path Detector",
        description=(
            "Find hardcoded paths in Python/JS/TS files. "
            "Reports absolute paths, environment variable references, "
            "and platform-specific paths that should be configurable."
        ),
        category="developer",
        timeout=60,
        params=[
            SkillParam(
                name="target",
                type="string",
                required=False,
                default="backend/app",
                description="Directory or file pattern to scan",
            ),
            SkillParam(
                name="severity",
                type="string",
                required=False,
                default="high",
                description="Minimum severity: low, medium, high",
            ),
        ],
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        target = str(kwargs.get("target", "backend/app"))
        severity = str(kwargs.get("severity", "high")).lower()

        findings = self._scan_for_hardcoded_paths(target)

        # Filter by severity
        filtered = self._filter_by_severity(findings, severity)

        return {
            "success": True,
            "action": "hardcoded_path_detector",
            "findings": filtered,
            "stats": {
                "total_paths": len(findings),
                "filtered": len(filtered),
                "files_scanned": len(set(f["file"] for f in findings)),
            },
        }

    def _scan_for_hardcoded_paths(self, target: str) -> list[dict]:
        """Scan for hardcoded paths in source files."""
        from app.skills.shared_utils import get_source_files

        files = get_source_files(target)
        findings = []

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    for pattern, description in HARDCODED_PATH_PATTERNS:
                        if re.search(pattern, line):
                            # Check if it's using an environment variable
                            is_env_ref = any(
                                f'os.environ.get("{var}"' in line or
                                f'os.getenv("{var}"' in line or
                                f'process.env.{var}' in line
                                for var in ENV_VAR_REPLACEMENTS.keys()
                            )

                            severity = self._determine_severity(pattern, line)

                            findings.append({
                                "file": str(file_path),
                                "line": line_num,
                                "line_content": line.strip(),
                                "pattern": pattern,
                                "description": description,
                                "severity": severity,
                                "is_env_ref": is_env_ref,
                                "recommendation": self._get_recommendation(pattern, line),
                            })
                            break  # Only report one pattern per line
            except Exception as exc:
                log.warning("Failed to scan %s: %s", file_path, exc)
                continue

        return findings

    def _determine_severity(self, pattern: str, line: str) -> str:
        """Determine severity level for a path pattern."""
        if "UDOS_CODE" in pattern or "UDOS_VAULT" in pattern:
            return "high"
        if "/Users/fredbook" in pattern:
            return "high"
        if "~/Library" in pattern or "~/." in pattern:
            return "medium"
        return "low"

    def _get_recommendation(self, pattern: str, line: str) -> str:
        """Get recommendation for fixing a hardcoded path."""
        if "UDOS_CODE" in pattern:
            return "Use os.environ.get('UDOS_CODE') instead"
        if "UDOS_VAULT" in pattern:
            return "Use os.environ.get('UDOS_VAULT') instead"
        if "~/Library" in pattern or "~/." in pattern:
            return "Use os.path.expanduser() instead"
        if "/tmp/" in pattern:
            return "Use tempfile.gettempdir() or os.environ.get('TMPDIR') instead"
        return "Consider using environment variables or configuration files"

    def _filter_by_severity(self, findings: list[dict], severity: str) -> list[dict]:
        """Filter findings by severity level."""
        severity_map = {"low": 0, "medium": 1, "high": 2}
        min_level = severity_map.get(severity, 1)

        return [
            f for f in findings
            if severity_map.get(f["severity"], 1) >= min_level
        ]

    def _generate_report(self, findings: list[dict]) -> str:
        """Generate markdown report of findings."""
        if not findings:
            return "No hardcoded paths found at the specified severity level."

        lines = [
            "# Hardcoded Path Detector Report",
            "",
            f"**Total findings:** {len(findings)}",
            "",
            "## Summary by Severity",
            "",
        ]

        # Count by severity
        severity_counts = {}
        for f in findings:
            severity = f["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        for sev, count in sorted(severity_counts.items(), reverse=True):
            lines.append(f"- **{sev.upper()}:** {count} paths")

        lines.extend(["", "## Findings", ""])

        # Group by file
        by_file: dict[str, list[dict]] = {}
        for f in findings:
            by_file.setdefault(f["file"], []).append(f)

        for file_path, file_findings in sorted(by_file.items()):
            lines.append(f"### {file_path}")
            lines.append("")

            for f in file_findings:
                lines.append(f"- **Line {f['line']}**: {f['description']}")
                lines.append(f"  - Pattern: `{f['pattern']}`")
                lines.append(f"  - Severity: {f['severity'].upper()}")
                if f['is_env_ref']:
                    lines.append("  - ⚠️ Already using environment variable")
                else:
                    lines.append(f"  - 💡 {f['recommendation']}")
                lines.append("")

        return "\n".join(lines)
