"""ask_vault — Query AppFlowy knowledge base via the knowledge bridge.

This skill allows users/agents to query AppFlowy workspaces, documents,
and semantic search results through the uCore knowledge API.

Usage:
  POST /api/skills/ask_vault/run
  Body: {"query": "project architecture", "workspace_id": "optional"}
"""
from __future__ import annotations

from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.knowledge.appflowy import (
    list_workspaces, list_documents, get_document_content, semantic_search,
)


class AskVault(BaseSkill):
    meta = SkillMeta(
        id="ask_vault",
        name="Ask Vault",
        description="Query AppFlowy knowledge base — search documents, list workspaces, retrieve content",
        category="knowledge",
        timeout=30,
        params=[
            SkillParam(
                name="query",
                type="string",
                required=True,
                description="Search query or action (search, list-workspaces, list-docs, get-doc)",
            ),
            SkillParam(
                name="workspace_id",
                type="string",
                required=False,
                description="AppFlowy workspace ID (optional)",
            ),
            SkillParam(
                name="limit",
                type="number",
                required=False,
                default=10,
                description="Max results for search",
            ),
        ],
    )

    async def run(self, **kwargs) -> dict:
        query = kwargs.get("query", "").strip()
        workspace_id = kwargs.get("workspace_id")
        limit = int(kwargs.get("limit", 10))

        # Action-based queries
        if query == "list-workspaces":
            workspaces = list_workspaces()
            return {
                "success": True,
                "action": "list-workspaces",
                "count": len(workspaces),
                "workspaces": [
                    {"id": w["id"], "name": w["name"], "source": w.get("source", "?")}
                    for w in workspaces
                ],
            }

        if query == "list-docs":
            docs = list_documents(workspace_id)
            return {
                "success": True,
                "action": "list-docs",
                "count": len(docs),
                "documents": [
                    {"id": d["id"], "title": d.get("title", "Untitled"), "type": d.get("type", "?")}
                    for d in docs[:limit]
                ],
            }

        # Semantic search
        # Check if query looks like a content retrieval
        if "::" in query:
            # Format: get-doc::document_id
            parts = query.split("::", 1)
            action, doc_id = parts[0].strip(), parts[1].strip()
            if action in ("get-doc", "get-content", "read"):
                content = get_document_content(doc_id, workspace_id)
                if content:
                    return {
                        "success": True,
                        "action": "get-content",
                        "document_id": doc_id,
                        "content": content[:5000],  # Truncate to 5k chars
                    }
                return {"success": False, "error": f"Document '{doc_id}' not found"}

        # Default: semantic search
        results = semantic_search(query, workspace_id, limit)
        return {
            "success": True,
            "action": "search",
            "query": query,
            "count": len(results),
            "results": [
                {"content": r.get("content", "")[:200], "source": r.get("source", "?")}
                for r in results
            ],
            "note": "Results are text-based matches from AppFlowy vector metadata. For full vector search, install an embedding model.",
        }
