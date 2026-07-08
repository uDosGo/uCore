"""Control Service — aggregates all uCore ecosystem status into one payload.

Used by the Control Panel (Developer Surface) to display:
- Status badges (Cline, OpenRouter, Hivemind, Roundtable, Ollama, Feed, Slate, Budget)
- Live feed stream
- Agent status (Hivemind consensus, Roundtable swarm, Cline session, Ollama models)
- Cost dashboard (daily/weekly/monthly)
- Active mission (from .tasker)
- Tasker overview, MCP servers, Slates, Alerts
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.services.control")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

async def _http_get(url: str, timeout: float = 3.0) -> dict | None:
    """Async HTTP GET — runs blocking urllib in thread pool to avoid blocking the event loop."""
    def _sync_get() -> dict | None:
        try:
            import urllib.request
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except Exception:
            return None
    return await asyncio.to_thread(_sync_get)


async def _httpx_get(url: str, timeout: float = 3.0) -> dict | None:
    """Async HTTP GET via httpx."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            if resp.status_code < 400:
                return resp.json()
    except Exception:
        pass
    return None


async def _run_shell(cmd: list[str], timeout: float = 3.0) -> str:
    """Run a shell command in a thread pool, return stdout or ''."""
    def _sync_run() -> str:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
            return result.stdout.strip()
        except Exception:
            return ""
    return await asyncio.to_thread(_sync_run)


