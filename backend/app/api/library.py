"""Library Index API — endpoints for unified vault search."""
from __future__ import annotations

from pathlib import Path

from aiohttp import web


def _is_allowed_library_path(path: Path) -> bool:
    """Allow reads only from configured library roots."""
    from app.services.library_index import VAULT_PATHS

    try:
        resolved = path.expanduser().resolve()
    except Exception:
        return False

    for root in VAULT_PATHS.values():
        try:
            if resolved.is_relative_to(root.expanduser().resolve()):
                return True
        except Exception:
            continue
    return False


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


async def handle_library_file(request: web.Request) -> web.Response:
    """GET /api/library/file?path=... — read an indexed vault file."""
    path_value = request.query.get("path", "").strip()
    if not path_value:
        return web.json_response(
            {"error": "Query parameter 'path' is required"},
            status=400,
        )

    path = Path(path_value)
    if not _is_allowed_library_path(path):
        return web.json_response(
            {"error": "Path is outside library roots"},
            status=403,
        )
    if not path.exists() or not path.is_file():
        return web.json_response({"error": "File not found"}, status=404)

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

    return web.json_response({
        "path": str(path),
        "filename": path.name,
        "extension": path.suffix.lower().lstrip("."),
        "content": content,
    })


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
    app.router.add_get("/api/library/file", handle_library_file)
    app.router.add_get("/api/library/stats", handle_library_stats)
