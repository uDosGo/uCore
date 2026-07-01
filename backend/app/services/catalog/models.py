"""Catalog data models and types."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EntryType(str, Enum):
    """Catalog entry types."""
    LLM = "llm"
    SKILL = "skill"
    LIBRARY = "lib"
    MCP = "mcp"
    VENDOR = "vendor"
    REPO = "repo"


class RelationshipType(str, Enum):
    """Types of relationships between catalog entries."""
    DEPENDS_ON = "depends_on"
    PROVIDES = "provides"
    RELATED_TO = "related_to"
    IMPLEMENTS = "implements"
    USES = "uses"


    input_price_per_m_tokens: float
    output_price_per_m_tokens: float
    context_window: int
    capabilities: List[str] = Field(default_factory=list)
    performance_score: Optional[float] = None
    routing_rules: Optional[Dict[str, Any]] = None


class SkillMetadata(BaseModel):
    """Metadata for skill entries."""
    version: str
    dependencies: List[SpatialUID] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    mcp_server: Optional[SpatialUID] = None
    author: str = ""
    max_complexity: Optional[int] = None


class RepoMetadata(BaseModel):
    """Metadata for repository entries."""
    url: str
    stars: Optional[int] = None
    last_commit: Optional[str] = None
    license: Optional[str] = None
    language: Optional[str] = None
    mcp_server: Optional[str] = None


class MCPServerMetadata(BaseModel):
    """Metadata for MCP server entries."""
    version: str
    port: int
    status: str = "unknown"
    tools: List[str] = Field(default_factory=list)
    provider: str = ""
    transport: str = "stdio"


class CatalogEntry(BaseModel):
    """Core catalog entry with spatial UID."""
    uid: str
    type: EntryType
    name: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to this entry."""
        self.relationships.append(relationship)
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """Add a tag to this entry."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "uid": self.uid,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "relationships": [
                {
                    "type": r.type.value,
                    "target": r.target,
                    "weight": r.weight,
                }
                for r in self.relationships
            ],
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SpatialUID(str):
    """Spatial UID for catalog entries.

    Format: {domain}.{namespace}.{entity}
    Examples:
        - llm.openrouter.gpt-oss-20b
        - skill.code-review.python
        - mcp.browser.lightpanda
    """

    def __new__(cls, value: str):
        """Validate and create SpatialUID."""
        if not cls._validate(value):
            raise ValueError(f"Invalid SpatialUID: {value}")
        return super().__new__(cls, value)

    @staticmethod
    def _validate(uid: str) -> bool:
        """Validate SpatialUID format."""
        pattern = r'^[a-z]+(\.[a-z0-9-]+){2}$'
        return re.match(pattern, uid) is not None

    @staticmethod
    def generate(domain: str, namespace: str, entity: str) -> SpatialUID:
        """Generate a spatial UID with validation.

        Args:
            domain: Lower-case, alphabetic only (llm, skill, mcp, vendor, repo, lib)
            namespace: Lower-case, alphanumeric with hyphens
            entity: Lower-case, alphanumeric with hyphens

        Returns:
            A validated SpatialUID
        """
        domain = re.sub(r'[^a-z]', '', domain.lower())
        namespace = re.sub(r'[^a-z0-9-]', '-', namespace.lower())
        entity = re.sub(r'[^a-z0-9-]', '-', entity.lower())
        return SpatialUID(f"{domain}.{namespace}.{entity}")

    @property
    def domain(self) -> str:
        """Get the domain part of the UID."""
        return self.split('.')[0]

    @property
    def namespace(self) -> str:
        """Get the namespace part of the UID."""
        return self.split('.')[1]

    @property
    def entity(self) -> str:
        """Get the entity part of the UID."""
        return self.split('.')[2]

    def get_path(self, base_dir: Path) -> Path:
        """Get the file path for this UID in the catalog."""
        return base_dir / "uids" / f"{self}.json"


# Type aliases for convenience
CatalogEntryDict = Dict[str, Any]
RelationshipDict = Dict[str, Any]
