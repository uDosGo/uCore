"""Ollama Snack — Ollama LLM server management for uCore menu."""
from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

from snackmachine.registry import SnackPlugin, SnackSpec, register_snack

log = logging.getLogger("ollama-snack")


class OllamaSnack(SnackPlugin):
    """Ollama server management snack."""

    def __init__(self, menu_delegate=None):
        self._menu_delegate = menu_delegate
        self._status = "checking"
        self._models = []
        self._disable_file = Path("~/.ucore/ollama_disabled").expanduser()

    @property
    def spec(self) -> SnackSpec:
        # Dynamic icon based on status
        icon = "🏖️" if self._status == "running" else "○"
        if self._status == "checking":
            icon = "⟳"
        elif self._disable_file.exists():
            icon = "○"

        return SnackSpec(
            id="ollama-manager",
            name="Ollama",
            icon=icon,
            kind="multi-action",
            category="ai",
            enabled=True,
            actions=["start", "stop", "restart"],
            metadata={
                "status": self._status,
                "models": self._models,
                "description": "Manage local Ollama LLM server",
            },
        )

    def is_available(self) -> bool:
        return True  # Always available

    def execute(self, action: Optional[str] = None, **kwargs) -> Any:
        if action == "start":
            return self._start_ollama()
        elif action == "stop":
            return self._stop_ollama()
        elif action == "restart":
            self._stop_ollama()
            time.sleep(2)
            return self._start_ollama()
        return False

    def _start_ollama(self) -> bool:
        """Start Ollama server explicitly."""
        log.info("Starting Ollama from menu...")
        try:
            # Remove disable flag so watchdog doesn't kill it
            if self._disable_file.exists():
                self._disable_file.unlink()

            # Start ollama serve as standalone process
            proc = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            log.info("Ollama started (PID %s)", proc.pid)
            self._status = "checking"
            if self._menu_delegate:
                self._menu_delegate.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "updateUI:", None, False
                )
            time.sleep(2)
            self._refresh_status()
            return True
        except Exception as e:
            log.exception("Failed to start Ollama: %s", e)
            return False

    def _stop_ollama(self) -> bool:
        """Stop Ollama server permanently (sets disable flag)."""
        log.info("Stopping Ollama permanently...")
        try:
            # Kill all ollama processes
            result = subprocess.run(
                ["pgrep", "-f", "ollama"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            pids = [int(p) for p in result.stdout.strip().splitlines() if p.strip()]
            pids = [p for p in pids if p != __import__("os").getpid()]

            if pids:
                for pid in pids:
                    try:
                        __import__("os").kill(pid, 9)
                    except (ProcessLookupError, OSError):
                        pass

            # Kill leftover processes
            for leftover in ["ollama_llama_server", "ollama-runner"]:
                with __import__("contextlib").suppress(Exception):
                    subprocess.run(
                        ["pkill", "-9", leftover],
                        capture_output=True,
                        timeout=3,
                        check=False,
                    )

            # Set disable flag
            self._disable_file.parent.mkdir(parents=True, exist_ok=True)
            self._disable_file.write_text(f"disabled by menu at {time.time()}")

            self._status = "stopped"
            self._models = []
            if self._menu_delegate:
                self._menu_delegate.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "updateUI:", None, False
                )
            log.info("Ollama fully stopped and disabled")
            return True
        except Exception as e:
            log.exception("Failed to stop Ollama: %s", e)
            return False

    def _refresh_status(self) -> None:
        """Refresh Ollama status and models."""
        try:
            import json
            import urllib.request

            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._models = [m["name"] for m in data.get("models", [])]
                self._status = "running"
        except Exception:
            if self._disable_file.exists():
                self._status = "stopped"
            else:
                self._status = "installed"
            self._models = []

        if self._menu_delegate:
            self._menu_delegate.performSelectorOnMainThread_withObject_waitUntilDone_(
                "updateUI:", None, False
            )

    def update_status(self, status: str, models: list = None) -> None:
        """Update status from external refresh."""
        self._status = status
        if models is not None:
            self._models = models
        if self._menu_delegate:
            self._menu_delegate.performSelectorOnMainThread_withObject_waitUntilDone_(
                "updateUI:", None, False
            )


# Register on import
def register(menu_delegate=None):
    """Register the Ollama snack."""
    plugin = OllamaSnack(menu_delegate)
    register_snack(plugin)
    return plugin
