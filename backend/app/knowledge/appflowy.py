"""AppFlowy database connector — reads local AppFlowy data.

AppFlowy stores data in:
  ~/Library/Application Support/com.appflowy.appflowy.flutter/
    data/                        # local workspace
    data_beta.appflowy.cloud/    # cloud-synced workspace
      {workspace_id}/flowy-database.db   # collab snapshots
      vector.db                  # vector embeddings (768d, vec0)
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("ucore.knowledge.appflowy")

APPFLOWY_DIR = Path.home() / "Library/Application Support/com.appflowy.appflowy.flutter"
CLOUD_DIR = APPFLOWY_DIR / "data_beta.appflowy.cloud"
LOCAL_DIR = APPFLOWY_DIR / "data"

WORKSPACE_TYPES = {
    "cloud": CLOUD_DIR,
    "local": LOCAL_DIR,
}


def _find_database(workspace_id: str | None = None) -> Optional[Path]:
    """Find the AppFlowy database path."""
    for name, base_dir in WORKSPACE_TYPES.items():
        if not base_dir.exists():
            continue
        if workspace_id:
            candidate = base_dir / workspace_id / "flowy-database.db"
            if candidate.exists():
                return candidate
        else:
            # Return the workspace in use
            for sub in sorted(base_dir.iterdir()):
                if sub.is_dir():
                    candidate = sub / "flowy-database.db"
                    if candidate.exists():
                        return candidate
    return None


def _get_db() -> Optional[sqlite3.Connection]:
    path = _find_database()
    if not path:
        return None
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def list_workspaces() -> list[dict]:
    """List all AppFlowy workspaces."""
    results = []
    for source, base_dir in WORKSPACE_TYPES.items():
        if not base_dir.exists():
            continue
        for sub in sorted(base_dir.iterdir()):
            if sub.is_dir() and (sub / "flowy-database.db").exists():
                db_path = sub / "flowy-database.db"
                try:
                    conn = sqlite3.connect(str(db_path))
                    cur = conn.execute(
                        "SELECT id, name, icon, member_count FROM user_workspace_table LIMIT 10"
                    )
                    for row in cur.fetchall():
                        results.append({
                            "id": row[0],
                            "name": row[1],
                            "icon": row[2],
                            "member_count": row[3],
                            "source": source,
                        })
                    conn.close()
                except Exception as e:
                    log.warning("Error reading workspace from %s: %s", sub, e)
    return results


def list_documents(workspace_id: str | None = None) -> list[dict]:
    """List documents (collab snapshots) from AppFlowy."""
    db_path = _find_database(workspace_id)
    if not db_path:
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT object_id, title, collab_type, timestamp FROM collab_snapshot "
        "WHERE collab_type IN ('document', 'database', 'folder') "
        "ORDER BY timestamp DESC LIMIT 100"
    )
    docs = []
    for row in cur.fetchall():
        docs.append({
            "id": row["object_id"],
            "title": row["title"],
            "type": row["collab_type"],
            "updated_at": row["timestamp"],
        })
    conn.close()
    return docs


def get_document(object_id: str, workspace_id: str | None = None) -> Optional[dict]:
    """Get a single document's content from AppFlowy."""
    db_path = _find_database(workspace_id)
    if not db_path:
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT object_id, title, collab_type, desc, timestamp, data "
        "FROM collab_snapshot WHERE object_id = ? LIMIT 1",
        (object_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["object_id"],
        "title": row["title"],
        "type": row["collab_type"],
        "description": row["desc"],
        "updated_at": row["timestamp"],
        "data_size": len(row["data"]) if row["data"] else 0,
    }


def semantic_search(query: str, workspace_id: str | None = None, limit: int = 10) -> list[dict]:
    """Search AppFlowy vector database using text matching.

    Note: Full vector search requires an embedding model.
    This uses text-based fallback on metadata/content tables.
    """
    db_path = _find_database(workspace_id)
    if not db_path:
        return []
    
    vec_path = db_path.parent.parent / "vector.db"
    if not vec_path.exists():
        return []
    
    conn = sqlite3.connect(str(vec_path))
    conn.row_factory = sqlite3.Row
    
    # Text-based search on metadata text tables
    results = []
    search_term = f"%{query}%"
    
    for i in range(5):
        table = f"af_collab_embeddings_2560_metadatatext0{i}"
        try:
            cur = conn.execute(
                f"SELECT rowid, data FROM {table} WHERE data LIKE ? LIMIT ?",
                (search_term, limit),
            )
            for row in cur.fetchall():
                results.append({
                    "rowid": row["rowid"],
                    "content": row["data"][:500],
                    "source": table,
                })
        except Exception:
            pass
    
    conn.close()
    return results[:limit]


def get_document_content(object_id: str, workspace_id: str | None = None) -> Optional[str]:
    """Extract text content from a collab snapshot blob.
    
    AppFlowy stores content as protobuf (protobuf) binary data.
    Returns a best-effort text extraction.
    """
    doc = get_document(object_id, workspace_id)
    if not doc:
        return None
    
    db_path = _find_database(workspace_id)
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("SELECT data FROM collab_snapshot WHERE object_id = ?", (object_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row or not row[0]:
        return None
    
    data = row[0]
    
    # Try to extract UTF-8 strings from binary protobuf
    try:
        text = data.decode("utf-8", errors="ignore")
        # Strip non-printable chars, keep reasonable text
        import re
        text = re.sub(r'[^\x20-\x7E\x0A\x0D\u00A0-\u024F\u0400-\u04FF\u4E00-\u9FFF]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:10000] if text else "(empty content)"
    except Exception:
        return "(binary content — rendering not supported)"
