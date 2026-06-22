"""Central config API — grouped user, system, installation, and secret variables."""
from __future__ import annotations

import os

from aiohttp import web

from app.core.settings import settings
from app.secret.store import get_store


def _entry(label: str, value: str, *, masked: bool = False) -> dict[str, str | bool]:
    return {"label": label, "value": value, "masked": masked}


async def handle_get_config(request: web.Request) -> web.Response:
    """GET /api/config — grouped config values for the settings surface."""
    secret_store = get_store()
    secret_items = secret_store.list()
    known_env = [
        name
        for name in (
            "OPENROUTER_API_KEY",
            "GITHUB_TOKEN",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "MISTRAL_API_KEY",
            "DEEPSEEK_API_KEY",
            "GROQ_API_KEY",
            "HUGGINGFACE_TOKEN",
            "REPLICATE_API_KEY",
            "COHERE_API_KEY",
            "AI21_API_KEY",
        )
        if os.environ.get(name)
    ]

    return web.json_response({
        "user": [
            _entry("Username", settings.user_name),
            _entry("Email", settings.user_email),
            _entry("Clipboard Shortcut", settings.clipboard_shortcut),
        ],
        "system": [
            _entry("Debug", "Enabled" if settings.debug else "Disabled"),
            _entry("Host", settings.host),
            _entry("Port", str(settings.port)),
            _entry("Auto Start", "Enabled" if settings.auto_start else "Disabled"),
            _entry("CORS", "Enabled" if settings.enable_cors else "Disabled"),
            _entry("Auth", "Required" if settings.require_auth else "Optional"),
            _entry("Ollama URL", settings.ollama_base_url),
            _entry("Ollama Model", settings.ollama_default_model),
            _entry("Ollama Timeout", str(settings.ollama_timeout)),
            _entry("API Key", "Configured" if settings.api_key else "Unset", masked=True),
        ],
        "installation": [
            _entry("UDOS_ROOT", str(settings.udos_root)),
            _entry("Data Dir", str(settings.data_dir)),
            _entry("Config Dir", str(settings.config_dir)),
            _entry("Logs Dir", str(settings.logs_dir)),
            _entry("Surface Registry", settings.surface_registry_path),
            _entry("Install Name", settings.install_name),
        ],
        "secrets": {
            "store_dir": str(settings.secrets_dir),
            "store_file": str(settings.secrets_file),
            "key_file": str(settings.secret_key_file),
            "count": len(secret_items),
            "items": secret_items,
            "env_keys": known_env,
        },
    })