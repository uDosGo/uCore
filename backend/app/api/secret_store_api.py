"""Secret Store API — Manage API keys and credentials through the UI."""
from __future__ import annotations

from aiohttp import web
from app.secret.store import get_store

import logging
log = logging.getLogger("ucore.api.secrets")


async def handle_list_secrets(request: web.Request) -> web.Response:
    """GET /api/secrets — list all stored secrets (masked)."""
    store = get_store()
    secrets = store.list()
    return web.json_response({"secrets": secrets, "count": len(secrets)})


async def handle_get_secret(request: web.Request) -> web.Response:
    """GET /api/secrets/{name} — get a secret value."""
    name = request.match_info.get("name", "")
    store = get_store()
    value = store.get(name)
    if value is None:
        return web.json_response({"error": f"Secret '{name}' not found"}, status=404)
    env_val = __import__("os").environ.get(name)
    return web.json_response({
        "name": name,
        "value": value,
        "from_env": bool(env_val),
        "masked": value[:4] + "****" + value[-4:] if len(value) > 8 else "****",
    })


async def handle_set_secret(request: web.Request) -> web.Response:
    """POST /api/secrets/{name} — set a secret value.

    Body: {"value": "sk-or-v1-..."}
    """
    name = request.match_info.get("name", "")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    value = body.get("value", "").strip()
    if not value:
        return web.json_response({"error": "value is required"}, status=400)

    store = get_store()
    store.set(name, value)
    store.save()

    return web.json_response({
        "name": name,
        "status": "saved",
        "masked": value[:4] + "****" + value[-4:] if len(value) > 8 else "****",
    })


async def handle_delete_secret(request: web.Request) -> web.Response:
    """DELETE /api/secrets/{name} — delete a secret."""
    name = request.match_info.get("name", "")
    store = get_store()
    deleted = store.delete(name)
    if not deleted:
        return web.json_response({"error": f"Secret '{name}' not found"}, status=404)
    store.save()
    return web.json_response({"name": name, "status": "deleted"})


async def handle_list_env_vars(request: web.Request) -> web.Response:
    """GET /api/secrets/env — list available env vars that could be imported."""
    import os
    known_prefixes = ["OPENROUTER", "ANTHROPIC", "OPENAI", "GEMINI",
                       "MISTRAL", "DEEPSEEK", "GROQ", "GITHUB",
                       "HUGGINGFACE", "REPLICATE", "COHERE", "AI21"]
    env_vars = []
    for key, val in sorted(os.environ.items()):
        if any(key.startswith(p) for p in known_prefixes):
            env_vars.append({
                "name": key,
                "present": True,
                "masked": val[:4] + "****" + val[-4:] if len(val) > 8 else "****",
            })
    return web.json_response({"env_vars": env_vars, "count": len(env_vars)})


async def handle_import_from_env(request: web.Request) -> web.Response:
    """POST /api/secrets/import-env — import secrets from environment."""
    store = get_store()
    store.sync_from_env()
    store.save()
    secrets = store.list()
    return web.json_response({"secrets": secrets, "count": len(secrets), "status": "imported"})
