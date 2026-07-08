"""System Health Aggregator — Unified health reporting for uCore.

Provides a single entrypoint for full-system health checks, aggregating:
- HTTP server liveness
- MCP structural integrity (guardrails)
- Skill registry load status
- Plate/template verification
- Database connectivity
- Disk space
- Maintenance scheduler status

Usage:
    from app.services.system_health import get_full_health
    report = await get_full_health()
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.system_health")

_HEALTH_START_TIME = time.time()


@dataclass
class HealthComponent:
    name: str
    ok: bool
    message: str = ""
    detail: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


async def _check_http_liveness() -> HealthComponent:
    t0 = time.perf_counter()
    return HealthComponent(
        name="http_server",
        ok=True,
        message="uCore HTTP server responding",
        latency_ms=(time.perf_counter() - t0) * 1000,
    )


async def _check_mcp_integrity() -> HealthComponent:
    t0 = time.perf_counter()
    try:
        from app.api.mcp_guardrails import validate_mcp_integrity
        report = validate_mcp_integrity()
        return HealthComponent(
            name="mcp_integrity",
            ok=report["ok"],
            message="MCP layer healthy" if report["ok"] else f"MCP integrity failure: {report['errors']}",
            detail={"checks": len(report.get("checks", [])), "errors": report.get("errors", [])},
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
    except Exception as e:
        return HealthComponent(
            name="mcp_integrity",
            ok=False,
            message=f"MCP integrity check error: {e}",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )


async def _check_skill_registry() -> HealthComponent:
    t0 = time.perf_counter()
    try:
        from app.skills.registry import list_skills as _list_skills
        skills = _list_skills()
        loaded = len(skills)
        # Check for load warnings
        try:
            from app.skills.registry import get_load_warnings
            warnings = get_load_warnings()
        except (ImportError, AttributeError):
            warnings = []
        ok = loaded > 0 and len(warnings) == 0
        return HealthComponent(
            name="skill_registry",
            ok=ok,
            message=f"Skills loaded: {loaded}" + (f", warnings: {len(warnings)}" if warnings else ""),
            detail={"count": loaded, "warnings": warnings},
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
    except Exception as e:
        return HealthComponent(
            name="skill_registry",
            ok=False,
            message=f"Skill registry error: {e}",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )


async def _check_plate_health() -> HealthComponent:
    t0 = time.perf_counter()
    try:
        from backend.plate_refresh.verification import verify_all_plates
        report = verify_all_plates()
        return HealthComponent(
            name="plate_health",
            ok=report.get("ok", False),
            message=f"Plates: {report.get('verified', 0)} verified, {report.get('failed', 0)} failed",
            detail=report,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
    except ImportError:
        return HealthComponent(
            name="plate_health",
            ok=True,
            message="Plate verification module not available (ok)",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
    except Exception as e:
        return HealthComponent(
            name="plate_health",
            ok=False,
            message=f"Plate check error: {e}",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )


async def _check_database() -> HealthComponent:
    t0 = time.perf_counter()
    try:
        from app.core.database import get_conn
        conn = get_conn()
        cur = conn.execute("SELECT 1")
        cur.fetchone()
        return HealthComponent(
            name="database",
            ok=True,
            message="Database connection healthy",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
    except Exception as e:
        return HealthComponent(
            name="database",
            ok=False,
            message=f"Database error: {e}",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )


async def _check_disk_space() -> HealthComponent:
    t0 = time.perf_counter()
    try:
        home = Path.home()
        usage = shutil.disk_usage(home)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        ok = free_gb > 1.0  # More than 1GB free
        return HealthComponent(
            name="disk_space",
            ok=ok,
            message=f"Disk: {free_gb:.1f} GB free / {total_gb:.1f} GB total",
            detail={"free_gb": round(free_gb, 1), "total_gb": round(total_gb, 1)},
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
    except Exception as e:
        return HealthComponent(
            name="disk_space",
            ok=False,
            message=f"Disk check error: {e}",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )


async def _check_maintenance_scheduler() -> HealthComponent:
    t0 = time.perf_counter()
    try:
        from app.services.maintenance_scheduler import get_maintenance_scheduler
        sched = get_maintenance_scheduler()
        if sched is None:
            return HealthComponent(
                name="maintenance_scheduler",
                ok=True,
                message="Maintenance scheduler not started (ok for dev mode)",
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        status = sched.status()
        return HealthComponent(
            name="maintenance_scheduler",
            ok=True,
            message=f"Scheduler: {len(status.get('jobs', []))} jobs configured",
            detail=status,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
    except Exception as e:
        return HealthComponent(
            name="maintenance_scheduler",
            ok=False,
            message=f"Scheduler check error: {e}",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )


async def get_full_health() -> dict[str, Any]:
    """Run all health checks concurrently and return a unified report.

    Returns a dict with:
      - status: "healthy" | "degraded" | "unhealthy"
      - uptime_seconds: float
      - components: list of {name, ok, message, detail, latency_ms}
      - total_checks: int
      - passed_checks: int
      - failed_checks: int
    """
    checks = await asyncio.gather(
        _check_http_liveness(),
        _check_mcp_integrity(),
        _check_skill_registry(),
        _check_plate_health(),
        _check_database(),
        _check_disk_space(),
        _check_maintenance_scheduler(),
    )

    components = [
        {
            "name": c.name,
            "ok": c.ok,
            "message": c.message,
            "detail": c.detail,
            "latency_ms": round(c.latency_ms, 2),
        }
        for c in checks
    ]

    passed = sum(1 for c in checks if c.ok)
    failed = len(checks) - passed

    if failed == 0:
        status = "healthy"
    elif passed > len(checks) // 2:
        status = "degraded"
    else:
        status = "unhealthy"

    return {
        "status": status,
        "uptime_seconds": round(time.time() - _HEALTH_START_TIME, 1),
        "version": _get_version(),
        "components": components,
        "total_checks": len(checks),
        "passed_checks": passed,
        "failed_checks": failed,
    }


def _get_version() -> str:
    try:
        from app.core.settings import settings
        return settings.version
    except Exception:
        return "unknown"


async def run_self_repair() -> dict[str, Any]:
    """Attempt automatic repair of known issues.

    Triggers:
      1. MCP self-heal skill (structural repair)
      2. Skill registry reload
      3. Plate verification (identify corrupted plates)

    Returns repair report.
    """
    repairs: list[dict[str, Any]] = []

    # 1. MCP self-heal
    try:
        from app.skills.builtin.skill_mcp_self_heal import MCPSelfHealSkill
        skill = MCPSelfHealSkill()
        result = await skill.run(dry_run=False)
        repairs.append({"component": "mcp_layer", "success": result.get("success", False), "message": result.get("message", "")})
    except Exception as e:
        repairs.append({"component": "mcp_layer", "success": False, "message": str(e)})

    # 2. Skill registry reload
    try:
        from app.skills.registry import reload_registry
        reload_result = reload_registry()
        repairs.append({"component": "skill_registry", "success": True, "message": f"Registry reloaded: {reload_result}"})
    except Exception as e:
        repairs.append({"component": "skill_registry", "success": False, "message": str(e)})

    # 3. Plate verification
    try:
        from backend.plate_refresh.verification import verify_all_plates
        plate_result = verify_all_plates()
        repairs.append({"component": "plate_health", "success": plate_result.get("ok", False), "detail": plate_result})
    except Exception as e:
        repairs.append({"component": "plate_health", "success": False, "message": str(e)})

    # 4. Run health check post-repair
    health = await get_full_health()

    return {
        "repairs": repairs,
        "repairs_successful": sum(1 for r in repairs if r.get("success")),
        "repairs_failed": sum(1 for r in repairs if not r.get("success")),
        "health_after_repair": health["status"],
        "components_healthy": health["passed_checks"],
        "components_total": health["total_checks"],
    }
