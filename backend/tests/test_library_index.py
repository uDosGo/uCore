"""Tests for the unified library index service and API endpoints.

Covers:
- backend/app/services/library_index.py (build_index, search, get_stats)
- backend/app/api/library.py (library endpoints)
- backend/app/api/vault_api.py (vault topology endpoints)
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

# ─── Service Tests (library_index.py) ────────────────────────────────


class TestLibraryIndexService:
    """Unit tests for the library_index service functions."""

    @pytest.fixture(autouse=True)
    def setup_tmp_index(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ):
        """Create a temp index dir and patch INDEX_DIR/INDEX_DB."""
        self.index_dir = tmp_path / "indices"
        self.index_db = self.index_dir / "library.db"
        self.vault_dir = tmp_path / "vault"
        self.vault_dir.mkdir()

        monkeypatch.setattr("app.services.library_index.INDEX_DIR", self.index_dir)
        monkeypatch.setattr("app.services.library_index.INDEX_DB", self.index_db)

    def _create_test_files(self, source: str, files: dict[str, str]) -> Path:
        """Create test files in a vault source directory."""
        source_dir = self.vault_dir / source
        source_dir.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            fpath = source_dir / name
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content, encoding="utf-8")
        return source_dir

    def test_build_index_empty_vault(self):
        """build_index with no files returns zero counts."""
        from app.services.library_index import build_index

        vault_paths = {"user": self.vault_dir / "user"}
        result = build_index(vault_paths=vault_paths)

        assert result["status"] == "completed"
        assert result["total_indexed"] == 0
        assert len(result["sources"]) == 1
        assert result["sources"][0]["status"] == "missing"

    def test_build_index_with_markdown_files(self):
        """build_index indexes markdown files with frontmatter."""
        from app.services.library_index import build_index

        self._create_test_files("user", {
            "note1.md": "---\ntitle: Hello World\ntags: [test, demo]\n---\nThis is a test note.",
            "note2.md": "---\ntitle: Another Note\n---\nContent here.",
        })

        vault_paths = {"user": self.vault_dir / "user"}
        result = build_index(vault_paths=vault_paths)

        assert result["status"] == "completed"
        assert result["total_indexed"] == 2
        assert result["sources"][0]["files"] == 2
        assert result["sources"][0]["status"] == "ok"

    def test_build_index_with_code_files(self):
        """build_index indexes TypeScript and Python files."""
        from app.services.library_index import build_index

        self._create_test_files("code", {
            "app.ts": "export const app = {};",
            "utils.py": "def helper(): pass",
            "readme.md": "# Readme",
        })

        vault_paths = {"code": self.vault_dir / "code"}
        result = build_index(vault_paths=vault_paths)

        assert result["total_indexed"] == 3  # .ts, .py, .md

    def test_build_index_excludes_dirs(self):
        """build_index excludes node_modules, .git, etc."""
        from app.services.library_index import build_index

        self._create_test_files("user", {
            "good.md": "# Good file",
            "node_modules/bad.md": "# Should be excluded",
            ".git/config.md": "# Should be excluded",
        })

        vault_paths = {"user": self.vault_dir / "user"}
        result = build_index(vault_paths=vault_paths)

        assert result["total_indexed"] == 1

    def test_search_empty_index(self):
        """search returns empty list when index doesn't exist."""
        from app.services.library_index import search

        results = search("test query")
        assert results == []

    def test_search_finds_files(self):
        """search returns matching files from FTS."""
        from app.services.library_index import build_index, search

        self._create_test_files("user", {
            "python-guide.md": "---\ntitle: Python Guide\n---\nLearn Python programming.",
            "javascript-guide.md": "---\ntitle: JavaScript Guide\n---\nLearn JavaScript programming.",
            "unrelated.md": "---\ntitle: Other\n---\nSomething else entirely.",
        })

        vault_paths = {"user": self.vault_dir / "user"}
        build_index(vault_paths=vault_paths)

        results = search("Python")
        assert len(results) >= 1
        assert any("python" in r["filename"].lower() for r in results)

    def test_search_with_source_filter(self):
        """search filters by source when specified."""
        from app.services.library_index import build_index, search

        self._create_test_files("user", {
            "note.md": "---\ntitle: User Note\n---\nUser content.",
        })
        self._create_test_files("shared", {
            "note.md": "---\ntitle: Shared Note\n---\nShared content.",
        })

        vault_paths = {
            "user": self.vault_dir / "user",
            "shared": self.vault_dir / "shared",
        }
        build_index(vault_paths=vault_paths)

        user_results = search("note", source="user")
        assert all(r["source"] == "user" for r in user_results)

    def test_get_stats_no_index(self):
        """get_stats returns not-built status when index doesn't exist."""
        from app.services.library_index import get_stats

        stats = get_stats()
        assert stats["status"] == "not-built"
        assert stats["total_entries"] == 0

    def test_get_stats_with_index(self):
        """get_stats returns correct counts after indexing."""
        from app.services.library_index import build_index, get_stats

        self._create_test_files("user", {
            "a.md": "# A",
            "b.md": "# B",
            "c.md": "# C",
        })

        vault_paths = {"user": self.vault_dir / "user"}
        build_index(vault_paths=vault_paths)

        stats = get_stats()
        assert stats["status"] == "ok"
        assert stats["total_entries"] == 3
        assert stats["by_source"]["user"] == 3

    def test_frontmatter_parsing(self):
        """_parse_frontmatter extracts YAML frontmatter correctly."""
        from app.services.library_index import _parse_frontmatter

        content = "---\ntitle: Test\ntags: [a, b, c]\n---\nBody content here."
        fm, body = _parse_frontmatter(content)

        assert fm["title"] == "Test"
        assert fm["tags"] == ["a", "b", "c"]
        assert "Body content here" in body

    def test_frontmatter_parsing_no_frontmatter(self):
        """_parse_frontmatter returns empty dict when no frontmatter."""
        from app.services.library_index import _parse_frontmatter

        content = "Just plain content without frontmatter."
        fm, body = _parse_frontmatter(content)

        assert fm == {}
        assert body == content

    def test_get_preview(self):
        """_get_preview extracts first paragraph."""
        from app.services.library_index import _get_preview

        content = "First paragraph here.\n\nSecond paragraph ignored."
        preview = _get_preview(content, max_chars=50)

        assert "First paragraph" in preview
        assert len(preview) <= 50


