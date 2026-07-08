"""Snack Template - Base class for all snacks.

Snacks follow the same pattern as Skills:
- Templated with YAML metadata
- Publishable/Restorable via SnackShack
- Tagged by category/lane (System Operations, Dev Mode, User Mission Operations)
- Version tracked for dogfooding protection
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel
from snackmachine.registry import SnackPlugin, SnackSpec


class SnackParam(BaseModel):
    """Parameter definition for snack actions."""
    name: str
    type: str = "string"  # string, number, boolean, object, array
    description: str = ""
    required: bool = False
    default: Any = None


class SnackMeta(BaseModel):
    """Metadata for a snack - matches SnackSpec but for templating."""
    id: str
    name: str
    description: str = ""
    category: str = "custom"  # clipboard, ai, surface, system, dev, mission
    icon: str = "🍎"
    kind: str = "action"  # action, multi-action, badge, toggle, separator
    version: str = "1.0.0"
    author: str = "uCore"
    tags: list[str] = []  # System Operations, Dev Mode, User Mission Operations
    params: list[SnackParam] = []
    timeout: int = 60
    requires_confirmation: bool = False


class BaseSnack(SnackPlugin):
    """Base class for all snacks with template support."""

    meta: SnackMeta

    @property
    def spec(self) -> SnackSpec:
        """Convert meta to SnackSpec for registry compatibility."""
        return SnackSpec(
            id=self.meta.id,
            name=self.meta.name,
            icon=self.meta.icon,
            kind=self.meta.kind,
            category=self.meta.category,
            enabled=True,
            actions=self.meta.tags,  # Use tags as actions for multi-action snacks
            metadata={
                "description": self.meta.description,
                "version": self.meta.version,
                "author": self.meta.author,
                "tags": self.meta.tags,
                "timeout": self.meta.timeout,
                "requires_confirmation": self.meta.requires_confirmation,
            },
        )

    def validate(self, **kwargs) -> list[str]:
        """Validate required parameters."""
        return [f"Missing: {p.name}" for p in self.meta.params if p.required and p.name not in kwargs]

    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        """Execute the snack action - to be overridden."""
        raise NotImplementedError
