"""SQLite helper utilities for uCore.

Provides shared database connection patterns extracted from duplicate code.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def get_sqlite_connection(
    db_path: Path,
    row_factory: Any = sqlite3.Row,
) -> sqlite3.Connection:
    """Create a SQLite connection with standard configuration.

    This is a shared utility extracted from duplicate _connect methods.

    Args:
        db_path: Path to the SQLite database file
        row_factory: Row factory for the connection (default: sqlite3.Row)

    Returns:
        Configured SQLite connection
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = row_factory
    return conn
