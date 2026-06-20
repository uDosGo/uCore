"""
Provider Router — Routes chat requests to AI providers based on config/models.yaml

Replaces legacy Hivemind MCP server with pure Python.
Reads config/models.yaml for provider/model configuration.
Supports: Ollama (local), OpenRouter (cloud), OkLocal (branded Ollama)

Usage:
    from provider_router import ProviderRouter
    router = ProviderRouter()
    response = await router.chat(messages, provider="ollama")
    async for token in router.chat_stream(messages, provider="openrouter"):
        print(token)
"""

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncGenerator, Optional

import aiohttp
import yaml

log = logging.getLogger("snackbar.provider_router")

# ─── Env File Loader ────────────────────────────────────────────

_env_loaded = False


def _load_env_file(path: Path) -> None:
    """Load a .env file into environment variables (if not already loaded).

    This provides a fallback for launchd services that may not inherit
    the user's shell environment variables.
    """
    global _env_loaded
    if _env_loaded:
        return

    env_path = Path(path)
    if not env_path.exists():
        return

    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r'^export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
                if match:
                    key, value = match.groups()
                    value = value.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value
        _env_loaded = True
        log.info(f"Loaded env vars from {env_path}")
    except Exception as e:
        log.warning(f"Failed to load env file {env_path}: {e}")


# ─── Config ─────────────────────────────────────────────────────

@dataclass
class ProviderConfig:
    """Configuration for a single provider."""
    name: str
    type: str  # "ollama", "openrouter", "oklocal"
    base_url: str
    api_key: Optional[str] = None
    default_model: str = ""
    priority: int = 10
    enabled: bool = True
    timeout: int = 60
    models: list = field(default_factory=list)

    @classmethod
    def from_yaml(cls, name: str, data: dict) -> "ProviderConfig":
        return cls(
            name=name,
            type=data.get("type", "ollama"),
            base_url=data.get("base_url", "http://localhost:11434"),
            api_key=data.get("api_key") or os.environ.get(f"{name.upper()}_API_KEY"),
            default_model=data.get("default_model", ""),
            priority=data.get("priority", 10),
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 60),
            models=data.get("models", []),
        )


# ─── Router ─────────────────────────────────────────────────────

