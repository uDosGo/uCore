"""uCore API — metadata endpoints (system info, etc.)"""
from __future__ import annotations

import time as time_mod
from aiohttp import web
from ..core.settings import settings
import platform as plat
import subprocess


async def system_info_handler(request: web.Request) -> web.Response:
    """Return system/platform metadata with real-time resource data."""
    resources = _get_resource_snapshot()
    return web.json_response({
        "platform": plat.system(),
        "machine": plat.machine(),
        "python": plat.python_version(),
        "hostname": plat.node(),
        "app": settings.app_name,
        "version": settings.version,
        "resources": resources,
        "services": _get_service_status(),
    })


def _get_resource_snapshot() -> dict:
    resources = {}
    # CPU load
    try:
        load1, load5, load15 = _get_load_avg()
        resources["cpu_load_1m"] = round(load1, 2)
        resources["cpu_load_5m"] = round(load5, 2)
        resources["cpu_load_15m"] = round(load15, 2)
        resources["cpu_count"] = _count_cores()
    except OSError:
        pass
    # Memory
    try:
        mem = _get_memory_info()
        resources.update(mem)
    except Exception:
        pass
    # Disk
    try:
        resources["disk"] = _get_disk_info()
    except Exception:
        pass
    # Uptime
    try:
        resources["uptime_seconds"] = _get_uptime()
    except Exception:
        pass
    return resources


def _get_load_avg() -> tuple[float, float, float]:
    """Get load average — works on macOS and Linux."""
    try:
        return tuple(float(v) for v in open("/proc/loadavg").read().split()[:3])
    except (FileNotFoundError, OSError):
        pass
    try:
        result = subprocess.run(["sysctl", "-n", "vm.loadavg"], capture_output=True, text=True, timeout=5)
        values = result.stdout.strip().strip("{}").split()
        return float(values[0]), float(values[1]), float(values[2])
    except Exception:
        return 0.0, 0.0, 0.0


def _count_cores() -> int:
    import os
    return os.cpu_count() or 1


def _get_memory_info() -> dict:
    try:
        result = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5)
        page_size = 16384  # Apple Silicon
        free = active = inactive = wired = 0
        for line in result.stdout.splitlines():
            if "Pages free" in line:
                free = int(line.split()[-1].rstrip("."))
            elif "Pages active" in line:
                active = int(line.split()[-1].rstrip("."))
            elif "Pages inactive" in line:
                inactive = int(line.split()[-1].rstrip("."))
            elif "Pages wired down" in line:
                wired = int(line.split()[-1].rstrip("."))
        total = free + active + inactive
        used = active + wired
        return {
            "memory_free_mb": round(free * page_size / 1024 / 1024, 1),
            "memory_active_mb": round(active * page_size / 1024 / 1024, 1),
            "memory_used_pct": round(used / max(total, 1) * 100, 1),
            "memory_total_mb": round(total * page_size / 1024 / 1024, 1),
        }
    except Exception:
        return {}


def _get_disk_info() -> dict:
    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        parts = result.stdout.splitlines()[-1].split()
        if len(parts) >= 5:
            return {"total": parts[1], "used": parts[2], "free": parts[3], "used_pct": int(parts[4].rstrip("%"))}
    except Exception:
        pass
    return {}


def _get_uptime() -> float:
    try:
        result = subprocess.run(["sysctl", "-n", "kern.boottime"], capture_output=True, text=True, timeout=5)
        import re
        m = re.search(r"sec\s*=\s*(\d+)", result.stdout)
        if m:
            return time_mod.time() - int(m.group(1))
    except Exception:
        pass
    return 0.0


def _get_service_status() -> dict:
    services = {"ucore": "running"}
    # Ollama
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2):
            services["ollama"] = "running"
    except Exception:
        services["ollama"] = "stopped"
    # Docker
    try:
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=3)
        containers = [c for c in result.stdout.splitlines() if c.strip()]
        services["docker"] = "running" if result.returncode == 0 else "unavailable"
        if containers:
            services["containers"] = containers[:5]
    except Exception:
        services["docker"] = "unavailable"
    return services


async def maintenance_status_handler(request: web.Request) -> web.Response:
    """Return maintenance scheduler status and last-run information."""
    from app.services.maintenance_scheduler import get_maintenance_scheduler

    scheduler = get_maintenance_scheduler()
    if scheduler is None:
        return web.json_response({"status": "unavailable", "reason": "scheduler not started"}, status=503)
    return web.json_response({"status": "ok", **scheduler.status()})


async def workflow_status_handler(request: web.Request) -> web.Response:
    """Return workflow surface status for Developer/System UI wiring."""
    from app.services.maintenance_scheduler import get_maintenance_scheduler
    from app.services.workflow_status import build_workflow_status

    scheduler = get_maintenance_scheduler()
    maintenance = None
    if scheduler is not None:
        maintenance = {"status": "ok", **scheduler.status()}
    return web.json_response({"status": "ok", **build_workflow_status(maintenance=maintenance)})
