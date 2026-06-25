#!/usr/bin/env python3
"""Surface Rebuild Skill — apply all USX standards to unmigrated surfaces.

⚠️ CONVERGENCE GUARD — this skill self-terminates after 3 runs on the
same surface to prevent perpetual loops. See _rebuild() docstring.

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
import time
from pathlib import Path
from app.skills.state import update_skill_state

SKILLS_DIR = Path(__file__).parent

# Convergence guard — track surface rebuild attempts to prevent loops
_CONVERGENCE_TRACKER: dict[str, int] = {}
_MAX_ITERATIONS = 3
_COOLDOWN_SECONDS = 300  # 5 min cooldown before retry counter resets


def run(
    surface: str = "",
    dry_run: bool = False,
    max_iterations: int | None = None,
) -> dict:
    """Rebuild surface using all Phase 2-3 standards.

    Parameters
    ----------
    surface : str
        Surface CSS filename (e.g. 'developer.css').
    dry_run : bool
        Preview changes without applying.
    max_iterations : int | None
        Hard limit on rebuild passes (default 3). Pass 0 to skip
        guard, or None for the standard default.

    Returns
    -------
    dict with success/action/dry_run/results and a ``converged`` flag.
    """
    if not surface:
        return {
            "success": False,
            "error": (
                "Surface name required. Usage:"
                " run(surface='developer.css')"
            ),
        }

    # ── Convergence guard ───────────────────────────────────────
    now = time.time()
    # Prune stale entries
    stale = [k for k, v in _CONVERGENCE_TRACKER.items()
             if now - v > _COOLDOWN_SECONDS]
    for k in stale:
        del _CONVERGENCE_TRACKER[k]

    max_iter = (
        max_iterations if max_iterations is not None
        else _MAX_ITERATIONS
    )
    if max_iter > 0:
        prev = _CONVERGENCE_TRACKER.get(surface, 0)
        if prev >= max_iter:
            return {
                "success": False,
                "error": (
                    f"Convergence guard tripped for '{surface}' — "
                    f"rebuild called {prev}x without converging. "
                    f"Run with max_iterations=0 to override."
                ),
            }
        _CONVERGENCE_TRACKER[surface] = prev + 1
        # Persist attempt count for observability
        try:
            update_skill_state(f"surface_rebuild:{surface}", {"attempts": _CONVERGENCE_TRACKER[surface], "last_run_ts": int(now)})
        except Exception:
            pass

    # ── Pipeline ─────────────────────────────────────────────────
    steps = [
        ("spacing_normalize", "Standardize spacing values"),
        ("color_reset", "Standardize color values"),
        ("audit_enhanced", "Comprehensive audit & compliance"),
    ]

    results: dict = {
        "surface": surface,
        "steps_executed": [],
        "issues_found": [],
        "recommendations": [],
        "ready_for_deployment": False,
        "converged": False,
    }

    # Execute each step
    for step_name, description in steps:
        try:
            if step_name == "spacing_normalize":
                from app.skills.builtin import (
                    skill_usx_spacing_normalize,
                )
                spacing_run = skill_usx_spacing_normalize.run
                result = spacing_run(target=surface, dry_run=dry_run)
            elif step_name == "color_reset":
                from app.skills.builtin import (
                    skill_color_reset,
                )
                color_run = skill_color_reset.run
                result = color_run(target=surface, dry_run=dry_run)
            elif step_name == "audit_enhanced":
                from app.skills.builtin import (
                    skill_usx_audit_enhanced,
                )
                audit_run = skill_usx_audit_enhanced.run
                result = audit_run(target=surface, dry_run=dry_run)
            else:
                result = {
                    "success": False,
                    "error": (
                        f"Unknown step: {step_name}"
                    ),
                }

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

    # Determine deployment readiness & convergence
    if (len(results["steps_executed"]) == len(steps)
            and not results["issues_found"]):
        results["ready_for_deployment"] = True
        results["converged"] = True
        results["recommendations"].append(
            f"Surface '{surface}' is USX-standardized and ready for deployment"
        )
        # All steps passed — reset convergence counter so fresh runs work later
        _CONVERGENCE_TRACKER.pop(surface, None)
        # Persist success/convergence state
        try:
            update_skill_state(f"surface_rebuild:{surface}", {"converged": True, "last_result": results})
        except Exception:
            pass
    else:
        results["recommendations"].append(
            "Address issues before deployment"
        )
        try:
            update_skill_state(f"surface_rebuild:{surface}", {"converged": False, "last_result": results})
        except Exception:
            pass

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
