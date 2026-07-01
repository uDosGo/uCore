#!/usr/bin/env python3
"""dev_tags_assessment — Tag scripts and docs for assessment and cleanup.

Scans workspace files and adds dev tags to identify:
- Working code (✅)
- Placeholders (⚪)
- Deprecated code (⛔)
- Duplicates (🔁)
- Legacy leftovers (📜)
- Experimental (🧪)
- Broken code (💥)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Dev Tags mapping
DEV_TAGS = {
    "WORKING": "✅",
    "PLACEHOLDER": "⚪",
    "DEPRECATED": "⛔",
    "DUPLICATE": "🔁",
    "LEGACY": "📜",
    "EXPERIMENTAL": "🧪",
    "BROKEN": "💥",
}

# Patterns to detect tag types
PATTERNS = {
    "PLACEHOLDER": [
        r"TODO.*implement",
        r"FIXME.*later",
        r"pass\s*#.*placeholder",
        r"raise\s+NotImplementedError",
        r"#\s*TODO: stub",
    ],
    "DEPRECATED": [
        r"#\s*DEPRECATED",
        r"#\s*deprecated",
        r"@deprecated",
        r"deprecated::",
    ],
    "EXPERIMENTAL": [
        r"#\s*EXPERIMENTAL",
        r"#\s*experimental",
        r"experimental::",
    ],
    "BROKEN": [
        r"#\s*BROKEN",
        r"#\s*broken",
        r"broken::",
        r"except.*pass",
    ],
}


@dataclass
class FileAssessment:
    path: str
    dev_tag: str
    confidence: float
    reasons: list[str]
    line_matches: list[int]


def assess_file(file_path: Path) -> FileAssessment | None:
    """Assess a single file for dev tags."""
    if not file_path.exists():
        return None

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    reasons = []
    line_matches = []
    tag = "WORKING"
    confidence = 1.0

    for line_num, line in enumerate(content.split("\n"), 1):
        for tag_type, patterns in PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    reasons.append(f"Line {line_num}: {pattern}")
                    line_matches.append(line_num)
                    if tag_type == "BROKEN":
                        tag = "BROKEN"
                        confidence = 0.9
                    elif tag_type == "DEPRECATED":
                        tag = "DEPRECATED"
                        confidence = max(confidence, 0.8)
                    elif tag_type == "EXPERIMENTAL":
                        tag = "EXPERIMENTAL"
                        confidence = max(confidence, 0.7)
                    elif tag_type == "PLACEHOLDER":
                        tag = "PLACEHOLDER"
                        confidence = max(confidence, 0.6)

    return FileAssessment(
        path=str(file_path),
        dev_tag=tag,
        confidence=confidence,
        reasons=reasons,
        line_matches=line_matches,
    )


def scan_workspace(
    root: Path,
    extensions: list[str] | None = None,
    exclude_dirs: list[str] | None = None,
) -> list[FileAssessment]:
    """Scan workspace for files to assess."""
    extensions = extensions or [".py", ".ts", ".tsx", ".js", ".jsx", ".md"]
    exclude_dirs = exclude_dirs or [
        ".git",
        "node_modules",
        "__pycache__",
        ".next",
        "dist",
        ".venv",
    ]

    assessments = []

    for ext in extensions:
        for file_path in root.rglob(f"*{ext}"):
            # Skip excluded directories
            if any(part in exclude_dirs for part in file_path.parts):
                continue

            assessment = assess_file(file_path)
            if assessment and assessment.reasons:
                assessments.append(assessment)

    return assessments


def generate_report(assessments: list[FileAssessment]) -> str:
    """Generate markdown report of assessments."""
    lines = [
        "# Dev Tags Assessment Report",
        "",
        f"**Total files assessed:** {len(assessments)}",
        "",
        "## Summary by Tag",
        "",
    ]

    # Count by tag
    tag_counts: dict[str, int] = {}
    for a in assessments:
        tag_counts[a.dev_tag] = tag_counts.get(a.dev_tag, 0) + 1

    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        icon = DEV_TAGS.get(tag, "❓")
        lines.append(f"- {icon} **{tag}:** {count} files")

    lines.extend(["", "## Files Needing Attention", ""])

    # Group by tag
    by_tag: dict[str, list[FileAssessment]] = {}
    for a in assessments:
        by_tag.setdefault(a.dev_tag, []).append(a)

    for tag in ["BROKEN", "DEPRECATED", "PLACEHOLDER", "EXPERIMENTAL"]:
        if tag in by_tag:
            icon = DEV_TAGS.get(tag, "❓")
            lines.append(f"### {icon} {tag}")
            lines.append("")
            for a in by_tag[tag][:20]:  # Limit to 20 per tag
                rel_path = a.path
                lines.append(f"- `{rel_path}` (confidence: {a.confidence:.0%})")
                if a.reasons:
                    lines.append(f"  - {a.reasons[0]}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    assessments = scan_workspace(root)
    print(generate_report(assessments))