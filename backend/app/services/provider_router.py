"""Provider Router — LiteLLM-powered multi-provider routing.

Delegates to LiteLLM for all LLM calls. Supports Ollama (local),
OpenRouter (cloud), and any provider LiteLLM supports.

Usage:
    from provider_router import ProviderRouter
    router = ProviderRouter()
    response = await router.chat(messages, model="ollama/qwen2.5-coder:3b")
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("snackbar.provider_router")

_env_loaded = False


def _load_env_file(path: Path) -> None:
    """Load .env file into environment if not already loaded."""
    global _env_loaded
    if _env_loaded:
        return
    if not path.exists():
        return
    _env_loaded = True
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = val


# Load env files on import
_env_paths = [
    Path.home() / ".ucore" / ".env",
    Path.home() / ".ucore" / "config" / "hivemind.env",
]
for _ep in _env_paths:
    _load_env_file(_ep)


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""

    name: str
    type: str
    base_url: str = ""
    default_model: str = ""
    priority: int = 1
    enabled: bool = True
    models: list[str] = field(default_factory=list)
    timeout: int = 60
    api_key: str | None = None

    @classmethod
    def from_yaml(cls, name: str, data: dict) -> ProviderConfig:
        """Create ProviderConfig from a YAML config dictionary."""
        provider_type = data.get("type", "ollama")

        # Resolve api_key: explicit value > env var {NAME}_API_KEY
        api_key = data.get("api_key")
        if api_key is None:
            env_key = f"{name.upper()}_API_KEY"
            api_key = os.environ.get(env_key)

        # Default base_url by type
        base_url = data.get("base_url", "")
        if not base_url:
            if provider_type == "ollama":
                base_url = "http://localhost:11434"
            elif provider_type == "openrouter":
                base_url = "https://openrouter.ai/api/v1"

        return cls(
            name=name,
            type=provider_type,
            base_url=base_url,
            default_model=data.get("default_model", ""),
            priority=data.get("priority", 10),
            enabled=data.get("enabled", True),
            models=data.get("models", []),
            timeout=data.get("timeout", 60),
            api_key=api_key,
        )


class ProviderRouter:
    """Multi-provider LLM router backed by LiteLLM."""

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._load_config()
        self._litellm_available = False
        self.cache = None
        self.providers: dict[str, ProviderConfig] = {}
        self._counter = 0
        self._total_latency_ms: float = 0.0
        self._last_latency_ms: float | None = None
        try:
            import litellm  # noqa: F401
            self._litellm_available = True
            log.info("LiteLLM provider router ready")
        except ImportError:
            log.warning("LiteLLM not installed — falling back to HTTP calls")

    def _load_config(self) -> None:
        """Load provider configuration. Override in tests via monkeypatch."""
        pass

    # ── Provider Registry ─────────────────────────────────────────

    def get_provider(self, name: str | None = None) -> ProviderConfig:
        """Return a provider config by name, or fallback default."""
        if name and name in self.providers:
            return self.providers[name]

        # Fallback: return highest priority enabled provider
        enabled = [p for p in self.providers.values() if p.enabled]
        if enabled:
            enabled.sort(key=lambda p: p.priority)
            return enabled[0]

        # No providers configured — return safe default
        return ProviderConfig(
            name="ollama", type="ollama",
            base_url="http://localhost:11434",
            default_model="qwen2.5-coder:7b-instruct-q4_K_M",
        )

    def get_provider_required(self, name: str) -> ProviderConfig:
        """Return provider by name; raise if missing or disabled."""
        prov = self.providers.get(name)
        if prov is None:
            raise ValueError(f"Provider '{name}' not found")
        return prov

    def list_providers(self) -> list[dict[str, Any]]:
        """List all configured providers with their metadata."""
        if self.providers:
            return [
                {
                    "name": p.name,
                    "type": p.type,
                    "base_url": p.base_url,
                    "default_model": p.default_model,
                    "priority": p.priority,
                    "enabled": p.enabled,
                    "models": p.models,
                    "timeout": p.timeout,
                }
                for p in self.providers.values()
            ]
        return [
            {"id": "ollama", "name": "Ollama (local)",
             "base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")},
            {"id": "openrouter", "name": "OpenRouter (cloud)",
             "base_url": "https://openrouter.ai/api/v1"},
        ]

    def list_models(self) -> list[dict[str, Any]]:
        """List models from configured providers."""
        models: list[dict[str, Any]] = []
        for prov in self.providers.values():
            if prov.models:
                for m in prov.models:
                    models.append({"id": m, "provider": prov.name})
            elif prov.default_model:
                models.append({
                    "id": prov.default_model,
                    "provider": prov.name,
                })
        if models:
            return models
        return [
            {"id": "ollama/qwen2.5-coder:3b", "provider": "ollama", "cost": "free"},
            {"id": "ollama/qwen2.5-coder:7b-instruct-q4_K_M",
             "provider": "ollama", "cost": "free"},
            {"id": "openrouter/qwen/qwen2.5-coder-32b-instruct",
             "provider": "openrouter", "cost": "mid"},
            {"id": "openrouter/anthropic/claude-3.5-sonnet",
             "provider": "openrouter", "cost": "premium"},
        ]

    # ── Stats ─────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Return usage statistics including latency and cache info."""
        cache_stats: dict[str, Any] = {}
        if self.cache is not None:
            try:
                cache_stats = self.cache.stats()
            except Exception:
                cache_stats = {"hits": 0, "misses": 0, "entries": 0}
        avg_latency = (
            self._total_latency_ms / self._counter
            if self._counter > 0
            else 0
        )
        return {
            "requests": self._counter,
            "last_latency_ms": self._last_latency_ms,
            "average_latency_ms": avg_latency,
            "cache": cache_stats,
        }

    def _record_latency(self, ms: float) -> None:
        self._counter += 1
        self._last_latency_ms = ms
        self._total_latency_ms += ms

    # ── Chat ──────────────────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        max_price: float | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send chat completion with caching, fallback, and latency tracking."""
        import time

        provider_name = provider or "ollama"
        model_name = model or self._default_model(provider_name)

        # Check cache if available
        if self.cache is not None:
            cached = self.cache.get(
                provider=provider_name, model=model_name,
                messages=messages,
            )
            if cached is not None:
                self._record_latency(0)
                return cached

        t0 = time.time()

        result = await self._route_chat(
            provider_name, messages, model_name, **kwargs,
        )

        elapsed = (time.time() - t0) * 1000
        self._record_latency(elapsed)
        # Don't double-count if _chat_ollama was called via fallback
        # — it already recorded in this same chat() invocation.

        # Store in cache if available and successful
        if self.cache is not None and "error" not in result:
            self.cache.set(
                provider=provider_name, model=model_name,
                messages=messages, response=result,
            )

        return result

    async def _route_chat(
        self,
        provider_name: str,
        messages: list[dict[str, str]],
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Route chat to the right handler with fallback logic."""

        # Get provider config
        try:
            prov = self.get_provider(provider_name)
        except ValueError:
            return {"error": f"Provider '{provider_name}' not available"}

        if prov.type == "ollama":
            return await self._chat_ollama(prov, messages, model, prov.timeout)

        if prov.type == "openrouter":
            # Try OpenRouter, fall back to Ollama on failure
            try:
                result = await self._chat_openrouter(
                    prov, messages, model, prov.timeout,
                )
                if "error" not in result:
                    return result
                # OpenRouter returned an error — try fallback
                fallback = await self._fallback_ollama(
                    prov, messages, model, prov.timeout,
                )
                if fallback:
                    return fallback
                return result
            except Exception as exc:
                fallback = await self._fallback_ollama(
                    prov, messages, model, prov.timeout,
                )
                if fallback:
                    fallback.setdefault("fallback", {})["reason"] = str(exc)
                    return fallback
                return {"error": str(exc)}

        # Unknown provider type
        return {"error": f"Unknown provider type: {prov.type}"}

    async def _chat_ollama(
        self, provider: ProviderConfig,
        messages: list[dict[str, str]],
        model: str, timeout: int = 60,
    ) -> dict[str, Any]:
        """Chat via Ollama (local HTTP API)."""
        return await self._chat_http(messages, model, provider.name)

    async def _chat_openrouter(
        self, provider: ProviderConfig,
        messages: list[dict[str, str]],
        model: str, timeout: int = 60,
    ) -> dict[str, Any]:
        """Chat via OpenRouter API. Fallback handled by _route_chat."""
        # Check API key
        if not provider.api_key:
            return {"error": "OpenRouter API key not configured"}

        return await self._chat_http(messages, model, provider.name)

    async def _fallback_ollama(
        self,
        provider: ProviderConfig,
        messages: list[dict[str, str]],
        model: str,
        timeout: int,
    ) -> dict[str, Any] | None:
        """Invoke Ollama fallback and merge fallback metadata."""
        if "ollama" not in self.providers:
            return None
        ollama = self.providers["ollama"]
        fallback_model = ollama.default_model or model
        result = await self._chat_ollama(
            ollama, messages, fallback_model, timeout,
        )
        result["fallback"] = {
            "used": True,
            "from_provider": provider.name,
        }
        return result

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ):
        """Stream chat completion tokens."""
        model_name = model or self._default_model(provider)
        if self._litellm_available:
            from litellm import acompletion
            response = await acompletion(
                model=model_name,
                messages=messages,
                stream=True,
                **kwargs,
            )
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            result = await self._chat_http(
                messages, model_name, provider, **kwargs,
            )
            yield result.get("content", "")

    async def _chat_litellm(
        self, messages: list[dict[str, str]], model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        from litellm import acompletion
        response = await acompletion(model=model, messages=messages, **kwargs)
        choice = response.choices[0]
        return {
            "content": choice.message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": (
                    response.usage.prompt_tokens if response.usage else 0
                ),
                "completion_tokens": (
                    response.usage.completion_tokens if response.usage else 0
                ),
            },
        }

    async def _chat_http(
        self, messages: list[dict[str, str]], model: str,
        provider: str | None = None, **kwargs: Any,
    ) -> dict[str, Any]:
        import aiohttp
        is_openrouter = provider == "openrouter"
        base_url = (
            "https://openrouter.ai/api/v1" if is_openrouter
            else "http://localhost:11434"
        )
        ollama_model = model.split("/", 1)[-1] if "/" in model else model

        async with aiohttp.ClientSession() as session:
            if is_openrouter:
                url = f"{base_url}/chat/completions"
                prov = self.providers.get("openrouter")
                api_key = prov.api_key if prov else ""
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost",
                }
                payload = {
                    "model": ollama_model,
                    "messages": messages,
                }
            else:
                url = f"{base_url}/chat"
                headers = {}
                payload = {
                    "model": ollama_model,
                    "messages": messages,
                    "stream": False,
                }

            async with session.post(
                url, json=payload, headers=headers,
            ) as resp:
                data = await resp.json()
                if is_openrouter:
                    if "choices" in data:
                        return {
                            "content": data["choices"][0]["message"]["content"],
                            "model": data.get("model", model),
                            "usage": data.get("usage", {}),
                        }
                    return {
                        "error": data.get("error", {}).get(
                            "message", "OpenRouter request failed",
                        ),
                    }
                return {
                    "content": data.get("message", {}).get("content", ""),
                    "model": model,
                    "usage": {},
                }

    def _default_model(self, provider: str | None = None) -> str:
        if provider == "openrouter":
            return "openrouter/qwen/qwen2.5-coder-32b-instruct"
        return "ollama/qwen2.5-coder:3b"


def get_router() -> ProviderRouter:
    return ProviderRouter()