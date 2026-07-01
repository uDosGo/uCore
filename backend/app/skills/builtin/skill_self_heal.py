#!/usr/bin/env python3
"""Skill: Self-Heal — Autonomous recovery actions.

Converts the legacy self_heal.py classes into proper BaseSkill subclasses
so they are discoverable through the main skills registry.

Registered skills:
  - recover_port_conflict: Detect and resolve port conflicts
  - diagnose_system: Comprehensive system diagnostics
  - cleanup_resources: Kill zombie processes, clear caches
  - restart_backend: Gracefully restart backend
  - reset_database: Clear database and rebuild schema
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.self_heal")


class RecoverPortConflictSkill(BaseSkill):
    meta = SkillMeta(
        id="recover_port_conflict",
        name="Recover Port Conflict",
        description="Detect and resolve port conflicts",
        category="system",
        params=[
            SkillParam(name="port", type="integer", description="Port to check", default=8484),
        ],
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        port = kwargs.get("port", 8484)
        try:
            from app.services.process_manager import get_process_manager

            pm = get_process_manager()
            report = pm.get_port_conflict_report()

            if not report["conflicts"]:
                return {"success": True, "message": "No port conflicts detected", "details": report}

            cleaned = 0
            for conflict in report["conflicts"]:
                if pm.cleanup_port(conflict["port"], force=True):
                    cleaned += 1

            return {
                "success": True,
                "message": f"Cleaned {cleaned} port conflicts",
                "details": {"cleaned": cleaned, "conflicts": report["conflicts"]},
            }
        except Exception as e:
            log.error("Port recovery failed: %s", e)
            return {"success": False, "message": f"Recovery failed: {e}", "details": {"error": str(e)}}


class DiagnoseSystemSkill(BaseSkill):
    meta = SkillMeta(
        id="diagnose_system",
        name="Diagnose System",
        description="Analyze system health and identify issues",
        category="system",
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        try:
            from app.services.process_manager import get_process_manager

            pm = get_process_manager()
            diag = pm.get_system_diagnostics()

            issues = []
            if diag["system"]["cpu_percent"] > 80:
                issues.append("High CPU usage")
            if diag["system"]["memory_percent"] > 80:
                issues.append("High memory usage")
            if diag["system"]["disk_percent"] > 80:
                issues.append("Low disk space")
            if diag["ports"]["backend"]["available"] is False:
                issues.append(f"Backend port in use by {diag['ports']['backend']['process_name']}")

            status = "warning" if issues else "ok"
            return {
                "success": True,
                "message": f"System diagnostics complete ({status})",
                "details": {"status": status, "issues": issues, "diagnostics": diag},
            }
        except Exception as e:
            log.error("Diagnostics failed: %s", e)
            return {"success": False, "message": f"Diagnostics failed: {e}", "details": {"error": str(e)}}


class CleanupResourcesSkill(BaseSkill):
    meta = SkillMeta(
        id="cleanup_resources",
        name="Cleanup Resources",
        description="Kill zombie processes, clear caches, free memory",
        category="maintenance",
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        try:
            from app.services.process_manager import get_process_manager

            pm = get_process_manager()
            killed = pm.cleanup_stale_processes()
            return {
                "success": True,
                "message": f"Cleaned up {killed} stale processes",
                "details": {"processes_killed": killed},
            }
        except Exception as e:
            log.error("Cleanup failed: %s", e)
            return {"success": False, "message": f"Cleanup failed: {e}", "details": {"error": str(e)}}


class RestartBackendSkill(BaseSkill):
    meta = SkillMeta(
        id="restart_backend",
        name="Restart Backend",
        description="Restart the backend service",
        category="system",
        timeout=10,
    )

    async def run(self, **kwargs) -> dict:
        return {
            "success": True,
            "message": "Restart backend skill registered (execute via CLI)",
            "details": {"instruction": "Run: python3 -m app --port 8484 --restart"},
        }


class ResetDatabaseSkill(BaseSkill):
    meta = SkillMeta(
        id="reset_database",
        name="Reset Database",
        description="Clear database and rebuild schema",
        category="destructive",
        params=[
            SkillParam(name="keep_data", type="boolean", description="Keep existing data", default=True),
        ],
        timeout=60,
    )

    async def run(self, **kwargs) -> dict:
        try:
            from app.core.database import migrate_db

            result = migrate_db()
            return {
                "success": True,
                "message": "Database reset complete",
                "details": {"migration_result": result, "keep_data": kwargs.get("keep_data", True)},
            }
        except Exception as e:
            log.error("Database reset failed: %s", e)
            return {"success": False, "message": f"Database reset failed: {e}", "details": {"error": str(e)}}
