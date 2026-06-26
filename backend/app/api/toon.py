from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

from app.mcp.toon import TOONContextServer

log = logging.getLogger("ucore.api.toon")

# Global TOON server instance
_toon_server = None


def get_toon_server() -> TOONContextServer:
    global _toon_server
    if _toon_server is None:
        _toon_server = TOONContextServer()
    return _toon_server


async def handle_toon_encode(request: web.Request) -> web.Response:
    """POST /api/toon/encode — Convert content to TOON format."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({
            "error": "Invalid JSON",
            "status": "error",
        }, status=400)
    
    content = body.get("content", "")
    content_type = body.get("content_type", "text")
    
    if not content:
        return web.json_response({
            "error": "content is required",
            "status": "error",
        }, status=400)
    
    try:
        toon_server = get_toon_server()
        
        # Check cache first
        cached = toon_server.get(content, content_type)
        if cached:
            return web.json_response({
                "status": "cached",
                "toon_content": cached.toon_content,
                "compression_ratio": cached.compression_ratio,
                "original_size": cached.original_size,
                "toon_size": cached.toon_size,
                "hit_count": cached.hit_count,
            })
        
        # Generate TOON content
        toon_content = toon_server.toon_encode(content, content_type)
        
        # Cache the result
        toon_server.set(content, toon_content, content_type)
        
        return web.json_response({
            "status": "encoded",
            "toon_content": toon_content,
            "compression_ratio": toon_server._calculate_compression_ratio(content, toon_content),
            "original_size": len(content),
            "toon_size": len(toon_content),
        })
        
    except Exception as e:
        log.error(f"TOON encoding error: {e}")
        return web.json_response({
            "error": str(e),
            "status": "error",
        }, status=500)


async def handle_toon_stats(request: web.Request) -> web.Response:
    """GET /api/toon/stats — Get TOON server statistics."""
    try:
        toon_server = get_toon_server()
        stats = toon_server.stats()
        
        return web.json_response({
            "status": "ok",
            "stats": stats,
        })
        
    except Exception as e:
        log.error(f"TOON stats error: {e}")
        return web.json_response({
            "error": str(e),
            "status": "error",
        }, status=500)


async def handle_toon_clear(request: web.Request) -> web.Response:
    """POST /api/toon/clear — Clear TOON cache."""
    try:
        toon_server = get_toon_server()
        toon_server.clear()
        
        return web.json_response({
            "status": "cleared",
            "message": "TOON cache cleared successfully",
        })
        
    except Exception as e:
        log.error(f"TOON clear error: {e}")
        return web.json_response({
            "error": str(e),
            "status": "error",
        }, status=500)
