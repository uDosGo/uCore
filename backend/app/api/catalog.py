"""Catalog API endpoints."""

from __future__ import annotations

from typing import List

from aiohttp import web
from app.services.catalog import CatalogService, CatalogEntry, SpatialUID, EntryType

log = __import__("logging").getLogger("ucore.api.catalog")


async def list_entries(request: web.Request) -> web.Response:
    """GET /api/catalog/entries — List catalog entries with filtering.

    Query params:
        - type: Filter by entry type (llm, skill, lib, mcp, vendor, repo)
        - search: Full-text search query
        - limit: Maximum number of entries (default: 50)
        - offset: Number of entries to skip (default: 0)
    """
    try:
        catalog = CatalogService()
        entry_type = request.query.get("type")
        search = request.query.get("search")
        limit = int(request.query.get("limit", 50))
        offset = int(request.query.get("offset", 0))

        entries: List[CatalogEntry] = []

        if search:
            if entry_type:
                entries = catalog.search(search, limit, EntryType(entry_type))
            else:
                entries = catalog.search(search, limit)
        elif entry_type:
            entries = catalog.list_entries(EntryType(entry_type), limit, offset)
        else:
            entries = catalog.list_entries(limit=limit, offset=offset)

        return web.json_response({
            "entries": [entry.to_dict() for entry in entries],
            "count": len(entries),
        })

    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.error(f"Error listing entries: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_entry(request: web.Request) -> web.Response:
    """GET /api/catalog/entries/{uid} — Get a catalog entry by UID.

    Args:
        uid: Spatial UID of the entry
    """
    try:
        uid = SpatialUID(request.match_info["uid"])
        catalog = CatalogService()
        entry = catalog.get_entry(uid)

        if not entry:
            return web.json_response({"error": "Entry not found"}, status=404)

        return web.json_response(entry.to_dict())

    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.error(f"Error getting entry: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def search_catalog(request: web.Request) -> web.Response:
    """GET /api/catalog/search — Full-text search across catalog.

    Query params:
        - q: Search query
        - type: Filter by entry type
        - limit: Maximum number of results (default: 20)
    """
    try:
        catalog = CatalogService()
        query = request.query.get("q")
        entry_type = request.query.get("type")
        limit = int(request.query.get("limit", 20))

        if not query:
            return web.json_response({"error": "Query parameter 'q' is required"}, status=400)

        entries = catalog.search(query, limit, EntryType(entry_type) if entry_type else None)

        return web.json_response({
            "entries": [entry.to_dict() for entry in entries],
            "count": len(entries),
        })

    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.error(f"Error searching catalog: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_relationships(request: web.Request) -> web.Response:
    """GET /api/catalog/relationships/{uid} — Get relationships for an entry.

    Query params:
        - depth: Maximum depth of relationships (default: 1)

    Args:
        uid: Spatial UID of the entry
    """
    try:
        uid = SpatialUID(request.match_info["uid"])
        depth = int(request.query.get("depth", 1))
        catalog = CatalogService()
        relationships = catalog.get_relationships(uid, depth)

        return web.json_response({
            "uid": uid,
            "relationships": relationships,
        })

    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.error(f"Error getting relationships: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_graph(request: web.Request) -> web.Response:
    """GET /api/catalog/graph/{uid} — Get dependency graph for an entry.

    Query params:
        - depth: Maximum depth of relationships (default: 1)

    Args:
        uid: Spatial UID of the entry
    """
    try:
        uid = SpatialUID(request.match_info["uid"])
        depth = int(request.query.get("depth", 1))
        catalog = CatalogService()
        graph = catalog.get_graph(uid, depth)

        return web.json_response(graph)

    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.error(f"Error getting graph: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def sync_catalog(request: web.Request) -> web.Response:
    """POST /api/catalog/sync — Trigger catalog sync from sources.

    Query params:
        - source: Specific source to sync (optional)
    """
    try:
        CatalogService()
        source = request.query.get("source")

        # TODO: Implement actual sync logic
        # For now, just return a success message
        return web.json_response({
            "status": "synced",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "source": source or "all",
        })

    except Exception as e:
        log.error(f"Error syncing catalog: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_stats(request: web.Request) -> web.Response:
    """GET /api/catalog/stats — Get catalog statistics.

    Returns:
        Dictionary with catalog statistics
    """
    try:
        catalog = CatalogService()
        stats = catalog.get_stats()

        return web.json_response(stats)

    except Exception as e:
        log.error(f"Error getting stats: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


# Setup routes
def setup_routes(app: web.Application) -> None:
    """Setup catalog API routes."""
    app.router.add_get("/api/catalog/entries", list_entries)
    app.router.add_get("/api/catalog/entries/{uid}", get_entry)
    app.router.add_get("/api/catalog/search", search_catalog)
    app.router.add_get("/api/catalog/relationships/{uid}", get_relationships)
    app.router.add_get("/api/catalog/graph/{uid}", get_graph)
    app.router.add_post("/api/catalog/sync", sync_catalog)
    app.router.add_get("/api/catalog/stats", get_stats)
