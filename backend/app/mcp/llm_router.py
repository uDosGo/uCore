"""Hivemind LLM Router — Route agent requests to appropriate LLM backends.

Supports three tiers:
  1. Roundtable AI (local, priority 1)
  2. Ollama (local, priority 2)
  3. OpenAI fallback (priority 3)

API keys are sourced from the Secret Store (AES-256-GCM encrypted),
with env var fallback for development convenience.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import aiohttp

from app.secret.store import get_store

log = logging.getLogger("ucore.mcp.hivemind.llm_router")


@dataclass
class LLMBackend:
    name: str
    base_url: str
    api_key: str | None = None
    models: list[str] = field(default_factory=list)
    priority: int = 1
    type: str = "openai_compatible"


class LLMRouter:
    """Routes agent requests to the appropriate LLM backend."""

    def __init__(self, config_path: str | None = None):
        self.backends: list[LLMBackend] = []
        self._session: aiohttp.ClientSession | None = None
        if config_path:
            self._load_config(config_path)
        else:
            self._init_defaults()

    def _init_defaults(self):
        """Initialize with default backend configuration.

        API keys are sourced from the Secret Store (AES-256-GCM encrypted),
        with env var fallback for development convenience.
        """
        store = get_store()

        self.backends = [
            LLMBackend(
                name="roundtable",
                base_url=os.environ.get(
                    "ROUNDTABLE_BASE_URL", "http://localhost:4891/v1"
                ),
                models=["claude-sonnet-4-20250514", "claude-opus-4-20250514", "gpt-4o"],
                priority=1,
            ),
            LLMBackend(
                name="ollama",
                base_url=os.environ.get(
                    "OLLAMA_BASE_URL", "http://localhost:11434/v1"
                ),
                models=["llama3", "codellama", "mistral"],
                priority=2,
            ),
            LLMBackend(
                name="fallback",
                base_url="https://api.openai.com/v1",
                api_key=store.get("OPENAI_API_KEY")
                or os.environ.get("OPENAI_API_KEY"),
                models=["gpt-4o-mini"],
                priority=3,
                type="openai",
            ),
        ]

    def _resolve_template(self, value: str | None, default: str = "") -> str:
        """Resolve ${VAR} templates from env vars or Secret Store."""
        if not value or "${" not in value:
            return value if value is not None else default
        import re

        store = get_store()

        def _replacer(m: re.Match) -> str:
            var_name = m.group(1)
            stored = store.get(var_name)
            if stored:
                return stored
            return os.environ.get(var_name, m.group(0))

        return re.sub(r"\$\{(\w+)\}", _replacer, value)

    def _resolve_api_key(self, value: str | None) -> str | None:
        """Resolve ${VAR} templates with Optional[str] return."""
        if not value or "${" not in value:
            return value
        return self._resolve_template(value)

    def _load_config(self, config_path: str):
        """Load backend configuration from a YAML/JSON file.

        Also wires CostManager budgets from router.budgets config.
        """
        import yaml

        with open(config_path) as f:
            if config_path.endswith((".yaml", ".yml")):
                config = yaml.safe_load(f)
            else:
                config = json.load(f)

        router_config = config.get("router", {})

        # Wire budgets into CostManager
        budgets = router_config.get("budgets", {})
        if budgets:
            from app.services.cost_manager import get_cost_manager
            cm = get_cost_manager()
            if "daily" in budgets:
                cm.daily_budget = float(budgets["daily"])

        backends_config = router_config.get("backends", {})

        self.backends = []
        for name, cfg in backends_config.items():
            raw_key = cfg.get("api_key")
            self.backends.append(
                LLMBackend(
                    name=name,
                    base_url=self._resolve_template(
                        cfg.get("base_url", ""), ""
                    ),
                    api_key=self._resolve_api_key(raw_key),
                    models=cfg.get("models", []),
                    priority=cfg.get("priority", 99),
                    type=cfg.get("type", "openai_compatible"),
                )
            )

        # Sort by priority (lower = higher priority)
        self.backends.sort(key=lambda b: b.priority)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send a chat completion request, trying backends in priority order.

        Args:
            model: The model name to use (e.g., "claude-sonnet-4-20250514")
            messages: List of message dicts with "role" and "content"
            system_prompt: Optional system prompt to prepend
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Response dict with "content", "model", "backend" keys
        """
        session = await self._get_session()

        # Find backends that support this model, sorted by priority
        candidates = [
            b for b in self.backends if model in b.models
        ]
        if not candidates:
            # Try all backends as fallback
            candidates = sorted(self.backends, key=lambda b: b.priority)

        errors: list[str] = []
        for backend in candidates:
            try:
                result = await self._try_backend(
                    session, backend, model, messages,
                    system_prompt, temperature, max_tokens,
                )
                if result:
                    return result
            except Exception as exc:
                err = f"{backend.name}: {exc}"
                errors.append(err)
                log.warning("Backend %s failed: %s", backend.name, err)

        return {
            "error": "All backends failed",
            "errors": errors,
            "content": None,
        }

    async def _try_backend(
        self,
        session: aiohttp.ClientSession,
        backend: LLMBackend,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any] | None:
        """Try a single backend for chat completion."""
        headers = {"Content-Type": "application/json"}
        if backend.api_key:
            headers["Authorization"] = f"Bearer {backend.api_key}"

        payload_messages = list(messages)
        if system_prompt:
            payload_messages.insert(0, {
                "role": "system",
                "content": system_prompt,
            })

        payload = {
            "model": model,
            "messages": payload_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        url = f"{backend.base_url.rstrip('/')}/chat/completions"
        log.debug("Sending request to %s (%s)", backend.name, url)

        async with session.post(
            url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=120)
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                log.warning(
                    "Backend %s returned %d: %s",
                    backend.name, resp.status, text[:200],
                )
                return None

            data = await resp.json()
            choices = data.get("choices", [])
            if not choices:
                return None

            return {
                "content": choices[0].get("message", {}).get("content", ""),
                "model": data.get("model", model),
                "backend": backend.name,
                "usage": data.get("usage", {}),
            }

    async def health_check(self) -> list[dict[str, Any]]:
        """Check health of all configured backends."""
        results = []
        for backend in self.backends:
            try:
                session = await self._get_session()
                url = f"{backend.base_url.rstrip('/')}/models"
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    results.append({
                        "name": backend.name,
                        "url": backend.base_url,
                        "healthy": resp.status == 200,
                        "status": resp.status,
                    })
            except Exception as exc:
                results.append({
                    "name": backend.name,
                    "url": backend.base_url,
                    "healthy": False,
                    "error": str(exc),
                })
        return results

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
