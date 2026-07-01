#!/usr/bin/env python3
"""Pico Component Audit Skill — identify where Pico CSS classes can replace custom CSS.

Scans JSX/TSX and CSS files to find opportunities for:
- Pico nav (https://picocss.com/docs/nav)
- Pico forms (input, label, select, etc.)
- Pico buttons
- Pico cards
- Pico tables
- Pico badges/pills
- Pico dialogs/modals

Reports: filename, pattern found, suggested Pico class/pattern, confidence
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

SRC_DIR = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "src"

# Pico patterns to look for
PICO_PATTERNS = {
    "nav": {
        "regex": r"<nav|\.navbar|\.nav(?:\s|$|[^-])|\.top-bar|\.header-nav",
        "pico_class": "nav (or <nav> with role='list')",
        "docs": "https://picocss.com/docs/nav",
    },
    "button": {
        "regex": r"<button|\.btn|\.button|\.action-btn|\.command-btn",
        "pico_class": "button (or button[type])",
        "docs": "https://picocss.com/docs/button",
    },
    "form": {
        "regex": r"<form|<input|<label|<select|<textarea",
        "pico_class": "form / input / label / select / textarea",
        "docs": "https://picocss.com/docs/forms",
    },
    "card": {
        "regex": r"\.card(?:\s|$|[^-])|\.panel(?:\s|$|[^-])|\.box(?:\s|$|[^-])",
        "pico_class": "article (semantic card element)",
        "docs": "https://picocss.com/docs/content",
    },
    "table": {
        "regex": r"<table|\.table|\.data-table",
        "pico_class": "table",
        "docs": "https://picocss.com/docs/table",
    },
    "badge": {
        "regex": r"\.badge|\.pill|\.tag(?:\s|$|[^-])|\.label(?:\s|$|[^-])",
        "pico_class": "span.pico-badge or similar",
        "docs": "https://picocss.com/docs/utilities",
    },
    "modal": {
        "regex": r"\.modal|\.dialog(?:\s|$|[^-])|\.popup|\.overlay",
        "pico_class": "dialog (semantic <dialog> element)",
        "docs": "https://picocss.com/docs/modal",
    },
}


def run(target: str = "", dry_run: bool = False) -> dict:
    """Audit JSX/CSS files for Pico component opportunities."""
    jsx_files = _get_jsx_files(target)
    css_files = _get_css_files(target)
    results = {
        "files_scanned": 0,
        "patterns_found": defaultdict(list),
        "total_opportunities": 0,
        "recommendations": [],
    }

    for jsx_file in jsx_files:
        rel = str(jsx_file.relative_to(SRC_DIR))
        results["files_scanned"] += 1
        content = jsx_file.read_text()
        _scan_for_patterns(content, rel, results, "jsx")

    for css_file in css_files:
        rel = str(css_file.relative_to(SRC_DIR))
        if css_file.name.startswith("usx-"):
            continue  # Skip canonical USX files
        results["files_scanned"] += 1
        content = css_file.read_text()
        _scan_for_patterns(content, rel, results, "css")

    # Generate recommendations
    results["total_opportunities"] = sum(len(v) for v in results["patterns_found"].values())
    if results["total_opportunities"] > 0:
        results["recommendations"].append(
            f"Found {results['total_opportunities']} opportunities for Pico integration",
        )
        for pattern, hits in results["patterns_found"].items():
            results["recommendations"].append(
                f"  {pattern}: {len(hits)} files — see {PICO_PATTERNS[pattern]['docs']}",
            )

    return {
        "success": True,
        "action": "audit",
        "dry_run": dry_run,
        "results": results,
    }


def _scan_for_patterns(content: str, rel: str, results: dict, filetype: str) -> None:
    """Scan content for Pico patterns."""
    for pattern_name, pattern_info in PICO_PATTERNS.items():
        if re.search(pattern_info["regex"], content, re.IGNORECASE):
            results["patterns_found"][pattern_name].append({
                "file": rel,
                "type": filetype,
                "pico_class": pattern_info["pico_class"],
            })


def _get_jsx_files(target: str = "") -> list[Path]:
    if not SRC_DIR.exists():
        return []
    if target:
        return list(SRC_DIR.rglob(f"*{target}*"))
    return list(SRC_DIR.rglob("*.[jt]sx"))


def _get_css_files(target: str = "") -> list[Path]:
    if not SRC_DIR.exists():
        return []
    if target:
        return list(SRC_DIR.rglob(f"*{target}*.css"))
    return list(SRC_DIR.rglob("*.css"))


if __name__ == "__main__":
    import json
    result = run(dry_run=True)
    print(json.dumps(result, indent=2, default=lambda x: dict(x) if hasattr(x, "__dict__") else str(x)))
