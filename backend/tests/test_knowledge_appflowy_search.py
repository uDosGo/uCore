from __future__ import annotations

import sqlite3
from pathlib import Path

from app.knowledge import appflowy


def test_semantic_search_falls_back_to_local_index(
    tmp_path: Path,
    monkeypatch,
):
    db_path = tmp_path / "ws_x" / "flowy-database.db"
    db_path.parent.mkdir(parents=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE VIRTUAL TABLE ucore_vault_index_fts
        USING fts5(
            object_id UNINDEXED,
            title,
            body,
            tags,
            source_name,
            rel_path
        )
        """
    )
    conn.execute(
        """
        INSERT INTO ucore_vault_index_fts
        (object_id, title, body, tags, source_name, rel_path)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "import_Global_Vault_notes_hello_md",
            "Hello Note",
            "hello mission content",
            "hello mission",
            "Global Vault",
            "notes/hello.md",
        ),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        "app.knowledge.appflowy._find_database",
        lambda workspace_id=None: db_path,
    )

    results = appflowy.semantic_search("hello", workspace_id="ws_x", limit=5)

    assert len(results) == 1
    assert results[0]["title"] == "Hello Note"
    assert results[0]["source"].startswith("ucore_vault_index:")


def test_list_documents_reads_workspace_metadata(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "ws_meta" / "flowy-database.db"
    db_path.parent.mkdir(parents=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE collab_snapshot (
            object_id TEXT,
            title TEXT,
            collab_type TEXT,
            desc TEXT,
            timestamp TEXT,
            data BLOB
        )
        """
    )
    conn.execute(
        """
        INSERT INTO collab_snapshot
        (object_id, title, collab_type, desc, timestamp, data)
        VALUES (?, ?, 'document', '', '2026-06-22T00:00:00Z', ?)
        """,
        (
            "import_Global_Vault_notes_alpha_md",
            "Alpha",
            (
                b'{"workspace_id":"vault-global-vault",'
                b'"source":"Global Vault",'
                b'"rel_path":"notes/alpha.md"}'
            ),
        ),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        "app.knowledge.appflowy._find_database",
        lambda workspace_id=None: db_path,
    )

    docs = appflowy.list_documents(workspace_id="ws_meta")

    assert len(docs) == 1
    assert docs[0]["workspace_id"] == "vault-global-vault"
    assert docs[0]["source"] == "Global Vault"
    assert docs[0]["rel_path"] == "notes/alpha.md"
