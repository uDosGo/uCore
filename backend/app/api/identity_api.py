"""Identity API — uDos Identity System endpoints.

Spec: UDN-IDENTITY-API-001
"""
from __future__ import annotations

from aiohttp import web

from app.services.identity import get_full_identity, ensure_identity, load_identity, save_identity


async def handle_get_identity(request: web.Request) -> web.Response:
    """GET /api/identity — Return full identity info."""
    identity = get_full_identity()
    resp = web.json_response(identity)
    # Identity headers for downstream routing
    resp.headers["X-Udos-User"] = identity.get("user_id", "")
    resp.headers["X-Udos-Install"] = identity.get("install_id", "")
    resp.headers["X-Udos-Session"] = identity.get("session_id", "")
    return resp


async def handle_init_identity(request: web.Request) -> web.Response:
    """POST /api/identity/init — Initialize or re-initialize identity."""
    body = await request.json() if request.can_read_body else {}
    identity = load_identity()

    if identity.is_valid() and not body.get("force"):
        return web.json_response({
            "success": True,
            "message": "Identity already exists",
            "identity": identity.to_dict(),
        })

    ensure_identity()
    identity = load_identity()
    return web.json_response({
        "success": True,
        "message": "Identity initialized",
        "identity": identity.to_dict(),
    })


async def handle_set_codeword(request: web.Request) -> web.Response:
    """POST /api/identity/codeword — Set a friendly codeword for this device."""
    body = await request.json()
    codeword = (body.get("codeword") or "").strip()
    if not codeword:
        return web.json_response({"success": False, "error": "codeword is required"}, status=400)

    identity = load_identity()
    identity.codeword = codeword
    save_identity(identity)

    return web.json_response({"success": True, "codeword": codeword})


def register_identity_routes(app: web.Application) -> None:
    """Register identity API routes."""
    app.router.add_get("/api/identity", handle_get_identity)
    app.router.add_post("/api/identity/init", handle_init_identity)
    app.router.add_post("/api/identity/codeword", handle_set_codeword)
