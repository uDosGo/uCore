"""Spool / Activity Feed API endpoints."""
from __future__ import annotations

from aiohttp import web

from app.services.spool_reader import read_spool, summarize_spool


async def handle_spool_feed(request: web.Request) -> web.Response:
    try:
        max_entries = int(request.query.get("max", 50))
    except (ValueError, TypeError):
        max_entries = 50
    levels_str = request.query.get("levels", "")
    levels = [l.strip().upper() for l in levels_str.split(",") if l.strip()] if levels_str else None
    modules_str = request.query.get("modules", "")
    modules = [m.strip() for m in modules_str.split(",") if m.strip()] if modules_str else None
    search = request.query.get("search", "") or None
    since = request.query.get("since", "") or None
    errors_only = request.query.get("errors_only", "").lower() in ("1", "true", "yes")
    entries = read_spool(max_entries=max_entries, levels=levels, modules=modules,
                          search=search, since=since, errors_only=errors_only)
    return web.json_response({"success": True, "count": len(entries), "entries": [e.to_dict() for e in entries]})


async def handle_spool_summary(request: web.Request) -> web.Response:
    try:
        hours = int(request.query.get("hours", 24))
    except (ValueError, TypeError):
        hours = 24
    summary = summarize_spool(hours=hours)
    return web.json_response({"success": True, "hours": hours, "summary": summary, "format": "markdown"})


def register_spool_routes(app: web.Application) -> None:
    app.router.add_get("/api/spool/feed", handle_spool_feed)
    app.router.add_get("/api/spool/summary", handle_spool_summary)
