"""AppFlowy vault sync engine — import Markdown vaults into AppFlowy DB.

This module handles initial bulk imports and ongoing one-way sync from
file system vaults (like ~/Vault/, ~/Public/, ~/Shared/) into the
central AppFlowy database.

Architecture:
  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
  │ ~/Vault/*.md │───▶│  Sync Engine     │───▶│  AppFlowy DB    │
  │ ~/Public/*   │    │  (this module)   │    │  (SQLite/collab)│
  │ ~/Shared/*   │    │                  │    │                 │
  └─────────────┘    └──────────────────┘    └─────────────────┘
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("ucore.af_manager.sync")

# ─── Frontmatter parsing ───────────────────────────────────────────
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter from Markdown content.

    Returns (frontmatter_dict, body_without_frontmatter).
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    body = content[match.end() :]
    try:
        fm = yaml.safe_load(match.group(1))
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError:
        fm = {}

    return fm, body


# ─── Source Vault Scanner ──────────────────────────────────────────
def scan_vault(
    source_dir: str,
    tags: list[str] | None = None,
    extensions: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Recursively scan a vault directory for importable files.

    Returns a list of file records:
      { path, rel_path, name, ext, tags, frontmatter, body, size, modified }
    """
    if extensions is None:
        extensions = {".md", ".json", ".yaml", ".yml", ".txt", ".csv"}

    base = Path(source_dir).expanduser()
    if not base.exists():
        log.warning("Source vault directory not found: %s", base)
        return []

    records: list[dict[str, Any]] = []
    # Directories to skip
    skip_dirs = {".git", ".obsidian", ".trash", "__pycache__", "node_modules", ".DS_Store"}

    for entry in sorted(base.rglob("*")):
        # Skip hidden files and dirs
        if any(p.startswith(".") and p != "." for p in entry.parts):
            continue
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            continue

        ext = entry.suffix.lower()
        if ext not in extensions:
            continue

        rel_path = str(entry.relative_to(base))
        stat = entry.stat()

        content = entry.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(content) if ext == ".md" else ({}, content)

        entry_tags = list(tags or [])
        # Add folder-based tags
        folder_parts = list(entry.relative_to(base).parent.parts)
        entry_tags.extend(
            t for t in folder_parts if t not in {".", ""} and not t.startswith("_")
        )

        # Merge frontmatter tags
        fm_tags = fm.get("tags", [])
        if isinstance(fm_tags, str):
            fm_tags = [fm_tags]
        entry_tags.extend(t for t in fm_tags if t not in entry_tags)

        records.append({
            "path": str(entry),
            "rel_path": rel_path,
            "name": entry.stem,
            "ext": ext,
            "tags": entry_tags,
            "frontmatter": fm,
            "body": body[:100000],  # cap at 100KB for body
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })

    log.info("Scanned %s: %d files found", source_dir, len(records))
    return records


# ─── AppFlowy DB Inserter ──────────────────────────────────────────
def import_file_to_appflowy(
    db_path: str,
    record: dict[str, Any],
    source_name: str,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """Import a single file record into the AppFlowy database.

    This writes metadata into the collab_snapshot table so it appears
    in the AppFlowy document list and becomes searchable.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Generate a deterministic object_id based on source + relative path
    object_id = f"import_{source_name}_{record['rel_path']}".replace("/", "_").replace("\\", "_")
    object_id = re.sub(r"[^a-zA-Z0-9_-]", "_", object_id)

    title = record.get("frontmatter", {}).get("title") or record["name"]
    tags_json = json.dumps(record["tags"])

    now = datetime.now(timezone.utc).isoformat()

    # Check if already exists
    cur.execute(
        "SELECT object_id FROM collab_snapshot WHERE object_id = ?",
        (object_id,),
    )
    exists = cur.fetchone()

    body = record["body"]
    # Store frontmatter summary as data blob
    blob_data = json.dumps(
        {
            "title": title,
            "source": source_name,
            "rel_path": record["rel_path"],
            "tags": record["tags"],
            "frontmatter": record.get("frontmatter", {}),
            "body_preview": body[:500],
        }
    ).encode("utf-8")

    if exists:
        cur.execute(
            """UPDATE collab_snapshot
               SET title = ?, data = ?, desc = ?, timestamp = ?
               WHERE object_id = ?""",
            (title, blob_data, tags_json, now, object_id),
        )
        action = "updated"
    else:
        cur.execute(
            """INSERT INTO collab_snapshot
               (object_id, title, collab_type, desc, timestamp, data)
               VALUES (?, ?, 'document', ?, ?, ?)""",
            (object_id, title, tags_json, now, blob_data),
        )
        action = "created"

    conn.commit()
    conn.close()

    return {"object_id": object_id, "action": action, "title": title, "tags": record["tags"]}


# ─── Bulk Import ───────────────────────────────────────────────────
def run_import(
    config: dict[str, Any],
    progress_callback=None,
) -> dict[str, Any]:
    """Run a full import from all configured source vaults into AppFlowy.

    Returns a summary dict with counts per source.
    """
    from .config import get_source_dirs, get_appflowy_data_dir

    data_dir = get_appflowy_data_dir(config)
    sources = get_source_dirs(config)

    # Find the database
    db_paths = list(Path(data_dir).expanduser().rglob("flowy-database.db"))
    if not db_paths:
        raise FileNotFoundError(f"No AppFlowy database found in {data_dir}")

    # Use the local workspace DB (prefer the first one)
    db_path = str(db_paths[0])
    log.info("Using AppFlowy database: %s", db_path)

    total_imported = 0
    total_updated = 0
    total_errors = 0
    source_results = []

    for source in sources:
        if not source.get("enabled", True):
            log.info("Source disabled, skipping: %s", source["name"])
            continue

        local_path = source["local_path"]
        source_name = source["name"]
        tags = source.get("tags", [])
        organization = source.get("organization", "folder")

        log.info("Importing source: %s from %s", source_name, local_path)

        if progress_callback:
            progress_callback(f"Scanning {source_name}...", 0)

        records = scan_vault(local_path, tags=tags)
        if not records:
            log.info("No files found in %s", local_path)
            source_results.append({"source": source_name, "files": 0, "created": 0, "updated": 0})
            continue

        created = 0
        updated = 0
        errors = 0

        for i, record in enumerate(records):
            try:
                result = import_file_to_appflowy(db_path, record, source_name)
                if result["action"] == "created":
                    created += 1
                else:
                    updated += 1

                if progress_callback:
                    pct = int((i + 1) / len(records) * 100)
                    progress_callback(f"Importing {source_name}: {record['name']}", pct)
            except Exception as e:
                errors += 1
                log.error("Failed to import %s: %s", record["path"], e)

        total_imported += created
        total_updated += updated
        total_errors += errors
        source_results.append({
            "source": source_name,
            "files": len(records),
            "created": created,
            "updated": updated,
            "errors": errors,
        })

    summary = {
        "status": "completed",
        "db_path": db_path,
        "sources": source_results,
        "total_imported": total_imported,
        "total_updated": total_updated,
        "total_errors": total_errors,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    log.info("Import complete: %d created, %d updated, %d errors", total_imported, total_updated, total_errors)
    return summary
