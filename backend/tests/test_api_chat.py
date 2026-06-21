"""Integration tests for Chat API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.chat import handle_chat, handle_chat_prompts, handle_models


class ChatAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_post("/api/chat", handle_chat)
        app.router.add_get("/api/chat/prompts", handle_chat_prompts)
        app.router.add_get("/api/models", handle_models)
        return app

    async def test_list_models(self):
        resp = await self.client.get("/api/models")
        assert resp.status == 200
        data = await resp.json()
        assert "providers" in data
        assert "count" in data
        assert data["count"] >= 4  # openai, anthropic, deepseek, openrouter

    async def test_list_models_structure(self):
        resp = await self.client.get("/api/models")
        data = await resp.json()
        for provider in data["providers"]:
            assert "name" in provider
            assert "type" in provider or "id" in provider
            assert "default_model" in provider or "models" in provider

    async def test_chat_prompts_default(self):
        resp = await self.client.get("/api/chat/prompts")
        assert resp.status == 200
        data = await resp.json()
        assert data["agent"] == "assist"
        assert data["count"] == 4
        for p in data["prompts"]:
            assert "title" in p
            assert "prompt" in p

    async def test_chat_prompts_for_vault(self):
        resp = await self.client.get("/api/chat/prompts?agent=vault")
        assert resp.status == 200
        data = await resp.json()
        assert data["agent"] == "vault"
        assert data["count"] == 4

    async def test_chat_prompts_for_developer(self):
        resp = await self.client.get("/api/chat/prompts?agent=developer")
        assert resp.status == 200
        data = await resp.json()
        assert data["agent"] == "developer"

    async def test_chat_missing_message(self):
        resp = await self.client.post("/api/chat", json={})
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data

    async def test_chat_invalid_json(self):
        resp = await self.client.post("/api/chat", data=b"not json",
                                       headers={"Content-Type": "application/json"})
        assert resp.status == 400

    async def test_chat_with_message(self):
        """Chat with a simple message — should get a response or error if no provider configured."""
        resp = await self.client.post("/api/chat", json={"message": "Hello, what is 1+1?"})
        # If no API key is configured, it might return 500 with provider error.
        # Either way, we should get a valid JSON response.
        assert resp.status in (200, 500)
        data = await resp.json()
        if resp.status == 200:
            assert "response" in data
            assert "model" in data
        else:
            assert "error" in data
