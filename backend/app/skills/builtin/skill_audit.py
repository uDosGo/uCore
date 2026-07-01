#!/usr/bin/env python3
"""Skill Audit — comprehensive skill health and compliance audit.

Audits all registered skills:
1. Skill state persistence
2. Recent execution logs
3. Error rates
4. Compliance with skill standards
5. DevMode operation logging

Integrates with health API and provides audit trail.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app.skills.state import read_state
from app.core.logging import log


def run(
    skill_filter: str = "",
    include_logs: bool = True,
    check_compliance: bool = True,
) -> dict[str, Any]:
    """Run comprehensive skill audit.

    Parameters
    ----------
    skill_filter : str
        Optional filter to audit specific skills (e.g., "surface_").
    include_logs : bool
        Include recent log entries in audit.
    check_compliance : bool
        Check skill compliance with standards.

    Returns
    -------
    dict with audit results, compliance status, and recommendations.
    """
    audit_start = time.time()

    # Read current skill state
    state = read_state()

    # Get all skill modules
    skills_dir = Path(__file__).parent / "builtin"
    all_skills = _discover_skills(skills_dir)

    # Filter if requested
    if skill_filter:
        all_skills = [s for s in all_skills if skill_filter in s]

    audit_results: dict[str, Any] = {
        "timestamp": int(audit_start),
        "total_skills": len(all_skills),
        "filtered": bool(skill_filter),
        "skills": {},
        "summary": {
            "healthy": 0,
            "warning": 0,
            "error": 0,
            "unknown": 0,
        },
        "dev_mode_operations": [],
        "recommendations": [],
    }

    # Audit each skill
    for skill_name in all_skills:
        skill_audit = _audit_single_skill(
            skill_name,
            state.get(skill_name, {}),
            include_logs,
            check_compliance
        )
        audit_results["skills"][skill_name] = skill_audit

        # Update summary
        status = skill_audit.get("status", "unknown")
        audit_results["summary"][status] = audit_results["summary"].get(status, 0) + 1

        # Track DevMode operations
        if skill_audit.get("dev_mode_operation"):
            audit_results["dev_mode_operations"].append({
                "skill": skill_name,
                "operation": skill_audit.get("last_operation"),
                "timestamp": skill_audit.get("last_updated_ts"),
            })

    # Generate recommendations
    audit_results["recommendations"] = _generate_recommendations(audit_results)

    # Log audit completion
    audit_duration = time.time() - audit_start
    log.info(
        f"📊 [SKILL_AUDIT] Completed in {audit_duration:.2f}s - "
        f"Healthy: {audit_results['summary']['healthy']}, "
        f"Warnings: {audit_results['summary']['warning']}, "
        f"Errors: {audit_results['summary']['error']}"
    )

    # Persist audit results
    _persist_audit_results(audit_results)

    return {
        "success": True,
        "action": "skill_audit",
        "results": audit_results,
    }


def _discover_skills(skills_dir: Path) -> list[str]:
    """Discover all skill modules."""
    skills = []
    if not skills_dir.exists():
        return skills

    for skill_file in skills_dir.glob("skill_*.py"):
        skill_name = skill_file.stem.replace("skill_", "")
        skills.append(skill_name)

    return sorted(skills)


def _audit_single_skill(
    skill_name: str,
    skill_state: dict,
    include_logs: bool,
    check_compliance: bool,
) -> dict[str, Any]:
    """Audit a single skill."""
    audit: dict[str, Any] = {
        "name": skill_name,
        "status": "unknown",
        "state": skill_state,
        "issues": [],
        "dev_mode_operation": False,
    }

    # Check if skill has state
    if not skill_state:
        audit["status"] = "unknown"
        audit["issues"].append("No state recorded")
        return audit

    # Check last updated
    last_updated = skill_state.get("last_updated_ts", 0)
    age_hours = (time.time() - last_updated) / 3600 if last_updated else None

    if age_hours is None:
        audit["status"] = "unknown"
        audit["issues"].append("No timestamp in state")
    elif age_hours > 24:
        audit["status"] = "warning"
        audit["issues"].append(f"Stale state ({age_hours:.1f}h old)")
    else:
        audit["status"] = "healthy"

    # Check for errors in state
    if skill_state.get("error"):
        audit["status"] = "error"
        audit["issues"].append(f"Error in state: {skill_state['error']}")

    # Check for convergence (surface_rebuild specific)
    if "surface_rebuild" in skill_name:
        attempts = skill_state.get("attempts", 0)
        converged = skill_state.get("converged", False)

        if attempts >= 3 and not converged:
            audit["status"] = "error"
            audit["issues"].append(f"Convergence guard tripped ({attempts} attempts)")
        elif attempts > 0 and not converged:
            audit["status"] = "warning"
            audit["issues"].append(f"Pending convergence ({attempts} attempts)")

        # Surface rebuild is a DevMode operation
        audit["dev_mode_operation"] = True
        audit["last_operation"] = "rebuild"
        audit["last_updated_ts"] = last_updated

    # Check compliance if requested
    if check_compliance:
        compliance_issues = _check_skill_compliance(skill_name)
        audit["issues"].extend(compliance_issues)
        if compliance_issues:
            audit["status"] = "warning"

    # Include recent logs if requested
    if include_logs:
        audit["recent_logs"] = _get_skill_logs(skill_name)

    return audit


def _check_skill_compliance(skill_name: str) -> list[str]:
    """Check skill compliance with standards."""
    issues = []

    # Check if skill file exists and has proper structure
    skills_dir = Path(__file__).parent / "builtin"
    skill_file = skills_dir / f"skill_{skill_name}.py"

    if not skill_file.exists():
        issues.append(f"Skill file not found: {skill_file}")
        return issues

    try:
        content = skill_file.read_text()

        # Check for required elements
        if "def run(" not in content:
            issues.append("Missing run() function")

        if "from __future__ import annotations" not in content:
            issues.append("Missing future annotations import")

        # Check for proper logging
        if "log." not in content and "logging." not in content:
            issues.append("No logging detected")

    except Exception as e:
        issues.append(f"Failed to read skill file: {e}")

    return issues


def _get_skill_logs(skill_name: str) -> list[str]:
    """Get recent log entries for a skill."""
    logs = []
    log_dir = Path.home() / ".ucore" / "logs"

    if not log_dir.exists():
        return logs

    # Check ucore.log for skill mentions
    log_file = log_dir / "ucore.log"
    if log_file.exists():
        try:
            lines = log_file.read_text().splitlines()
            # Get last 10 lines mentioning this skill
            relevant = [line for line in lines if skill_name in line]
            logs.extend(relevant[-10:])
        except Exception:
            pass

    return logs


def _generate_recommendations(audit_results: dict) -> list[str]:
    """Generate recommendations based on audit results."""
    recommendations = []

    summary = audit_results.get("summary", {})

    if summary.get("error", 0) > 0:
        recommendations.append(
            f"Address {summary['error']} skills with errors"
        )

    if summary.get("warning", 0) > 0:
        recommendations.append(
            f"Review {summary['warning']} skills with warnings"
        )

    if summary.get("unknown", 0) > 0:
        recommendations.append(
            f"Run {summary['unknown']} skills without state to initialize them"
        )

    # Check for stale skills
    stale_skills = [
        name for name, data in audit_results.get("skills", {}).items()
        if any("Stale state" in issue for issue in data.get("issues", []))
    ]
    if stale_skills:
        recommendations.append(
            f"Consider running stale skills: {', '.join(stale_skills[:3])}"
        )

    # DevMode operations
    dev_ops = audit_results.get("dev_mode_operations", [])
    if dev_ops:
        recommendations.append(
            f"DevMode operations tracked: {len(dev_ops)} operations logged"
        )

    return recommendations


def _persist_audit_results(audit_results: dict) -> None:
    """Persist audit results to state."""
    try:
        from app.skills.state import update_skill_state

        update_skill_state("skill_audit", {
            "last_audit_ts": audit_results["timestamp"],
            "summary": audit_results["summary"],
            "total_skills": audit_results["total_skills"],
        })
    except Exception:
        pass
