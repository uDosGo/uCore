"""AppFlowy Editor Snack — edit AppFlowy documents from the snackbar.

Category: knowledge
Tags: Knowledge, AppFlowy, Editor

Actions:
  list-documents  — list available AppFlowy documents
  open-document   — open a document for editing (param: object_id)
  save-document   — save changes back to AppFlowy DB
  sync-from-vault — import a vault file into AppFlowy
  search          — search AppFlowy documents
"""
from __future__ import annotations

import logging
import sqlite3
from typing import Any, Optional

from app.knowledge.appflowy import (
    _find_database,
    get_document,
    get_document_content,
    list_documents,
    semantic_search,
)
from snackmachine.registry import SnackPlugin, SnackSpec, register_snack

log = logging.getLogger("appflowy-editor-snack")


class AppFlowyEditorSnack(SnackPlugin):
    """Snack plugin for editing AppFlowy documents."""

    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate

    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(
            id="appflowy-editor",
            name="AppFlowy Editor",
            icon="📝",
            kind="multi-action",
            category="knowledge",
            enabled=True,
            actions=[
                "list-documents",
                "open-document",
                "save-document",
                "sync-from-vault",
                "search",
            ],
            metadata={
                "description": "Edit AppFlowy documents from the snackbar",
                "tags": ["Knowledge", "AppFlowy", "Editor"],
                "version": "1.0.0",
            },
        )

    def is_available(self) -> bool:
        """Check if AppFlowy database is accessible."""
        return _find_database() is not None

    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if action == "list-documents":
            return self._list_documents()
        elif action == "open-document":
            return self._open_document(kwargs.get("object_id", ""))
        elif action == "save-document":
            return self._save_document(
                kwargs.get("object_id", ""),
                kwargs.get("content", ""),
            )
        elif action == "sync-from-vault":
            return self._sync_from_vault(kwargs.get("vault_path", ""))
        elif action == "search":
            return self._search(kwargs.get("query", ""))
        return False

    def _list_documents(self) -> list[dict]:
        """List available AppFlowy documents."""
        return list_documents()

    def _open_document(self, object_id: str) -> dict | None:
        """Open a document for editing."""
        if not object_id:
            return {"error": "object_id required"}
        doc = get_document(object_id)
        content = get_document_content(object_id)
        if doc:
            doc["content"] = content
        return doc

    def _save_document(self, object_id: str, content: str) -> dict:
        """Save content back to AppFlowy collab snapshot."""
        if not object_id:
            return {"error": "object_id required"}
        db_path = _find_database()
        if not db_path:
            return {"error": "AppFlowy database not found"}
        try:
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                "UPDATE collab_snapshot SET data = ?, "
                "timestamp = datetime('now') "
                "WHERE object_id = ?",
                (content.encode("utf-8"), object_id),
            )
            conn.commit()
            conn.close()
            return {"success": True, "object_id": object_id}
        except Exception as e:
            return {"error": str(e)}

    def _sync_from_vault(self, vault_path: str) -> dict:
        """Import a vault file into AppFlowy."""
        if not vault_path:
            return {"error": "vault_path required"}
        try:
            from pathlib import Path
            path = Path(vault_path).expanduser()
            if not path.exists():
                return {"error": f"Path not found: {vault_path}"}
            content = path.read_text(encoding="utf-8")
            # Save as a new document in AppFlowy via the snack module
            from app.af_manager.sync import run_import
            from app.af_manager.config import load_config

            cfg = load_config()
            cfg.setdefault("sources", []).append({
                "name": path.stem,
                "local_path": str(path),
                "tags": ["snack-import"],
            })
            result = run_import(cfg)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e)}

    def _search(self, query: str) -> list[dict] | dict:
        """Search AppFlowy documents."""
        if not query:
            return {"error": "query required"}
        return semantic_search(query)


# Register on import
def register(menu_delegate=None):
    """Register the AppFlowy editor snack."""
    plugin = AppFlowyEditorSnack(menu_delegate)
    register_snack(plugin)
    return plugin