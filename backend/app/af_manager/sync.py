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
import re
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger("ucore.af_manager.sync")

APPFLOWY_DB_NAME = "flowy-database.db"

# ─── Frontmatter parsing ───────────────────────────────────────────
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter from Markdown content.

    Returns (frontmatter_dict, body_without_frontmatter).
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    body = content[match.end():]
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
        entry_tags.extend(
            str(t)
            for t in fm_tags
            if str(t) not in entry_tags
        )

        records.append({
            "path": str(entry),
            "rel_path": rel_path,
            "name": entry.stem,
            "ext": ext,
            "tags": entry_tags,
            "frontmatter": fm,
            "body": body[:100000],  # cap at 100KB for body
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
        })

    log.info("Scanned %s: %d files found", source_dir, len(records))
    return records


# ─── AppFlowy DB Inserter ──────────────────────────────────────────
def import_file_to_appflowy(
    db_path: str,
    record: dict[str, Any],
    source_name: str,
    workspace_id: str | None = None,
    ingest_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Import a single file record into the AppFlowy database.

    This writes metadata into the collab_snapshot table so it appears
    in the AppFlowy document list and becomes searchable.
    """
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=10000")
            cur = conn.cursor()
            break
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower() or attempt == max_attempts:
                raise
            time.sleep(0.25 * attempt)

    # Generate a deterministic object_id based on source + relative path
    object_id = f"import_{source_name}_{record['rel_path']}".replace("/", "_").replace("\\", "_")
    object_id = re.sub(r"[^a-zA-Z0-9_-]", "_", object_id)
    row_id = object_id

    title = record.get("frontmatter", {}).get("title") or record["name"]
    clean_tags = [str(tag) for tag in record.get("tags", [])]
    tags_json = json.dumps(clean_tags, default=str)
    columns = {
        str(row[1])
        for row in cur.execute("PRAGMA table_info(collab_snapshot)").fetchall()
    }
    has_id_col = "id" in columns

    now = datetime.now(UTC).isoformat()

    # Check if already exists
    cur.execute(
        "SELECT object_id FROM collab_snapshot WHERE object_id = ?",
        (object_id,),
    )
    exists = cur.fetchone()

    body = record["body"]
    # Store frontmatter summary as data blob
    metadata: dict[str, Any] = {}
    frontmatter = record.get("frontmatter") or {}
    if isinstance(frontmatter, dict):
        mission = str(frontmatter.get("mission") or "").strip()
        task = str(frontmatter.get("task") or "").strip()
        binder = str(frontmatter.get("binder") or "").strip()
        if mission:
            metadata["mission"] = mission
        if task:
            metadata["task"] = task
        if binder:
            metadata["binder"] = binder

    payload = {
        "title": title,
        "source": source_name,
        "workspace_id": workspace_id,
        "rel_path": record["rel_path"],
        "tags": clean_tags,
        "frontmatter": frontmatter,
        "body_preview": body[:500],
    }
    if metadata:
        payload["metadata"] = metadata
    if ingest_context:
        payload["ingest_context"] = {
            "mission": ingest_context.get("mission"),
            "binder": ingest_context.get("binder"),
        }

    blob_data = json.dumps(payload, default=str).encode("utf-8")

    if exists:
        if has_id_col:
            cur.execute(
                """UPDATE collab_snapshot
                   SET id = ?, title = ?, data = ?, desc = ?, timestamp = ?
                   WHERE object_id = ?""",
                (row_id, title, blob_data, tags_json, now, object_id),
            )
        else:
            cur.execute(
                """UPDATE collab_snapshot
                   SET title = ?, data = ?, desc = ?, timestamp = ?
                   WHERE object_id = ?""",
                (title, blob_data, tags_json, now, object_id),
            )
        action = "updated"
    else:
        if has_id_col:
            cur.execute(
                """INSERT INTO collab_snapshot
                   (id, object_id, title, collab_type, desc, timestamp, data)
                   VALUES (?, ?, ?, 'document', ?, ?, ?)""",
                (row_id, object_id, title, tags_json, now, blob_data),
            )
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

    _upsert_local_index(
        db_path=db_path,
        object_id=object_id,
        workspace_id=workspace_id,
        source_name=source_name,
        rel_path=record["rel_path"],
        title=title,
        body=body,
        tags=record["tags"],
        modified=record.get("modified"),
    )

    return {
        "object_id": object_id,
        "action": action,
        "title": title,
        "tags": clean_tags,
        "workspace_id": workspace_id,
    }


def _ensure_local_index_tables(conn: sqlite3.Connection) -> None:
    """Create uCore sidecar index tables inside a workspace DB when missing."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ucore_vault_index (
            object_id TEXT PRIMARY KEY,
            workspace_id TEXT,
            source_name TEXT NOT NULL,
            rel_path TEXT NOT NULL,
            title TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            body TEXT,
            modified TEXT,
            indexed_at TEXT NOT NULL
        )
        """,
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS ucore_vault_index_fts
        USING fts5(
            object_id UNINDEXED,
            title,
            body,
            tags,
            source_name,
            rel_path
        )
        """,
    )


