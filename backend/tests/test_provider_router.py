"""Unit tests for the ProviderRouter service."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.services.provider_router import ProviderRouter, ProviderConfig


class TestProviderRouter:
    """Test ProviderRouter without external API calls."""

    def test_init_with_default_providers(self, tmp_path: Path, monkeypatch):
        """When no config files exist, falls back to ollama + openrouter."""
        monkeypatch.setattr("app.services.provider_router.ProviderRouter._load_config", lambda self: None)
        router = ProviderRouter()
        router.providers = {
            "ollama": ProviderConfig(name="ollama", type="ollama",
                                     base_url="http://localhost:11434",
                                     default_model="qwen2.5-coder:7b", priority=1),
            "openrouter": ProviderConfig(name="openrouter", type="openrouter",
                                         base_url="https://openrouter.ai/api/v1",
                                         default_model="deepseek/deepseek-chat", priority=5),
        }
        assert "ollama" in router.providers
        assert "openrouter" in router.providers

    def test_get_provider_by_name(self):
        router = ProviderRouter()
        router.providers = {
            "ollama": ProviderConfig(name="ollama", type="ollama",
                                     base_url="http://localhost:11434",
                                     default_model="qwen2.5-coder:7b", priority=1),
        }
        prov = router.get_provider("ollama")
        assert prov.name == "ollama"
        assert prov.type == "ollama"

    def test_get_provider_nonexistent_returns_highest_priority(self):
        router = ProviderRouter()
        router.providers = {
            "low": ProviderConfig(name="low", type="ollama",
                                  base_url="http://localhost:11434",
                                  default_model="model-low", priority=10),
            "high": ProviderConfig(name="high", type="openrouter",
                                   base_url="https://example.com",
                                   default_model="model-high", priority=1),
        }
        prov = router.get_provider("nonexistent")
        assert prov.name == "high"  # highest priority

    def test_get_provider_disabled_skipped(self):
        router = ProviderRouter()
        router.providers = {
            "disabled_provider": ProviderConfig(name="disabled_provider", type="ollama",
                                                base_url="http://localhost:11434",
                                                default_model="model", priority=1, enabled=False),
            "enabled_provider": ProviderConfig(name="enabled_provider", type="openrouter",
                                               base_url="https://example.com",
                                               default_model="model", priority=5, enabled=True),
        }
        prov = router.get_provider("disabled_provider")
        assert prov.name == "disabled_provider"  # explicit name still works

    def test_get_provider_no_enabled_raises(self):
        router = ProviderRouter()
        router.providers = {}
        with pytest.raises(ValueError, match="No enabled providers"):
            router.get_provider()

    def test_list_providers_structure(self):
        router = ProviderRouter()
        router.providers = {
            "ollama": ProviderConfig(name="ollama", type="ollama",
                                     base_url="http://localhost:11434",
                                     default_model="qwen2.5-coder:7b", priority=1, enabled=True),
        }
        providers = router.list_providers()
        assert len(providers) == 1
        p = providers[0]
        assert p["name"] == "ollama"
        assert p["type"] == "ollama"
        assert p["default_model"] == "qwen2.5-coder:7b"
        assert p["enabled"] is True
        assert p["priority"] == 1

    def test_list_models_with_default_model(self):
        router = ProviderRouter()
        router.providers = {
            "ollama": ProviderConfig(name="ollama", type="ollama",
                                     base_url="http://localhost:11434",
                                     default_model="qwen2.5-coder:7b", priority=1),
        }
        models = router.list_models()
        assert len(models) == 1
        assert models[0]["id"] == "qwen2.5-coder:7b"
        assert models[0]["provider"] == "ollama"

    def test_list_models_with_model_list(self):
        router = ProviderRouter()
        router.providers = {
            "openrouter": ProviderConfig(name="openrouter", type="openrouter",
                                         base_url="https://openrouter.ai",
                                         models=["model-a", "model-b"], priority=5),
        }
        models = router.list_models()
        assert len(models) == 2
        assert models[0]["id"] == "model-a"

    def test_provider_config_from_yaml(self):
        cfg = ProviderConfig.from_yaml("test_provider", {
            "type": "ollama",
            "base_url": "http://test:11434",
            "default_model": "test-model",
            "priority": 3,
            "enabled": True,
            "timeout": 30,
        })
        assert cfg.name == "test_provider"
        assert cfg.type == "ollama"
        assert cfg.base_url == "http://test:11434"
        assert cfg.default_model == "test-model"
        assert cfg.priority == 3
        assert cfg.enabled is True
        assert cfg.timeout == 30

    def test_provider_config_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("TEST_PROVIDER_API_KEY", "sk-test-key-12345")
        cfg = ProviderConfig.from_yaml("test_provider", {
            "type": "openrouter",
            "base_url": "https://api.test.com",
            "default_model": "test-model",
        })
        assert cfg.api_key == "sk-test-key-12345"

    def test_provider_config_defaults(self):
        cfg = ProviderConfig.from_yaml("minimal", {"type": "ollama"})
        assert cfg.name == "minimal"
        assert cfg.type == "ollama"
        assert cfg.base_url == "http://localhost:11434"
        assert cfg.priority == 10
        assert cfg.enabled is True
        assert cfg.timeout == 60


@pytest.mark.asyncio
async def test_chat_unknown_provider_type():
    """Chat with unknown provider type returns error."""
    router = ProviderRouter()
    router.providers = {
        "unknown": ProviderConfig(name="unknown", type="nonexistent_type",
                                  base_url="http://localhost", default_model="m"),
    }
    result = await router.chat(messages=[{"role": "user", "content": "hi"}], provider="unknown")
    assert "error" in result


@pytest.mark.asyncio
async def test_chat_openrouter_no_api_key():
    """OpenRouter chat without API key returns error."""
    router = ProviderRouter()
    router.providers = {
        "openrouter": ProviderConfig(name="openrouter", type="openrouter",
                                     base_url="https://openrouter.ai",
                                     default_model="test-model", api_key=None),
    }
    result = await router.chat(messages=[{"role": "user", "content": "hi"}], provider="openrouter")
    assert "error" in result
    assert "API key not configured" in result["error"]
