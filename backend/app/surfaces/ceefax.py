"""Ceefax Teletext Surface - 48x36 character grid with feed pages."""

from __future__ import annotations
import uuid, logging
from datetime import datetime, timezone
from typing import Optional
from aiohttp import web

log = logging.getLogger("ucore")

PAGE_COLS = 48
PAGE_ROWS = 36

SOURCE_ICONS = {
    "email": "\U0001F4E7", "rss": "\U0001F4E1", "github": "\U0001F419",
    "slack": "\U0001F4AC", "hackernews": "\U0001F4F0", "bbc": "\U0001F4F0",
    "apple-mail": "\U0001F4E7", "world-map": "\U0001F5FA",
}

DEFAULT_PAGE_TITLES = {100: "Welcome", 101: "System Status", 200: "News Feed", 500: "Live Feed", 888: "Colour Test Card"}


def _blank_buffer():
    return [[{"char": " ", "fg": 7, "bg": 0} for _ in range(PAGE_COLS)] for _ in range(PAGE_ROWS)]


def _write_str(buf, row, col, text, fg=7, bg=0, bold=False):
    for i, ch in enumerate(text):
        c = col + i
        if c < PAGE_COLS:
            buf[row][c] = {"char": ch, "fg": fg, "bg": bg, "bold": bold}


def _fill_row(buf, row, ch=" ", fg=7, bg=0):
    for c in range(PAGE_COLS):
        buf[row][c] = {"char": ch, "fg": fg, "bg": bg}


class CeefaxStore:
    def __init__(self):
        self._pages = {}
        self._feed_items = []
        self._seed_default_pages()

    def _seed_default_pages(self):
        for num, title in DEFAULT_PAGE_TITLES.items():
            self._pages[num] = {"number": num, "title": title, "buffer": _blank_buffer(), "last_updated": datetime.now(timezone.utc).isoformat(), "source": "system"}

    def get(self, num):
        return self._pages.get(num)

    def set(self, num, page):
        self._pages[num] = page

    def list(self):
        return [{"number": p["number"], "title": p["title"], "last_updated": p.get("last_updated"), "source": p.get("source", "unknown")} for p in sorted(self._pages.values(), key=lambda x: x["number"])]

    def add_feed_item(self, item):
        self._feed_items.append(item)
        self._rebuild_feed_page(item.get("page", 500))

    def get_latest_feed_items(self, limit=10):
        return sorted(self._feed_items, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    def list_feeds(self):
        return [
            {"id": "email", "name": "Email", "enabled": True, "icon": "\U0001F4E7"},
            {"id": "rss", "name": "RSS Feeds", "enabled": True, "icon": "\U0001F4E1"},
            {"id": "github", "name": "GitHub", "enabled": True, "icon": "\U0001F419"},
            {"id": "slack", "name": "Slack", "enabled": False, "icon": "\U0001F4AC"},
        ]

    def _rebuild_feed_page(self, page_number):
        items = [it for it in self._feed_items if it.get("page") == page_number]
        items = sorted(items, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
        buf = _blank_buffer()
        _fill_row(buf, 0, " ", 7, 4)
        _write_str(buf, 0, 2, f"CEETEX {page_number}", 7, 4)
        _write_str(buf, 0, 28, f"P{page_number}", 7, 4)
        title = f"LIVE FEED P{page_number}"
        _write_str(buf, 2, 4, "\u2554" + "\u2550" * 26 + "\u2557", 3, 0, True)
        _write_str(buf, 3, 4, "\u2551" + f"  {title:24s}" + "\u2551", 3, 0, True)
        _write_str(buf, 4, 4, "\u255a" + "\u2550" * 26 + "\u255d", 3, 0, True)
        if not items:
            _write_str(buf, 6, 4, "No feed items yet.", 7, 0)
            _write_str(buf, 7, 4, "Feed items will appear here", 7, 0)
            _write_str(buf, 8, 4, "when skills broadcast them.", 7, 0)
        else:
            row = 6
            for item in items:
                if row >= 22: break
                source = item.get("source", "unknown")
                icon = SOURCE_ICONS.get(source, "\U0001F4E1")
                ts = item.get("timestamp", "")
                try: time_str = datetime.fromisoformat(ts).strftime("%H:%M")
                except Exception: time_str = "--:--"
                _write_str(buf, row, 2, f"{icon} {source.upper():8s}", 6, 0)
                _write_str(buf, row, 34, time_str, 6, 0)
                row += 1
                if row >= 22: break
                _write_str(buf, row, 2, item.get("title", "Untitled")[:44], 3, 0, True)
                row += 1
                if row >= 22: break
                _write_str(buf, row, 2, item.get("body", "")[:44], 7, 0)
                row += 1
        _fill_row(buf, 24, " ", 7, 1)
        now_str = datetime.now(timezone.utc).strftime("%a %d %b %Y  %H:%M:%S")
        _write_str(buf, 24, 2, f"CEETEX {page_number}  Live Feed  {now_str}", 7, 1)
        self._pages[page_number] = {"number": page_number, "title": f"Live Feed P{page_number}", "buffer": buf, "last_updated": datetime.now(timezone.utc).isoformat(), "source": "feed-poller"}

    def rebuild_all_feed_pages(self):
        for page_num in range(500, 600):
            self._rebuild_feed_page(page_num)


def register_ceefax_routes(app, store):
    async def handle_get_page(request):
        num = int(request.match_info["num"])
        page = store.get(num)
        if not page: return web.json_response({"error": f"Page {num} not found"}, status=404)
        return web.json_response({"page": page})

    async def handle_set_page(request):
        num = int(request.match_info["num"])
        try:
            body = await request.json()
            store.set(num, {"number": num, "title": body.get("title", f"Page {num}"), "buffer": body.get("buffer", []), "last_updated": datetime.now(timezone.utc).isoformat(), "source": body.get("source", "api")})
            return web.json_response({"status": "ok", "page": num})
        except Exception as e: return web.json_response({"error": str(e)})

    async def handle_list_pages(request):
        return web.json_response({"pages": store.list()})

    async def handle_push_feed(request):
        try:
            body = await request.json()
            item = {"id": uuid.uuid4().hex[:8], "source": body.get("source", "unknown"), "title": body.get("title", "Untitled"), "body": body.get("body", ""), "timestamp": datetime.now(timezone.utc).isoformat(), "page": body.get("page", 500)}
            store.add_feed_item(item)
            return web.json_response({"status": "ok", "item": item})
        except Exception as e: return web.json_response({"error": str(e)})

    async def handle_feed_latest(request):
        limit = int(request.query.get("limit", "10"))
        items = store.get_latest_feed_items(limit)
        return web.json_response({"items": items, "count": len(items)})

    async def handle_list_feeds(request):
        return web.json_response({"feeds": store.list_feeds()})

    async def handle_rebuild_feeds(request):
        store.rebuild_all_feed_pages()
        return web.json_response({"status": "ok", "pages_rebuilt": 100})

    app.router.add_get("/api/ceefax/page/{num}", handle_get_page)
    app.router.add_post("/api/ceefax/page/{num}", handle_set_page)
    app.router.add_get("/api/ceefax/pages", handle_list_pages)
    app.router.add_post("/api/ceefax/feed", handle_push_feed)
    app.router.add_get("/api/ceefax/feed/latest", handle_feed_latest)
    app.router.add_get("/api/ceefax/feeds", handle_list_feeds)
    app.router.add_post("/api/ceefax/feed/rebuild", handle_rebuild_feeds)
