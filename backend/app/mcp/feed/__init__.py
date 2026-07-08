"""Feed MCP Server — unified incoming data layer for user activity.

Provides ingest, query, suggest, and link tools for the Activity Pod (SQLite).
Bridges browser history, email, messages, alerts, and search activity into
the Spool, Tasker, and Binder systems.
"""

from .feed_server import FeedServer

__all__ = ["FeedServer"]
