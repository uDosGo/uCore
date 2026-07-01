"""Clipboard Snack — Clipboard buffer management for uCore menu."""
from __future__ import annotations

import logging
from typing import Any, Optional

from snackmachine.registry import SnackPlugin, SnackSpec, register_snack

log = logging.getLogger("clipboard-snack")


class ClipboardSnack(SnackPlugin):
    """Clipboard buffer management snack."""
    
    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate
        self._clipboard_recent = []
        self._clipboard_saved = []
    
    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(
            id="clipboard-buffer",
            name="Clipboard Buffer",
            icon="📋",
            kind="multi-action",
            category="clipboard",
            enabled=True,
            actions=["open-panel", "search", "capture", "clear-history", "clear-all"],
            shortcut="ctrl+cmd+v",
            metadata={"description": "Manage clipboard history and saved items"},
        )
    
    def is_available(self) -> bool:
        return True  # Always available
    
    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if not self._menu_delegate:
            log.warning("No menu delegate available for clipboard actions")
            return False
        
        if action == "open-panel" or action is None:
            self._menu_delegate.showClipboardPopover_(None)
        elif action == "search":
            self._menu_delegate.searchClipboard_(None)
        elif action == "capture":
            self._menu_delegate.captureClipboard_(None)
        elif action == "clear-history":
            self._menu_delegate.clearClipboardHistory_(None)
        elif action == "clear-all":
            self._menu_delegate.clearClipboardAll_(None)
        else:
            log.warning(f"Unknown clipboard action: {action}")
            return False
        return True
    
    def update_items(self, recent: list, saved: list) -> None:
        """Update clipboard items from backend."""
        self._clipboard_recent = recent
        self._clipboard_saved = saved
    
    def get_items(self) -> tuple:
        return self._clipboard_recent, self._clipboard_saved


# Register on import
def register(menu_delegate=None):
    """Register the clipboard snack."""
    plugin = ClipboardSnack(menu_delegate)
    register_snack(plugin)
    return plugin