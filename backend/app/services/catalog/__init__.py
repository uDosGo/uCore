"""Catalog Service — Unified resource discovery and indexing for uCode.

Provides a central catalog for LLMs, skills, libraries, MCP servers, vendors,
and repositories with spatial UID-based relationships.
"""

from .catalog_service import CatalogService
from .models import CatalogEntry, EntryType, SpatialUID

__all__ = ["CatalogService", "CatalogEntry", "SpatialUID", "EntryType"]
