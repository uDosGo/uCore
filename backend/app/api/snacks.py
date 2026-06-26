"""API routes for Snack queue and delivery."""
from __future__ import annotations

from aiohttp import web

from app.menu.clipboard_buffer import (
    add_clipboard_item,
    capture_current_clipboard,
    cleanup_history,
    clear_history,
    copy_text_to_clipboard,
    delete_item,
    get_item_by_id,
    get_recent_items,
    pin_item,
    search_items,
)
from app.menu.system_snacks import (
    list_system_snacks,
    read_system_badges,
    run_system_snack,
)
from app.models.snack import SnackPriority, SnackType
from app.services.snackbar_orchestrator import SnackbarOrchestrator

# Shared service instance
_orch = SnackbarOrchestrator()


def register_snack_routes(app: web.Application) -> None:
    app.router.add_get("/api/snacks", list_queue)
    app.router.add_post("/api/snacks", queue_snack)
    app.router.add_get("/api/snacks/history", get_history)
    app.router.add_post("/api/snacks/{snack_id}/deliver", deliver_snack)
    app.router.add_post("/api/snacks/{snack_id}/fail", fail_snack)
    app.router.add_post("/api/snacks/{snack_id}/retry", retry_snack)
    app.router.add_delete("/api/snacks/queue", clear_queue)
    app.router.add_get("/api/snacks/system", list_system)
    app.router.add_get("/api/snacks/system/badges", list_system_badges)
    app.router.add_post("/api/snacks/system/{snack_id}/run", run_system)
    app.router.add_get("/api/snacks/clipboard", list_clipboard)
    app.router.add_get("/api/snacks/clipboard/search", search_clipboard)
    app.router.add_post("/api/snacks/clipboard/capture", capture_clipboard)
    app.router.add_post("/api/snacks/clipboard/save", save_clipboard_item)
    app.router.add_post("/api/snacks/clipboard/{item_id}/pin", pin_clipboard_item)
    app.router.add_post("/api/snacks/clipboard/{item_id}/paste", paste_clipboard_item)
    app.router.add_delete("/api/snacks/clipboard/{item_id}", delete_clipboard_item)
    app.router.add_post("/api/snacks/clipboard/cleanup", cleanup_clipboard)
    app.router.add_post("/api/snacks/clipboard/clear", clear_clipboard)


async def list_queue(request: web.Request) -> web.Response:
    """GET /api/snacks — list pending snacks in priority order"""
    queue = _orch.get_queue()
    return web.json_response({
        "snacks": [s.model_dump(mode="json") for s in queue],
        "pending": len(queue),
    })


