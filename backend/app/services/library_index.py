"""Unified Library Index — consolidates all vault sources into a
single searchable index at ~/.ucore/indices/.

Vault topology (confirmed):
  user   → ~/Vault/                    (one personal vault)
  shared → ~/Shared/                   (many shared vaults)
  global → ~/Public/global-knowledge/  (global knowledge bank)
  public → ~/Public/doc-sites/         (published vaults)
  code   → ~/Code/                     (dev repos)

The index is stored as SQLite at ~/.ucore/indices/library.db with
FTS5 for full-text search across all sources.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.library_index")

INDEX_DIR = Path.home() / ".ucore" / "indices"
INDEX_DB = INDEX_DIR / "library.db"

VAULT_PATHS = {
    "user": Path.home() / "Vault",
    "shared": Path.home() / "Shared",
    "global": Path.home() / "Public" / "global-knowledge",
    "public": Path.home() / "Public" / "doc-sites",
    "code": Path.home() / "Code",
}

SUPPORTED_EXTENSIONS = {
    ".md", ".yaml", ".yml", ".json", ".txt", ".csv", ".py",
    ".ts", ".tsx", ".js", ".jsx", ".vue",
}
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".next",
    ".obsidian", ".vscode", "dist", ".mypy_cache",
    ".pytest_cache", ".venv", "venv",
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


# ─── Schema ────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS library_entries (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    source TEXT NOT NULL,
    vault_layer TEXT NOT NULL,
    binder TEXT,
    mission TEXT,
    tags_json TEXT,
    type TEXT DEFAULT 'file',
    extension TEXT,
    size INTEGER DEFAULT 0,
    modified_at TEXT,
    created_at TEXT,
    is_readonly INTEGER DEFAULT 0,
    is_shared INTEGER DEFAULT 0,
    is_published INTEGER DEFAULT 0,
    frontmatter_json TEXT,
    preview TEXT,
    indexed_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS library_fts
USING fts5(
    id UNINDEXED,
    filename,
    title,
    preview,
    tags,
    source UNINDEXED,
    path UNINDEXED
);

CREATE TABLE IF NOT EXISTS index_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


# ─── Frontmatter ───────────────────────────────────────────────────

def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter. Returns (frontmatter, body)."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content
    body = content[match.end():]
    try:
        import yaml
        fm = yaml.safe_load(match.group(1))
        if not isinstance(fm, dict):
            fm = {}
    except Exception:
        fm = {}
    return fm, body


def _get_preview(content: str, max_chars: int = 300) -> str:
    """Extract first paragraph as preview."""
    clean = FRONTMATTER_RE.sub("", content)
    lines = []
    for line in clean.split("\n"):
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
        if len("\n".join(lines)) > max_chars:
            break
    return "\n".join(lines)[:max_chars]


def _default_binder_for(source: str) -> str | None:
    """Return the fallback binder for files without explicit metadata."""
    if source == "user":
        return "Sandbox"
    return None


# ─── Scanner ───────────────────────────────────────────────────────

def _scan_source(source: str, base_path: Path) -> list[dict[str, Any]]:
    """Scan a single vault source for indexable files."""
    import os

    entries: list[dict[str, Any]] = []
    if not base_path.exists():
        log.debug("Source path missing: %s", base_path)
        return entries

    source_layer = source.title()

    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for fname in files:
            fpath = Path(root) / fname
            ext = fpath.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            try:
                stat = fpath.stat()
                content = fpath.read_text(
                    encoding="utf-8", errors="replace",
                )
            except Exception:
                continue

            fm, body = (
                _parse_frontmatter(content)
                if ext == ".md"
                else ({}, content)
            )
            tags = fm.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            tags = [str(t) for t in tags] if isinstance(tags, list) else []

            # Add folder-based tags
            rel_parent = fpath.relative_to(base_path).parent
            for part in rel_parent.parts:
                if part not in (".", "") and not part.startswith("_"):
                    if part not in tags:
                        tags.append(part)

            entry_id = f"{source}:{fpath.relative_to(base_path)}"
            entry_id = re.sub(r"[^a-zA-Z0-9_:./-]", "_", entry_id)

            entries.append({
                "id": entry_id,
                "path": str(fpath),
                "filename": fpath.name,
                "source": source,
                "vault_layer": source_layer,
                "binder": (
                    str(fm.get("binder") or "")
                    or _default_binder_for(source)
                ),
                "mission": str(fm.get("mission") or "") or None,
                "tags": tags,
                "type": "file",
                "extension": ext[1:] if ext else "",
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime, tz=UTC,
                ).isoformat(),
                "created_at": datetime.fromtimestamp(
                    stat.st_ctime, tz=UTC,
                ).isoformat(),
                "is_readonly": source == "global",
                "is_shared": source == "shared",
                "is_published": source == "public",
                "frontmatter": fm,
                "preview": _get_preview(body),
            })

    log.info("Scanned %s: %d files", source, len(entries))
    return entries


# ─── Index Builder ─────────────────────────────────────────────────

def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create tables if missing."""
    conn.executescript(SCHEMA_SQL)


