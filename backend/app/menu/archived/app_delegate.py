#!/usr/bin/env python3
"""App delegate for unified menu.

Extracted from unified_menu_simple.py to improve maintainability.
"""
from __future__ import annotations

import logging
from typing import Optional

from AppKit import NSObject, NSMenu, NSMenuItem
# NOTE: NSApplication and NSApplicationDelegate removed — unused imports
# (NSApplicationDelegate is also unavailable in PyObjC 12.x / Python 3.14)

log = logging.getLogger("ucore.menu.app_delegate")


class UnifiedMenuDelegate(NSObject):
    """Main menu delegate for unified menu bar app."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_item = None
        self.menu = None
    
    def applicationDidFinishLaunching_(self, notification) -> None:
        """Called when application finishes launching."""
        log.info("Unified menu application did finish launching")
        
        # Create status icon
        self.status_item = self._create_status_icon()
        
        # Create menu
        self.menu = self._create_menu()
        
        # Set menu to status item
        if self.status_item and self.menu:
            self.status_item.setMenu_(self.menu)
    
    def applicationWillTerminate_(self, notification) -> None:
        """Called when application is about to terminate."""
        log.info("Unified menu application will terminate")
        
        # Clean up
        if self.status_item:
            self.status_item.dispose()
    
    def _create_status_icon(self) -> Optional[object]:
        """Create the status icon."""
        from app.menu.status_icon import _make_status_icon
        
        return _make_status_icon()
    
    def _create_menu(self) -> NSMenu:
        """Create the menu."""
        menu = NSMenu.alloc().init()
        
        # TODO: Add menu items for actual functionality
        
        return menu