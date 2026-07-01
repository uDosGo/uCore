#!/usr/bin/env python3
"""Status icon management for unified menu.

Extracted from unified_menu_simple.py to improve maintainability.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Optional

from AppKit import NSStatusBar, NSStatusItem, NSVariableStatusItemLength
# NOTE: SEL removed in PyObjC 12.x / Python 3.14 — selectors use objc.selector type

log = logging.getLogger("ucore.menu.status_icon")


def _make_status_icon(connected: bool = False) -> Optional[NSStatusItem]:
    """Create a status icon in the macOS menu bar.
    
    Uses emoji as button title (SF Symbols not available in PyObjC 12.x).
    
    Args:
        connected: Whether backend is connected
        
    Returns:
        NSStatusItem or None if creation fails
    """
    try:
        # Create status item
        status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        
        if not status_item:
            log.error("Failed to create status item")
            return None
        
        # Set emoji as button title (SF Symbols not available in PyObjC 12.x)
        button = status_item.button()
        if button:
            # Use popcorn emoji — changes based on connection status
            button.setTitle_("🍿" if connected else "🍿")
        
        return status_item
    except Exception as exc:
        log.error("Failed to create status icon: %s", exc)
        return None


def update_status_icon(status_item: Optional[NSStatusItem], connected: bool) -> None:
    """Update the status icon appearance.
    
    Args:
        status_item: NSStatusItem to update
        connected: Whether backend is connected
    """
    try:
        if status_item:
            button = status_item.button()
            if button:
                # Connected = full popcorn, disconnected = dimmed popcorn
                button.setTitle_("🍿" if connected else "🍿")
    except Exception as exc:
        log.error("Failed to update status icon: %s", exc)