def _upsert_entry(conn: sqlite3.Connection, entry: dict[str, Any]) -> None:
    """Insert or replace a single entry + FTS row."""
    now = datetime.now(UTC).isoformat()
    tags_json = json.dumps(entry["tags"], default=str)
    fm_json = json.dumps(entry["frontmatter"], default=str)
    title = entry["frontmatter"].get("title") or entry["filename"]

    conn.execute(
        """
        INSERT INTO library_entries
        (id, path, filename, source, vault_layer, binder, mission,
         tags_json, type, extension, size, modified_at, created_at,
         is_readonly, is_shared, is_published, frontmatter_json,
         preview, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          path = excluded.path,
          filename = excluded.filename,
          source = excluded.source,
          vault_layer = excluded.vault_layer,
          binder = excluded.binder,
          mission = excluded.mission,
          tags_json = excluded.tags_json,
          extension = excluded.extension,
          size = excluded.size,
          modified_at = excluded.modified_at,
          created_at = excluded.created_at,
          is_readonly = excluded.is_readonly,
          is_shared = excluded.is_shared,
          is_published = excluded.is_published,
          frontmatter_json = excluded.frontmatter_json,
          preview = excluded.preview,
          indexed_at = excluded.indexed_at
        """,
        (
            entry["id"], entry["path"], entry["filename"],
            entry["source"], entry["vault_layer"],
            entry["binder"], entry["mission"],
            tags_json, entry["type"], entry["extension"],
            entry["size"], entry["modified_at"], entry["created_at"],
            int(entry["is_readonly"]), int(entry["is_shared"]),
            int(entry["is_published"]), fm_json,
            entry["preview"], now,
        ),
    )

    # Update FTS
    conn.execute(
        "DELETE FROM library_fts WHERE id = ?", (entry["id"],),
    )
    conn.execute(
        """
        INSERT INTO library_fts
        (id, filename, title, preview, tags, source, path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry["id"], entry["filename"], title,
            entry["preview"], " ".join(entry["tags"]),
            entry["source"], entry["path"],
        ),
    )


def build_index(
    sources: list[str] | None = None,
    vault_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    """Build the unified library index from all vault sources.

    Args:
        sources: Optional list of source names to index
                 (default: all).
        vault_paths: Optional override for vault paths.

    Returns:
        Summary dict with counts per source.
    """
    paths = vault_paths or VAULT_PATHS
    target_sources = sources or list(paths.keys())

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(INDEX_DB))
    _ensure_schema(conn)

    total_indexed = 0
    source_stats: list[dict[str, Any]] = []

    for source in target_sources:
        base_path = paths.get(source)
        if not base_path or not base_path.exists():
            source_stats.append({
                "source": source,
                "path": str(base_path) if base_path else None,
                "files": 0,
                "status": "missing",
            })
            continue

        entries = _scan_source(source, base_path)
        for entry in entries:
            _upsert_entry(conn, entry)

        total_indexed += len(entries)
        source_stats.append({
            "source": source,
            "path": str(base_path),
            "files": len(entries),
            "status": "ok",
        })

    # Update meta
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO index_meta (key, value) VALUES (?, ?)",
        ("last_build", now),
    )
    conn.execute(
        "INSERT OR REPLACE INTO index_meta (key, value) VALUES (?, ?)",
        ("total_entries", str(total_indexed)),
    )

    conn.commit()
    conn.close()

    log.info(
        "Library index built: %d entries across %d sources",
        total_indexed, len(target_sources),
    )

    return {
        "status": "completed",
        "index_path": str(INDEX_DB),
        "total_indexed": total_indexed,
        "sources": source_stats,
        "timestamp": now,
    }


# ─── Search ────────────────────────────────────────────────────────

def search(
    query: str,
    source: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Full-text search across the unified library index."""
    if not INDEX_DB.exists():
        return []

    conn = sqlite3.connect(str(INDEX_DB))
    conn.row_factory = sqlite3.Row

    rows: list[sqlite3.Row]
    if query.strip() in {"", "*"}:
        if source:
            sql = """
                SELECT * FROM library_entries
                WHERE source = ?
                ORDER BY modified_at DESC
                LIMIT ?
            """
            rows = conn.execute(sql, (source, limit)).fetchall()
        else:
            sql = """
                SELECT * FROM library_entries
                ORDER BY modified_at DESC
                LIMIT ?
            """
            rows = conn.execute(sql, (limit,)).fetchall()
    elif source:
        sql = """
            SELECT le.* FROM library_entries le
            JOIN library_fts fts ON le.id = fts.id
            WHERE library_fts MATCH ?
              AND le.source = ?
            ORDER BY rank
            LIMIT ?
        """
        rows = conn.execute(sql, (query, source, limit)).fetchall()
    else:
        sql = """
            SELECT le.* FROM library_entries le
            JOIN library_fts fts ON le.id = fts.id
            WHERE library_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        rows = conn.execute(sql, (query, limit)).fetchall()

    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "path": row["path"],
            "filename": row["filename"],
            "source": row["source"],
            "vault_layer": row["vault_layer"],
            "binder": row["binder"],
            "mission": row["mission"],
            "tags": json.loads(row["tags_json"] or "[]"),
            "extension": row["extension"],
            "size": row["size"],
            "modified_at": row["modified_at"],
            "preview": row["preview"],
        })

    conn.close()
    return results


# ─── Stats ─────────────────────────────────────────────────────────

def get_stats() -> dict[str, Any]:
    """Return index statistics."""
    if not INDEX_DB.exists():
        return {
            "status": "not-built",
            "index_path": str(INDEX_DB),
            "total_entries": 0,
        }

    conn = sqlite3.connect(str(INDEX_DB))
    conn.row_factory = sqlite3.Row

    total = conn.execute(
        "SELECT COUNT(*) FROM library_entries",
    ).fetchone()[0]

    by_source: dict[str, int] = {}
    for row in conn.execute(
        "SELECT source, COUNT(*) as cnt FROM library_entries "
        "GROUP BY source ORDER BY cnt DESC",
    ).fetchall():
        by_source[row["source"]] = row["cnt"]

    last_build = conn.execute(
        "SELECT value FROM index_meta WHERE key = 'last_build'",
    ).fetchone()

    conn.close()

    return {
        "status": "ok",
        "index_path": str(INDEX_DB),
        "total_entries": total,
        "by_source": by_source,
        "last_build": last_build[0] if last_build else None,
    }
