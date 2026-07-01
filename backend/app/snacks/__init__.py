"""Snack Management Package.

Provides:
- Snack templates (like Skill templates)
- SnackShack for publishing/restore flow
- Snack registry integration
"""
from .templates.snack_template import BaseSnack, SnackMeta, SnackParam

__all__ = ["BaseSnack", "SnackMeta", "SnackParam"]