def _upsert_local_index(
    *,
    db_path: str,
    object_id: str,
    workspace_id: str | None,
    source_name: str,
    rel_path: str,
    title: str,
    body: str,
    tags: list[str],
    modified: str | None,
) -> None:
    """Upsert local index rows and FTS records for imported vault content."""
    try:
        conn = sqlite3.connect(db_path)
        _ensure_local_index_tables(conn)
        clean_tags = [str(tag) for tag in tags]
        tags_json = json.dumps(clean_tags, default=str)
        tags_text = " ".join(clean_tags)
        now = datetime.now(UTC).isoformat()

        conn.execute(
            """
            INSERT INTO ucore_vault_index
            (object_id, workspace_id, source_name, rel_path, title, tags_json, body, modified, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(object_id) DO UPDATE SET
              workspace_id = excluded.workspace_id,
              source_name = excluded.source_name,
              rel_path = excluded.rel_path,
              title = excluded.title,
              tags_json = excluded.tags_json,
              body = excluded.body,
              modified = excluded.modified,
              indexed_at = excluded.indexed_at
            """,
            (
                object_id,
                workspace_id,
                source_name,
                rel_path,
                title,
                tags_json,
                body,
                modified,
                now,
            ),
        )
        conn.execute(
            "DELETE FROM ucore_vault_index_fts WHERE object_id = ?",
            (object_id,),
        )
        conn.execute(
            """
            INSERT INTO ucore_vault_index_fts
            (object_id, title, body, tags, source_name, rel_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (object_id, title, body, tags_text, source_name, rel_path),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        log.warning("Skipping local index update for %s: %s", object_id, exc)


def _discover_workspace_catalog(data_dir: str) -> dict[str, dict[str, str]]:
    """Discover workspace IDs, names, and DB paths from AppFlowy data dirs."""
    root = Path(data_dir).expanduser()
    candidates = [
        root / "data",
        root / "data_beta.appflowy.cloud",
    ]

    catalog: dict[str, dict[str, str]] = {}
    for base in candidates:
        if not base.exists():
            continue
        for sub in sorted(base.iterdir()):
            if not sub.is_dir():
                continue
            db_path = sub / APPFLOWY_DB_NAME
            if not db_path.exists():
                continue

            workspace_id = sub.name
            workspace_name = sub.name
            try:
                conn = sqlite3.connect(str(db_path))
                cur = conn.execute(
                    "SELECT id, name FROM user_workspace_table LIMIT 1",
                )
                row = cur.fetchone()
                conn.close()
                if row:
                    workspace_id = str(row[0] or workspace_id)
                    workspace_name = str(row[1] or workspace_name)
            except Exception:
                # Keep folder-name fallback when table/schema is unavailable.
                pass

            entry = {
                "id": workspace_id,
                "name": workspace_name,
                "db_path": str(db_path),
            }
            catalog[workspace_id] = entry
            catalog[workspace_name.lower()] = entry

    return catalog


def _select_workspace_entry(
    source: dict[str, Any],
    catalog: dict[str, dict[str, str]],
    default_workspace: str,
    fallback_db_path: str,
) -> dict[str, str]:
    """Resolve target workspace DB for a source using id/name/default hints."""
    source_workspace_id = str(source.get("workspace_id") or "").strip()
    source_workspace_name = str(source.get("workspace") or "").strip()

    if source_workspace_id and source_workspace_id in catalog:
        return catalog[source_workspace_id]

    if source_workspace_name:
        key = source_workspace_name.lower()
        if key in catalog:
            return catalog[key]
        if source_workspace_name in catalog:
            return catalog[source_workspace_name]

    if default_workspace:
        default_key = default_workspace.lower()
        if default_workspace in catalog:
            return catalog[default_workspace]
        if default_key in catalog:
            return catalog[default_key]

    source_name = str(source.get("name") or "vault").strip() or "vault"
    virtual_id = "vault-" + re.sub(r"[^a-z0-9]+", "-", source_name.lower()).strip("-")
    return {
        "id": virtual_id,
        "name": source_name,
        "db_path": fallback_db_path,
    }


def _resolve_source_path(local_path: str, source_name: str) -> str:
    """Resolve source path using compatibility fallbacks for legacy layouts."""
    expanded = Path(local_path).expanduser()
    if expanded.exists():
        return str(expanded)

    # Only apply compatibility fallbacks for home-relative paths.
    if not local_path.startswith("~"):
        return str(expanded)

    home = Path.home()
    candidates: list[Path] = []
    name = source_name.lower()
    if "public" in name:
        candidates.extend([home / "Vault" / "Public", home / "Public"])
    elif "shared" in name:
        candidates.extend([home / "Vault" / "Shared", home / "Shared"])
    elif "vault" in name:
        candidates.extend([home / "Vault"])

    for candidate in candidates:
        if candidate.exists():
            log.info(
                "Using fallback path for %s: %s",
                source_name,
                candidate,
            )
            return str(candidate)

    return str(expanded)


# ─── Bulk Import ───────────────────────────────────────────────────
def run_import(
    config: dict[str, Any],
    progress_callback=None,
    ingest_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a full import from all configured source vaults into AppFlowy.

    Returns a summary dict with counts per source.
    """
    from .config import get_appflowy_data_dir, get_source_dirs

    data_dir = get_appflowy_data_dir(config)
    sources = get_source_dirs(config)

    appflowy_cfg = config.get("appflowy", {})
    default_workspace = str(
        appflowy_cfg.get("default_workspace")
        or appflowy_cfg.get("default_workspace_id")
        or "",
    ).strip()

    # Find the database
    db_paths = list(Path(data_dir).expanduser().rglob("flowy-database.db"))
    if not db_paths:
        raise FileNotFoundError(f"No AppFlowy database found in {data_dir}")

    # Use the local workspace DB (prefer the first one)
    db_path = str(db_paths[0])
    log.info("Using AppFlowy database: %s", db_path)

    workspace_catalog = _discover_workspace_catalog(data_dir)

    ingest_context = ingest_context or {}
    mission_context = str(ingest_context.get("mission") or "").strip()
    binder_context = str(ingest_context.get("binder") or "").strip()
    requested_files_raw = ingest_context.get("files")
    requested_files: set[str] = set()
    if isinstance(requested_files_raw, list):
        requested_files = {
            str(item).strip().lower()
            for item in requested_files_raw
            if str(item).strip()
        }

    total_imported = 0
    total_updated = 0
    total_errors = 0
    source_results = []

    for source in sources:
        if not source.get("enabled", True):
            log.info("Source disabled, skipping: %s", source["name"])
            continue

        source_name = source["name"]
        local_path = _resolve_source_path(source["local_path"], source_name)
        tags = source.get("tags", [])

        workspace_entry = _select_workspace_entry(
            source=source,
            catalog=workspace_catalog,
            default_workspace=default_workspace,
            fallback_db_path=db_path,
        )
        target_db_path = workspace_entry["db_path"]
        target_workspace_id = workspace_entry.get("id") or None
        target_workspace_name = workspace_entry.get("name") or "default"

        log.info(
            "Importing source: %s from %s into workspace=%s (%s)",
            source_name,
            local_path,
            target_workspace_name,
            target_workspace_id or "default",
        )

        if progress_callback:
            progress_callback(f"Scanning {source_name}...", 0)

        records = scan_vault(local_path, tags=tags)
        if requested_files:
            records = [
                record
                for record in records
                if (
                    Path(str(record.get("rel_path") or "")).name.lower()
                    in requested_files
                    or str(record.get("rel_path") or "").lower() in requested_files
                )
            ]
        if not records:
            log.info("No files found in %s", local_path)
            source_results.append({"source": source_name, "files": 0, "created": 0, "updated": 0})
            continue

        created = 0
        updated = 0
        errors = 0

        for i, record in enumerate(records):
            try:
                enriched_record = dict(record)
                enriched_frontmatter = dict(record.get("frontmatter") or {})
                enriched_tags = list(record.get("tags") or [])
                if mission_context and not str(enriched_frontmatter.get("mission") or "").strip():
                    enriched_frontmatter["mission"] = mission_context
                if binder_context and not str(enriched_frontmatter.get("binder") or "").strip():
                    enriched_frontmatter["binder"] = binder_context
                if mission_context:
                    mission_tag = f"mission:{mission_context}"
                    if mission_tag not in enriched_tags:
                        enriched_tags.append(mission_tag)
                if binder_context:
                    binder_tag = f"binder:{binder_context}"
                    if binder_tag not in enriched_tags:
                        enriched_tags.append(binder_tag)

                enriched_record["frontmatter"] = enriched_frontmatter
                enriched_record["tags"] = enriched_tags

                result = import_file_to_appflowy(
                    db_path=target_db_path,
                    record=enriched_record,
                    source_name=source_name,
                    workspace_id=target_workspace_id,
                    ingest_context={
                        "mission": mission_context,
                        "binder": binder_context,
                    },
                )
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
            "workspace_id": target_workspace_id,
            "workspace": target_workspace_name,
            "db_path": target_db_path,
            "files": len(records),
            "created": created,
            "updated": updated,
            "errors": errors,
        })

    summary = {
        "status": "completed",
        "db_path": db_path,
        "ingest_context": {
            "mission": mission_context,
            "binder": binder_context,
            "file_count": len(requested_files),
        },
        "workspace_count": len({
            item.get("workspace_id") or item.get("db_path")
            for item in source_results
        }),
        "sources": source_results,
        "total_imported": total_imported,
        "total_updated": total_updated,
        "total_errors": total_errors,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    log.info("Import complete: %d created, %d updated, %d errors", total_imported, total_updated, total_errors)
    return summary


def _source_index_stats(
    db_path: str,
    source_name: str,
    workspace_id: str | None,
) -> dict[str, Any]:
    """Return indexed count and last indexed timestamp for a source."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        if workspace_id:
            row = conn.execute(
                """
                  SELECT COUNT(*) AS indexed_count,
                      MAX(indexed_at) AS last_indexed_at
                FROM ucore_vault_index
                WHERE source_name = ? AND workspace_id = ?
                """,
                (source_name, workspace_id),
            ).fetchone()
        else:
            row = conn.execute(
                """
                  SELECT COUNT(*) AS indexed_count,
                      MAX(indexed_at) AS last_indexed_at
                FROM ucore_vault_index
                WHERE source_name = ?
                """,
                (source_name,),
            ).fetchone()
        conn.close()
        if not row:
            return {"indexed_count": 0, "last_indexed_at": None}
        return {
            "indexed_count": int(row["indexed_count"] or 0),
            "last_indexed_at": row["last_indexed_at"],
        }
    except Exception:
        return {"indexed_count": 0, "last_indexed_at": None}


def get_index_coverage(config: dict[str, Any]) -> dict[str, Any]:
    """Compute per-source import/index coverage for vault sources."""
    from .config import get_appflowy_data_dir, get_source_dirs

    data_dir = get_appflowy_data_dir(config)
    sources = get_source_dirs(config)
    appflowy_cfg = config.get("appflowy", {})
    default_workspace = str(
        appflowy_cfg.get("default_workspace")
        or appflowy_cfg.get("default_workspace_id")
        or "",
    ).strip()

    db_paths = list(Path(data_dir).expanduser().rglob(APPFLOWY_DB_NAME))
    if not db_paths:
        return {
            "status": "missing-db",
            "sources": [],
            "source_count": 0,
            "indexed_total": 0,
            "expected_total": 0,
            "coverage_pct": 0,
        }

    default_db_path = str(db_paths[0])
    workspace_catalog = _discover_workspace_catalog(data_dir)

    results: list[dict[str, Any]] = []
    indexed_total = 0
    expected_total = 0
    for source in sources:
        if not source.get("enabled", True):
            continue

        source_name = source["name"]
        local_path = _resolve_source_path(source["local_path"], source_name)
        tags = source.get("tags", [])
        workspace_entry = _select_workspace_entry(
            source=source,
            catalog=workspace_catalog,
            default_workspace=default_workspace,
            fallback_db_path=default_db_path,
        )

        expected_count = len(scan_vault(local_path, tags=tags))
        indexed = _source_index_stats(
            db_path=workspace_entry["db_path"],
            source_name=source_name,
            workspace_id=workspace_entry.get("id") or None,
        )
        indexed_count = int(indexed["indexed_count"])
        expected_total += expected_count
        indexed_total += indexed_count

        coverage_pct = (
            int((indexed_count / expected_count) * 100)
            if expected_count
            else 100
        )
        results.append(
            {
                "source": source_name,
                "workspace": workspace_entry.get("name") or "default",
                "workspace_id": workspace_entry.get("id") or None,
                "db_path": workspace_entry["db_path"],
                "local_path": local_path,
                "expected_count": expected_count,
                "indexed_count": indexed_count,
                "coverage_pct": coverage_pct,
                "last_indexed_at": indexed.get("last_indexed_at"),
            },
        )

    total_pct = (
        int((indexed_total / expected_total) * 100)
        if expected_total
        else 100
    )
    return {
        "status": "ok",
        "source_count": len(results),
        "sources": results,
        "indexed_total": indexed_total,
        "expected_total": expected_total,
        "coverage_pct": total_pct,
        "timestamp": datetime.now(UTC).isoformat(),
    }
