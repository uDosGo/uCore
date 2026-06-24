#!/usr/bin/env python3
"""Lucide Icon Migration Skill — verify icon usage and coverage after Lucide React migration.

With Icon.tsx now using Lucide icons, this skill:
1. Audits all JSX/TSX files for Icon component usage
2. Verifies all used icon names have Lucide mappings
3. Reports any missing icons
4. Suggests Lucide equivalents for unmapped icons
"""
from __future__ import annotations
import re
from pathlib import Path
from collections import defaultdict

SRC_DIR = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "src"

# Icon.tsx LUCIDE_MAP (sync with Icon.tsx changes)
LUCIDE_MAP = {
    "add", "check_circle", "sync", "hourglass_empty", "radio_button_unchecked",
    "stop_circle", "error", "grid_view", "widgets", "smart_toy", "menu_book",
    "build", "tune", "play_circle", "play_arrow", "visibility", "refresh",
    "bug_report", "delete", "analytics", "star", "checklist", "history", "chat",
    "bolt", "apps", "download", "language", "auto_awesome", "arrow_back", "web",
    "terminal", "folder", "map", "puzzle", "account_tree", "settings_suggest",
    "school", "code", "commit", "open_in_new", "chevron_up", "chevron_down",
    "unfold_less", "unfold_more", "view_in_ar", "palette", "link", "query_stats",
    "monitor_heart", "restaurant_menu", "layers", "close", "auto_stories", "debug",
    "dashboard", "home", "settings", "flag", "description", "edit", "folder_open",
    "folder_special", "info", "input", "list", "priority_high", "search", "help",
    "cloud_upload", "upload_file", "publish", "rocket_launch", "fact_check",
    "component_exchange", "folder_sync", "check", "more_vert", "arrow_forward",
    "arrow_upward", "arrow_downward", "warning", "info_outline", "help_outline",
    "done_all", "cancel", "redo", "undo", "dns",
}


def run(target: str = "", dry_run: bool = False) -> dict:
    """Audit icon usage in JSX/TSX files."""
    jsx_files = _get_jsx_files(target)
    results = {
        "files_scanned": 0,
        "icon_occurrences": defaultdict(int),
        "unmapped_icons": [],
        "coverage": 0.0,
        "warnings": [],
    }

    for jsx_file in jsx_files:
        rel = str(jsx_file.relative_to(SRC_DIR))
        results["files_scanned"] += 1
        content = jsx_file.read_text()

        # Find all Icon component usages: <Icon name="icon_name"
        matches = re.findall(r'<Icon\s+[^>]*name=["\']([^"\']+)["\']', content)
        for icon_name in matches:
            results["icon_occurrences"][icon_name] += 1
            if icon_name not in LUCIDE_MAP:
                results["unmapped_icons"].append({
                    "file": rel, "icon": icon_name,
                })

    # Calculate coverage
    total_unique = len(results["icon_occurrences"])
    mapped_unique = sum(1 for i in results["icon_occurrences"] if i in LUCIDE_MAP)
    results["coverage"] = (mapped_unique / total_unique * 100) if total_unique > 0 else 100.0

    # Warnings for low coverage
    if results["coverage"] < 100:
        results["warnings"].append(
            f"Icon coverage: {results['coverage']:.1f}% ({mapped_unique}/{total_unique})"
        )
        if results["unmapped_icons"]:
            results["warnings"].append(
                f"Found {len(results['unmapped_icons'])} unmapped icon usages"
            )

    return {
        "success": True,
        "action": "audit",
        "dry_run": dry_run,
        "results": results,
    }


def _get_jsx_files(target: str = "") -> list[Path]:
    if not SRC_DIR.exists():
        return []
    if target:
        return list(SRC_DIR.rglob(f"*{target}*"))
    return list(SRC_DIR.rglob("*.[jt]sx"))


if __name__ == "__main__":
    import json
    result = run(dry_run=True)
    print(json.dumps(result, indent=2, default=lambda x: dict(x) if hasattr(x, '__dict__') else str(x)))
