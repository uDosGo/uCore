"""uCore — unified backend entry point

Usage:
    python -m backend.app                     Start with default settings
    python -m backend.app --port 8484
    python -m backend.app --port 8484 --auto-start
    python -m backend.app --help
    UCORE_DEBUG=1 python -m backend.app
"""
from __future__ import annotations

import argparse

from .core.logging import log
from .core.settings import settings


def main():
    parser = argparse.ArgumentParser(description="uCore — unified daemon")
    parser.add_argument(
        "--port", type=int, default=settings.port,
        help="Port to listen on (default: %(default)s)",
    )
    parser.add_argument(
        "--host", type=str, default=settings.host,
        help="Host to bind to (default: %(default)s)",
    )
    parser.add_argument(
        "--auto-start", action="store_true", default=settings.auto_start,
        help="Auto-start surfaces on boot",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug logging (or set UCORE_DEBUG=1)",
    )
    args = parser.parse_args()

    # Override settings from CLI args
    settings.port = args.port
    settings.host = args.host
    settings.auto_start = args.auto_start
    if args.debug:
        settings.debug = True

    log.info("╔══════════════════════════════════════════╗")
    log.info("║       uCore v%s — unified daemon        ║", settings.version)
    log.info("╚══════════════════════════════════════════╝")
    log.info("Host: %s:%d", settings.host, settings.port)
    log.info("Debug: %s", settings.debug)
    log.info("Auto-start surfaces: %s", settings.auto_start)

    # Delegate to snackbar
    from .core.snackbar import main as run_snackbar
    run_snackbar()


if __name__ == "__main__":
    main()