class ProviderRouter:
    """Routes chat requests to the best available provider.

    Reads config from:
      1. ~/.config/udos/config.yaml (primary)
      2. ~/.config/udos/models.yaml (model definitions)
      3. Environment variables for API keys
    """

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or os.path.expanduser("~/.config/udos"))
        self.providers: dict[str, ProviderConfig] = {}
        self._load_config()

    def _load_config(self):
        """Load provider configuration from config files."""
        # Try DevStudio config first, then ~/.config/udos
        config_paths = [
            Path("/Users/fredbook/Code/DevStudio/config/models.yaml"),
            self.config_dir / "models.yaml",
            self.config_dir / "config.yaml",
        ]

        for path in config_paths:
            if path.exists():
                try:
                    with open(path) as f:
                        data = yaml.safe_load(f)
                    if data:
                        self._parse_config(data)
                        log.info(f"Loaded config from {path}")
                        return
                except Exception as e:
                    log.warning(f"Failed to load {path}: {e}")

        # Fallback: default providers
        log.warning("No config found, using default providers")
        self.providers["ollama"] = ProviderConfig(
            name="ollama", type="ollama",
            base_url="http://localhost:11434",
            default_model="qwen2.5-coder:7b",
            priority=1,
        )
        self.providers["openrouter"] = ProviderConfig(
            name="openrouter", type="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            default_model="deepseek/deepseek-chat",
            priority=5,
        )

    def _parse_config(self, data: dict):
        """Parse YAML config into provider configs.

        Supports multiple config formats:
          1. providers: dict of {name: {type, base_url, ...}}  (standard)
          2. models: list of {id, provider, tier, ...}          (models.yaml format)
          3. models: dict of {name: {type, base_url, ...}}      (legacy)
        """
        # Format 1: providers dict
        providers_data = data.get("providers", {})
        if isinstance(providers_data, dict):
            for name, cfg in providers_data.items():
                if isinstance(cfg, dict):
                    self.providers[name] = ProviderConfig.from_yaml(name, cfg)

        # Format 2: models list — extract unique providers from model entries
        models_list = data.get("models", [])
        if isinstance(models_list, list):
            # Group models by provider
            provider_models: dict[str, list] = {}
            for m in models_list:
                if not isinstance(m, dict):
                    continue
                provider_name = m.get("provider", "ollama")
                if provider_name not in provider_models:
                    provider_models[provider_name] = []
                provider_models[provider_name].append(m)

            # Create provider configs from discovered providers
            provider_defaults: dict[str, dict] = {
                "ollama": {"type": "ollama", "base_url": "http://localhost:11434", "priority": 1},
                "openrouter": {"type": "openrouter", "base_url": "https://openrouter.ai/api/v1", "priority": 5},
                "deepseek": {"type": "openrouter", "base_url": "https://openrouter.ai/api/v1", "priority": 5},
                "mistral": {"type": "openrouter", "base_url": "https://openrouter.ai/api/v1", "priority": 5},
                "google": {"type": "openrouter", "base_url": "https://openrouter.ai/api/v1", "priority": 5},
                "xai": {"type": "openrouter", "base_url": "https://openrouter.ai/api/v1", "priority": 5},
                "github-copilot": {"type": "openrouter", "base_url": "https://openrouter.ai/api/v1", "priority": 5},
                "oklocal": {"type": "oklocal", "base_url": "http://localhost:11434", "priority": 2},
            }
            for prov_name, models in provider_models.items():
                if prov_name not in self.providers:
                    defaults = provider_defaults.get(prov_name)
                    if defaults is None:
                        defaults = {"type": "openrouter", "base_url": "https://openrouter.ai/api/v1", "priority": 10}
                    self.providers[prov_name] = ProviderConfig(
                        name=prov_name,
                        type=str(defaults["type"]),
                        base_url=str(defaults["base_url"]),
                        api_key=os.environ.get(f"{prov_name.upper()}_API_KEY"),
                        priority=int(defaults["priority"]),
                        models=models,
                    )

        # Format 3: models dict (legacy)
        if isinstance(models_list, dict):
            for name, cfg in models_list.items():
                if isinstance(cfg, dict) and name not in self.providers:
                    self.providers[name] = ProviderConfig.from_yaml(name, cfg)

        # Also check for routing strategy
        routing = data.get("routing", {})
        if routing:
            for name, priority in routing.get("priority", {}).items():
                if name in self.providers:
                    self.providers[name].priority = priority

    def get_provider(self, name: Optional[str] = None) -> ProviderConfig:
        """Get a provider by name, or the highest priority enabled provider."""
        if name and name in self.providers:
            return self.providers[name]

        # Return highest priority enabled provider
        sorted_providers = sorted(
            [p for p in self.providers.values() if p.enabled],
            key=lambda p: p.priority,
        )
        if sorted_providers:
            return sorted_providers[0]

        raise ValueError("No enabled providers available")

    def list_providers(self) -> list[dict]:
        """List all configured providers."""
        return [
            {
                "name": p.name,
                "type": p.type,
                "default_model": p.default_model,
                "enabled": p.enabled,
                "priority": p.priority,
                "models": p.models,
            }
            for p in self.providers.values()
        ]

    def list_models(self) -> list[dict]:
        """List all available models across providers."""
        models = []
        for provider in self.providers.values():
            if provider.models:
                for m in provider.models:
                    models.append({
                        "id": m if isinstance(m, str) else m.get("id", ""),
                        "provider": provider.name,
                        "type": provider.type,
                    })
            elif provider.default_model:
                models.append({
                    "id": provider.default_model,
                    "provider": provider.name,
                    "type": provider.type,
                })
        return models

    # ─── Chat Methods ───────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """Send a chat request to the specified provider.

        Returns:
            dict with keys: content, model, provider, error (optional)
        """
        prov = self.get_provider(provider)
        model_id = model or prov.default_model
        timeout_s = timeout or prov.timeout

        try:
            if prov.type in ("ollama", "oklocal"):
                return await self._chat_ollama(prov, messages, model_id, timeout_s)
            elif prov.type == "openrouter":
                return await self._chat_openrouter(prov, messages, model_id, timeout_s)
            else:
                return {"error": f"Unknown provider type: {prov.type}"}
        except Exception as e:
            log.error(f"Provider {prov.name} error: {e}")
            return {"error": str(e), "provider": prov.name}

    async def chat_stream(
        self,
        messages: list[dict],
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[tuple[Optional[str], Optional[dict]], None]:
        """Stream a chat response token by token.

        Yields:
            (token, None) for each token
            (None, final_dict) for the final response
        """
        prov = self.get_provider(provider)
        model_id = model or prov.default_model

        try:
            if prov.type in ("ollama", "oklocal"):
                async for token, final in self._stream_ollama(prov, messages, model_id):
                    yield token, final
            elif prov.type == "openrouter":
                async for token, final in self._stream_openrouter(prov, messages, model_id):
                    yield token, final
            else:
                yield None, {"error": f"Unknown provider type: {prov.type}"}
        except Exception as e:
            log.error(f"Stream error from {prov.name}: {e}")
            yield None, {"error": str(e), "provider": prov.name}

    # ─── Ollama Provider ────────────────────────────────────────

    async def _chat_ollama(
        self, prov: ProviderConfig, messages: list[dict],
        model: str, timeout: int,
    ) -> dict:
        """Call Ollama API for chat completion."""
        url = f"{prov.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return {"error": f"Ollama error {resp.status}: {text[:200]}"}
                data = await resp.json()
                return {
                    "content": data.get("message", {}).get("content", ""),
                    "model": data.get("model", model),
                    "provider": prov.name,
                }

    async def _stream_ollama(
        self, prov: ProviderConfig, messages: list[dict], model: str,
    ) -> AsyncGenerator[tuple[Optional[str], Optional[dict]], None]:
        """Stream from Ollama API."""
        url = f"{prov.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    yield None, {"error": f"Ollama error {resp.status}: {text[:200]}"}
                    return

                full_content = ""
                async for line in resp.content:
                    if line:
                        try:
                            data = json.loads(line.decode().strip())
                            if "message" in data:
                                token = data["message"].get("content", "")
                                if token:
                                    full_content += token
                                    yield token, None
                            if data.get("done"):
                                yield None, {
                                    "content": full_content,
                                    "model": data.get("model", model),
                                    "provider": prov.name,
                                }
                                return
                        except json.JSONDecodeError:
                            continue

    # ─── OpenRouter Provider ────────────────────────────────────

    async def _chat_openrouter(
        self, prov: ProviderConfig, messages: list[dict],
        model: str, timeout: int,
    ) -> dict:
        """Call OpenRouter API for chat completion."""
        if not prov.api_key:
            return {"error": "OpenRouter API key not configured"}

        url = f"{prov.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
        }

        headers = {
            "Authorization": f"Bearer {prov.api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return {"error": f"OpenRouter error {resp.status}: {text[:200]}"}
                data = await resp.json()
                choice = data.get("choices", [{}])[0]
                return {
                    "content": choice.get("message", {}).get("content", ""),
                    "model": data.get("model", model),
                    "provider": prov.name,
                }

    async def _stream_openrouter(
        self, prov: ProviderConfig, messages: list[dict], model: str,
    ) -> AsyncGenerator[tuple[Optional[str], Optional[dict]], None]:
        """Stream from OpenRouter API."""
        if not prov.api_key:
            yield None, {"error": "OpenRouter API key not configured"}
            return

        url = f"{prov.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        headers = {
            "Authorization": f"Bearer {prov.api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    yield None, {"error": f"OpenRouter error {resp.status}: {text[:200]}"}
                    return

                full_content = ""
                async for line in resp.content:
                    if line:
                        line = line.decode().strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                yield None, {
                                    "content": full_content,
                                    "model": model,
                                    "provider": prov.name,
                                }
                                return
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                token = delta.get("content", "")
                                if token:
                                    full_content += token
                                    yield token, None
                            except json.JSONDecodeError:
                                continue


# ─── Convenience ────────────────────────────────────────────────

_router: Optional[ProviderRouter] = None


def get_router() -> ProviderRouter:
    """Get or create the singleton provider router."""
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router
