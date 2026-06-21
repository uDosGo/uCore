"""Tests for local-first AppFlowy knowledge endpoints."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.knowledge import (
    handle_local_databases,
    handle_local_tables,
    handle_local_query,
    handle_local_export,
)


class LocalKnowledgeApiTest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/knowledge/local/databases", handle_local_databases)
        app.router.add_get("/api/knowledge/local/tables", handle_local_tables)
        app.router.add_post("/api/knowledge/local/query", handle_local_query)
        app.router.add_post("/api/knowledge/local/export", handle_local_export)
        return app

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.tmp = Path("/tmp/ucore_test_appflowy.db")
        if self.tmp.exists():
            self.tmp.unlink()
        with sqlite3.connect(str(self.tmp)) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS task_table (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO task_table(name) VALUES ('alpha')")
            conn.commit()

    async def asyncTearDown(self):
        if self.tmp.exists():
            self.tmp.unlink()
        await super().asyncTearDown()

    async def test_local_tables(self):
        resp = await self.client.get(f"/api/knowledge/local/tables?db={self.tmp}")
        assert resp.status == 200
        data = await resp.json()
        assert "task_table" in data["tables"]

    async def test_local_query_read(self):
        resp = await self.client.post(
            "/api/knowledge/local/query",
            json={"db": str(self.tmp), "sql": "SELECT * FROM task_table", "write": False},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 1

    async def test_local_query_write(self):
        resp = await self.client.post(
            "/api/knowledge/local/query",
            json={
                "db": str(self.tmp),
                "sql": "INSERT INTO task_table(name) VALUES (?)",
                "params": ["beta"],
                "write": True,
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["rowcount"] == 1

    async def test_local_query_reject_unsafe(self):
        resp = await self.client.post(
            "/api/knowledge/local/query",
            json={"db": str(self.tmp), "sql": "DROP TABLE task_table", "write": True},
        )
        assert resp.status == 400
