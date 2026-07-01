import os
import logging

DEV_MODE = os.environ.get("DEV_MODE", "0").lower() in ("1", "true", "yes")

logger = logging.getLogger("ucore.dev")

def dev_log(message: str) -> None:
    if DEV_MODE:
        logger.info(f"[DEV] {message}")
