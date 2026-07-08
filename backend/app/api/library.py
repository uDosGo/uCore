"""Library Index API — endpoints for unified vault search."""
from __future__ import annotations

from aiohttp import web


async def handle_library_build(request: web.Request) -> web.Response:
    """POST /api/library/build — rebuild the unified index."""
    try:
        from app.services.library_index import build_index

        result = build_index()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_library_search(request: web.Request) -> web.Response:
    """GET /api/library/search?q=...&source=..."""
    try:
        from app.services.library_index import search

        query = request.query.get("q", "")
        source = request.query.get("source")
        limit = int(request.query.get("limit", 50))

        if not query:
            return web.json_response(
                {"error": "Query parameter 'q' is required"},
                status=400,
            )

        results = search(query, source=source, limit=limit)
        return web.json_response({
            "query": query,
            "source": source,
            "count": len(results),
            "results": results,
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_library_stats(request: web.Request) -> web.Response:
    """GET /api/library/stats — index statistics."""
    try:
        from app.services.library_index import get_stats

        stats = get_stats()
        return web.json_response(stats)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def register_library_routes(app: web.Application) -> None:
    """Register library index routes."""
    app.router.add_post("/api/library/build", handle_library_build)
    app.router.add_get("/api/library/search", handle_library_search)
    app.router.add_get("/api/library/stats", handle_library_stats)
