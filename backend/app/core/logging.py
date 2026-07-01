"""uCore logging — unified log configuration for all services"""
from __future__ import annotations

import logging
import sys

from .settings import settings


def setup_logging() -> logging.Logger:
    """Configure and return the root uCore logger."""
    logger = logging.getLogger("ucore")
    level = logging.DEBUG if settings.debug else logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger


# Convenience
log = setup_logging()