def _tasker_dir() -> Path | None:
    """Locate .tasker directory."""
    candidates = [
        Path(os.environ.get("UCORE_ROOT", "")) / ".tasker",
        Path.home() / "Code" / "uCore" / ".tasker",
        Path.cwd() / ".tasker",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


# ---------------------------------------------------------------------------
# Status badge checks
# ---------------------------------------------------------------------------

async def check_cline() -> dict:
    """Check Cline CLI availability."""
    result = {"online": False, "detail": "Cline CLI not reachable"}
    # Try Cline CLI health endpoint
    data = await _http_get("http://localhost:8485/health", timeout=1.0)
    if data:
        result["online"] = True
        result["detail"] = "Cline CLI connected"
        result["data"] = data
        return result
    # Fallback: check if cline CLI is in PATH
    cli_path = await _run_shell(["which", "cline"], timeout=1.0)
    if cli_path:
        result["online"] = True
        result["detail"] = f"Cline CLI available at {cli_path}"
        return result
    return result


async def check_openrouter() -> dict:
    """Check OpenRouter API connectivity."""
    # Try local config
    config_path = Path(os.environ.get("UCORE_ROOT", Path.home() / "Code" / "uCore")) / "config" / "openrouter.yaml"
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key and config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                cfg = yaml.safe_load(f) or {}
            api_key = cfg.get("api_key", "")
        except Exception:
            pass

    result = {"online": False, "detail": "No API key configured", "credits": 0}
    if not api_key:
        return result

    # Validate key against OpenRouter
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {api_key}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            result["online"] = True
            result["detail"] = "API key valid"
            result["data"] = body
            result["credits"] = body.get("data", {}).get("credits", 0)
    except Exception:
        result["detail"] = "OpenRouter API unreachable"
    return result


async def check_hivemind() -> dict:
    """Check Hivemind health on port 8490."""
    data = await _http_get("http://localhost:8490/health", timeout=1.0)
    if data:
        return {"online": True, "detail": "Hivemind responding", "data": data}
    return {"online": False, "detail": "Hivemind not reachable on port 8490"}


async def check_roundtable() -> dict:
    """Check Roundtable agent status."""
    data = await _http_get("http://localhost:8490/api/hivemind/roundtable", timeout=1.0)
    if data:
        return {"online": True, "detail": "Roundtable available", "data": data}
    return {"online": False, "detail": "Roundtable not reachable"}


async def check_ollama() -> dict:
    """Check Ollama status."""
    data = await _http_get("http://localhost:11434/api/tags", timeout=1.5)
    if data and "models" in data:
        return {
            "online": True,
            "detail": f"{len(data.get('models', []))} models available",
            "model_count": len(data.get("models", [])),
        }
    return {"online": False, "detail": "Ollama not running"}


async def check_feed() -> dict:
    """Check Feed Pod connectivity."""
    data = await _http_get("http://localhost:8484/api/feed/query?limit=1", timeout=1.0)
    if data is not None:
        return {"online": True, "detail": "Feed Pod connected", "activity_count": data.get("count", 0)}
    return {"online": False, "detail": "Feed Pod not reachable"}


async def check_slate() -> dict:
    """Check Slate template system."""
    data = await _http_get("http://localhost:8484/api/templates/list", timeout=1.0)
    if data:
        templates = data if isinstance(data, list) else data.get("templates", [])
        return {"online": True, "detail": f"{len(templates)} templates", "template_count": len(templates)}
    return {"online": False, "detail": "Slate system not reachable"}


async def get_cost_status() -> dict:
    """Get budget/cost status."""
    data = await _http_get("http://localhost:8484/api/hivemind/llm/cost", timeout=1.0)
    if data:
        daily = data.get("daily", {})
        return {
            "online": True,
            "detail": f"${daily.get('used', 0):.2f} / ${daily.get('limit', 0):.2f}",
            "daily": daily,
            "weekly": data.get("weekly", {}),
            "monthly": data.get("monthly", {}),
        }
    # Fallback: try budget API
    data = await _http_get("http://localhost:8484/api/budget/status", timeout=1.0)
    if data:
        return {"online": True, "detail": "Budget data available", **data}
    return {"online": False, "detail": "Cost/budget data unavailable", "daily": {}}


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------

async def get_recent_feed(limit: int = 20) -> list[dict]:
    """Get recent feed activities."""
    data = await _http_get(f"http://localhost:8484/api/feed/query?limit={limit}", timeout=1.5)
    if data:
        return data.get("activities", [])
    return []


async def get_unprocessed_count() -> int:
    """Count unprocessed feed items."""
    data = await _http_get("http://localhost:8484/api/feed/query?limit=200", timeout=1.5)
    if data:
        activities = data.get("activities", [])
        return sum(1 for a in activities if not a.get("processed", False))
    return 0


# ---------------------------------------------------------------------------
# Agent status
# ---------------------------------------------------------------------------

async def get_hivemind_status() -> dict:
    """Get Hivemind consensus status."""
    data = await _http_get("http://localhost:8490/api/hivemind/status", timeout=1.0)
    if data:
        return data
    health = await _http_get("http://localhost:8490/health", timeout=1.0)
    if health:
        return {"status": "running", "detail": "Hivemind server alive", "data": health}
    return {"status": "offline", "detail": "Hivemind not reachable"}


async def get_roundtable_status() -> dict:
    """Get Roundtable swarm status."""
    data = await _http_get("http://localhost:8490/api/hivemind/roundtable", timeout=1.0)
    if data:
        return data
    return {"status": "unknown", "detail": "Roundtable status unavailable"}


async def get_cline_status() -> dict:
    """Get current Cline session info."""
    data = await _http_get("http://localhost:8485/status", timeout=1.0)
    if data:
        return {"active": True, "data": data}
    return {"active": False, "detail": "No active Cline session"}


async def get_ollama_status() -> dict:
    """Get detailed Ollama status."""
    data = await _http_get("http://localhost:11434/api/tags", timeout=1.5)
    if not data:
        return {"online": False, "models": []}
    models = data.get("models", [])
    return {
        "online": True,
        "model_count": len(models),
        "models": [{"name": m.get("name", "unknown"), "size_gb": round(m.get("size", 0) / 1e9, 2)} for m in models[:8]],
    }


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------

async def get_cost_summary() -> dict:
    """Get cost summary (daily, weekly, monthly, top models)."""
    data = await _http_get("http://localhost:8484/api/hivemind/llm/cost", timeout=1.0)
    if data:
        return {
            "daily": data.get("daily", {}),
            "weekly": data.get("weekly", {}),
            "monthly": data.get("monthly", {}),
            "top_models": data.get("top_models", []),
        }
    # Fallback
    budget = await _http_get("http://localhost:8484/api/budget/status", timeout=1.0)
    if budget:
        return {"daily": budget, "weekly": {}, "monthly": {}, "top_models": []}
    return {"daily": {}, "weekly": {}, "monthly": {}, "top_models": []}


# ---------------------------------------------------------------------------
# Mission
# ---------------------------------------------------------------------------

async def get_active_mission() -> dict:
    """Get active mission from .tasker."""
    td = _tasker_dir()
    if not td:
        return {"name": "", "tasks_total": 0, "tasks_done": 0, "binder_count": 0, "progress_pct": 0}

    # Read sprint status
    sprint_files = sorted(td.glob("sprint-*.md"))
    if not sprint_files:
        return {"name": "", "tasks_total": 0, "tasks_done": 0, "binder_count": 0, "progress_pct": 0}

    latest = sprint_files[-1]
    content = latest.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    name = latest.stem.replace("sprint-", "").replace("-", " ").title()
    tasks_total = sum(1 for l in lines if l.strip().startswith("- ["))
    tasks_done = sum(1 for l in lines if l.strip().startswith("- [x]"))
    # Count binders
    binders = list(td.glob("binder-*.md"))

    progress_pct = round((tasks_done / tasks_total) * 100) if tasks_total > 0 else 0

    # Try tasker API for richer data
    api_data = await _http_get("http://localhost:8484/api/tasker/tasks?limit=50", timeout=1.0)
    if api_data:
        tasks = api_data if isinstance(api_data, list) else api_data.get("tasks", [])
        tasks_total = max(tasks_total, len(tasks))
        tasks_done = max(tasks_done, sum(1 for t in tasks if t.get("status") in ("done", "completed")))
        progress_pct = round((tasks_done / tasks_total) * 100) if tasks_total > 0 else 0

    return {
        "name": name,
        "tasks_total": tasks_total,
        "tasks_done": tasks_done,
        "binder_count": len(binders),
        "progress_pct": progress_pct,
    }


# ---------------------------------------------------------------------------
# Tasker overview
# ---------------------------------------------------------------------------

async def get_tasker_overview() -> dict:
    """Get tasker summary."""
    data = await _http_get("http://localhost:8484/api/tasker/tasks?limit=100", timeout=1.0)
    if data:
        tasks = data if isinstance(data, list) else data.get("tasks", [])
        done = sum(1 for t in tasks if t.get("status") in ("done", "completed"))
        pending = [t for t in tasks if t.get("status") not in ("done", "completed")]
        next_task = pending[0].get("id", "") if pending else ""
        return {
            "total": len(tasks),
            "done": done,
            "next": next_task,
        }

    # Fallback: scan .tasker directory
    td = _tasker_dir()
    if not td:
        return {"total": 0, "done": 0, "next": ""}

    task_files = list(td.glob("*.md"))
    done = 0
    for tf in task_files:
        if "[x]" in tf.read_text(encoding="utf-8", errors="replace")[:500]:
            done += 1
    return {"total": len(task_files), "done": done, "next": ""}


# ---------------------------------------------------------------------------
# MCP servers
# ---------------------------------------------------------------------------

async def get_mcp_servers() -> list[dict]:
    """Get MCP server status."""
    data = await _http_get("http://localhost:8484/api/mcp/tools", timeout=1.0)
    if data:
        tools = data if isinstance(data, list) else data.get("tools", [])
        # Group by server
        servers: dict[str, dict] = {}
        for t in tools:
            srv = t.get("server", "unknown")
            if srv not in servers:
                servers[srv] = {"name": srv, "online": True, "tools": 0}
            servers[srv]["tools"] += 1
        return list(servers.values())

    # Fallback: hardcoded known servers with health checks
    known = [
        {"name": "snackbar", "url": "http://localhost:8484/health", "endpoint": "localhost:8484"},
        {"name": "hivemind", "url": "http://localhost:8490/health", "endpoint": "localhost:8490"},
        {"name": "vault", "url": "http://localhost:8765/health", "endpoint": "localhost:8765"},
        {"name": "gridsmith", "url": "http://localhost:8888/health", "endpoint": "localhost:8888"},
    ]
    results = []
    for s in known:
        health = await _http_get(s["url"], timeout=1.5)
        results.append({
            "name": s["name"],
            "online": health is not None,
            "endpoint": s["endpoint"],
            "tools": 0,
        })
    return results


# ---------------------------------------------------------------------------
# Slates
# ---------------------------------------------------------------------------

async def get_slate_list() -> list[dict]:
    """Get available Slates."""
    data = await _http_get("http://localhost:8484/api/templates/list", timeout=1.0)
    if data:
        if isinstance(data, list):
            return data
        return data.get("templates", [])

    # Fallback: scan plates directory
    plates_dir = Path(os.environ.get("UCORE_ROOT", Path.home() / "Code" / "uCore")) / "plates"
    if plates_dir.is_dir():
        templates = []
        for p in sorted(plates_dir.iterdir()):
            if p.is_dir() and not p.name.startswith("."):
                templates.append({"name": p.name, "path": str(p), "active": p.name == "surface"})
        return templates
    return []


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

async def get_active_alerts() -> list[dict]:
    """Generate active alerts based on status checks."""
    alerts = []

    # Budget alert
    cost = await get_cost_status()
    daily = cost.get("daily", {})
    if daily:
        used = float(daily.get("used", 0))
        limit = float(daily.get("limit", 0))
        if limit > 0 and used / limit > 0.8:
            alerts.append({
                "type": "warning",
                "message": f"Daily budget nearly exhausted (${used:.2f}/${limit:.2f})",
                "source": "budget",
            })

    # Feed backlog
    unprocessed = await get_unprocessed_count()
    if unprocessed > 100:
        alerts.append({
            "type": "warning",
            "message": f"Feed backlog: {unprocessed} unprocessed activities",
            "source": "feed",
        })

    # Hivemind
    hive = await check_hivemind()
    if not hive.get("online"):
        alerts.append({
            "type": "error",
            "message": "Hivemind not responding on port 8490",
            "source": "hivemind",
        })

    # OpenRouter credits
    or_status = await check_openrouter()
    credits = or_status.get("credits", 0)
    if or_status.get("online") and credits < 5.0:
        alerts.append({
            "type": "warning",
            "message": f"OpenRouter credits low: ${credits:.2f} remaining",
            "source": "openrouter",
        })

    return alerts


# ---------------------------------------------------------------------------
# Main aggregation
# ---------------------------------------------------------------------------

async def get_control_status() -> dict:
    """Aggregate all ecosystem status into one payload."""
    # Run all checks concurrently
    statuses, feed, agents, cost, mission, tasker, mcp, slates, alerts = await asyncio.gather(
        _gather_statuses(),
        _gather_feed(),
        _gather_agents(),
        get_cost_summary(),
        get_active_mission(),
        get_tasker_overview(),
        get_mcp_servers(),
        get_slate_list(),
        get_active_alerts(),
    )

    return {
        "statuses": statuses,
        "feed": feed,
        "agents": agents,
        "cost": cost,
        "mission": mission,
        "tasker": tasker,
        "mcp": mcp,
        "slates": slates,
        "alerts": alerts,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _gather_statuses() -> dict:
    results = await asyncio.gather(
        check_cline(),
        check_openrouter(),
        check_hivemind(),
        check_roundtable(),
        check_ollama(),
        check_feed(),
        check_slate(),
        get_cost_status(),
    )
    keys = ["cline", "openrouter", "hivemind", "roundtable", "ollama", "feed", "slate", "budget"]
    return dict(zip(keys, results))


async def _gather_feed() -> dict:
    recent, unprocessed = await asyncio.gather(
        get_recent_feed(limit=20),
        get_unprocessed_count(),
    )
    return {"recent": recent, "unprocessed": unprocessed}


async def _gather_agents() -> dict:
    hive, rt, cline, ollama = await asyncio.gather(
        get_hivemind_status(),
        get_roundtable_status(),
        get_cline_status(),
        get_ollama_status(),
    )
    return {"hivemind": hive, "roundtable": rt, "cline": cline, "ollama": ollama}
