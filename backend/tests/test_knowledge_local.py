"""Tests for local-first AppFlowy SQLite integration helpers."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.knowledge.local_first import (
    discover_databases,
    export_to_vault,
    list_tables,
    run_query,
    spool_event,
)


def test_discover_databases_none(tmp_path: Path, monkeypatch):
    """When no AppFlowy databases exist, returns empty dict."""
    monkeypatch.setattr("app.knowledge.local_first.Path.home", lambda: tmp_path)
    result = discover_databases()
    assert result == {}


def test_discover_databases_local_first(tmp_path: Path, monkeypatch):
    """Discover AppFlowy/data/database.sqlite."""
    monkeypatch.setattr("app.knowledge.local_first.Path.home", lambda: tmp_path)
    db_path = tmp_path / "AppFlowy/data/database.sqlite"
    db_path.parent.mkdir(parents=True)
    db_path.write_text("", encoding="utf-8")

    chat_path = tmp_path / "AppFlowy/data/chat.sqlite"
    chat_path.write_text("", encoding="utf-8")

    result = discover_databases()
    assert "database" in result
    assert str(db_path) == result["database"]
    assert "chat" in result


def test_list_tables(tmp_path: Path, monkeypatch):
    """list_tables with an in-memory SQLite database."""
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    conn.execute("CREATE TABLE tasks (id INTEGER, title TEXT)")
    conn.commit()
    conn.close()

    tables = list_tables(str(db_file))
    assert "users" in tables
    assert "tasks" in tables
    assert len(tables) == 2


def test_run_query_select(tmp_path: Path):
    """run_query executes SELECT and returns rows."""
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO items VALUES (1, 'first')")
    conn.execute("INSERT INTO items VALUES (2, 'second')")
    conn.commit()
    conn.close()

    result = run_query(str(db_file), "SELECT * FROM items ORDER BY id")
    assert result["write"] is False
    assert result["count"] == 2
    assert result["rows"][0]["name"] == "first"


def test_run_query_select_with_params(tmp_path: Path):
    """run_query handles query parameters safely."""
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO items VALUES (1, 'first')")
    conn.commit()
    conn.close()

    result = run_query(str(db_file), "SELECT * FROM items WHERE id = ?", params=[1])
    assert result["count"] == 1


def test_run_query_rejects_unsafe_sql(tmp_path: Path):
    """run_query rejects DROP/ALTER statements."""
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE items (id INTEGER)")
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="SELECT"):
        run_query(str(db_file), "DROP TABLE items")


def test_run_query_write(tmp_path: Path):
    """run_query in write mode executes and creates backup."""
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.commit()
    conn.close()

    result = run_query(
        str(db_file),
        "DELETE FROM items",
        write=True,
    )
    assert result["write"] is True
    assert "backup" in result
    assert Path(result["backup"]).exists()


def test_run_query_write_rejects_unsafe(tmp_path: Path):
    """run_query write rejects SELECT statements."""
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE items (id INTEGER)")
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="INSERT"):
        run_query(str(db_file), "SELECT * FROM items", write=True)


def test_spool_event(tmp_path: Path, monkeypatch):
    """spool_event appends JSONL to replies file."""
    monkeypatch.setattr("app.knowledge.local_first.SPOOL_PATH", tmp_path / "replies.jsonl")
    spool_event({"type": "test", "status": "ok"})
    spool_event({"type": "test2", "status": "done"})

    lines = (tmp_path / "replies.jsonl").read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    data1 = json.loads(lines[0])
    assert data1["type"] == "test"
    assert data1["status"] == "ok"
    assert "timestamp" in data1


def test_export_to_vault_no_databases(tmp_path: Path, monkeypatch):
    """export_to_vault with no databases returns empty exports."""
    monkeypatch.setattr("app.knowledge.local_first.discover_databases", dict)
    monkeypatch.setattr("app.knowledge.local_first.SPOOL_PATH", tmp_path / "replies.jsonl")

    result = export_to_vault(vault_dir=str(tmp_path / "vault"))
    assert result["count"] == 0
    assert result["exports"] == []


def test_export_to_vault_with_database(tmp_path: Path, monkeypatch):
    """export_to_vault exports tables to JSONL."""
    import sqlite3
    db_file = tmp_path / "database.sqlite"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE pages (id INTEGER, title TEXT)")
    conn.execute("INSERT INTO pages VALUES (1, 'Home')")
    conn.execute("INSERT INTO pages VALUES (2, 'About')")
    conn.commit()
    conn.close()

    monkeypatch.setattr("app.knowledge.local_first.discover_databases", lambda: {"db": str(db_file)})
    monkeypatch.setattr("app.knowledge.local_first.SPOOL_PATH", tmp_path / "replies.jsonl")

    vault_dir = tmp_path / "vault"
    result = export_to_vault(vault_dir=str(vault_dir), limit_per_table=10)
    assert result["count"] == 1
    assert result["exports"][0]["database"] == "db"
    assert result["exports"][0]["table"] == "pages"
    assert result["exports"][0]["rows"] == 2

    # Verify JSONL output
    jsonl_file = vault_dir / "db" / "pages.jsonl"
    assert jsonl_file.exists()
    lines = jsonl_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["title"] == "Home"
