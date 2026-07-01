#!/usr/bin/env python3
"""Maintenance Skill Test Run — Execute on return to verify system health.

This script runs a series of self-healing skills to verify:
- Port conflicts are resolved
- System diagnostics are clean
- Resources are cleaned up
- Database is healthy
- MCP bridge is responsive

Run after system restart or when returning to work.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.skills.self_heal import execute_skill, list_skills
from app.services.popcorn_manager import get_popcorn_status, is_popcorn_running
from app.services.mcp import get_bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] maintenance: %(message)s",
)
log = logging.getLogger("maintenance_test_run")


async def run_maintenance_tests() -> dict:
    """Run all maintenance skills and return results."""
    results = {
        "skills": {},
        "system": {},
        "mcp": {},
    }

    # ─── 1. List available skills ─────────────────────────────────
    log.info("Available skills: %s", list_skills())

    # ─── 2. Diagnose system ───────────────────────────────────────
    log.info("Running diagnose_system...")
    results["skills"]["diagnose_system"] = await execute_skill("diagnose_system")
    log.info("System status: %s", results["skills"]["diagnose_system"].details.get("status"))

    # ─── 3. Recover port conflicts ─────────────────────────────────
    log.info("Running recover_port_conflict...")
    results["skills"]["recover_port_conflict"] = await execute_skill("recover_port_conflict")
    log.info("Port conflicts cleaned: %s", results["skills"]["recover_port_conflict"].details.get("cleaned", 0))

    # ─── 4. Cleanup resources ─────────────────────────────────────
    log.info("Running cleanup_resources...")
    results["skills"]["cleanup_resources"] = await execute_skill("cleanup_resources")
    log.info("Processes killed: %s", results["skills"]["cleanup_resources"].details.get("processes_killed", 0))

    # ─── 5. Reset database (schema check) ─────────────────────────
    log.info("Running reset_database (schema check)...")
    results["skills"]["reset_database"] = await execute_skill("reset_database", keep_data=True)
    log.info("Database migration: %s", results["skills"]["reset_database"].success)

    # ─── 6. Check Popcorn status ───────────────────────────────────
    log.info("Checking Popcorn status...")
    results["system"]["popcorn"] = {
        "running": is_popcorn_running(),
        "status": get_popcorn_status(),
    }
    log.info("Popcorn running: %s", results["system"]["popcorn"]["running"])

    # ─── 7. Check MCP bridge ───────────────────────────────────────
    log.info("Checking MCP bridge...")
    try:
        bridge = get_bridge()
        results["mcp"]["peers"] = bridge.get_peers()
        log.info("MCP peers: %s", list(results["mcp"]["peers"].keys()))
    except Exception as e:
        results["mcp"]["error"] = str(e)
        log.warning("MCP bridge check failed: %s", e)

    return results


def main():
    """Main entry point."""
    log.info("=" * 50)
    log.info("uCore Maintenance Test Run")
    log.info("=" * 50)

    results = asyncio.run(run_maintenance_tests())

    # Print summary
    log.info("=" * 50)
    log.info("Summary:")
    for skill_name, result in results["skills"].items():
        status = "✓" if result.success else "✗"
        log.info("  %s %s: %s", status, skill_name, result.message)

    # Save results
    output_path = Path.home() / ".ucore/logs/maintenance_test_run.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, default=str))
    log.info("Results saved to: %s", output_path)

    # Return exit code
    all_success = all(r.success for r in results["skills"].values())
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())