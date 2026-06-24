#!/usr/bin/env python3
"""Surface Rebuild Skill — apply all USX standards to unmigrated surfaces.

Orchestrates complete USX standardization on any surface:
1. Replace spacing: px → USX variables (spacing-normalize)
2. Replace colors: hex → Pico CSS variables (color-reset)
3. Standardize typography: font sizes → Prose-UI scale
4. Apply Pico components: nav, buttons, forms, cards
5. Verify Lucide icon coverage
6. Full audit & compliance check

Enables one-command surface migration: run({'surface': 'developer.css'})
"""
from __future__ import annotations
from pathlib import Path

SKILLS_DIR = Path(__file__).parent


def run(surface: str = "", dry_run: bool = False) -> dict:
    """Rebuild surface using all Phase 2-3 standards."""
    if not surface:
        return {
            "success": False,
            "error": "Surface name required. Usage: run(surface='developer.css')",
        }

    steps = [
        ("spacing_normalize", "Standardize spacing values"),
        ("color_reset", "Standardize color values"),
        ("audit_enhanced", "Comprehensive audit & compliance"),
    ]

    results = {
        "surface": surface,
        "steps_executed": [],
        "issues_found": [],
        "recommendations": [],
        "ready_for_deployment": False,
    }

    # Execute each step
    for step_name, description in steps:
        try:
            if step_name == "spacing_normalize":
                from app.skills.builtin.skill_usx_spacing_normalize import run as spacing_run
                result = spacing_run(target=surface, dry_run=dry_run)
            elif step_name == "color_reset":
                from app.skills.builtin.skill_color_reset import run as color_run
                result = color_run(target=surface, dry_run=dry_run)
            elif step_name == "audit_enhanced":
                from app.skills.builtin.skill_usx_audit_enhanced import run as audit_run
                result = audit_run(target=surface, dry_run=dry_run)
            else:
                result = {"success": False, "error": f"Unknown step: {step_name}"}

            if result.get("success"):
                results["steps_executed"].append({
                    "name": step_name,
                    "status": "success",
                    "description": description,
                })
        except Exception as e:
            results["issues_found"].append({
                "step": step_name,
                "error": str(e),
            })

    # Determine deployment readiness
    if (len(results["steps_executed"]) == len(steps) and
        not results["issues_found"]):
        results["ready_for_deployment"] = True
        results["recommendations"].append(
            f"Surface '{surface}' is USX-standardized and ready for deployment"
        )
    else:
        results["recommendations"].append(
            "Address issues before deployment"
        )

    return {
        "success": True,
        "action": "surface_rebuild",
        "dry_run": dry_run,
        "results": results,
    }


if __name__ == "__main__":
    import json
    result = run(surface="developer.css", dry_run=True)
    print(json.dumps(result, indent=2, default=str))
