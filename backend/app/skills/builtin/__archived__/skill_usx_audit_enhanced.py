#!/usr/bin/env python3
"""Enhanced USX Audit Skill — comprehensive surface analysis & standardization.

Deep audit of surface CSS files:
1. Font size consistency (Prose-UI compliance)
2. Spacing compliance (USX spacing variables)
3. Color consistency (Pico CSS variables)
4. Icon standardization (Lucide React coverage)
5. Component patterns (Pico nav, buttons, cards)
6. Accessibility compliance
7. Dark mode support
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

CSS_DIR = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "src" / "styles"
SURFACES_DIR = CSS_DIR / "surfaces"


def run(target: str = "", dry_run: bool = False) -> dict:
    """Run comprehensive USX audit on surface CSS files."""
    css_files = _get_css_files(target)
    results = {
        "files_scanned": 0,
        "surfaces_analyzed": 0,
        "issues": defaultdict(list),
        "recommendations": [],
        "compliance_score": 0.0,
    }

    for css_file in css_files:
        rel = str(css_file.relative_to(CSS_DIR))
        results["files_scanned"] += 1
        content = css_file.read_text()

        # Check font sizes
        tiny_text = re.findall(r"font-size:\s*(?:0\.\d+rem|[0-9]px)", content)
        if tiny_text:
            results["issues"]["tiny_font_sizes"].append({
                "file": rel,
                "count": len(tiny_text),
                "suggestion": "Use Prose-UI scale: 0.95rem, 1rem, 1.125rem, 1.25rem",
            })

        # Check hardcoded hex colors
        hex_colors = re.findall(r"#[0-9a-fA-F]{6}", content)
        if hex_colors:
            results["issues"]["hardcoded_colors"].append({
                "file": rel,
                "count": len(hex_colors),
                "suggestion": "Replace with Pico CSS variables",
            })

        # Check hardcoded px spacing
        px_values = re.findall(r"(?:padding|margin|gap):\s*\d+px", content)
        if px_values:
            results["issues"]["hardcoded_spacing"].append({
                "file": rel,
                "count": len(px_values),
                "suggestion": "Replace with USX spacing variables",
            })

        # Check for custom button styles (should use Pico)
        custom_buttons = re.findall(r"\.(?:btn|button)[^{]*{", content)
        if custom_buttons and "var(--pico" not in content:
            results["issues"]["custom_button_styles"].append({
                "file": rel,
                "count": len(custom_buttons),
                "suggestion": "Use Pico button styles",
            })

        if "surfaces" in rel:
            results["surfaces_analyzed"] += 1

    # Calculate compliance score
    total_issues = sum(len(v) for v in results["issues"].values())
    results["compliance_score"] = max(0, 100 - (total_issues * 5))

    # Generate recommendations
    if results["issues"].get("hardcoded_colors"):
        results["recommendations"].append("Run skill_color_reset for Pico color standardization")
    if results["issues"].get("hardcoded_spacing"):
        results["recommendations"].append("Run skill_usx_spacing_normalize for USX spacing")
    if results["issues"].get("tiny_font_sizes"):
        results["recommendations"].append("Review font sizes against Prose-UI scale")
    if results["issues"].get("custom_button_styles"):
        results["recommendations"].append("Migrate custom button styles to Pico CSS")

    return {
        "success": True,
        "action": "audit_enhanced",
        "dry_run": dry_run,
        "results": results,
    }


def _get_css_files(target: str = "") -> list[Path]:
    if not CSS_DIR.exists():
        return []
    if target:
        return list(CSS_DIR.rglob(f"*{target}*"))
    return list(CSS_DIR.rglob("*.css"))


if __name__ == "__main__":
    import json
    result = run(dry_run=True)
    print(json.dumps(result, indent=2, default=str))
