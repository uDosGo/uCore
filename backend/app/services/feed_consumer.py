"""feed_consumer — Bridge Feed Activity Pod into Spool (feed in motion).

Consumes activity events from the Feed MCP Server and writes them
into the Spool for audit trail / real-time event streaming. Also
provides hooks for triggering tasks and binder suggestions.

Used by:
  - Feed MCP server (feed_ingest_activity → spool)
  - FeedPanel.vue (auto-refresh polls)
  - Nugget runtime (batch ingestion scripts)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .spool_writer import write_spool

log = logging.getLogger("ucore.services.feed_consumer")


class FeedConsumer:
    """Consumes feed activity events and bridges them into Spool/Tasker."""

    def __init__(self):
        self._pod_path: Path | None = None

    def consume_activity(self, activity: dict[str, Any]) -> None:
        """Write a feed activity event into the Spool.

        Args:
            activity: Dict with source, type, title, content, timestamp keys
        """
        source = activity.get("source", "unknown")
        activity_type = activity.get("type", "unknown")
        title = activity.get("title", "")

        write_spool(
            level="INFO",
            module="feed_consumer",
            message=(
                f"Feed activity: source={source} type={activity_type} "
                f"title={title[:60] if title else 'untitled'}"
            ),
            tags=["feed", source, activity_type],
        )

        log.info(
            "Feed consumed: source=%s type=%s title=%.40s",
            source, activity_type, title,
        )

        # Hook: Check if activity should trigger tasks
        self._maybe_trigger_tasks(activity)

    def _maybe_trigger_tasks(self, activity: dict[str, Any]) -> None:
        """Check if activity content should trigger task creation.

        Placeholder: full AI-driven trigger logic lives in the Nugget
        runtime (scripts/analyze_feed.py). This hook is wired for
        future integration.
        """
        content = activity.get("content", "")
        title = activity.get("title", "")

        # Basic keyword triggers — future: AI-powered pattern detection
        keywords = []
        combined = f"{title} {content}".lower()

        if any(w in combined for w in ("bug", "crash", "error", "broken")):
            keywords.append("bug-report")
        if any(w in combined for w in ("tool", "utility", "script")):
            keywords.append("tool-suggestion")
        if any(w in combined for w in ("doc", "readme", "guide", "tutorial")):
            keywords.append("doc-suggestion")

        if keywords:
            write_spool(
                level="INFO",
                module="feed_trigger",
                message=(
                    f"Activity triggered keywords: {keywords} "
                    f"from source={activity.get('source')}"
                ),
                tags=["feed-trigger"] + keywords,
            )
