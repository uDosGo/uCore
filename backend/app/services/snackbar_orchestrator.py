"""SnackbarOrchestrator — priority-based snack queue and delivery for uCore.

Supports both in-memory and SQLite persistence backends.
"""
from __future__ import annotations

import json

from app.core.database import get_db, snack_from_row
from app.models.snack import Snack, SnackPriority, SnackStatus, SnackType


class SnackbarOrchestrator:
    """Orchestrates snack queuing, delivery, and lifecycle with optional persistence."""

    def __init__(self, persist: bool = True) -> None:
        self._persist = persist
        self._cache: dict[str, Snack] = {}
        self._history_cache: list[Snack] = []

    # ─── SQL Helpers ─────────────────────────────────────────────

    def _load_queue_from_db(self) -> list[Snack]:
        """Load queued snacks from DB, sorted by priority then timestamp."""
        if not self._persist:
            return sorted(
                self._cache.values(),
                key=lambda s: (s.priority.value, s.timestamp),
            )
        with get_db() as db:
            cursor = db.execute(
                "SELECT * FROM snacks WHERE status = 'queued' ORDER BY priority ASC, timestamp ASC",
            )
            return [Snack(**snack_from_row(row)) for row in cursor.fetchall()]

    def _load_history_from_db(self) -> list[Snack]:
        """Load delivered/failed snacks from DB."""
        if not self._persist:
            return self._history_cache.copy()
        with get_db() as db:
            cursor = db.execute(
                "SELECT * FROM snacks WHERE status IN ('delivered', 'failed') ORDER BY timestamp DESC",
            )
            return [Snack(**snack_from_row(row)) for row in cursor.fetchall()]

    def _save_to_db(self, snack: Snack) -> None:
        """Insert or replace a snack in the database."""
        if not self._persist:
            self._cache[snack.id] = snack
            return
        with get_db() as db:
            db.execute(
                """INSERT OR REPLACE INTO snacks
                   (id, type, priority, status, content_json, source, target,
                    timestamp, delivered_at, retry_count, max_retries, timeout_seconds)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snack.id,
                    snack.type.value,
                    snack.priority.value,
                    snack.status.value,
                    json.dumps(snack.content),
                    snack.source,
                    snack.target,
                    snack.timestamp.isoformat(),
                    snack.delivered_at.isoformat() if snack.delivered_at else None,
                    snack.retry_count,
                    snack.max_retries,
                    snack.timeout_seconds,
                ),
            )

    def _delete_from_db(self, snack_id: str) -> bool:
        """Delete a snack from the database."""
        if not self._persist:
            if snack_id in self._cache:
                del self._cache[snack_id]
                return True
            return False
        with get_db() as db:
            cursor = db.execute("DELETE FROM snacks WHERE id = ?", (snack_id,))
            return cursor.rowcount > 0

    def _move_to_history_db(self, snack: Snack) -> None:
        """Update a snack's status and ensure it's moved to history."""
        if not self._persist:
            if snack.id in self._cache:
                del self._cache[snack.id]
            self._history_cache.append(snack)
            return
        self._save_to_db(snack)

    # ─── Public API ──────────────────────────────────────────────

    def queue_snack(
        self,
        type: SnackType = SnackType.MESSAGE,
        content: dict | None = None,
        priority: SnackPriority = SnackPriority.NORMAL,
        source: str = "system",
        target: str | None = None,
        timeout_seconds: int | None = None,
    ) -> Snack:
        """Create a snack and add it to the queue."""
        snack = Snack(
            type=type,
            priority=priority,
            content=content or {},
            source=source,
            target=target,
            timeout_seconds=timeout_seconds,
        )
        self._save_to_db(snack)
        return snack

    def get_queue(self) -> list[Snack]:
        """Return the queue sorted by priority (critical first) then timestamp."""
        return self._load_queue_from_db()

    def deliver_next(self) -> Snack | None:
        """Deliver the highest-priority queued snack."""
        queue = self.get_queue()
        if not queue:
            return None
        snack = queue[0]
        snack.deliver()
        self._move_to_history_db(snack)
        return snack

    def deliver_snack(self, snack_id: str) -> Snack | None:
        """Deliver a specific snack by ID."""
        if self._persist:
            snack = self._load_one(snack_id)
        else:
            snack = self._cache.get(snack_id)
        if snack is None:
            return None
        snack.deliver()
        self._move_to_history_db(snack)
        return snack

    def _load_one(self, snack_id: str) -> Snack | None:
        """Load a single snack by ID from DB."""
        with get_db() as db:
            cursor = db.execute("SELECT * FROM snacks WHERE id = ?", (snack_id,))
            row = cursor.fetchone()
            return Snack(**snack_from_row(row)) if row else None

    def fail_snack(self, snack_id: str) -> Snack | None:
        """Mark a snack as failed and move to history."""
        if self._persist:
            snack = self._load_one(snack_id)
        else:
            snack = self._cache.get(snack_id)
        if snack is None:
            return None
        snack.fail()
        self._move_to_history_db(snack)
        return snack

    def retry_snack(self, snack_id: str) -> Snack | None:
        """Re-queue a failed snack if retries remain."""
        history = self._load_history_from_db()
        for snack in history:
            if snack.id == snack_id and snack.status == SnackStatus.FAILED:
                if snack.retry_count < snack.max_retries:
                    snack.retry_count += 1
                    snack.queue()
                    if self._persist:
                        self._delete_from_db(snack_id)
                        self._save_to_db(snack)
                    else:
                        self._cache[snack.id] = snack
                        self._history_cache.remove(snack)
                    return snack
                return None
        return None

    def get_history(self, limit: int | None = None) -> list[Snack]:
        """Return delivery history, optionally limited to last N entries."""
        history = self._load_history_from_db()
        if limit is not None:
            return history[:limit]
        return history

    def pending_count(self) -> int:
        """Return number of snacks waiting in the queue."""
        return len(self.get_queue())

    def clear_queue(self) -> int:
        """Clear all pending snacks. Returns count cleared."""
        queue = self.get_queue()
        count = len(queue)
        if self._persist:
            with get_db() as db:
                db.execute("DELETE FROM snacks WHERE status = 'queued'")
        else:
            self._cache.clear()
        return count
