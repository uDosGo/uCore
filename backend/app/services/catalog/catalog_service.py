"""Catalog Service — Core catalog management with SQLite storage."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .models import (
    CatalogEntry,
    EntryType,
    SpatialUID,
)


class CatalogService:
    """Service for managing the catalog with SQLite storage."""

    _instance: Optional["CatalogService"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern for CatalogService."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the catalog service."""
        if hasattr(self, "_initialized"):
            return

        # Catalog directory
        self.catalog_dir = Path.home() / ".ucore" / "catalog"
        self.catalog_dir.mkdir(parents=True, exist_ok=True)

        # Database path
        self.db_path = self.catalog_dir / "index.db"

        # Initialize database
        self._init_database()

        self._initialized = True

    def _init_database(self):
        """Initialize SQLite database with full-text search."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                uid TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                metadata TEXT NOT NULL,
                relationships TEXT NOT NULL,
                tags TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create full-text search index
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS entry_fts USING fts5(
                uid,
                name,
                description,
                content='entries',
                content_rowid='rowid'
            )
        """)

        # Create relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                type TEXT NOT NULL,
                target TEXT NOT NULL,
                weight REAL DEFAULT 0.5,
                FOREIGN KEY (uid) REFERENCES entries(uid) ON DELETE CASCADE,
                FOREIGN KEY (target) REFERENCES entries(uid) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entries_type
            ON entries(type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entries_tags
            ON entries(tags)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_uid
            ON relationships(uid)
        """)

        conn.commit()
        conn.close()

    def add_entry(self, entry: CatalogEntry) -> bool:
        """Add or update a catalog entry.

        Args:
            entry: The catalog entry to add/update

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Insert or replace entry
            cursor.execute("""
                INSERT OR REPLACE INTO entries
                (uid, type, name, description, metadata, relationships, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.uid,
                entry.type.value,
                entry.name,
                entry.description,
                json.dumps(entry.metadata),
                json.dumps([r.dict() for r in entry.relationships]),
                json.dumps(entry.tags),
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
            ))

            # Update FTS index
            cursor.execute("""
                INSERT OR REPLACE INTO entry_fts (uid, name, description)
                VALUES (?, ?, ?)
            """, (entry.uid, entry.name, entry.description))

            # Insert relationships
            for rel in entry.relationships:
                cursor.execute("""
                    INSERT INTO relationships (uid, type, target, weight)
                    VALUES (?, ?, ?, ?)
                """, (entry.uid, rel.type.value, rel.target, rel.weight))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error adding entry: {e}")
            return False

    def get_entry(self, uid: SpatialUID) -> Optional[CatalogEntry]:
        """Get a catalog entry by UID.

        Args:
            uid: The spatial UID of the entry

        Returns:
            The catalog entry or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT uid, type, name, description, metadata, relationships, tags, created_at, updated_at
                FROM entries
                WHERE uid = ?
            """, (uid,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return self._row_to_entry(row)

        except Exception as e:
            print(f"Error getting entry: {e}")
            return None

    def list_entries(
        self,
        entry_type: Optional[EntryType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CatalogEntry]:
        """List catalog entries with optional filtering.

        Args:
            entry_type: Filter by entry type
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of catalog entries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if entry_type:
                cursor.execute("""
                    SELECT uid, type, name, description, metadata, relationships, tags, created_at, updated_at
                    FROM entries
                    WHERE type = ?
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (entry_type.value, limit, offset))
            else:
                cursor.execute("""
                    SELECT uid, type, name, description, metadata, relationships, tags, created_at, updated_at
                    FROM entries
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            print(f"Error listing entries: {e}")
            return []

    def search(
        self,
        query: str,
        limit: int = 20,
        entry_type: Optional[EntryType] = None,
    ) -> List[CatalogEntry]:
        """Full-text search across catalog entries.

        Args:
            query: Search query
            limit: Maximum number of results
            entry_type: Filter by entry type

        Returns:
            List of matching catalog entries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if entry_type:
                cursor.execute("""
                    SELECT e.uid, e.type, e.name, e.description, e.metadata, e.relationships, e.tags, e.created_at, e.updated_at
                    FROM entries e
                    JOIN entry_fts fts ON e.uid = fts.uid
                    WHERE fts MATCH ? AND e.type = ?
                    ORDER BY fts.rank
                    LIMIT ?
                """, (query, entry_type.value, limit))
            else:
                cursor.execute("""
                    SELECT e.uid, e.type, e.name, e.description, e.metadata, e.relationships, e.tags, e.created_at, e.updated_at
                    FROM entries e
                    JOIN entry_fts fts ON e.uid = fts.uid
                    WHERE fts MATCH ?
                    ORDER BY fts.rank
                    LIMIT ?
                """, (query, limit))

            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            print(f"Error searching catalog: {e}")
            return []

    def get_relationships(
        self,
        uid: SpatialUID,
        depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """Get dependency graph for a catalog entry.

        Args:
            uid: The spatial UID of the entry
            depth: Maximum depth of relationships to traverse

        Returns:
            List of relationships
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get direct relationships
            cursor.execute("""
                SELECT type, target, weight
                FROM relationships
                WHERE uid = ?
            """, (uid,))

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "type": row[0],
                    "target": row[1],
                    "weight": row[2],
                }
                for row in rows
            ]

        except Exception as e:
            print(f"Error getting relationships: {e}")
            return []

    def get_graph(
        self,
        uid: SpatialUID,
        depth: int = 1,
    ) -> Dict[str, Any]:
        """Get dependency graph for a catalog entry.

        Args:
            uid: The spatial UID of the entry
            depth: Maximum depth of relationships to traverse

        Returns:
            Graph with nodes and edges
        """
        graph = {
            "nodes": [],
            "edges": [],
        }

        visited: Set[SpatialUID] = set()

        def traverse(current_uid: SpatialUID, current_depth: int):
            if current_depth > depth or current_uid in visited:
                return

            visited.add(current_uid)

            # Add node
            entry = self.get_entry(current_uid)
            if entry:
                graph["nodes"].append({
                    "uid": entry.uid,
                    "type": entry.type.value,
                    "name": entry.name,
                })

            # Get relationships
            relationships = self.get_relationships(current_uid, 0)
            for rel in relationships:
                target_uid = SpatialUID(rel["target"])
                graph["edges"].append({
                    "from": current_uid,
                    "to": target_uid,
                    "type": rel["type"],
                })
                traverse(target_uid, current_depth + 1)

        traverse(uid, 0)
        return graph

    def delete_entry(self, uid: SpatialUID) -> bool:
        """Delete a catalog entry.

        Args:
            uid: The spatial UID of the entry

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM entries WHERE uid = ?", (uid,))
            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Error deleting entry: {e}")
            return False

    def clear_all(self) -> bool:
        """Clear all catalog entries.

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM entries")
            cursor.execute("DELETE FROM relationships")
            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Error clearing catalog: {e}")
            return False

    def _row_to_entry(self, row: tuple) -> CatalogEntry:
        """Convert database row to CatalogEntry.

        Args:
            row: Database row tuple

        Returns:
            CatalogEntry object
        """
        (
            uid,
            type_str,
            name,
            description,
            metadata_json,
            relationships_json,
            tags_json,
            created_at,
            updated_at,
        ) = row

        return CatalogEntry(
            uid=SpatialUID(uid),
            type=EntryType(type_str),
            name=name,
            description=description,
            metadata=json.loads(metadata_json),
            relationships=[
                Relationship(
                    type=str(r["type"]),
                    target=SpatialUID(r["target"]),
                    weight=r.get("weight", 0.5),
                )
                for r in json.loads(relationships_json)
            ],
            tags=json.loads(tags_json),
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(updated_at),
        )

    def get_stats(self) -> Dict[str, int]:
        """Get catalog statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total entries
            cursor.execute("SELECT COUNT(*) FROM entries")
            total = cursor.fetchone()[0]

            # Entries by type
            cursor.execute("""
                SELECT type, COUNT(*) as count
                FROM entries
                GROUP BY type
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # Total relationships
            cursor.execute("SELECT COUNT(*) FROM relationships")
            total_relationships = cursor.fetchone()[0]

            conn.close()

            return {
                "total_entries": total,
                "by_type": by_type,
                "total_relationships": total_relationships,
            }

        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                "total_entries": 0,
                "by_type": {},
                "total_relationships": 0,
            }
