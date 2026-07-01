#!/usr/bin/env python3
"""Surface Enhancement Report Generator

Generates comprehensive report of all surface enhancements using USX skills.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app.skills.state import read_state
from app.core.logging import log


def run(
    include_terminal_teletext: bool = True,
) -> dict[str, Any]:
    """Generate comprehensive surface enhancement report.

    Parameters
    ----------
    include_terminal_teletext : bool
        Include Terminal & Teletext grid modes in report.

    Returns
    -------
    dict with enhancement report and recommendations.
    """
    report_start = time.time()

    # Read current skill state
    state = read_state()

    # Discover all surfaces
    surfaces_dir = Path(__file__).resolve().parents[4] / "frontend" / "src" / "styles" / "surfaces"
    all_surfaces = _discover_surfaces(surfaces_dir)

    report: dict[str, Any] = {
        "timestamp": int(report_start),
        "surfaces": {},
        "summary": {
            "total_surfaces": len(all_surfaces),
            "enhanced": 0,
            "pending": 0,
            "tagged_for_work": 0,
        },
        "terminal_teletext": {},
        "recommendations": [],
    }

    # Analyze each surface
    for surface_name in all_surfaces:
        surface_report = _analyze_surface(
            surface_name,
            state.get(f"surface_rebuild:{surface_name}", {}),
            state.get(f"skill_usx_spacing_normalize:{surface_name}", {}),
            state.get(f"skill_color_reset:{surface_name}", {}),
        )
        report["surfaces"][surface_name] = surface_report

        # Update summary
        if surface_report.get("enhanced"):
            report["summary"]["enhanced"] += 1
        else:
            report["summary"]["pending"] += 1

        if surface_report.get("tagged_for_work"):
            report["summary"]["tagged_for_work"] += 1

    # Terminal & Teletext analysis
    if include_terminal_teletext:
        report["terminal_teletext"] = _analyze_terminal_teletext()

    # Generate recommendations
    report["recommendations"] = _generate_recommendations(report)

    # Log report completion
    report_duration = time.time() - report_start
    log.info(
        f"📊 [SURFACE_REPORT] Generated in {report_duration:.2f}s - "
        f"Enhanced: {report['summary']['enhanced']}/{report['summary']['total_surfaces']}, "
        f"Pending: {report['summary']['pending']}, "
        f"Tagged: {report['summary']['tagged_for_work']}"
    )

    # Persist report
    _persist_report(report)

    return {
        "success": True,
        "action": "surface_enhancement_report",
        "report": report,
    }


def _discover_surfaces(surfaces_dir: Path) -> list[str]:
    """Discover all surface CSS files."""
    surfaces = []
    if not surfaces_dir.exists():
        return surfaces

    for surface_file in surfaces_dir.glob("*.css"):
        surfaces.append(surface_file.stem)

    return sorted(surfaces)


def _analyze_surface(
    surface_name: str,
    rebuild_state: dict,
    spacing_state: dict,
    color_state: dict,
) -> dict[str, Any]:
    """Analyze a single surface's enhancement status."""
    analysis: dict[str, Any] = {
        "name": surface_name,
        "enhanced": False,
        "tagged_for_work": False,
        "usx_compliance": {
            "spacing": False,
            "colors": False,
            "typography": False,
        },
        "issues": [],
        "last_updated": None,
    }

    # Check if surface has been rebuilt
    if rebuild_state.get("converged"):
        analysis["enhanced"] = True
        analysis["usx_compliance"]["spacing"] = True
        analysis["usx_compliance"]["colors"] = True

    # Check spacing normalization
    if spacing_state.get("success"):
        analysis["usx_compliance"]["spacing"] = True

    # Check color reset
    if color_state.get("success"):
        analysis["usx_compliance"]["colors"] = True

    # Check for Terminal/Teletext
    if "terminal" in surface_name.lower() or "teletext" in surface_name.lower():
        analysis["tagged_for_work"] = True
        analysis["issues"].append("Terminal/Teletext grid mode - specialized work required")

    # Get last updated timestamp
    timestamps = [
        rebuild_state.get("last_updated_ts", 0),
        spacing_state.get("last_updated_ts", 0),
        color_state.get("last_updated_ts", 0),
    ]
    if any(timestamps):
        analysis["last_updated"] = max(timestamps)

    return analysis


def _analyze_terminal_teletext() -> dict[str, Any]:
    """Analyze Terminal & Teletext grid modes."""
    return {
        "status": "tagged_for_specialized_work",
        "work_tag": "docs/TERMINAL_TELETEXT_GRID_WORK_TAG.md",
        "components": [
            "Terminal Viewport",
            "Teletext Page Rendering",
            "Grid Tools UI",
            "Character Maps",
        ],
        "enhancement_needed": [
            "USX spacing integration",
            "Pico CSS color variables",
            "Grid algebra optimization",
            "Character rendering improvements",
        ],
        "separation_maintained": True,
        "note": "Grid-based CSS intentionally separate from USX layout",
    }


def _generate_recommendations(report: dict) -> list[str]:
    """Generate recommendations based on report."""
    recommendations = []

    summary = report.get("summary", {})

    if summary.get("pending", 0) > 0:
        recommendations.append(
            f"Run USX skills on {summary['pending']} pending surfaces"
        )

    if summary.get("tagged_for_work", 0) > 0:
        recommendations.append(
            f"Review {summary['tagged_for_work']} surfaces tagged for specialized work"
        )

    terminal_teletext = report.get("terminal_teletext", {})
    if terminal_teletext.get("status") == "tagged_for_specialized_work":
        recommendations.append(
            "Follow Terminal & Teletext work tag for grid mode enhancements"
        )

    # Check for surfaces without recent updates
    stale_surfaces = [
        name for name, data in report.get("surfaces", {}).items()
        if not data.get("last_updated") or
        (time.time() - data.get("last_updated", 0)) > 86400  # 24h
    ]
    if stale_surfaces:
        recommendations.append(
            f"Consider refreshing stale surfaces: {', '.join(stale_surfaces[:3])}"
        )

    return recommendations


def _persist_report(report: dict) -> None:
    """Persist report to state."""
    try:
        from app.skills.state import update_skill_state

        update_skill_state("surface_enhancement_report", {
            "last_report_ts": report["timestamp"],
            "summary": report["summary"],
        })
    except Exception:
        pass
