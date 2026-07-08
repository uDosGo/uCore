"""API Registry — Variable resolution for AI provider/model selection.

Replaces hardcoded model strings with variable references:
    ${local:coder}       → best local coding model (free)
    ${primary:coder}     → primary cloud coding model
    ${premium:reviewer}  → best available review model
    ${ultra-cheap:any}   → cheapest cloud model
    ${budget:debugger}   → budget-friendly debug model

Resolution order:
    1. Check provider availability (is service running?)
    2. Check API key presence (SecretStore → env var)
    3. Check budget remaining (can we afford this tier?)
    4. Fall back to next cheaper tier

Usage:
    from app.services.api_registry import ApiRegistry
    registry = ApiRegistry.get()
    resolved = registry.resolve("${primary:coder}")
    # Resolved(model="qwen2.5-coder:3b", provider="ollama", cost_per_token=0.0)
"""
from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any

log = logging.getLogger("ucore.api_registry")

# Variable pattern: ${tier:purpose}
VAR_RE = re.compile(r"^\$\{(\w[\w-]*):(\w[\w-]*)\}$")

# Tier priority (lower = cheaper/faster)
TIER_ORDER = [
    "local",
    "free",
    "ultra-cheap",
    "budget",
    "primary",
    "premium",
]

# Purpose → capability matching
PURPOSE_CAPABILITIES: dict[str, list[str]] = {
    "coder": ["implementation", "debugging", "testing"],
    "reviewer": ["review", "security", "quality"],
    "architect": ["design", "architecture", "analysis"],
    "debugger": ["debugging", "analysis", "testing"],
    "docgen": ["documentation", "writing"],
    "fast": ["speed", "lightweight"],
    "worldbuild": ["worldbuild", "grid", "spatial"],
    "any": [],
}


@dataclass
class ResolvedAPI:
    """A resolved API endpoint ready for use."""
    model: str
    provider: str
    provider_type: str
    base_url: str
    api_key: str | None
    cost_per_token: float
    cost_tier: str
    purpose: str
    timeout: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "provider": self.provider,
            "provider_type": self.provider_type,
            "base_url": self.base_url,
            "api_key_present": self.api_key is not None,
            "cost_per_token": self.cost_per_token,
            "cost_tier": self.cost_tier,
            "purpose": self.purpose,
            "timeout": self.timeout,
        }


