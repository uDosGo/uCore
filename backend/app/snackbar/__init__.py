"""Snackbar package — modular daemon for uCore.

Route handlers are split into modules under ``snackbar/modules/`` and loaded
dynamically by ``server.py``.  Each module exposes a ``register(app)`` function
that receives the aiohttp Application and registers its routes.
"""
from __future__ import annotations

from .server import create_app, main

__all__ = ["create_app", "main"]