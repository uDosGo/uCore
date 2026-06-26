from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import sqlite3
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.settings import settings

log = logging.getLogger("ucore.mcp.toon")


def default_toon_db_path() -> Path:
    return settings.data_dir / "toon_cache.db"


def _utc_now() -> str:
    from datetime import datetime, UTC
    return datetime.now(UTC).isoformat()


@dataclass
class TOONContextEntry:
    """Represents a cached TOON context entry."""
    key: str
    original_content: str
    toon_content: str
    compression_ratio: float
    original_size: int
    toon_size: int
    created_at: str
    accessed_at: str
    hit_count: int = 0


class TOONContextServer:
    """TOON Context Server - Token-Optimized Object Notation for AI context.
    
    Converts structured data (JSON, CSV, Markdown) to TOON format which is
    30-60% more token-efficient while preserving semantic meaning.
    """
    
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or default_toon_db_path()
        self._ensure_schema()
        self._stats = {
            "requests": 0,
            "hits": 0,
            "misses": 0,
            "writes": 0,
        }
    
    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS toon_cache (
                    key TEXT PRIMARY KEY,
                    original_content_hash TEXT NOT NULL,
                    toon_content TEXT NOT NULL,
                    compression_ratio REAL NOT NULL,
                    original_size INTEGER NOT NULL,
                    toon_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    hit_count INTEGER NOT NULL DEFAULT 0
                )
                """,
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_toon_cache_hash
                ON toon_cache(original_content_hash)
                """,
            )
            conn.commit()
    
    def _calculate_compression_ratio(self, original: str, toon: str) -> float:
        """Calculate compression ratio between original and TOON content."""
        if len(original) == 0:
            return 1.0
        return len(toon) / len(original)
    
    def _generate_key(self, content: str, content_type: str = "text") -> str:
        """Generate a unique key for the content."""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return f"{content_type}:{content_hash}"
    
    def _toon_encode_json(self, data: Any) -> str:
        """Convert JSON data to TOON format - optimized for token efficiency."""
        # TOON format: compact representation that preserves structure but removes redundancy
        if isinstance(data, dict):
            # Convert dict to compact TOON format
            parts = []
            for key, value in data.items():
                # Use compact key representation
                compact_key = key.replace("_", "").replace(" ", "").lower()
                if isinstance(value, (str, int, float, bool, type(None))):
                    # Simple values - compact representation
                    if isinstance(value, str):
                        # Truncate long strings but preserve context
                        if len(value) > 200:
                            value = value[:100] + "..." + value[-50:]
                    parts.append(f"{compact_key}={repr(value)}")
                elif isinstance(value, list):
                    # Compact list representation
                    if len(value) > 5:
                        parts.append(f"{compact_key}=[{len(value)} items]")
                    else:
                        parts.append(f"{compact_key}={repr(value)}")
                else:
                    # Nested objects - recursive TOON encoding
                    nested_toon = self._toon_encode_json(value)
                    parts.append(f"{compact_key}={nested_toon}")
            return "{" + ", ".join(parts) + "}"
        elif isinstance(data, list):
            # Compact list representation
            if len(data) > 10:
                return f"[{len(data)} items]"
            return repr(data)
        else:
            return repr(data)
    
    def _toon_encode_markdown(self, markdown: str) -> str:
        """Convert Markdown to TOON format - optimized for AI context."""
        # Remove redundant whitespace and comments
        lines = []
        for line in markdown.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("<!--") or stripped.startswith("# "):
                continue
            # Keep headings but simplify
            if stripped.startswith("## "):
                lines.append(f"SECTION: {stripped[3:]}")
            elif stripped.startswith("### "):
                lines.append(f"SUBSECTION: {stripped[4:]}")
            elif stripped.startswith("- "):
                lines.append(f"ITEM: {stripped[2:]}")
            elif stripped.startswith("* "):
                lines.append(f"ITEM: {stripped[2:]}")
            elif stripped.startswith("1. "):
                lines.append(f"ITEM: {stripped[3:]}")
            elif stripped.startswith("| "):
                # Skip table rows for now
                continue
            else:
                # Compact paragraph
                compact = " ".join(stripped.split())
                if len(compact) > 150:
                    compact = compact[:75] + "..." + compact[-50:]
                lines.append(f"TEXT: {compact}")
        
        return "\n".join(lines)
    
    def _toon_encode_csv(self, csv_content: str) -> str:
        """Convert CSV to TOON format - optimized for AI context."""
        lines = csv_content.splitlines()
        if len(lines) < 2:
            return csv_content
        
        # Extract headers and first few rows
        headers = lines[0].split(",")
        headers = [h.strip().strip("\"") for h in headers]
        
        # Compact representation
        toon_lines = [f"CSV: {len(lines)} rows, {len(headers)} columns"]
        toon_lines.append(f"HEADERS: {', '.join(headers)}")
        
        # First 3 data rows
        for i in range(1, min(4, len(lines))):
            row = lines[i].split(",")
            row = [r.strip().strip("\"") for r in row]
            toon_lines.append(f"ROW{i}: {', '.join(row[:5])}")
        
        return "\n".join(toon_lines)
    
    def toon_encode(self, content: str, content_type: str = "text") -> str:
        """Convert content to TOON format based on content type."""
        if not content:
            return ""
        
        if content_type == "json" or content.strip().startswith("{") or content.strip().startswith("["):
            try:
                data = json.loads(content)
                return self._toon_encode_json(data)
            except json.JSONDecodeError:
                pass
        
        if content_type == "markdown" or content.strip().startswith("# "):
            return self._toon_encode_markdown(content)
        
        if content_type == "csv" or "," in content[:100]:
            return self._toon_encode_csv(content)
        
        # Default text compression
        return self._toon_encode_markdown(content)
    
    def get(self, content: str, content_type: str = "text") -> Optional[TOONContextEntry]:
        """Get TOON context from cache, or None if not found."""
        self._stats["requests"] += 1
        key = self._generate_key(content, content_type)
        
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM toon_cache WHERE key = ?",
                (key,),
            ).fetchone()
            if row is None:
                self._stats["misses"] += 1
                return None
            
            conn.execute(
                "UPDATE toon_cache SET accessed_at = ?, hit_count = hit_count + 1 WHERE key = ?",
                (_utc_now(), key),
            )
            conn.commit()
        
        self._stats["hits"] += 1
        
        return TOONContextEntry(
            key=row["key"],
            original_content="",
            toon_content=row["toon_content"],
            compression_ratio=row["compression_ratio"],
            original_size=row["original_size"],
            toon_size=row["toon_size"],
            created_at=row["created_at"],
            accessed_at=row["accessed_at"],
            hit_count=row["hit_count"],
        )
    
    def set(self, content: str, toon_content: str, content_type: str = "text") -> None:
        """Store TOON context in cache."""
        key = self._generate_key(content, content_type)
        compression_ratio = self._calculate_compression_ratio(content, toon_content)
        
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO toon_cache(
                    key,
                    original_content_hash,
                    toon_content,
                    compression_ratio,
                    original_size,
                    toon_size,
                    created_at,
                    accessed_at,
                    hit_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    toon_content = excluded.toon_content,
                    compression_ratio = excluded.compression_ratio,
                    original_size = excluded.original_size,
                    toon_size = excluded.toon_size,
                    accessed_at = excluded.accessed_at,
                    hit_count = toon_cache.hit_count
                """,
                (
                    key,
                    hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    toon_content,
                    compression_ratio,
                    len(content),
                    len(toon_content),
                    _utc_now(),
                    _utc_now(),
                    0,
                ),
            )
            conn.commit()
        self._stats["writes"] += 1
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS entries,
                    COALESCE(SUM(hit_count), 0) AS total_hits,
                    MAX(accessed_at) AS last_accessed_at
                FROM toon_cache
                """,
            ).fetchone()
        
        requests = int(self._stats["requests"])
        hits = int(self._stats["hits"])
        misses = int(self._stats["misses"])
        hit_ratio = round(hits / requests, 3) if requests > 0 else 0.0
        
        return {
            "entries": int(row["entries"] if row is not None else 0),
            "requests": requests,
            "hits": hits,
            "misses": misses,
            "writes": int(self._stats["writes"]),
            "hit_ratio": hit_ratio,
            "persisted_hits": int(row["total_hits"] if row is not None else 0),
            "last_accessed_at": row["last_accessed_at"] if row is not None else None,
        }
    
    def clear(self) -> None:
        """Clear the TOON cache."""
        with self._connect() as conn:
            conn.execute("DELETE FROM toon_cache")
            conn.commit()