async def queue_snack(request: web.Request) -> web.Response:
    """POST /api/snacks — add a snack to the queue"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    type_str = data.get("type", "message")
    priority_str = data.get("priority", "normal")

    try:
        st = SnackType(type_str)
    except ValueError:
        return web.json_response({"error": f"Invalid type: {type_str}"}, status=400)

    try:
        pr = SnackPriority[priority_str.upper()]
    except KeyError:
        return web.json_response({"error": f"Invalid priority: {priority_str}"}, status=400)

    snack = _orch.queue_snack(
        type=st,
        content=data.get("content", {}),
        priority=pr,
        source=data.get("source", "api"),
        target=data.get("target"),
        timeout_seconds=data.get("timeout_seconds"),
    )
    return web.json_response(snack.model_dump(mode="json"), status=201)


async def get_history(request: web.Request) -> web.Response:
    """GET /api/snacks/history — list delivered/failed snacks"""
    limit = request.query.get("limit")
    try:
        limit = int(limit) if limit else None
    except ValueError:
        limit = None
    history = _orch.get_history(limit=limit)
    return web.json_response({
        "snacks": [s.model_dump(mode="json") for s in history],
        "count": len(history),
    })


async def deliver_snack(request: web.Request) -> web.Response:
    """POST /api/snacks/{snack_id}/deliver"""
    snack_id = request.match_info.get("snack_id")
    snack = _orch.deliver_snack(snack_id)
    if snack is None:
        return web.json_response({"error": "Snack not found"}, status=404)
    return web.json_response(snack.model_dump(mode="json"))


async def fail_snack(request: web.Request) -> web.Response:
    """POST /api/snacks/{snack_id}/fail"""
    snack_id = request.match_info.get("snack_id")
    snack = _orch.fail_snack(snack_id)
    if snack is None:
        return web.json_response({"error": "Snack not found"}, status=404)
    return web.json_response(snack.model_dump(mode="json"))


async def retry_snack(request: web.Request) -> web.Response:
    """POST /api/snacks/{snack_id}/retry"""
    snack_id = request.match_info.get("snack_id")
    snack = _orch.retry_snack(snack_id)
    if snack is None:
        return web.json_response({"error": "Snack not found or max retries reached"}, status=404)
    return web.json_response(snack.model_dump(mode="json"))


async def clear_queue(request: web.Request) -> web.Response:
    """DELETE /api/snacks/queue — clear all pending"""
    cleared = _orch.clear_queue()
    return web.json_response({"status": "cleared", "count": cleared})


async def list_system(request: web.Request) -> web.Response:
    """GET /api/snacks/system — list built-in macOS system snacks."""
    snacks = list_system_snacks()
    return web.json_response({"snacks": snacks, "count": len(snacks)})


async def list_system_badges(request: web.Request) -> web.Response:
    """GET /api/snacks/system/badges — fetch live badge values."""
    badges = read_system_badges()
    return web.json_response({"badges": badges, "count": len(badges)})


async def run_system(request: web.Request) -> web.Response:
    """POST /api/snacks/system/{snack_id}/run — execute a built-in system snack.

    Body (optional):
      {
        "action": "summarise|rewrite-professional|compose|format|to-html|validate",
        "text": "optional input"
      }
    """
    snack_id = request.match_info.get("snack_id", "")
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    result = run_system_snack(
        snack_id,
        action=body.get("action"),
        text=body.get("text"),
    )
    status = 200 if result.get("status") == "success" else 400
    return web.json_response(result, status=status)


async def list_clipboard(request: web.Request) -> web.Response:
    """GET /api/snacks/clipboard — list recent clipboard buffer items."""
    try:
        limit = int(request.query.get("limit", "50"))
    except ValueError:
        limit = 50
    include_pinned = request.query.get("include_pinned", "true").lower() != "false"
    items = get_recent_items(limit=limit, include_pinned=include_pinned)
    return web.json_response({"items": items, "count": len(items)})


async def search_clipboard(request: web.Request) -> web.Response:
    """GET /api/snacks/clipboard/search?q=... — search clipboard history."""
    q = (request.query.get("q") or "").strip()
    if not q:
        return web.json_response({"error": "q is required"}, status=400)
    try:
        limit = int(request.query.get("limit", "50"))
    except ValueError:
        limit = 50
    items = search_items(q, limit=limit)
    return web.json_response({"query": q, "items": items, "count": len(items)})


async def capture_clipboard(request: web.Request) -> web.Response:
    """POST /api/snacks/clipboard/capture — save current macOS clipboard text."""
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}
    source = body.get("source", "user_copy")
    metadata = body.get("metadata") or {}
    try:
        item = capture_current_clipboard(source=source, metadata=metadata)
    except Exception as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(item, status=201)


async def save_clipboard_item(request: web.Request) -> web.Response:
    """POST /api/snacks/clipboard/save — save text/snippet directly to buffer."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    content = (body.get("content") or "").strip()
    if not content:
        return web.json_response({"error": "content is required"}, status=400)

    source = body.get("source", "user_saved")
    item_type = body.get("type", "text")
    metadata = body.get("metadata") or {}
    pinned = bool(body.get("pinned", True))
    item = add_clipboard_item(
        source=source,
        type=item_type,
        content=content,
        metadata=metadata,
        pinned=pinned,
    )
    return web.json_response(item, status=201)


async def pin_clipboard_item(request: web.Request) -> web.Response:
    """POST /api/snacks/clipboard/{item_id}/pin — pin/unpin an item."""
    item_id = request.match_info.get("item_id", "")
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}
    pinned = bool(body.get("pinned", True))
    ok = pin_item(item_id, pinned=pinned)
    if not ok:
        return web.json_response({"error": "Item not found"}, status=404)
    return web.json_response({"id": item_id, "pinned": pinned, "status": "ok"})


async def paste_clipboard_item(request: web.Request) -> web.Response:
    """POST /api/snacks/clipboard/{item_id}/paste — copy item content into system clipboard."""
    item_id = request.match_info.get("item_id", "")
    item = get_item_by_id(item_id)
    if not item:
        return web.json_response({"error": "Item not found"}, status=404)
    try:
        copy_text_to_clipboard(item.get("content") or "")
    except Exception as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"status": "ok", "id": item_id})


async def delete_clipboard_item(request: web.Request) -> web.Response:
    """DELETE /api/snacks/clipboard/{item_id} — soft-delete from history."""
    item_id = request.match_info.get("item_id", "")
    ok = delete_item(item_id)
    if not ok:
        return web.json_response({"error": "Item not found"}, status=404)
    return web.json_response({"status": "deleted", "id": item_id})


async def cleanup_clipboard(request: web.Request) -> web.Response:
    """POST /api/snacks/clipboard/cleanup — prune old and overflow non-pinned items."""
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}
    try:
        max_items = int(body.get("max_items", 500))
        max_days = int(body.get("max_days", 30))
    except ValueError:
        return web.json_response({"error": "max_items and max_days must be integers"}, status=400)
    result = cleanup_history(max_items=max_items, max_days=max_days)
    return web.json_response({"status": "ok", **result, "max_items": max_items, "max_days": max_days})


async def clear_clipboard(request: web.Request) -> web.Response:
    """POST /api/snacks/clipboard/clear — clear history, optionally including pinned items."""
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}
    include_pinned = bool(body.get("include_pinned", False))
    count = clear_history(include_pinned=include_pinned)
    return web.json_response(
        {"status": "ok", "cleared": count, "include_pinned": include_pinned},
    )
