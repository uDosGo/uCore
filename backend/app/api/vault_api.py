"""Vault Topology API — exposes vault layer configuration to the frontend."""
from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web

log = logging.getLogger("ucore.vault_api")

# Mirror of library_index.VAULT_PATHS — the canonical vault topology
VAULT_LAYERS = [
    {
        "id": "user",
        "label": "User Vault",
        "icon": "mdi:account",
        "description": "Personal vault — your private documents and notes",
        "path": str(Path.home() / "Vault"),
    },
    {
        "id": "shared",
        "label": "Shared",
        "icon": "mdi:account-group",
        "description": "Shared vaults — team and collaborative workspaces",
        "path": str(Path.home() / "Shared"),
    },
    {
        "id": "global",
        "label": "Global Knowledge",
        "icon": "mdi:book-open-variant",
        "description": "Global knowledge bank — curated reference material",
        "path": str(Path.home() / "Public" / "global-knowledge"),
    },
    {
        "id": "public",
        "label": "Published",
        "icon": "mdi:web",
        "description": "Published vaults — publicly accessible doc sites",
        "path": str(Path.home() / "Public" / "doc-sites"),
    },
    {
        "id": "code",
        "label": "Code",
        "icon": "mdi:code-tags",
        "description": "Development repositories and code projects",
        "path": str(Path.home() / "Code"),
    },
]


async def handle_vault_topology(request: web.Request) -> web.Response:
    """GET /api/vault/topology — return vault layer topology with existence status."""
    layers = []
    for layer in VAULT_LAYERS:
        p = Path(layer["path"])
        layers.append({
            **layer,
            "exists": p.exists(),
            "is_dir": p.is_dir() if p.exists() else False,
        })
    return web.json_response({"layers": layers})


async def handle_vault_layers(request: web.Request) -> web.Response:
    """GET /api/vault/layers — return vault layer definitions (simpler form)."""
    return web.json_response({"layers": VAULT_LAYERS})


def register_vault_routes(app: web.Application) -> None:
    """Register vault topology routes."""
    app.router.add_get("/api/vault/topology", handle_vault_topology)
    app.router.add_get("/api/vault/layers", handle_vault_layers)
    log.debug("Vault topology routes registered")
