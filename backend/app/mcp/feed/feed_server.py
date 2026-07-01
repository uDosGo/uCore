"""feed_server — MCP tools for the Feed Activity Pod (SQLite).

Exposes four tools via the MCP dispatch system:
  - feed_ingest_activity: insert an activity event into user_activity
  - feed_query: query activities by source, timeframe, importance
  - feed_suggest_binders: AI-driven binder suggestions from activity clusters
  - feed_link_task: link a .tasker task to a feed activity

The Activity Pod is stored at ~/.ucore/pods/activity.db and initialized
from backend/schemas/activity.schema.sql on first access.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.mcp.feed_server")

DEFAULT_POD_PATH = Path.home() / ".ucore" / "pods" / "activity.db"
HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE.parent.parent.parent / "schemas" / "activity.schema.sql"


class FeedServer:
    """MCP server for Feed Activity Pod ingestion, query, suggestion, and linking."""

    def __init__(self, pod_path: str | None = None):
        self._pod_path = Path(pod_path or DEFAULT_POD_PATH).expanduser()
        self._pod_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._pod_path))
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    # ── lifecycle ─────────────────────────────────────────────────

    def _ensure_schema(self) -> None:
        """Run schema DDL if tables don't already exist."""
        if SCHEMA_PATH.exists():
            ddl = SCHEMA_PATH.read_text(encoding="utf-8")
            self._conn.executescript(ddl)
            self._conn.commit()
            log.debug("Feed schema ensured via %s", SCHEMA_PATH)
        else:
            log.warning("Feed schema file not found: %s", SCHEMA_PATH)

    def close(self) -> None:
        self._conn.close()

    # ── MCP Tool: feed_ingest_activity ────────────────────────────

    async def ingest_activity(
        self,
        source: str,
        type: str,
        title: str = "",
        content: str = "",
        url: str = "",
        contact_name: str = "",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Insert a user activity event into the Feed Pod."""
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO user_activity (source, type, title, content, url, importance, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                source,
                type,
                title,
                content,
                url,
                importance,
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        row_id = cursor.lastrowid
        log.info(
            "Feed ingest: id=%s source=%s type=%s title=%.40s",
            row_id, source, type, title,
        )
        return {"id": row_id, "message": "Activity ingested"}

    # ── MCP Tool: feed_query ──────────────────────────────────────

    async def query_feed(
        self,
        source: str | None = None,
        since: str | None = None,
        limit: int = 50,
        importance_min: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Query activities from the Feed Pod."""
        cursor = self._conn.cursor()
        query = "SELECT * FROM user_activity WHERE importance >= ?"
        params: list[Any] = [importance_min]

        if source:
            query += " AND source = ?"
            params.append(source)
        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ── MCP Tool: feed_suggest_binders ────────────────────────────

    async def suggest_binders(
        self, min_confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Generate binder suggestions from recent feed activity.

        Groups recent activities by source and content similarity,
        returning suggested binder names with confidence scores.
        """
        cursor = self._conn.cursor()

        # Get unprocessed activities from last 7 days
        cursor.execute(
            """SELECT DISTINCT source, COUNT(*) as cnt
               FROM user_activity
               WHERE processed = 0
                 AND timestamp >= datetime('now', '-7 days')
               GROUP BY source
               HAVING cnt >= 3
               ORDER BY cnt DESC""",
        )
        clusters = cursor.fetchall()

        suggestions: list[dict[str, Any]] = []
        for cluster in clusters:
            source = cluster["source"]
            count = cluster["cnt"]

            # Get sample titles for context
            cursor.execute(
                """SELECT title FROM user_activity
                   WHERE source = ? AND processed = 0
                   ORDER BY timestamp DESC LIMIT 5""",
                (source,),
            )
            titles = [r["title"] for r in cursor.fetchall() if r["title"]]

            confidence = min(0.9, 0.5 + (count * 0.1))
            if confidence >= min_confidence:
                name = f"{source.title()} Research"
                if titles:
                    kw = " ".join(titles)[:60]
                    name = f"{source.title()}: {kw}"

                suggestions.append({
                    "name": name,
                    "description": f"{count} recent {source} activities detected",
                    "confidence": round(confidence, 2),
                    "source": source,
                    "activity_count": count,
                    "sample_titles": titles,
                })

        return suggestions

    # ── MCP Tool: feed_link_task ───────────────────────────────────

    async def link_task_to_activity(
        self,
        task_id: str,
        activity_id: int,
        link_type: str = "source",
    ) -> dict[str, Any]:
        """Link a .tasker task to a feed activity."""
        cursor = self._conn.cursor()

        # Verify activity exists
        cursor.execute(
            "SELECT id FROM user_activity WHERE id = ?",
            (activity_id,),
        )
        if not cursor.fetchone():
            return {
                "success": False,
                "error": f"Activity {activity_id} not found",
            }

        # Check for existing link
        cursor.execute(
            """SELECT id FROM task_activity_links
               WHERE task_id = ? AND activity_id = ?""",
            (task_id, activity_id),
        )
        existing = cursor.fetchone()
        if existing:
            return {
                "success": True,
                "message": "Link already exists",
                "link_id": existing["id"],
            }

        cursor.execute(
            """INSERT INTO task_activity_links (task_id, activity_id, link_type)
               VALUES (?, ?, ?)""",
            (task_id, activity_id, link_type),
        )
        self._conn.commit()

        # Mark activity as processed
        self._conn.execute(
            "UPDATE user_activity SET processed = 1 WHERE id = ?",
            (activity_id,),
        )
        self._conn.commit()

        log.info(
            "Feed link: task=%s activity=%s type=%s",
            task_id, activity_id, link_type,
        )
        return {
            "message": "Task linked to activity",
            "task_id": task_id,
            "activity_id": activity_id,
            "link_type": link_type,
        }
