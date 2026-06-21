"""Knowledge API — AppFlowy bridge endpoints."""
from __future__ import annotations

from aiohttp import web
from app.knowledge.appflowy import (
    list_workspaces, list_documents, get_document,
    get_document_content, semantic_search,
)
from app.knowledge.local_first import (
    discover_databases,
    list_tables,
    run_query,
    export_to_vault,
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


async def handle_local_databases(request: web.Request) -> web.Response:
    """GET /api/knowledge/local/databases — discover local AppFlowy sqlite DBs."""
    dbs = discover_databases()
    return web.json_response({"databases": dbs, "count": len(dbs)})


async def handle_local_tables(request: web.Request) -> web.Response:
    """GET /api/knowledge/local/tables?db=<key|path> — list sqlite tables."""
    db = request.query.get("db", "database")
    dbs = discover_databases()
    db_path = dbs.get(db, db)
    try:
        tables = list_tables(db_path)
    except Exception as exc:
        return web.json_response({"error": str(exc), "db": db, "db_path": db_path}, status=400)
    return web.json_response({"db": db, "db_path": db_path, "tables": tables, "count": len(tables)})


async def handle_local_query(request: web.Request) -> web.Response:
    """POST /api/knowledge/local/query — run safe sqlite queries against local AppFlowy DB.

    Body:
      {
        "db": "database|chat|vector|/absolute/path/to.db",
        "sql": "SELECT ...",
        "params": [],
        "write": false
      }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    db = (body.get("db") or "database").strip()
    sql = (body.get("sql") or "").strip()
    params = body.get("params") or []
    write = bool(body.get("write", False))

    if not sql:
        return web.json_response({"error": "sql is required"}, status=400)

    dbs = discover_databases()
    db_path = dbs.get(db, db)
    try:
        result = run_query(db_path=db_path, sql=sql, params=params, write=write)
    except Exception as exc:
        return web.json_response({"error": str(exc), "db": db, "db_path": db_path}, status=400)
    return web.json_response({"db": db, "db_path": db_path, **result})


async def handle_local_export(request: web.Request) -> web.Response:
    """POST /api/knowledge/local/export — export AppFlowy sqlite rows to local vault snapshot."""
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}

    vault_dir = body.get("vault_dir", "~/vault/@appflowy")
    limit = int(body.get("limit_per_table", 2000))
    try:
        result = export_to_vault(vault_dir=vault_dir, limit_per_table=limit)
    except Exception as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(result)
