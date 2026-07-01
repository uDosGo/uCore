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


class ProviderRouter:
    """Multi-provider LLM router backed by LiteLLM."""

    _instance: ProviderRouter | None = None

    def __new__(cls) -> ProviderRouter:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._litellm_available = False
        try:
            import litellm  # noqa: F401
            self._litellm_available = True
            log.info("LiteLLM provider router ready")
        except ImportError:
            log.warning("LiteLLM not installed — falling back to HTTP calls")

    def list_providers(self) -> list[dict[str, Any]]:
        return [
            {"id": "ollama", "name": "Ollama (local)",
             "base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")},
            {"id": "openrouter", "name": "OpenRouter (cloud)",
             "base_url": "https://openrouter.ai/api/v1"},
        ]

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {"id": "ollama/qwen2.5-coder:3b", "provider": "ollama", "cost": "free"},
            {"id": "ollama/qwen2.5-coder:7b-instruct-q4_K_M", "provider": "ollama", "cost": "free"},
            {"id": "openrouter/qwen/qwen2.5-coder-32b-instruct", "provider": "openrouter", "cost": "mid"},
            {"id": "openrouter/anthropic/claude-3.5-sonnet", "provider": "openrouter", "cost": "premium"},
        ]

    async def chat(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        max_price: float | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send chat completion via LiteLLM or fallback HTTP."""
        model_name = model or self._default_model(provider)

        if self._litellm_available:
            return await self._chat_litellm(messages, model_name, **kwargs)
        return await self._chat_http(messages, model_name, provider, **kwargs)

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
            # Fallback: yield full response as single chunk
            result = await self._chat_http(messages, model_name, provider, **kwargs)
            yield result.get("content", "")

    async def _chat_litellm(
        self, messages: list[dict[str, str]], model: str, **kwargs: Any,
    ) -> dict[str, Any]:
        from litellm import acompletion
        response = await acompletion(model=model, messages=messages, **kwargs)
        choice = response.choices[0]
        return {
            "content": choice.message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        }

    async def _chat_http(
        self, messages: list[dict[str, str]], model: str,
        provider: str | None = None, **kwargs: Any,
    ) -> dict[str, Any]:
        import aiohttp
        base_url = "http://localhost:11434" if not provider or provider == "ollama" \
            else "https://openrouter.ai/api/v1"
        ollama_model = model.split("/", 1)[-1] if "/" in model else model

        async with aiohttp.ClientSession() as session:
            url = f"{base_url}/chat"
            if "openrouter" in base_url:
                url = f"{base_url}/chat/completions"
                headers = {"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY', '')}"}
                payload = {"model": ollama_model, "messages": messages}
            else:
                headers = {}
                payload = {"model": ollama_model, "messages": messages, "stream": False}

            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                if "openrouter" in base_url:
                    return {
                        "content": data["choices"][0]["message"]["content"],
                        "model": data.get("model", model),
                        "usage": data.get("usage", {}),
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