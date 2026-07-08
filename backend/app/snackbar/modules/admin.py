"""Admin routes — database migration."""
from __future__ import annotations

from aiohttp import web


async def migrate_admin_handler(request: web.Request) -> web.Response:
    """GET /api/admin/migrate — run database migration."""
    try:
        from app.core.database import migrate_db

        result = migrate_db()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def register(app: web.Application) -> None:
    app.router.add_get("/api/admin/migrate", migrate_admin_handler)
