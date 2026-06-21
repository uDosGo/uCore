"""Integration tests for clipboard buffer snack APIs."""
from __future__ import annotations

from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.snacks import register_snack_routes


class ClipboardAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        register_snack_routes(app)
        return app

    async def asyncSetUp(self):
        await super().asyncSetUp()
        import app.menu.clipboard_buffer as cb
        import app.api.snacks as snacks_api

        self.tmp = Path("/tmp/ucore_clipboard_tests")
        if self.tmp.exists():
            for p in sorted(self.tmp.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    p.rmdir()
            self.tmp.rmdir()
        self.tmp.mkdir(parents=True, exist_ok=True)

        cb.BASE_DIR = self.tmp
        cb.JSONL_PATH = self.tmp / "clipboard.jsonl"
        cb.SQLITE_PATH = self.tmp / "clipboard.db"
        cb.IMAGES_DIR = self.tmp / "images"

        self._clipboard_text = ""

        def fake_copy(text: str) -> None:
            self._clipboard_text = text

        def fake_read() -> str:
            return self._clipboard_text

        self._orig_copy = cb.copy_text_to_clipboard
        self._orig_read = cb.read_clipboard_text
        cb.copy_text_to_clipboard = fake_copy
        cb.read_clipboard_text = fake_read
        self._orig_api_copy = snacks_api.copy_text_to_clipboard
        snacks_api.copy_text_to_clipboard = fake_copy

    async def asyncTearDown(self):
        import app.menu.clipboard_buffer as cb
        import app.api.snacks as snacks_api

        cb.copy_text_to_clipboard = self._orig_copy
        cb.read_clipboard_text = self._orig_read
        snacks_api.copy_text_to_clipboard = self._orig_api_copy

        if self.tmp.exists():
            for p in sorted(self.tmp.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    p.rmdir()
            self.tmp.rmdir()
        await super().asyncTearDown()

    async def test_save_and_list(self):
        resp = await self.client.post(
            "/api/snacks/clipboard/save",
            json={"content": "hello world", "source": "test", "pinned": True},
        )
        assert resp.status == 201
        saved = await resp.json()
        assert saved["pinned"] is True

        lr = await self.client.get("/api/snacks/clipboard?limit=10")
        assert lr.status == 200
        data = await lr.json()
        assert data["count"] == 1
        assert data["items"][0]["content"] == "hello world"

    async def test_search_pin_delete(self):
        r1 = await self.client.post("/api/snacks/clipboard/save", json={"content": "alpha task", "pinned": False})
        item = await r1.json()
        item_id = item["id"]

        sr = await self.client.get("/api/snacks/clipboard/search?q=alpha")
        assert sr.status == 200
        sdata = await sr.json()
        assert sdata["count"] == 1

        pr = await self.client.post(f"/api/snacks/clipboard/{item_id}/pin", json={"pinned": True})
        assert pr.status == 200

        dr = await self.client.delete(f"/api/snacks/clipboard/{item_id}")
        assert dr.status == 200

    async def test_capture_and_paste(self):
        self._clipboard_text = "copied from mac"
        cap = await self.client.post("/api/snacks/clipboard/capture", json={"source": "user_copy"})
        assert cap.status == 201
        item = await cap.json()

        self._clipboard_text = ""
        paste = await self.client.post(f"/api/snacks/clipboard/{item['id']}/paste")
        assert paste.status == 200
        assert self._clipboard_text == "copied from mac"

    async def test_cleanup(self):
        for i in range(5):
            await self.client.post(
                "/api/snacks/clipboard/save",
                json={"content": f"item-{i}", "pinned": False},
            )
        cr = await self.client.post("/api/snacks/clipboard/cleanup", json={"max_items": 2, "max_days": 999})
        assert cr.status == 200

        lr = await self.client.get("/api/snacks/clipboard")
        data = await lr.json()
        assert data["count"] <= 2

    async def test_clear_history_keeps_pinned(self):
        keep = await self.client.post(
            "/api/snacks/clipboard/save",
            json={"content": "keep-me", "pinned": True},
        )
        assert keep.status == 201
        await self.client.post(
            "/api/snacks/clipboard/save",
            json={"content": "drop-me", "pinned": False},
        )

        clear = await self.client.post(
            "/api/snacks/clipboard/clear",
            json={"include_pinned": False},
        )
        assert clear.status == 200

        lr = await self.client.get("/api/snacks/clipboard")
        data = await lr.json()
        assert data["count"] == 1
        assert data["items"][0]["content"] == "keep-me"