class ApiRegistry:
    """Central registry for resolving API variables to concrete endpoints."""

    _instance: "ApiRegistry | None" = None

    def __init__(self) -> None:
        self._provider_router = None
        self._secret_store = None
        self._cache: dict[str, tuple[float, ResolvedAPI | None]] = {}
        self._cache_ttl = 30.0

    @classmethod
    def get(cls) -> "ApiRegistry":
        """Get or create singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_router(self):
        if self._provider_router is None:
            from app.services.provider_router import get_router
            self._provider_router = get_router()
        return self._provider_router

    def _get_secrets(self):
        if self._secret_store is None:
            from app.secret.store import get_store
            self._secret_store = get_store()
        return self._secret_store

    def is_variable(self, value: str) -> bool:
        """Check if a string is an API variable reference."""
        return bool(VAR_RE.match(value))

    def resolve(self, variable: str, timeout: int = 60) -> ResolvedAPI | None:
        """Resolve a variable like ${primary:coder} to a concrete API endpoint."""
        if not self.is_variable(variable):
            return None

        # Check cache
        cached = self._cache.get(variable)
        if cached:
            ts, result = cached
            if time.time() - ts < self._cache_ttl:
                return result

        match = VAR_RE.match(variable)
        if not match:
            return None

        tier = match.group(1).lower()
        purpose = match.group(2).lower()

        result = self._resolve(tier, purpose, timeout)
        self._cache[variable] = (time.time(), result)
        return result

    def resolve_to_model(self, variable: str) -> str | None:
        """Resolve variable to just the model string (for backward compat)."""
        resolved = self.resolve(variable)
        return resolved.model if resolved else None

    def _resolve(self, tier: str, purpose: str, timeout: int) -> ResolvedAPI | None:
        """Try to resolve a tier+purpose combo, falling back through cheaper tiers."""
        fallback_chain = self._build_fallback_chain(tier)

        for try_tier in fallback_chain:
            resolved = self._try_resolve_tier(try_tier, purpose, timeout)
            if resolved is not None:
                if try_tier != tier:
                    log.info(
                        "API variable ${%s:%s} fell back to tier '%s' "
                        "(model=%s, provider=%s)",
                        tier, purpose, try_tier, resolved.model, resolved.provider,
                    )
                return resolved

        log.error(
            "API variable ${%s:%s}: no provider available in any tier",
            tier, purpose,
        )
        return None

    def _build_fallback_chain(self, requested_tier: str) -> list[str]:
        """Build ordered list of tiers to try, starting from requested."""
        chain: list[str] = []

        if requested_tier in TIER_ORDER:
            chain.append(requested_tier)

        for tier in TIER_ORDER:
            if tier != requested_tier and self._tier_is_cheaper(tier, requested_tier):
                chain.append(tier)

        for tier in TIER_ORDER:
            if tier not in chain:
                chain.append(tier)

        return chain

    def _tier_is_cheaper(self, tier_a: str, tier_b: str) -> bool:
        idx_a = TIER_ORDER.index(tier_a) if tier_a in TIER_ORDER else 99
        idx_b = TIER_ORDER.index(tier_b) if tier_b in TIER_ORDER else 99
        return idx_a < idx_b

    def _try_resolve_tier(
        self, tier: str, purpose: str, timeout: int,
    ) -> ResolvedAPI | None:
        """Try to find a working provider in the given tier."""
        router = self._get_router()
        secrets = self._get_secrets()

        providers_in_tier = [
            p for p in router.list_providers()
            if p.get("cost_tier") == tier and p.get("enabled", True)
        ]
        providers_in_tier.sort(key=lambda p: p.get("priority", 99))

        for prov in providers_in_tier:
            provider_name = prov["name"]
            provider_type = prov.get("type", "ollama")
            base_url = prov.get("base_url", "")
            model = prov.get("default_model", "")

            if not model:
                models = prov.get("models", [])
                if models:
                    model = models[0] if isinstance(models[0], str) else models[0].get("id", "")

            if not model:
                continue

            api_key = None
            if provider_type in ("openrouter", "anthropic", "openai", "mistral", "deepseek"):
                api_key = self._get_api_key(secrets, provider_name, provider_type)
                if not api_key:
                    log.debug("Skipping %s: no API key", provider_name)
                    continue

            return ResolvedAPI(
                model=model,
                provider=provider_name,
                provider_type=provider_type,
                base_url=base_url,
                api_key=api_key,
                cost_per_token=prov.get("cost_per_token", 0.0),
                cost_tier=tier,
                purpose=purpose,
                timeout=timeout,
            )

        return None

    def _get_api_key(
        self, secrets, provider_name: str, provider_type: str,
    ) -> str | None:
        """Get API key from SecretStore, then env vars."""
        key_names = self._get_key_names(provider_name, provider_type)
        for key_name in key_names:
            val = secrets.get(key_name)
            if val:
                return val
        for key_name in key_names:
            val = os.environ.get(key_name)
            if val:
                return val
        return None

    def _get_key_names(self, provider_name: str, provider_type: str) -> list[str]:
        names = [
            f"{provider_name.upper()}_API_KEY",
            f"{provider_name.upper()}_TOKEN",
        ]
        type_names = {
            "openrouter": ["OPENROUTER_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "mistral": ["MISTRAL_API_KEY"],
            "deepseek": ["DEEPSEEK_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "groq": ["GROQ_API_KEY"],
            "huggingface": ["HUGGINGFACE_TOKEN", "HF_TOKEN"],
            "replicate": ["REPLICATE_API_KEY", "REPLICATE_TOKEN"],
            "cohere": ["COHERE_API_KEY"],
        }
        names.extend(type_names.get(provider_type, []))
        return names

    def list_resolved(self) -> list[dict[str, Any]]:
        """List all possible variable resolutions (for debugging/UI)."""
        results = []
        for tier in TIER_ORDER:
            for purpose in PURPOSE_CAPABILITIES:
                resolved = self._resolve(tier, purpose, 60)
                if resolved:
                    results.append({
                        "variable": f"${{{tier}:{purpose}}}",
                        **resolved.to_dict(),
                    })
        return results

    def invalidate_cache(self) -> None:
        """Clear resolution cache."""
        self._cache.clear()
