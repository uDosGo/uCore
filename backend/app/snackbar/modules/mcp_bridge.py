"""MCP bridge routes — proxy queries and AI chat to MCP services."""
from __future__ import annotations

from aiohttp import web


async def mcp_query_handler(request: web.Request) -> web.Response:
    """POST /api/mcp/query — proxy a query to MCP bridge."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON body"}, status=400,
        )

    try:
        from app.services.mcp import get_bridge

        bridge = get_bridge()
        peer = data.get("peer", "forge")
        tool = data.get("tool", "")
        params = data.get("params", {})
        result = await bridge.call_tool(peer, tool, params)
        return web.json_response({"result": result})
    except ImportError as e:
        return web.json_response(
            {"error": f"MCP bridge not available: {e}"},
            status=501,
        )
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def mcp_status_handler(request: web.Request) -> web.Response:
    """GET /api/mcp/status — get MCP mesh status."""
    try:
        from app.services.mcp import get_bridge

        bridge = get_bridge()
        status = await bridge.get_mesh_status()
        return web.json_response(status)
    except ImportError:
        return web.json_response(
            {"status": "unavailable",
             "message": "MCP bridge not loaded"},
        )


async def mcp_providers_handler(request: web.Request) -> web.Response:
    """GET /api/mcp/providers — list AI providers."""
    try:
        from app.services.provider_router import get_router

        router = get_router()
        return web.json_response({
            "providers": router.list_providers(),
            "models": router.list_models(),
        })
    except ImportError as e:
        return web.json_response(
            {"error": f"Provider router not available: {e}"},
            status=501,
        )


async def mcp_chat_handler(request: web.Request) -> web.Response:
    """POST /api/mcp/chat — chat with AI provider."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON body"}, status=400,
        )
    messages = data.get("messages", [])
    provider = data.get("provider")
    model = data.get("model")
    if not messages:
        return web.json_response(
            {"error": "messages are required"}, status=400,
        )
    try:
        from app.services.provider_router import get_router

        router = get_router()
        result = await router.chat(
            messages, provider=provider, model=model,
        )
        return web.json_response(result)
    except ImportError as e:
        return web.json_response(
            {"error": f"Provider router not available: {e}"},
            status=501,
        )
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def register(app: web.Application) -> None:
    app.router.add_post("/api/mcp/query", mcp_query_handler)
    app.router.add_get("/api/mcp/status", mcp_status_handler)
    app.router.add_get("/api/mcp/providers", mcp_providers_handler)
    app.router.add_post("/api/mcp/chat", mcp_chat_handler)
