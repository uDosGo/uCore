"""AppFlowy Workspace Sync Snack — Mirror local vault to AppFlowy workspace.

Provides menu bar integration for syncing uDos Vault to self-hosted AppFlowy.
Uses direct SQLite database access (no HTTP API required).
Configuration stored in secret store for security.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from snackmachine.registry import SnackPlugin, SnackSpec, register_snack
from app.secret.store import SecretStore

log = logging.getLogger("appflowy-sync-snack")

# Configuration
VAULT_PATH = os.path.expanduser("~/vault")
SPOOL_PATH = Path(
    os.environ.get(
        "UCORE_SNACKS_REPLIES", "~/.local/share/snackmachine/replies.jsonl"
    )
).expanduser()
SYNC_CONFIG_PATH = os.path.expanduser("~/.ucore/sync_config.yaml")
SECRET_KEY_APPFLOWY_DATA_DIR = "appflowy_data_dir"


class AppFlowySyncSnack(SnackPlugin):
    """AppFlowy workspace sync snack for vault mirroring."""

    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate
        self._last_sync_status = "idle"
        self._last_sync_result: dict[str, Any] = {}

    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(
            id="appflowy-workspace-sync",
            name="AppFlowy Sync",
            icon="📦",
            kind="multi-action",
            category="system",
            enabled=True,
            actions=[
                "sync-full-vault",
                "sync-binder",
                "view-status",
                "open-settings",
            ],
            metadata={
                "description": "Sync local vault to AppFlowy workspace",
                "last_sync": self._last_sync_status,
            },
        )

    def is_available(self) -> bool:
        """Check if AppFlowy data directory exists (from secret store)."""
        try:
            store = SecretStore()
            store.load()
            data_dir = store.get(SECRET_KEY_APPFLOWY_DATA_DIR)
            if not data_dir:
                # Fallback to config file
                from app.af_manager.config import (
                    load_config,
                    get_appflowy_data_dir,
                )
                config = load_config(SYNC_CONFIG_PATH)
                data_dir = get_appflowy_data_dir(config)
            return Path(data_dir).expanduser().exists()
        except Exception:
            return False

    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if action == "sync-full-vault":
            return self._sync_full_vault()
        elif action == "sync-binder":
            binder = kwargs.get("binder", "vault_sync")
            return self._sync_binder(binder)
        elif action == "view-status":
            return self._view_status()
        elif action == "open-settings":
            return self._open_settings()
        else:
            log.warning(f"Unknown appflowy sync action: {action}")
            return False

    def _log_to_spool(
        self, status: str, output: str, binder: str = "vault"
    ) -> None:
        """Log result to Snackbar spool."""
        SPOOL_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "snack_id": "appflowy_sync",
            "status": status,
            "output": output,
            "binder": binder,
            "timestamp": self._get_timestamp(),
        }
        with open(SPOOL_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _get_timestamp(self) -> str:
        """Get ISO timestamp."""
        from datetime import UTC, datetime
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _sync_full_vault(self) -> bool:
        """Sync entire vault to AppFlowy using existing sync engine."""
        return self._sync_binder("vault_sync")

    def _sync_binder(self, binder_name: str) -> bool:
        """Sync a specific binder/vault to AppFlowy workspace."""
        try:
            # Use the existing af_manager sync module
            import importlib
            run_import = importlib.import_module(
                "app.af_manager.sync"
            ).run_import
            load_config = importlib.import_module(
                "app.af_manager.config"
            ).load_config

            config = load_config(SYNC_CONFIG_PATH)

            # Get data_dir from secret store (preferred) or config
            store = SecretStore()
            store.load()
            data_dir = store.get(SECRET_KEY_APPFLOWY_DATA_DIR)
            if data_dir:
                config["appflowy"] = config.get("appflowy", {})
                config["appflowy"]["data_dir"] = data_dir

            # Filter to specific source if binder_name provided
            if binder_name and binder_name != "vault_sync":
                sources = config.get("sources", [])
                matched = [s for s in sources if s.get("name") == binder_name]
                if matched:
                    config["sources"] = matched
                else:
                    self._log_to_spool(
                        "error",
                        f"Binder not found: {binder_name}",
                        binder_name,
                    )
                    return False

            log.info(f"Running AppFlowy sync for: {binder_name}")
            result = run_import(config)

            self._last_sync_result = result
            success = result.get("success", False)
            self._last_sync_status = "success" if success else "error"
            self._log_to_spool(
                "success" if success else "error",
                f"Synced {result.get('imported', 0)} files",
                binder_name,
            )
            return result.get("success", False)

        except Exception as e:
            log.exception(f"Sync failed: {e}")
            self._last_sync_status = "error"
            self._log_to_spool("error", str(e), binder_name)
            return False

    def _view_status(self) -> bool:
        """Show sync status."""
        log.info(f"Last sync status: {self._last_sync_status}")
        log.info(f"Last sync result: {self._last_sync_result}")
        return True

    def _open_settings(self) -> bool:
        """Open AppFlowy sync config for editing and prompt for data_dir."""
        config_path = Path(SYNC_CONFIG_PATH)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create default config if not exists
        if not config_path.exists():
            config_path.write_text(
                "# AppFlowy sync configuration\n"
                "# data_dir can be stored in secret store for security\n"
                "appflowy:\n"
                "  data_dir: ~/Library/Application Support/"
                "com.appflowy.appflowy.flutter\n"
                "sources:\n"
                "  - name: Global Vault\n"
                "    local_path: ~/vault\n"
                "    tags: [personal, knowledge]\n"
            )

        # Open the config file in default editor
        subprocess.run(["open", str(config_path)], check=False)

        # Also open secret store UI if available
        try:
            from app.secret.store import SecretStore
            store = SecretStore()
            store.load()
            # Check if we should prompt for data_dir in secret store
            if not store.get(SECRET_KEY_APPFLOWY_DATA_DIR):
                log.info("Consider storing appflowy_data_dir in secret store")
        except Exception:
            pass

        return True


# Register on import
def register(menu_delegate=None):
    """Register the AppFlowy sync snack."""
    plugin = AppFlowySyncSnack(menu_delegate)
    register_snack(plugin)
    return plugin

