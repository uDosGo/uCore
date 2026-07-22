"""uCore — unified backend entry point

Usage:
    python -m backend.app                     Start with default settings
    python -m backend.app --port 8484
    python -m backend.app --port 8484 --auto-start
    python -m backend.app --help
    UCORE_DEBUG=1 python -m backend.app
"""
from __future__ import annotations

import argparse

from .core.logging import log
from .core.settings import settings


def main():
    parser = argparse.ArgumentParser(description="uCore — unified daemon")
    parser.add_argument(
        "--port", type=int, default=settings.port,
        help="Port to listen on (default: %(default)s)",
    )
    parser.add_argument(
        "--host", type=str, default=settings.host,
        help="Host to bind to (default: %(default)s)",
    )
    parser.add_argument(
        "--auto-start", action="store_true", default=settings.auto_start,
        help="Auto-start surfaces on boot",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug logging (or set UCORE_DEBUG=1)",
    )
    args = parser.parse_args()

    # Override settings from CLI args
    settings.port = args.port
    settings.host = args.host
    settings.auto_start = args.auto_start
    if args.debug:
        settings.debug = True

    log.info("╔══════════════════════════════════════════╗")
    log.info("║       uCore v%s — unified daemon        ║", settings.version)
    log.info("╚══════════════════════════════════════════╝")
    log.info("Host: %s:%d", settings.host, settings.port)
    log.info("Debug: %s", settings.debug)
    log.info("Auto-start surfaces: %s", settings.auto_start)

    # ── Startup Health Check ──────────────────────────────────
    log.info("Running startup health checks...")
    try:
        import asyncio

        from .services.system_health import get_full_health, run_self_repair
        health = asyncio.run(get_full_health())
        status = health.get("status", "unknown")
        passed = health.get("passed_checks", 0)
        total = health.get("total_checks", 0)
        if status == "healthy":
            log.info("✅ Startup health: %s (%d/%d checks passed)",
                     status, passed, total)
        elif status == "degraded":
            log.warning("⚠️  Startup health: DEGRADED (%d/%d checks passed)",
                        passed, total)
            for c in health.get("components", []):
                if not c.get("ok"):
                    log.warning("   ✗ %s: %s", c["name"], c["message"])
            log.info("   Attempting self-repair...")
            repair = asyncio.run(run_self_repair())
            log.info("   Repair: %d successful, %d failed → health after: %s",
                     repair.get("repairs_successful", 0),
                     repair.get("repairs_failed", 0),
                     repair.get("health_after_repair", "unknown"))
        else:
            log.error("❌ Startup health: UNHEALTHY (%d/%d checks passed)",
                      passed, total)
            for c in health.get("components", []):
                if not c.get("ok"):
                    log.error("   ✗ %s: %s", c["name"], c["message"])
            log.error("   Server will start but may be unstable.")
    except Exception as exc:
        log.warning("⚠️  Startup health check error: %s", exc)

    # MCP Integrity Check (fast structural only)
    try:
        from .api.mcp_guardrails import validate_mcp_integrity
        report = validate_mcp_integrity()
        if not report["ok"]:
            log.warning("⚠️  MCP integrity check FAILED: %s", report["errors"])
            log.warning("   Run 'skill_mcp_self_heal' to attempt auto-repair")
        else:
            log.info("✅ MCP integrity check passed")
    except Exception as exc:
        log.warning("⚠️  MCP integrity check error: %s", exc)

    # ── Auto-Start Hivemind (port 8490) ────────────────────────
    # Hivemind is core to the agent execution pipeline:
    #   hivemind-consensus → design/planning/analysis tasks
    #   roundtable-dispatch → documentation/parallel-agent tasks
    # It runs as a child process and is cleaned up on shutdown.
    _start_hivemind()

    # Delegate to snackbar
    from .core.snackbar import main as run_snackbar
    run_snackbar()


def _start_hivemind() -> None:
    """Launch Hivemind MCP server as a background child process."""
    import atexit
    import subprocess
    import sys
    from pathlib import Path

    backend_dir = Path(__file__).parent
    agents_config = backend_dir.parent / "config" / "agents.yaml"
    llm_config = backend_dir.parent / "config" / "llm_router.yaml"

    try:
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "app.mcp.hivemind_server",
                "--host", "127.0.0.1",
                "--port", "8490",
                "--agents-config", str(agents_config),
                "--llm-config", str(llm_config),
            ],
            cwd=str(backend_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        atexit.register(proc.terminate)
        log.info("✅ Hivemind auto-started (PID %d) on port 8490", proc.pid)
    except Exception as exc:
        log.warning(
            "⚠️  Hivemind auto-start failed: %s —"
            " hivemind-consensus and roundtable-dispatch skills"
            " will be unavailable", exc,
        )


if __name__ == "__main__":
    main()
