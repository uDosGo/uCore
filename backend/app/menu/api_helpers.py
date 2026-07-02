#!/usr/bin/env python3
"""API helpers for unified menu - HTTP requests and status checks.

Extracted from unified_menu_simple.py to improve maintainability.
"""
from __future__ import annotations

import logging
from typing import Optional

from aiohttp import ClientSession

log = logging.getLogger("ucore.menu.api_helpers")


async def post_notification(title: str, message: str, subtitle: Optional[str] = None) -> None:
    """Post a notification to the macOS notification center.
    
    Args:
        title: Notification title
        message: Notification message
        subtitle: Optional subtitle
    """
    try:
        from AppKit import NSUserNotification, NSUserNotificationCenter
        
        notification = NSUserNotification.alloc().init()
        notification.setTitle_(title)
        notification.setInformativeText_(message)
        if subtitle:
            notification.setSubtitle_(subtitle)
        
        center = NSUserNotificationCenter.defaultUserNotificationCenter()
        center.deliverNotification_(notification)
        
        log.info("Notification posted: %s - %s", title, message)
    except Exception as exc:
        log.error("Failed to post notification: %s", exc)


async def api_get(path: str, timeout: float = 3.0) -> Optional[dict]:
    """Make an HTTP GET request to the uCore backend.
    
    Args:
        path: API endpoint path (e.g., "/api/health")
        timeout: Request timeout in seconds
        
    Returns:
        JSON response dict or None if request fails
    """
    try:
        async with ClientSession() as session:
            async with session.get(f"http://localhost:8484{path}", timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                log.warning("API request failed: %s %s", response.status, path)
                return None
    except Exception as exc:
        log.error("API request error: %s %s - %s", path, exc)
        return None


def api_get_sync(path: str, timeout: float = 3.0) -> Optional[dict]:
    """Synchronous wrapper for api_get — runs the coroutine in a fresh event loop.

    Use this from non-async code (e.g. threading.Timer callbacks).
    """
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(api_get(path, timeout))
        finally:
            loop.close()
    except Exception as exc:
        log.error("api_get_sync error: %s %s - %s", path, exc)
        return None


def is_ucore_alive() -> bool:
    """Check if uCore backend is running.
    
    Uses a raw TCP socket probe instead of HTTP to avoid triggering a
    known aiohttp bug where Python stdlib HTTP clients (urllib, http.client)
    cause the backend event loop to hang permanently.
    
    Returns:
        True if backend is responding, False otherwise
    """
    import socket
    try:
        with socket.create_connection(("127.0.0.1", 8484), timeout=2):
            return True
    except Exception:
        return False


def is_uihub_alive() -> bool:
    """Check if UI Hub is running.
    
    Returns:
        True if UI Hub is responding, False otherwise
    """
    try:
        import urllib.request
        
        req = urllib.request.Request("http://localhost:5175", method="HEAD")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status < 500
    except Exception:
        return False


def open_url(url: str) -> None:
    """Open a URL in the default browser.
    
    Args:
        url: URL to open
    """
    try:
        import webbrowser
        
        webbrowser.open(url)
        log.info("Opened URL: %s", url)
    except Exception as exc:
        log.error("Failed to open URL: %s", exc)