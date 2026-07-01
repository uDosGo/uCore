"""UDO model — Universal Device Object abstraction for uCore."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UDODeviceType(str, Enum):
    """Types of devices a UDO can represent."""

    SURFACE = "surface"         # UI surface
    CONTAINER = "container"     # Runtime container
    SERVICE = "service"         # System service
    SENSOR = "sensor"           # IoT/physical sensor
    ACTUATOR = "actuator"       # Physical output device
    MEDIA = "media"             # Media source/sink
    STORAGE = "storage"         # Storage volume
    NETWORK = "network"         # Network interface
    VIRTUAL = "virtual"         # Virtual/abstract device


class UDOStatus(str, Enum):
    """Operational status of a UDO."""

    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"
    SLEEPING = "sleeping"


class UDO(BaseModel):
    """Universal Device Object — unified abstraction for any device.

    UDOs are the core abstraction layer in uCore. Everything from surfaces
    to containers to physical IoT devices is represented as a UDO, providing
    a uniform interface for discovery, control, and monitoring.
    """

    id: str = Field(default_factory=lambda: f"udo_{uuid.uuid4().hex[:12]}")
    name: str
    device_type: UDODeviceType = UDODeviceType.VIRTUAL
    status: UDOStatus = UDOStatus.OFFLINE
    capabilities: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    parent_id: str | None = None
    last_heartbeat: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def ping(self) -> UDO:
        """Record a heartbeat ping."""
        self.last_heartbeat = datetime.now(UTC)
        self.updated_at = self.last_heartbeat
        if self.status == UDOStatus.OFFLINE:
            self.status = UDOStatus.ONLINE
        return self

    def get_capabilities(self) -> list[str]:
        """Return the list of capabilities."""
        return self.capabilities.copy()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return self.model_dump()

    model_config = {"frozen": False}
