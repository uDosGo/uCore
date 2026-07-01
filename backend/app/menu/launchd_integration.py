#!/usr/bin/env python3
"""Launchd integration for unified menu.

Extracted from unified_menu_simple.py to use launchd_manager as single source of truth.
"""
from __future__ import annotations

import logging

log = logging.getLogger("ucore.menu.launchd_integration")


def install_launchd() -> bool:
    """Install launchd plist for menu auto-start.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from app.menu.launchd_manager import install
        
        result = install()
        log.info("Launchd installed: %s", result)
        return result
    except Exception as exc:
        log.error("Failed to install launchd: %s", exc)
        return False


def uninstall_launchd() -> bool:
    """Uninstall launchd plist for menu.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from app.menu.launchd_manager import uninstall
        
        result = uninstall()
        log.info("Launchd uninstalled: %s", result)
        return result
    except Exception as exc:
        log.error("Failed to uninstall launchd: %s", exc)
        return False


def is_launchd_installed() -> bool:
    """Check if launchd plist is installed.
    
    Returns:
        True if installed, False otherwise
    """
    try:
        from app.menu.launchd_manager import is_installed
        
        result = is_installed()
        log.debug("Launchd installed: %s", result)
        return result
    except Exception as exc:
        log.error("Failed to check launchd: %s", exc)
        return False