"""Maintenance Service Data Models"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class BackupType(Enum):
    """Backup type"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class ArchiveType(Enum):
    """Archive type"""
    OLD_DATA = "old_data"
    TEMPORARY = "temporary"
    FAILED_OPERATIONS = "failed_operations"
    LOGS = "logs"
    CACHE = "cache"


class CompostType(Enum):
    """Compost type"""
    SYSTEM = "system"
    USER_DATA = "user_data"
    TEMPORARY = "temporary"
    FAILED = "failed"


@dataclass
class BackupInfo:
    """Backup information"""
    backup_id: str
    backup_type: BackupType
    created_at: datetime
    size_bytes: int
    location: str
    description: str = ""
    modules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "location": self.location,
            "description": self.description,
            "modules": self.modules,
            "metadata": self.metadata,
        }


@dataclass
class ArchiveInfo:
    """Archive information"""
    archive_id: str
    archive_type: ArchiveType
    created_at: datetime
    size_bytes: int
    location: str
    description: str = ""
    items: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "archive_id": self.archive_id,
            "archive_type": self.archive_type.value,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "location": self.location,
            "description": self.description,
            "items": self.items,
            "metadata": self.metadata,
        }


@dataclass
class CompostResult:
    """Compost result"""
    compost_id: str
    compost_type: CompostType
    created_at: datetime
    space_freed_bytes: int
    location: str
    description: str = ""
    items_removed: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "compost_id": self.compost_id,
            "compost_type": self.compost_type.value,
            "created_at": self.created_at.isoformat(),
            "space_freed_bytes": self.space_freed_bytes,
            "location": self.location,
            "description": self.description,
            "items_removed": self.items_removed,
            "metadata": self.metadata,
        }


@dataclass
class MaintenanceOperationResult:
    """Result of a maintenance operation"""
    success: bool
    operation: str
    message: str
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "operation": self.operation,
            "message": self.message,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp.isoformat(),
        }
