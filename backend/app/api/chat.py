"""Chat-related API endpoints for uCore.

Provides:
- POST /api/chat — chat completion (alias for /api/mcp/chat)
- GET /api/chat/prompts — dynamic prompt cards for AssistUI
- GET /api/models — available AI models from provider_router
"""
from __future__ import annotations

import logging

from aiohttp import web

from ..services.provider_router import ProviderRouter

log = logging.getLogger("ucore.chat")

# Shared router instance
_router: ProviderRouter | None = None


def get_router() -> ProviderRouter:
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router


async def handle_chat(request: web.Request) -> web.Response:
    """POST /api/chat — send a chat message and get response.

    Body: { "message": "...", "agent": "...", "model": "...", ... }
    Returns: { "response": "...", "agent": "...", "model": "...", "usage": {...} }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    message = body.get("message", "")
    if not message:
        return web.json_response({"error": "message is required"}, status=400)

    agent = body.get("agent", "assist")
    model = body.get("model")

    # Accept optional history/messages array for conversation continuity
    history = body.get("history") or body.get("messages")
    if not isinstance(history, list):
        history = []

    log.info(
        "Chat request: agent=%s, history_len=%d, message=%s...",
        agent, len(history), message[:80],
    )

    try:
        router = get_router()
        # Build messages array: history first, then new user message
        chat_messages = list(history)
        chat_messages.append({"role": "user", "content": message})
        response = await router.chat(
            messages=chat_messages,
            model=model,
        )
        return web.json_response({
            "response": response.get("content", ""),
            "agent": agent,
            "model": response.get("model", model),
            "usage": response.get("usage", {}),
        })
    except Exception as e:
        log.error("Chat error: %s", e)
        return web.json_response({
            "error": str(e),
            "message": "Chat request failed",
        }, status=500)


async def handle_chat_prompts(request: web.Request) -> web.Response:
    """GET /api/chat/prompts?agent=... — get prompt cards for an agent.

    Returns a list of suggested prompts/questions for the given agent.
    """
    agent = request.query.get("agent", "assist")

    prompts = {
        "vault": [
            {"title": "What's in my vault?", "prompt": "Show me my recent items and collections"},
            {"title": "Find something", "prompt": "Search my vault for documents about..."},
            {"title": "Organize", "prompt": "Help me organize my vault by topic"},
            {"title": "Recent changes", "prompt": "What's been updated recently in my vault?"},
        ],
        "devstudio": [
            {"title": "Check project health", "prompt": "Run project diagnostics and health check"},
            {"title": "Code review", "prompt": "Review recent code changes for issues"},
            {"title": "Fix linting", "prompt": "Find and fix linting errors in the project"},
            {"title": "Generate docs", "prompt": "Generate documentation from code"},
        ],
        "agent": [
            {"title": "System status", "prompt": "Show me the system status dashboard"},
            {"title": "Deploy update", "prompt": "Guide me through deploying the latest changes"},
            {"title": "Debug issue", "prompt": "Help me debug a problem with..."},
            {"title": "Optimize", "prompt": "Analyze performance and suggest optimizations"},
        ],
        "assist": [
            {"title": "What can you do?", "prompt": "What capabilities do you have?"},
            {"title": "Help me think", "prompt": "I'm thinking about... give me your perspective"},
            {"title": "Research", "prompt": "Research the topic of..."},
            {"title": "Write", "prompt": "Help me write a document about..."},
        ],
    }

    default_prompts = prompts.get(agent, prompts["assist"])

    return web.json_response({
        "agent": agent,
        "prompts": default_prompts,
        "count": len(default_prompts),
    })


async def handle_models(request: web.Request) -> web.Response:
    """GET /api/models — list available AI models.

    Returns models from the provider_router's configured providers.
    """
    try:
        router = get_router()
        providers = router.list_providers() if hasattr(router, "list_providers") else []

        if not providers:
            # Fallback: return hardcoded list
            providers = [
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                    "enabled": True,
                },
                {
                    "id": "anthropic",
                    "name": "Anthropic",
                    "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                    "enabled": True,
                },
                {
                    "id": "deepseek",
                    "name": "DeepSeek",
                    "models": ["deepseek-chat", "deepseek-coder"],
                    "enabled": True,
                },
                {
                    "id": "openrouter",
                    "name": "OpenRouter",
                    "models": ["deepseek/deepseek-chat", "mistral/mistral-large", "anthropic/claude-3"],
                    "enabled": True,
                },
            ]

        return web.json_response({
            "providers": providers,
            "count": len(providers),
        })
    except Exception as e:
        log.error("Models error: %s", e)
        return web.json_response({
            "providers": [],
            "count": 0,
            "error": str(e),
        })
