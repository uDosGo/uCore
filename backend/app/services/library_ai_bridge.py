"""Library AI Bridge — AI-powered vault search and recommendations.

Combines FTS5 search with quality-ranked model suggestions:
- Natural language queries ranked by agent context
- Agent-suggested: "Based on your mission, these files are relevant"

Usage:
    bridge = LibraryAIBridge()
    results = bridge.search("auth module tests", agent_id="reviewer")
    suggestions = await bridge.suggest_for_task("implement login flow")
"""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("ucore.library_ai_bridge")


class LibraryAIBridge:
    """Bridge between library index and AI systems."""

    def __init__(self) -> None:
        self._api_registry = None
        self._quality_scorer = None

    def _get_api_registry(self):
        if self._api_registry is None:
            from app.services.api_registry import ApiRegistry
            self._api_registry = ApiRegistry.get()
        return self._api_registry

    def _get_quality_scorer(self):
        if self._quality_scorer is None:
            from app.services.quality_scorer import QualityScorer
            self._quality_scorer = QualityScorer.get()
        return self._quality_scorer

    def search(
        self,
        query: str,
        agent_id: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search the library index with optional agent boosting."""
        from app.services.library_index import search as fts_search
        from app.services.library_index import get_stats

        fts_results = fts_search(query, limit=limit * 2)

        if not fts_results:
            return {
                "query": query,
                "results": [],
                "total": 0,
                "agent_boost": None,
            }

        agent_boost = None
        if agent_id:
            agent_boost = self._get_agent_boost(agent_id)
            fts_results = self._boost_by_agent(fts_results, agent_id)

        results = fts_results[:limit]

        return {
            "query": query,
            "results": results,
            "total": len(fts_results),
            "agent_boost": agent_boost,
            "index_stats": get_stats(),
        }

    async def suggest_for_task(
        self,
        task_summary: str,
        agent_id: str = "dev",
        limit: int = 5,
    ) -> dict[str, Any]:
        """Get AI-suggested files relevant to a task."""
        keywords = self._extract_keywords(task_summary)
        query = " ".join(keywords[:5])

        if not query:
            return {
                "task_summary": task_summary,
                "suggestions": [],
                "reason": "Could not extract keywords",
            }

        results = self.search(
            query=query,
            agent_id=agent_id,
            limit=limit,
        )

        return {
            "task_summary": task_summary,
            "agent_id": agent_id,
            "query_used": query,
            "suggestions": results.get("results", []),
            "total_found": results.get("total", 0),
        }

    def _get_agent_boost(self, agent_id: str) -> dict[str, Any] | None:
        agent_boosts = {
            "dev": {
                "preferred_extensions": ["py", "ts", "tsx", "js", "vue"],
                "preferred_sources": ["code", "user"],
                "boost_tags": ["implementation", "api", "frontend"],
            },
            "reviewer": {
                "preferred_extensions": ["py", "ts", "tsx", "js"],
                "preferred_sources": ["code"],
                "boost_tags": ["review", "security", "testing"],
            },
            "architect": {
                "preferred_extensions": ["md", "yaml", "yml", "py"],
                "preferred_sources": ["user", "shared", "global"],
                "boost_tags": ["architecture", "design", "spec"],
            },
            "debugger": {
                "preferred_extensions": ["py", "ts", "js", "log"],
                "preferred_sources": ["code"],
                "boost_tags": ["debugging", "error", "test", "log"],
            },
            "docgen": {
                "preferred_extensions": ["md", "py", "ts"],
                "preferred_sources": ["user", "shared", "public"],
                "boost_tags": ["documentation", "readme", "spec"],
            },
        }
        return agent_boosts.get(agent_id)

    def _boost_by_agent(
        self, results: list[dict], agent_id: str,
    ) -> list[dict]:
        boost = self._get_agent_boost(agent_id)
        if not boost:
            return results

        preferred_exts = set(boost.get("preferred_extensions", []))
        preferred_sources = set(boost.get("preferred_sources", []))
        boost_tags = set(boost.get("boost_tags", []))

        def score_result(r: dict) -> float:
            score = 0.0
            ext = r.get("extension", "")
            source = r.get("source", "")
            tags = set(r.get("tags", []))
            if ext in preferred_exts:
                score += 3.0
            if source in preferred_sources:
                score += 2.0
            overlap = tags & boost_tags
            score += len(overlap) * 1.5
            return score

        scored = [(score_result(r), r) for r in results]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]

    def _extract_keywords(self, text: str) -> list[str]:
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may",
            "might", "shall", "can", "need", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "and", "but",
            "or", "not", "so", "yet", "this", "that", "these",
            "those", "i", "me", "my", "we", "our", "you", "your",
            "it", "its", "they", "them", "their", "what", "which",
            "who", "how", "when", "where", "why", "all", "any",
        }
        words = text.lower().split()
        keywords = [
            w.strip(".,!?;:()[]{}\"'")
            for w in words
            if len(w) > 2 and w.lower() not in stop_words
        ]
        seen: set[str] = set()
        unique: list[str] = []
        for w in keywords:
            if w not in seen:
                seen.add(w)
                unique.append(w)
        return unique