"""uCore settings — unified configuration for snackbar + hivemind + API"""
from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    """Central uCore configuration."""

    # ── General ──────────────────────────────────────────────
    debug: bool = os.environ.get(
        "UCORE_DEBUG",
        "0",
    ).lower() in ("1", "true", "yes")
    app_name: str = "uCore"
    version: str = "4.0.5"

    # ── Server ───────────────────────────────────────────────
    host: str = os.environ.get("UCORE_HOST", "0.0.0.0")
    port: int = int(os.environ.get("UCORE_PORT", "8484"))
    auto_start: bool = os.environ.get(
        "UCORE_AUTO_START",
        "0",
    ).lower() in ("1", "true", "yes")

    # ── Paths ────────────────────────────────────────────────
    data_dir: Path = Path(
        os.environ.get("UCORE_DATA_DIR", os.path.expanduser("~/.ucore/data")),
    )
    config_dir: Path = Path(
        os.environ.get(
            "UCORE_CONFIG_DIR",
            os.path.expanduser("~/.ucore/config"),
        ),
    )
    logs_dir: Path = Path(
        os.environ.get("UCORE_LOGS_DIR", os.path.expanduser("~/.ucore/logs")),
    )
    secrets_dir: Path = Path(
        os.environ.get("UCORE_SECRETS_DIR", os.path.expanduser("~/.ucore")),
    )

    # ── Snackbar ─────────────────────────────────────────────
    snack_timeout: int = int(os.environ.get("UCORE_SNACK_TIMEOUT", "300"))
    snack_history_size: int = int(os.environ.get("UCORE_SNACK_HISTORY", "100"))

    # ── Surfaces ─────────────────────────────────────────────
    surface_registry_path: str = os.environ.get(
        "UCORE_SURFACE_REGISTRY",
        os.path.expanduser("~/.ucore/surfaces.json"),
    )

    # ── Security ─────────────────────────────────────────────
    require_auth: bool = os.environ.get(
        "UCORE_REQUIRE_AUTH",
        "0",
    ).lower() in ("1", "true")
    api_key: str | None = os.environ.get("UCORE_API_KEY", None)

    # ── Services ─────────────────────────────────────────────
    enable_cors: bool = os.environ.get(
        "UCORE_ENABLE_CORS",
        "1",
    ).lower() in ("1", "true", "yes")

    # ── Identity / User ──────────────────────────────────────
    user_name: str = os.environ.get("UCORE_USER_NAME", os.environ.get("USER", "fredbook"))
    user_email: str = os.environ.get("UCORE_USER_EMAIL", "fred@okagent.digital")
    install_name: str = os.environ.get("UDOS_INSTALL_NAME", socket.gethostname())

    # ── Spine (Code base path — all repos under ~/Code/) ─────
    udos_root: Path = Path(
        os.environ.get(
            "UDOS_ROOT",
            os.environ.get(
                "ROOT",
                os.environ.get("UDOS_CODE", os.path.expanduser("~/Code")),
            ),
        ),
    ).expanduser()

    # ── Ollama / AI ──────────────────────────────────────────
    ollama_base_url: str = os.environ.get(
        "UCORE_OLLAMA_URL", "http://localhost:11434",
    )
    ollama_default_model: str = os.environ.get(
        "UCORE_OLLAMA_MODEL", "qwen2.5-coder:3b",
    )
    ollama_fallback_model: str = os.environ.get(
        "UCORE_OLLAMA_FALLBACK_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M",
    )
    ollama_timeout: int = int(os.environ.get("UCORE_OLLAMA_TIMEOUT", "60"))

    # ── Tray / Shortcuts ──────────────────────────────────────
    clipboard_shortcut: str = os.environ.get(
        "UCORE_CLIPBOARD_SHORTCUT", "ctrl+cmd+v",
    )

    @property
    def secrets_file(self) -> Path:
        return self.secrets_dir / "secrets.enc"

    @property
    def secret_key_file(self) -> Path:
        return self.secrets_dir / ".store_key"


# Singleton
settings = Settings()
