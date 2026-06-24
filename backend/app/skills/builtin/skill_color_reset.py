#!/usr/bin/env python3
"""Color Reset Skill — standardize hardcoded hex colors to Pico CSS variables.

Replaces hardcoded hex color values with Pico CSS variable equivalents:
  Dark backgrounds: #0d1117 → var(--pico-background-color)
  Card backgrounds: #161b22 → var(--pico-card-background-color)
  Primary color: #58a6ff → var(--pico-primary)
  Text colors: #c9d1d9 → var(--pico-color)
  Borders: #30363d → var(--pico-border-color)
  Mutated: #f85149 → var(--pico-del-color)
  Inserted: #3fb950 → var(--pico-ins-color)

Context-aware replacement:
  - background: #0d1117 → background: var(--pico-background-color)
  - color: #c9d1d9 → color: var(--pico-color)
  - border-color: #30363d → border-color: var(--pico-border-color)
"""
from __future__ import annotations
import re
from pathlib import Path

CSS_DIR = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "src" / "styles"

# Color mapping: hex → Pico CSS variable
COLOR_MAP = {
    "0d1117": "pico-background-color",
    "161b22": "pico-card-background-color",
    "58a6ff": "pico-primary",
    "c9d1d9": "pico-color",
    "30363d": "pico-border-color",
    "f85149": "pico-del-color",
    "3fb950": "pico-ins-color",
    "8b949e": "pico-muted-color",
    "388bfd": "pico-primary",
}


def run(target: str = "", dry_run: bool = False) -> dict:
    """Scan and replace hardcoded hex colors with Pico CSS variables."""
    css_files = _get_css_files(target)
    results = {
        "files_scanned": 0,
        "replacements": [],
        "files_modified": 0,
        "errors": [],
    }

    for css_file in css_files:
        rel = str(css_file.relative_to(CSS_DIR))
        if css_file.name.startswith("usx-"):
            continue  # Skip canonical USX files

        results["files_scanned"] += 1
        content = css_file.read_text()
        original = content

        content = _fix_colors(content, rel, results)

        if content != original:
            results["files_modified"] += 1
            if not dry_run:
                css_file.write_text(content)
                results["replacements"].append({
                    "file": rel, "status": "fixed",
                })

    return {
        "success": True,
        "action": "color_reset",
        "dry_run": dry_run,
        "results": results,
    }


def _get_css_files(target: str = "") -> list[Path]:
    if not CSS_DIR.exists():
        return []
    if target:
        return list(CSS_DIR.rglob(f"*{target}*"))
    return list(CSS_DIR.rglob("*.css"))


def _fix_colors(content: str, rel: str, results: dict) -> str:
    """Replace hardcoded hex colors with Pico CSS variables."""
    lines = content.split("\n")
    new_lines = []

    for i, line in enumerate(lines):
        original_line = line
        stripped = line.strip()

        # Skip comments, @media, @import
        if stripped.startswith("/*") or stripped.startswith("*") or "@" in stripped:
            new_lines.append(line)
            continue

        # Skip lines that already use var()
        if "var(--" in stripped:
            new_lines.append(line)
            continue

        # Replace hex colors (case-insensitive)
        for hex_color, var_name in COLOR_MAP.items():
            # Match: #0d1117, #0D1117, etc.
            pattern = f"#{hex_color}"
            if pattern.lower() in line.lower():
                # Case-insensitive replacement
                new_line = re.sub(
                    rf"#{hex_color}(?i)",
                    f"var(--{var_name})",
                    line,
                    flags=re.IGNORECASE
                )
                if new_line != original_line:
                    results["replacements"].append({
                        "file": rel,
                        "line": i + 1,
                        "old": original_line.strip(),
                        "new": new_line.strip(),
                    })
                    line = new_line

        new_lines.append(line)

    return "\n".join(new_lines)


if __name__ == "__main__":
    import json
    result = run(target="", dry_run=True)
    print(json.dumps(result, indent=2, default=str))
