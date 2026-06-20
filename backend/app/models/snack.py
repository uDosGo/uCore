"""Snack model — a deterministic message/task in the uCore feed-spool."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


class SnackType(str, Enum):
    """Types of snacks."""
    TASK = "task"             # Executable task
    MESSAGE = "message"       # Informational message
    COMMAND = "command"       # Shell command
    EVENT = "event"           # System event
    NOTIFICATION = "notification"  # User notification
    QUERY = "query"           # Data query


class SnackPriority(int, Enum):
    """Priority levels — lower = higher priority."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class SnackStatus(str, Enum):
    """Delivery status."""
    QUEUED = "queued"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class Snack(BaseModel):
    """A deterministic snack (message/task) in the uCore feed-spool.

    Snacks are the primary communication mechanism — scheduled tasks,
    messages between surfaces, system events, etc. All delivery is
    deterministic and ordered by priority + timestamp.
    """
    id: str = Field(default_factory=lambda: f"snk_{uuid.uuid4().hex[:12]}")
    type: SnackType = SnackType.MESSAGE
    priority: SnackPriority = SnackPriority.NORMAL
    status: SnackStatus = SnackStatus.QUEUED
    content: dict[str, Any] = Field(default_factory=dict)
    source: str = "system"
    target: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[int] = None

    def deliver(self) -> Snack:
        """Mark the snack as delivered."""
        self.status = SnackStatus.DELIVERED
        self.delivered_at = datetime.now(timezone.utc)
        return self

    def queue(self) -> Snack:
        """Mark the snack as queued (reset for re-delivery)."""
        self.status = SnackStatus.QUEUED
        self.delivered_at = None
        return self

    def fail(self) -> Snack:
        """Mark the snack as failed."""
        self.status = SnackStatus.FAILED
        self.delivered_at = datetime.now(timezone.utc)
        return self

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=2)

    model_config = {"frozen": False}