# ─── Library API Tests (library.py) ──────────────────────────────────


class TestLibraryApi(AioHTTPTestCase):
    """Integration tests for the library API endpoints."""

    async def get_application(self):
        from app.api.library import register_library_routes

        app = web.Application()
        register_library_routes(app)
        return app

    async def asyncSetUp(self):
        await super().asyncSetUp()
        # Patch the library_index module to use temp directory
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.index_dir = self.tmp_dir / "indices"
        self.index_db = self.index_dir / "library.db"  # noqa: E501

        self._patches = [
            patch("app.services.library_index.INDEX_DIR", self.index_dir),
            patch("app.services.library_index.INDEX_DB", self.index_db),
        ]
        for p in self._patches:
            p.start()

    async def asyncTearDown(self):
        for p in self._patches:
            p.stop()
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        await super().asyncTearDown()

    async def test_library_stats_not_built(self):
        """GET /api/library/stats returns not-built when no index."""
        resp = await self.client.get("/api/library/stats")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "not-built"
        assert data["total_entries"] == 0

    async def test_library_build(self):
        """POST /api/library/build creates the index."""
        # Create a temp vault directory
        vault_dir = self.tmp_dir / "vault"
        vault_dir.mkdir()
        (vault_dir / "test.md").write_text("# Test", encoding="utf-8")

        with patch("app.services.library_index.VAULT_PATHS", {"user": vault_dir}):
            resp = await self.client.post("/api/library/build")
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "completed"

    async def test_library_search_missing_query(self):
        """GET /api/library/search returns 400 when q is missing."""
        resp = await self.client.get("/api/library/search")
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data

    async def test_library_search_empty_index(self):
        """GET /api/library/search returns empty results when no index."""
        resp = await self.client.get("/api/library/search?q=test")
        assert resp.status == 200
        data = await resp.json()
        assert data["results"] == []
        assert data["count"] == 0


# ─── Vault API Tests (vault_api.py) ──────────────────────────────────


class TestVaultApi(AioHTTPTestCase):
    """Integration tests for the vault topology API endpoints."""

    async def get_application(self):
        from app.api.vault_api import register_vault_routes

        app = web.Application()
        register_vault_routes(app)
        return app

    async def test_vault_topology(self):
        """GET /api/vault/topology returns vault layers with existence status."""
        resp = await self.client.get("/api/vault/topology")
        assert resp.status == 200
        data = await resp.json()

        assert "layers" in data
        assert len(data["layers"]) == 5

        layer_ids = [layer["id"] for layer in data["layers"]]
        assert "user" in layer_ids
        assert "shared" in layer_ids
        assert "global" in layer_ids
        assert "public" in layer_ids
        assert "code" in layer_ids

        # Each layer should have existence info
        for layer in data["layers"]:
            assert "exists" in layer
            assert "is_dir" in layer
            assert "path" in layer
            assert "icon" in layer

    async def test_vault_layers(self):
        """GET /api/vault/layers returns vault layer definitions."""
        resp = await self.client.get("/api/vault/layers")
        assert resp.status == 200
        data = await resp.json()

        assert "layers" in data
        assert len(data["layers"]) == 5

        # Verify layer structure
        layers = data["layers"]
        user_layer = next(lay for lay in layers if lay["id"] == "user")
        assert user_layer["label"] == "User Vault"
        assert user_layer["icon"] == "mdi:account"
        assert "path" in user_layer
        assert "description" in user_layer

    async def test_vault_topology_layer_structure(self):
        """Each vault layer has required fields."""
        resp = await self.client.get("/api/vault/topology")
        data = await resp.json()

        required = {"id", "label", "icon", "description", "path", "exists", "is_dir"}
        for layer in data["layers"]:
            missing = required - set(layer.keys())
            assert not missing, f"Layer {layer['id']} missing {missing}"
