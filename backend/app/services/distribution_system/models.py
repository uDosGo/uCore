"""Data models for the Distribution System."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ModuleStatus(Enum):
    """Status of a module in the distribution system."""
    INSTALLED = "installed"
    UPDATED = "updated"
    REMOVED = "removed"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class ModuleInfo:
    """Information about an installed module."""
    name: str
    version: str
    status: ModuleStatus
    description: str = ""
    type: str = "service"
    dependencies: List[str] = field(default_factory=list)
    health_status: str = "unknown"
    last_health_check: Optional[datetime] = None
    installed_path: Optional[str] = None
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["status"] = self.status.value
        result["last_health_check"] = (
            self.last_health_check.isoformat() if self.last_health_check else None
        )
        result["last_updated"] = (
            self.last_updated.isoformat() if self.last_updated else None
        )
        return result


@dataclass
class DistributionOperationResult:
    """Result of a distribution operation."""
    success: bool
    operation: str
    module_name: str
    message: str
    module_info: Optional[ModuleInfo] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "operation": self.operation,
            "module_name": self.module_name,
            "message": self.message,
            "module_info": self.module_info.to_dict() if self.module_info else None,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class SystemHealthReport:
    """System health report."""
    overall_status: str
    modules: List[ModuleInfo]
    services: List[Dict[str, Any]]
    issues: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_status": self.overall_status,
            "modules": [m.to_dict() for m in self.modules],
            "services": self.services,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }
