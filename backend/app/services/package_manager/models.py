"""Package Manager Data Models"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class PackageStatus(Enum):
    """Package installation status"""
    INSTALLED = "installed"
    INSTALLING = "installing"
    UPDATED = "updated"
    UPDATING = "updating"
    REMOVED = "removed"
    REMOVING = "removing"
    FAILED = "failed"
    CORRUPTED = "corrupted"
    PENDING = "pending"


@dataclass
class DependencyInfo:
    """Package dependency information"""
    name: str
    version: str
    required: bool = True
    installed: bool = False
    installed_version: Optional[str] = None


@dataclass
class PackageInfo:
    """Package information"""
    name: str
    version: str
    status: PackageStatus
    description: str = ""
    author: str = ""
    dependencies: List[DependencyInfo] = field(default_factory=list)
    installed_path: Optional[str] = None
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "description": self.description,
            "author": self.author,
            "dependencies": [
                {
                    "name": d.name,
                    "version": d.version,
                    "required": d.required,
                    "installed": d.installed,
                    "installed_version": d.installed_version,
                }
                for d in self.dependencies
            ],
            "installed_path": self.installed_path,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "metadata": self.metadata,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
        }


@dataclass
class PackageOperationResult:
    """Result of a package operation"""
    success: bool
    package_name: str
    message: str
    package_info: Optional[PackageInfo] = None
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "package_name": self.package_name,
            "message": self.message,
            "package_info": self.package_info.to_dict() if self.package_info else None,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp.isoformat(),
        }