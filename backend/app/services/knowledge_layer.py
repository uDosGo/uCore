"""Hivemind Shared Knowledge Layer.

Episodic memory for multi-agent orchestration.
Provides shared memory across agents with:
- Publish/subscribe for knowledge events
- Query/filter for knowledge retrieval
- Lock/unlock for concurrent access
- Status monitoring for knowledge health

Usage:
    kl = KnowledgeLayer()
    await kl.publish("agent.coder", {"type": "decision", "content": "..."})
    results = await kl.query("decision", limit=10)
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.knowledge_layer")

DB_PATH = Path.home() / ".ucore" / "knowledge" / "shared.db"


class KnowledgeLayer:
    """Shared knowledge layer for Hivemind multi-agent orchestration."""

    _instance: KnowledgeLayer | None = None
    _lock = threading.Lock()

    def __new__(cls) -> KnowledgeLayer:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._local = threading.local()
        self._initialized = True

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(DB_PATH))
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    async def publish(
        self,
        agent_id: str,
        event_type: str,
        payload: dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> str:
        """Publish a knowledge event from an agent.

        Args:
            agent_id: The publishing agent's ID
            event_type: Type of event (decision, observation, result, error)
            payload: The knowledge payload
            ttl_seconds: Time-to-live in seconds (default 24h)

        Returns:
            Event ID
        """
        import uuid
        event_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        conn = self._get_conn()
        conn.execute(
            """INSERT INTO knowledge_events
               (id, agent_id, event_type, payload, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                event_id,
                agent_id,
                event_type,
                json.dumps(payload),
                now,
                datetime.now(UTC).isoformat(),
            ),
        )
        conn.commit()

        log.debug(
            "Knowledge published: %s from %s [%s]",
            event_id, agent_id, event_type,
        )
        return event_id

    async def query(
        self,
        event_type: str | None = None,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query knowledge events with optional filters.

        Args:
            event_type: Filter by event type
            agent_id: Filter by agent ID
            limit: Max results
            offset: Pagination offset

        Returns:
            List of matching knowledge events
        """
        conn = self._get_conn()
        conditions = ["expires_at > datetime('now')"]
        params: list[Any] = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)

        where = " AND ".join(conditions)
        rows = conn.execute(
            f"SELECT * FROM knowledge_events WHERE {where} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()

        return [dict(r) for r in rows]

    async def search(
        self,
        query_text: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Full-text search across knowledge events.

        Args:
            query_text: Search query
            limit: Max results

        Returns:
            List of matching knowledge events
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT ke.* FROM knowledge_events ke
               JOIN knowledge_fts fts ON ke.id = fts.id
               WHERE fts MATCH ? AND ke.expires_at > datetime('now')
               ORDER BY fts.rank
               LIMIT ?""",
            (query_text, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    async def subscribe(
        self,
        agent_id: str,
        event_type: str | None = None,
    ) -> str:
        """Subscribe an agent to knowledge events.

        Args:
            agent_id: The subscribing agent's ID
            event_type: Optional event type filter

        Returns:
            Subscription ID
        """
        import uuid
        sub_id = str(uuid.uuid4())
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO subscriptions (id, agent_id, event_type)
               VALUES (?, ?, ?)""",
            (sub_id, agent_id, event_type),
        )
        conn.commit()
        log.info(
            "Agent %s subscribed to knowledge [%s]",
            agent_id, event_type or "*",
        )
        return sub_id

    async def get_subscriptions(
        self,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get active subscriptions.

        Args:
            agent_id: Optional filter by agent

        Returns:
            List of subscriptions
        """
        conn = self._get_conn()
        if agent_id:
            rows = conn.execute(
                "SELECT * FROM subscriptions WHERE agent_id = ?",
                (agent_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM subscriptions").fetchall()
        return [dict(r) for r in rows]

    async def lock(self, resource_id: str, agent_id: str) -> bool:
        """Acquire a lock on a knowledge resource.

        Args:
            resource_id: The resource to lock
            agent_id: The agent requesting the lock

        Returns:
            True if lock acquired, False if already locked
        """
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT * FROM locks WHERE resource_id = ? "
            "AND expires_at > datetime('now')",
            (resource_id,),
        ).fetchone()
        if existing:
            return False

        import uuid
        lock_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO locks (id, resource_id, agent_id, created_at, expires_at)
               VALUES (?, ?, ?, datetime('now'),
                       datetime('now', '+5 minutes'))""",
            (lock_id, resource_id, agent_id),
        )
        conn.commit()
        log.debug("Lock acquired: %s by %s", resource_id, agent_id)
        return True

    async def unlock(self, resource_id: str, agent_id: str) -> bool:
        """Release a lock on a knowledge resource.

        Args:
            resource_id: The resource to unlock
            agent_id: The agent releasing the lock

        Returns:
            True if lock released, False if not locked by this agent
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM locks WHERE resource_id = ? AND agent_id = ?",
            (resource_id, agent_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    async def status(self) -> dict[str, Any]:
        """Get knowledge layer status.

        Returns:
            Status dict with event counts, subscriptions, locks
        """
        conn = self._get_conn()
        event_count = conn.execute(
            "SELECT COUNT(*) FROM knowledge_events "
            "WHERE expires_at > datetime('now')",
        ).fetchone()[0]
        sub_count = conn.execute(
            "SELECT COUNT(*) FROM subscriptions",
        ).fetchone()[0]
        lock_count = conn.execute(
            "SELECT COUNT(*) FROM locks WHERE expires_at > datetime('now')",
        ).fetchone()[0]

        return {
            "active_events": event_count,
            "subscriptions": sub_count,
            "active_locks": lock_count,
            "db_path": str(DB_PATH),
        }

    async def cleanup_expired(self) -> int:
        """Remove expired events and locks.

        Returns:
            Number of expired items removed
        """
        conn = self._get_conn()
        removed = conn.execute(
            "DELETE FROM knowledge_events WHERE expires_at <= datetime('now')",
        ).rowcount
        removed += conn.execute(
            "DELETE FROM locks WHERE expires_at <= datetime('now')",
        ).rowcount
        conn.commit()
        if removed:
            log.info("Cleaned up %d expired knowledge items", removed)
        return removed


# ─── Schema ──────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS knowledge_events (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_knowledge_agent
    ON knowledge_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_type
    ON knowledge_events(event_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_expires
    ON knowledge_events(expires_at);

CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    id,
    payload,
    content='knowledge_events',
    content_rowid='rowid'
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    event_type TEXT
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_agent
    ON subscriptions(agent_id);

CREATE TABLE IF NOT EXISTS locks (
    id TEXT PRIMARY KEY,
    resource_id TEXT NOT NULL UNIQUE,
    agent_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_locks_resource
    ON locks(resource_id);
"""
