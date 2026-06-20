"""Knowledge API — AppFlowy bridge endpoints."""
from __future__ import annotations

from aiohttp import web
from app.knowledge.appflowy import (
    list_workspaces, list_documents, get_document,
    get_document_content, semantic_search,
)

import logging
log = logging.getLogger("ucore.api.knowledge")


async def handle_list_workspaces(request: web.Request) -> web.Response:
    """GET /api/knowledge/workspaces — list AppFlowy workspaces."""
    workspaces = list_workspaces()
    return web.json_response({"workspaces": workspaces, "count": len(workspaces)})


async def handle_list_documents(request: web.Request) -> web.Response:
    """GET /api/knowledge/documents — list documents in a workspace.

    Query params:
      workspace_id (optional) — filter by workspace
    """
    workspace_id = request.query.get("workspace_id")
    docs = list_documents(workspace_id)
    return web.json_response({"documents": docs, "count": len(docs)})


async def handle_get_document(request: web.Request) -> web.Response:
    """GET /api/knowledge/documents/{object_id} — get document metadata."""
    object_id = request.match_info.get("object_id", "")
    workspace_id = request.query.get("workspace_id")
    doc = get_document(object_id, workspace_id)
    if not doc:
        return web.json_response({"error": "Document not found"}, status=404)
    return web.json_response(doc)


async def handle_get_document_content(request: web.Request) -> web.Response:
    """GET /api/knowledge/documents/{object_id}/content — get document text."""
    object_id = request.match_info.get("object_id", "")
    workspace_id = request.query.get("workspace_id")
    content = get_document_content(object_id, workspace_id)
    if content is None:
        return web.json_response({"error": "Document not found"}, status=404)
    return web.json_response({"object_id": object_id, "content": content, "length": len(content)})


async def handle_search(request: web.Request) -> web.Response:
    """GET /api/knowledge/search?q=... — semantic search across AppFlowy."""
    query = request.query.get("q", "").strip()
    if not query:
        return web.json_response({"error": "q parameter is required"}, status=400)
    workspace_id = request.query.get("workspace_id")
    limit = int(request.query.get("limit", "10"))
    results = semantic_search(query, workspace_id, limit)
    return web.json_response({"query": query, "results": results, "count": len(results)})
