#!/usr/bin/env python3
"""USX Spacing Normalize Skill — replace hardcoded px with var(--usx-*) variables.

Maps hardcoded px padding/margin/gap values to USX spacing variables:
  4px  → var(--usx-spacing-xs)
  8px  → var(--usx-spacing-sm)
  12px → var(--usx-spacing-md)
  16px → var(--usx-spacing-lg)
  20px → var(--usx-section-separator)
  24px → var(--usx-spacing-xl)
  32px → var(--usx-spacing-2xl)

Context-aware replacements:
  - padding on card classes → var(--usx-card-padding-*)
  - gap on grid classes → var(--usx-grid-gap-*)
  - padding on badge/button classes → var(--usx-badge/button-padding-*)
"""
from __future__ import annotations
import re, logging
from pathlib import Path

log = logging.getLogger("ucore.skills.usx_spacing_normalize")

CSS_DIR = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "src" / "styles"
EXCLUDES = {"node_modules", ".git", "__pycache__"}

# Mapping: value → (variable, note)
PX_MAP = {
    2:  ("--usx-list-item-gap", "tightest"),
    4:  ("--usx-spacing-xs", "minimal"),
    6:  ("--usx-compact-gap", "compact"),
    8:  ("--usx-spacing-sm", "small"),
    10: ("--usx-spacing-sm", "rounds to 8px"),
    12: ("--usx-spacing-md", "standard medium"),
    14: ("--usx-card-padding-vertical", "card vertical"),
    16: ("--usx-spacing-lg", "standard large"),
    20: ("--usx-section-separator", "section separator"),
    24: ("--usx-spacing-xl", "extra large"),
    28: ("--usx-spacing-2xl", "rounds to 32px"),
    32: ("--usx-spacing-2xl", "extra extra large"),
}

# Context rules: (css_prop, rel_pattern_substring, replacement_var_expression)
CONTEXT_RULES = [
    ("padding", ["card"], "var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal)"),
    ("padding", ["badge", "pill"], "var(--usx-badge-padding-vertical) var(--usx-badge-padding-horizontal)"),
    ("padding", ["button", "btn"], "var(--usx-button-padding-vertical) var(--usx-button-padding-horizontal)"),
    ("gap",     ["grid"], "var(--usx-grid-gap)"),
    ("gap",     ["section", "panel"], "var(--usx-section-gap)"),
    ("padding", ["section", "panel"], "var(--usx-section-padding)"),
    ("gap",     ["compact", "sideba"], "var(--usx-compact-gap)"),
    ("padding", ["compact"], "var(--usx-compact-padding)"),
]


def run(target: str = "", dry_run: bool = False) -> dict:
    css_files = _get_css_files(target)
    results = {
        "files_scanned": 0, "replacements": [],
        "files_modified": 0, "errors": [],
    }

    for css_file in css_files:
        rel = str(css_file.relative_to(CSS_DIR))
        if any(e in str(rel) for e in ["node_modules", ".git", "__pycache__"]):
            continue
        if css_file.name.startswith("usx-"):
            continue  # Don't modify the canonical USX files themselves

        results["files_scanned"] += 1
        content = css_file.read_text()
        original = content

        content = _fix_spacing(content, rel, results)

        if content != original:
            results["files_modified"] += 1
            if not dry_run:
                css_file.write_text(content)
                results["replacements"].append({
                    "file": rel, "status": "fixed",
                })

    return {
        "success": True, "action": "normalize",
        "dry_run": dry_run, "results": results,
    }


def _get_css_files(target: str = "") -> list[Path]:
    if not CSS_DIR.exists():
        return []
    if target:
        return list(CSS_DIR.rglob(f"*{target}*"))
    return list(CSS_DIR.rglob("*.css"))


def _fix_spacing(content: str, rel: str, results: dict) -> str:
    lines = content.split("\n")
    new_lines = []
    for i, line in enumerate(lines):
        new_line = _replace_px_values(line, rel)
        if new_line != line:
            results["replacements"].append({
                "file": rel, "line": i + 1,
                "old": line.strip(),
                "new": new_line.strip(),
            })
        new_lines.append(new_line)
    return "\n".join(new_lines)


def _replace_px_values(line: str, rel: str) -> str:
    """Replace hardcoded px values in spacing CSS properties."""
    stripped = line.strip()

    # Skip lines already using var(), commented lines, or @media blocks
    if "var(--" in stripped or stripped.startswith("/*") or stripped.startswith("*"):
        return line
    if "@media" in stripped or "@import" in stripped or ":" not in stripped:
        return line

    for prop in ["padding", "margin", "gap"]:
        # Two-value: padding: 14px 16px;
        m = re.search(rf"({prop}:\s*)(\d+)px\s+(\d+)px(\s*[;!])", stripped)
        if m:
            v1, v2 = int(m.group(2)), int(m.group(3))
            if v1 in PX_MAP and v2 in PX_MAP:
                ctx_repl = _find_context_rule(prop, rel)
                if ctx_repl:
                    replacement = f"{m.group(1)}{ctx_repl}{m.group(4)}"
                else:
                    var1, _ = PX_MAP[v1]
                    var2, _ = PX_MAP[v2]
                    replacement = f"{m.group(1)}var({var1}) var({var2}){m.group(4)}"
                return line.replace(stripped, replacement)

        # Single value: gap: 8px; or padding: 14px;
        m = re.search(rf"({prop}:\s*)(\d+)px(\s*[;!])", stripped)
        if m:
            val = int(m.group(2))
            if val in PX_MAP:
                if val == 14:
                    # Check context: 14px padding → card-padding-vertical or section-padding
                    ctx_repl = _find_context_rule(prop, rel)
                    if ctx_repl:
                        replacement = f"{m.group(1)}{ctx_repl}{m.group(3)}"
                        return line.replace(stripped, replacement)
                var_name, _ = PX_MAP[val]
                replacement = f"{m.group(1)}var({var_name}){m.group(3)}"
                return line.replace(stripped, replacement)

    return line


def _find_context_rule(prop: str, rel: str) -> str | None:
    """Check if rel (filename) matches a context rule for the given prop."""
    for cprop, patterns, var_expr in CONTEXT_RULES:
        if cprop != prop:
            continue
        for pat in patterns:
            if pat in rel.lower():
                return var_expr
    return None


if __name__ == "__main__":
    import json
    result = run(target="workflow.css", dry_run=True)
    print(json.dumps(result, indent=2))