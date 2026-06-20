"""Dashboard Surface - system health widgets and notifications."""

from __future__ import annotations
import uuid, logging
from datetime import datetime, timezone
from typing import Optional
from aiohttp import web

log = logging.getLogger("ucore")


class DashboardStore:
    def __init__(self):
        self._widgets = {}
        self._notifications = []
        self._pinned = []
        self._seed_default_widgets()

    def _seed_default_widgets(self):
        for w in [
            {"id": "widget-system", "type": "system-status", "title": "System Status", "enabled": True, "position": 0, "config": {"refresh_interval": 10}},
            {"id": "widget-ceefax", "type": "surface-preview", "title": "Ceefax Teletext", "enabled": True, "position": 1, "config": {"surface": "ceefax", "page": 100}},
            {"id": "widget-mcp", "type": "mcp-status", "title": "AI Providers", "enabled": True, "position": 2, "config": {"refresh_interval": 30}},
            {"id": "widget-snacks", "type": "snack-queue", "title": "Snack Queue", "enabled": True, "position": 3, "config": {"max_items": 5}},
        ]:
            self._widgets[w["id"]] = w

    def list_widgets(self):
        return sorted(self._widgets.values(), key=lambda x: x.get("position", 99))

    def get_widget(self, widget_id):
        return self._widgets.get(widget_id)

    def set_widget(self, widget):
        self._widgets[widget["id"]] = widget; return widget

    def get_notifications(self, limit=20):
        return sorted(self._notifications, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    def add_notification(self, notification):
        notif = {"id": notification.get("id", uuid.uuid4().hex[:12]), "type": notification.get("type", "info"), "title": notification.get("title", ""), "body": notification.get("body", ""), "source": notification.get("source", "system"), "timestamp": datetime.now(timezone.utc).isoformat(), "read": False}
        self._notifications.append(notif); return notif

    def mark_notification_read(self, notif_id):
        for n in self._notifications:
            if n["id"] == notif_id: n["read"] = True; return True
        return False

    def clear_notifications(self):
        self._notifications.clear()

    def pin_item(self, item):
        pinned = {"id": item.get("id", uuid.uuid4().hex[:12]), "label": item.get("label", "Untitled"), "ref": item.get("ref", ""), "type": item.get("type", "link"), "pinned_at": datetime.now(timezone.utc).isoformat()}
        self._pinned.append(pinned); return pinned

    def unpin_item(self, item_id):
        for i, p in enumerate(self._pinned):
            if p["id"] == item_id: self._pinned.pop(i); return True
        return False

    def list_pinned(self):
        return list(reversed(self._pinned))


def register_dashboard_routes(app, store):
    async def handle_list_widgets(request):
        return web.json_response({"widgets": store.list_widgets()})

    async def handle_get_widget(request):
        w = store.get_widget(request.match_info["id"])
        if not w: return web.json_response({"error": "Widget not found"}, status=404)
        return web.json_response({"widget": w})

    async def handle_update_widget(request):
        try:
            body = await request.json(); body["id"] = request.match_info["id"]
            store.set_widget(body); return web.json_response({"status": "ok", "widget": body})
        except Exception as e: return web.json_response({"error": str(e)})

    async def handle_get_notifications(request):
        limit = int(request.query.get("limit", "20"))
        return web.json_response({"notifications": store.get_notifications(limit)})

    async def handle_add_notification(request):
        try:
            body = await request.json()
            notif = store.add_notification(body)
            return web.json_response({"status": "ok", "notification": notif})
        except Exception as e: return web.json_response({"error": str(e)})

    async def handle_mark_read(request):
        ok = store.mark_notification_read(request.match_info["id"])
        if not ok: return web.json_response({"error": "Not found"}, status=404)
        return web.json_response({"status": "ok"})

    async def handle_clear_notifications(request):
        store.clear_notifications(); return web.json_response({"status": "ok"})

    async def handle_list_pinned(request):
        return web.json_response({"pinned": store.list_pinned()})

    async def handle_pin_item(request):
        try:
            body = await request.json()
            item = store.pin_item(body); return web.json_response({"status": "ok", "item": item})
        except Exception as e: return web.json_response({"error": str(e)})

    async def handle_unpin_item(request):
        ok = store.unpin_item(request.match_info["id"])
        if not ok: return web.json_response({"error": "Not found"}, status=404)
        return web.json_response({"status": "ok"})

    app.router.add_get("/api/dashboard/widgets", handle_list_widgets)
    app.router.add_get("/api/dashboard/widgets/{id}", handle_get_widget)
    app.router.add_put("/api/dashboard/widgets/{id}", handle_update_widget)
    app.router.add_get("/api/dashboard/notifications", handle_get_notifications)
    app.router.add_post("/api/dashboard/notifications", handle_add_notification)
    app.router.add_post("/api/dashboard/notifications/{id}/read", handle_mark_read)
    app.router.add_delete("/api/dashboard/notifications", handle_clear_notifications)
    app.router.add_get("/api/dashboard/pinned", handle_list_pinned)
    app.router.add_post("/api/dashboard/pinned", handle_pin_item)
    app.router.add_delete("/api/dashboard/pinned/{id}", handle_unpin_item)
