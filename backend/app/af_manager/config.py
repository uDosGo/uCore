"""Configuration Manager for AppFlowy sync — reads sync_config.yaml."""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Optional

DEFAULT_CONFIG_PATH = Path("~/.ucore/sync_config.yaml").expanduser()
FALLBACK_CONFIG_PATH = Path(__file__).parent / "sync_config.yaml"


def load_config(config_path: Optional[str] = None) -> dict[str, Any]:
    """Load sync configuration from YAML file.

    Searches in order:
      1. Explicit path if provided
      2. ~/.ucore/sync_config.yaml
      3. Fallback: backend/app/af_manager/sync_config.yaml
    """
    candidates = []
    if config_path:
        candidates.append(Path(config_path).expanduser())
    candidates.append(DEFAULT_CONFIG_PATH)
    candidates.append(FALLBACK_CONFIG_PATH)

    for path in candidates:
        if path.exists():
            with open(path) as f:
                cfg = yaml.safe_load(f) or {}
                return cfg

    # Return sensible defaults
    return {
        "appflowy": {
            "data_dir": str(Path.home() / "Library/Application Support/com.appflowy.appflowy.flutter"),
        },
        "sources": [
            {
                "name": "Global Vault",
                "local_path": str(Path.home() / "Vault"),
                "tags": ["personal", "knowledge"],
                "workspace": "Global Vault",
            },
            {
                "name": "Public Vault",
                "local_path": str(Path.home() / "Vault" / "Public"),
                "tags": ["public", "blog"],
                "workspace": "Public Vault",
            },
            {
                "name": "Shared Vault",
                "local_path": str(Path.home() / "Vault" / "Shared"),
                "tags": ["shared", "collab"],
                "workspace": "Shared Vault",
            },
        ],
    }


def get_source_dirs(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Get source directories from config."""
    return config.get("sources", [])


def get_appflowy_data_dir(config: dict[str, Any]) -> str:
    """Get the AppFlowy data directory."""
    return config.get("appflowy", {}).get(
        "data_dir",
        str(Path.home() / "Library/Application Support/com.appflowy.appflowy.flutter"),
    )
