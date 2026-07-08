from __future__ import annotations

from pathlib import Path

import pytest

from app.services.chat_cache import ChatCache
from app.services.provider_router import ProviderConfig, ProviderRouter


def test_chat_cache_round_trip(tmp_path: Path):
    cache = ChatCache(tmp_path / "chat-cache.db")
    messages = [{"role": "user", "content": "hello"}]
    response = {
        "content": "world",
        "model": "qwen2.5-coder:7b-instruct-q4_K_M",
        "provider": "ollama",
    }

    cache.set(
        provider="ollama",
        model="qwen2.5-coder:7b-instruct-q4_K_M",
        messages=messages,
        response=response,
    )
    cached = cache.get(
        provider="ollama",
        model="qwen2.5-coder:7b-instruct-q4_K_M",
        messages=messages,
    )

    assert cached is not None
    assert cached["content"] == "world"
    assert cached["cache"]["hit"] is True


def test_chat_cache_stats(tmp_path: Path):
    cache = ChatCache(tmp_path / "chat-cache.db")
    messages = [{"role": "user", "content": "hello"}]

    cache.set(
        provider="ollama",
        model="qwen2.5-coder:7b-instruct-q4_K_M",
        messages=messages,
        response={
            "content": "world",
            "model": "qwen2.5-coder:7b-instruct-q4_K_M",
            "provider": "ollama",
        },
    )
    cache.get(
        provider="ollama",
        model="different-model",
        messages=messages,
    )
    cache.get(
        provider="ollama",
        model="qwen2.5-coder:7b-instruct-q4_K_M",
        messages=messages,
    )

    stats = cache.stats()

    assert stats["entries"] == 1
    assert stats["writes"] == 1
    assert stats["requests"] == 2
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_ratio"] == 0.5


@pytest.mark.asyncio
async def test_provider_router_chat_uses_cache(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.services.provider_router.ProviderRouter._load_config",
        lambda self: None,
    )

    router = ProviderRouter()
    router.cache = ChatCache(tmp_path / "router-cache.db")
    router.providers = {
        "ollama": ProviderConfig(
            name="ollama",
            type="ollama",
            base_url="http://localhost:11434",
            default_model="qwen2.5-coder:7b-instruct-q4_K_M",
            priority=1,
        ),
    }

    calls = {"count": 0}

    async def fake_chat_ollama(prov, messages, model, timeout):
        calls["count"] += 1
        return {
            "content": "cached-response",
            "model": model,
            "provider": prov.name,
        }

    monkeypatch.setattr(router, "_chat_ollama", fake_chat_ollama)

    messages = [{"role": "user", "content": "hello cache"}]
    first = await router.chat(messages=messages, provider="ollama")
    second = await router.chat(messages=messages, provider="ollama")

    assert first["content"] == "cached-response"
    assert second["content"] == "cached-response"
    assert second["cache"]["hit"] is True
    assert calls["count"] == 1
