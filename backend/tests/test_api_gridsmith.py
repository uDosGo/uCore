"""Integration tests for GridSmith REST endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.gridsmith_api import (
    handle_gridsmith_status,
    handle_gridsmith_tools,
    handle_gridsmith_grid_create,
    handle_gridsmith_import_basic,
)
import app.api.gridsmith_api as gridsmith_api


class _FakeGridSmithBridge:
    def status(self):
        return {"exists": True, "cli_path": "/tmp/gridsmith"}

    async def run(self, *args: str):
        if args[:2] == ("tools", "list"):
            return {"tools": [{"name": "import_basic_program"}]}
        if args[:2] == ("grid", "create"):
            return {"grid": {"cols": int(args[3]), "rows": int(args[5]), "cellCount": int(args[3]) * int(args[5])}}
        if args[:2] == ("world", "import-basic"):
            return {"world": {"id": "imported-basic"}, "files": {"manifest": "/tmp/world.json"}}
        raise AssertionError(f"Unexpected args: {args}")


class GridSmithAPITest(AioHTTPTestCase):
    async def get_application(self):
        self._old_get_bridge = gridsmith_api.get_gridsmith_bridge
        gridsmith_api.get_gridsmith_bridge = lambda: _FakeGridSmithBridge()
        app = web.Application()
        app.router.add_get('/api/gridsmith/status', handle_gridsmith_status)
        app.router.add_get('/api/gridsmith/tools', handle_gridsmith_tools)
        app.router.add_post('/api/gridsmith/grid/create', handle_gridsmith_grid_create)
        app.router.add_post('/api/gridsmith/world/import-basic', handle_gridsmith_import_basic)
        return app

    async def tearDownAsync(self):
        gridsmith_api.get_gridsmith_bridge = self._old_get_bridge
        await super().tearDownAsync()

    async def test_gridsmith_status(self):
        resp = await self.client.get('/api/gridsmith/status')
        assert resp.status == 200
        data = await resp.json()
        assert data['exists'] is True

    async def test_gridsmith_tools(self):
        resp = await self.client.get('/api/gridsmith/tools')
        assert resp.status == 200
        data = await resp.json()
        assert data['tools'][0]['name'] == 'import_basic_program'

    async def test_gridsmith_grid_create(self):
        resp = await self.client.post('/api/gridsmith/grid/create', json={'cols': 5, 'rows': 4})
        assert resp.status == 200
        data = await resp.json()
        assert data['grid']['cellCount'] == 20

    async def test_gridsmith_import_basic(self):
        resp = await self.client.post('/api/gridsmith/world/import-basic', json={
            'program': '10 PRINT "HI"',
            'world_name': 'Imported BASIC',
        })
        assert resp.status == 200
        data = await resp.json()
        assert data['world']['id'] == 'imported-basic'
