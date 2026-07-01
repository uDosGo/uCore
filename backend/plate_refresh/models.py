"""Pydantic models for the Plates system.

Defines PlateMeta, DestroyRebuildConfig, and related types
for canonical, versioned, recoverable blueprints.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SpoolArchiveConfig(BaseModel):
    """Configuration for ARCHIVE/COMPOST/BACKUP -> SPOOL pipeline.

    When a component is destroyed, its essence is compressed into
    an MCP-formatted SPOOL record for:
    1. Legacy/archival records that dont consume lots of space like .git can
    2. Avoiding re-developing the same deprecated skill
    3. Learning/wisdom from previous failures and upgrades
    """

    enabled: bool = True
    spool_dir: str = "~/.ucore/logs"
    compress_metadata: bool = True
    include_source: bool = False
    include_lessons: bool = True
    max_spool_age_days: int = 365


class DestroyRebuildConfig(BaseModel):
    """DESTROY/REBUILD protocol configuration."""

    salvage_keys: list[str] = []
    rebuild_command: str = ""
    backup_before_destroy: bool = True
    spool_archive: SpoolArchiveConfig = Field(
        default_factory=SpoolArchiveConfig,
    )


class PlateMeta(BaseModel):
    """Canonical plate metadata — extends SkillMeta pattern."""

    id: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    domain: Literal["skill", "snack", "mcp", "hivemind", "secret", "css", "vault"]
    description: str = ""
    json_schema: dict[str, Any] = Field(default_factory=dict, alias="schema")
    source: Literal["builtin", "user", "community"] = "builtin"
    checksum: str = ""
    dependencies: list[str] = []
    lessons: list[str] = Field(
        default_factory=list,
        description="Lessons learned from previous failures/upgrades",
    )
    created: datetime = Field(default_factory=datetime.now)
    updated: datetime = Field(default_factory=datetime.now)
    destroy: DestroyRebuildConfig = Field(default_factory=DestroyRebuildConfig)

    def compute_checksum(self, content: str) -> str:
        """Compute SHA-256 checksum of plate content."""

        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def validate_checksum(self, content: str) -> bool:
        """Validate content against stored checksum."""
        if not self.checksum:
            return True
        return self.compute_checksum(content) == self.checksum


class DriftReport(BaseModel):
    """Report from drift detection."""

    plate_id: str
    version: str
    drift_detected: bool
    differences: list[str] = []
    checksum_match: bool = True
    missing_keys: list[str] = []
    extra_keys: list[str] = []


class RebuildResult(BaseModel):
    """Result of a DESTROY/REBUILD operation."""

    plate_id: str
    success: bool
    salvaged: dict[str, Any] = {}
    rebuild_output: str = ""
    errors: list[str] = []
    backup_path: str = ""
