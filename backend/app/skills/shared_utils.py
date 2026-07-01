#!/usr/bin/env python3
"""Shared utilities for skills - extracted common functions.

This module contains shared utility functions extracted from duplicate code
across multiple skills to reduce code duplication.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class MockRequest:
    """Mock aiohttp web.Request for testing and handler reuse."""
    
    def __init__(self, body: dict):
        self._body = body
    
    async def json(self) -> dict:
        return self._body


def create_mock_request(body: dict) -> MockRequest:
    """Create a mock request for handler reuse.

    Shared utility extracted from:
    - mcp.py: multiple MockRequest classes (lines 930-940, 955-965, 980-990)

    Args:
        body: The request body to return

    Returns:
        MockRequest instance
    """
    return MockRequest(body)


def update_menu_delegate(menu_delegate: Any, method: str = "updateUI:", wait: bool = False) -> None:
    """Update menu delegate on main thread.

    Shared utility extracted from:
    - system_snack.py:274 (update_status method)
    - surface_snack.py:110 (update_surfaces method)

    Args:
        menu_delegate: The menu delegate object to call
        method: The selector method name to invoke
        wait: Whether to wait for completion

    Returns:
        None
    """
    if menu_delegate:
        menu_delegate.performSelectorOnMainThread_withObject_waitUntilDone_(method, None, wait)


def get_source_files(target: str = "") -> list[Path]:
    """Get all source files to scan.

    Uses environment variables for path resolution:
    - UDOS_CODE: Code repository root
    - UDOS_VAULT: Vault directory
    - HOME: Home directory

    Shared utility extracted from:
    - skill_duplicate_detector.py:156
    - skill_modularisation_planner.py:156
    - skill_dead_code_archiver.py:182

    Args:
        target: Optional directory or file pattern to scan

    Returns:
        List of Path objects for source files (.py, .js, .ts, .jsx, .tsx)
    """
    # Use UDOS_CODE as default root, fallback to shared_utils location
    root = Path(os.environ.get("UDOS_CODE", Path(__file__).parent.parent.parent.parent))
    
    if target:
        target_path = root / target
        if target_path.is_file():
            return [target_path]
        if target_path.is_dir():
            root = target_path

    extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}
    files = []
    for ext in extensions:
        files.extend(root.rglob(f"*{ext}"))

    exclude_dirs = {"node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build"}
    return [f for f in files if not any(ex in f.parts for ex in exclude_dirs)]