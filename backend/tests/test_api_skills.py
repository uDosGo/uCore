"""Integration tests for Skill API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.skills import handle_list_skills, handle_run_skill, handle_run_named_skill


class SkillsAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/skills", handle_list_skills)
        app.router.add_post("/api/skills/{skill_id}/run", handle_run_skill)
        app.router.add_post("/api/skills/run", handle_run_named_skill)
        return app

    async def test_list_skills(self):
        resp = await self.client.get("/api/skills")
        assert resp.status == 200
        data = await resp.json()
        assert "skills" in data
        assert "count" in data
        assert data["count"] >= 14  # 15 builtin skills at least

    async def test_run_skill_hello_world(self):
        """Hello-world skill should return a greeting."""
        resp = await self.client.post("/api/skills/hello-world/run", json={"params": {"name": "Test"}})
        assert resp.status == 200
        data = await resp.json()
        assert data.get("success") is True
        assert "Hello" in data.get("message", "")

    async def test_run_skill_nonexistent(self):
        resp = await self.client.post("/api/skills/nonexistent_skill_xyz/run", json={})
        assert resp.status == 404
        data = await resp.json()
        assert "error" in data

    async def test_run_named_skill_hello_world(self):
        resp = await self.client.post("/api/skills/run", json={"skill": "hello-world", "name": "Test"})
        assert resp.status == 200
        data = await resp.json()
        assert data.get("success") is True

    async def test_run_named_skill_no_name(self):
        resp = await self.client.post("/api/skills/run", json={})
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data

    async def test_run_named_skill_invalid_json(self):
        resp = await self.client.post("/api/skills/run", data=b"not json", headers={"Content-Type": "application/json"})
        assert resp.status == 400

    async def test_run_skill_with_params(self):
        """Run hello-world with explicit params (flat body)."""
        resp = await self.client.post("/api/skills/hello-world/run", json={"name": "Continue"})
        assert resp.status == 200
        data = await resp.json()
        assert data.get("success") is True
