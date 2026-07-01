from __future__ import annotations

import sqlite3
from pathlib import Path

from app.af_manager.sync import import_file_to_appflowy, run_import


def _init_workspace_db(
    db_path: Path,
    workspace_id: str,
    workspace_name: str,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_workspace_table (
            id TEXT,
            name TEXT,
            icon TEXT,
            member_count INTEGER
        )
        """,
    )
    conn.execute("DELETE FROM user_workspace_table")
    conn.execute(
        (
            "INSERT INTO user_workspace_table "
            "(id, name, icon, member_count) VALUES (?, ?, '', 1)"
        ),
        (workspace_id, workspace_name),
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS collab_snapshot (
            object_id TEXT PRIMARY KEY,
            title TEXT,
            collab_type TEXT,
            desc TEXT,
            timestamp TEXT,
            data BLOB
        )
        """,
    )
    conn.commit()
    conn.close()


def test_import_file_to_appflowy_updates_local_index(tmp_path: Path):
    db_path = tmp_path / "ws_a" / "flowy-database.db"
    _init_workspace_db(db_path, "ws_a", "Workspace A")

    record = {
        "rel_path": "projects/alpha.md",
        "name": "alpha",
        "frontmatter": {"title": "Alpha Note"},
        "body": "alpha body text",
        "tags": ["projects", "alpha"],
        "modified": "2026-06-22T00:00:00Z",
    }

    result = import_file_to_appflowy(
        db_path=str(db_path),
        record=record,
        source_name="Global Vault",
        workspace_id="ws_a",
    )

    assert result["action"] in {"created", "updated"}

    conn = sqlite3.connect(str(db_path))
    idx_count = conn.execute(
        "SELECT COUNT(*) FROM ucore_vault_index",
    ).fetchone()[0]
    fts_count = conn.execute(
        "SELECT COUNT(*) FROM ucore_vault_index_fts",
    ).fetchone()[0]
    conn.close()

    assert idx_count == 1
    assert fts_count == 1


def test_run_import_routes_source_to_named_workspace(
    tmp_path: Path,
    monkeypatch,
):
    data_dir = tmp_path / "appflowy"
    db_a = data_dir / "data" / "ws_a" / "flowy-database.db"
    db_b = data_dir / "data" / "ws_b" / "flowy-database.db"

    _init_workspace_db(db_a, "ws_a", "Global Vault")
    _init_workspace_db(db_b, "ws_b", "Public Vault")

    def fake_scan_vault(source_dir: str, tags=None, extensions=None):
        return [
            {
                "rel_path": "public/post.md",
                "name": "post",
                "frontmatter": {"title": "Public Post"},
                "body": "public body",
                "tags": ["public"],
                "modified": "2026-06-22T00:00:00Z",
                "path": str(Path(source_dir) / "public/post.md"),
            },
        ]

    monkeypatch.setattr("app.af_manager.sync.scan_vault", fake_scan_vault)

    config = {
        "appflowy": {
            "data_dir": str(data_dir),
            "default_workspace": "Global Vault",
        },
        "sources": [
            {
                "name": "Public Vault",
                "local_path": str(tmp_path / "vault" / "public"),
                "tags": ["public"],
                "workspace": "Public Vault",
                "enabled": True,
            },
        ],
    }

    summary = run_import(config)

    assert summary["total_imported"] == 1
    assert summary["workspace_count"] == 1
    assert summary["sources"][0]["workspace"] == "Public Vault"
    assert summary["sources"][0]["workspace_id"] == "ws_b"

    conn_a = sqlite3.connect(str(db_a))
    count_a = conn_a.execute(
        "SELECT COUNT(*) FROM collab_snapshot",
    ).fetchone()[0]
    conn_a.close()

    conn_b = sqlite3.connect(str(db_b))
    count_b = conn_b.execute(
        "SELECT COUNT(*) FROM collab_snapshot",
    ).fetchone()[0]
    conn_b.close()

    assert count_a == 0
    assert count_b == 1
