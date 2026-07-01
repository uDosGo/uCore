"""Surface runtime manager for on-demand process launch/stop.

Provides a lightweight launcher for known local surfaces that need an
actual process (for example, Vue UI Hub on Vite port 5174).
"""
from __future__ import annotations

import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.settings import settings


@dataclass(frozen=True)
class SurfaceRuntimeSpec:
    """Static runtime spec for a known surface."""

    surface_id: str
    cwd: Path
    command: list[str]
    port: int
    host: str = "127.0.0.1"


def _npm_bin() -> str:
    npm = shutil.which("npm")
    return npm or "npm"


class SurfaceRuntimeManager:
    """Launch/stop known surface runtimes and track managed processes."""

    def __init__(self) -> None:
        repo_root = settings.udos_root / "uCore"
        frontend_dir = repo_root / "frontend"
        self._specs: dict[str, SurfaceRuntimeSpec] = {
            "ui-hub": SurfaceRuntimeSpec(
                surface_id="ui-hub",
                cwd=repo_root / "frontend-vue",
                command=[
                    "pnpm",
                    "--filter",
                    "frontend-vue",
                    "run",
                    "dev",
                    "--",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "5174",
                ],
                port=5174,
            ),
        }
        self._aliases = {
            "uihub": "ui-hub",
            "frontend": "ui-hub",
        }
        self._processes: dict[str, subprocess.Popen[bytes]] = {}

    def _canonical_id(self, surface_id: str) -> str:
        key = surface_id.strip().lower()
        return self._aliases.get(key, key)

    def _is_port_open(self, host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=0.4):
                return True
        except OSError:
            return False

    def supports(self, surface_id: str) -> bool:
        canonical = self._canonical_id(surface_id)
        return canonical in self._specs

    def start(self, surface_id: str) -> dict | None:
        canonical = self._canonical_id(surface_id)
        spec = self._specs.get(canonical)
        if spec is None:
            return None

        if self._is_port_open(spec.host, spec.port):
            return {
                "success": True,
                "surface_id": canonical,
                "status": "running",
                "port": spec.port,
                "managed": canonical in self._processes,
                "message": f"{canonical} already running on {spec.port}",
            }

        existing = self._processes.get(canonical)
        if existing is not None and existing.poll() is None:
            return {
                "success": True,
                "surface_id": canonical,
                "status": "starting",
                "port": spec.port,
                "pid": existing.pid,
                "managed": True,
                "message": f"{canonical} is starting",
            }

        if not spec.cwd.exists():
            return {
                "success": False,
                "surface_id": canonical,
                "status": "error",
                "port": spec.port,
                "managed": False,
                "message": f"Surface cwd not found: {spec.cwd}",
            }

        try:
            proc = subprocess.Popen(
                spec.command,
                cwd=str(spec.cwd),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as exc:
            return {
                "success": False,
                "surface_id": canonical,
                "status": "error",
                "port": spec.port,
                "managed": False,
                "message": str(exc),
            }

        self._processes[canonical] = proc

        deadline = time.time() + 6.0
        while time.time() < deadline:
            if self._is_port_open(spec.host, spec.port):
                return {
                    "success": True,
                    "surface_id": canonical,
                    "status": "running",
                    "port": spec.port,
                    "pid": proc.pid,
                    "managed": True,
                    "message": f"Started {canonical} on {spec.port}",
                }
            if proc.poll() is not None:
                return {
                    "success": False,
                    "surface_id": canonical,
                    "status": "error",
                    "port": spec.port,
                    "managed": True,
                    "exit_code": proc.returncode,
                    "message": f"{canonical} exited early",
                }
            time.sleep(0.2)

        return {
            "success": True,
            "surface_id": canonical,
            "status": "starting",
            "port": spec.port,
            "pid": proc.pid,
            "managed": True,
            "message": f"Launched {canonical}; waiting for {spec.port}",
        }

    def stop(self, surface_id: str) -> dict | None:
        canonical = self._canonical_id(surface_id)
        spec = self._specs.get(canonical)
        if spec is None:
            return None

        proc = self._processes.get(canonical)
        if proc is None:
            running = self._is_port_open(spec.host, spec.port)
            return {
                "success": not running,
                "surface_id": canonical,
                "status": "running" if running else "stopped",
                "port": spec.port,
                "managed": False,
                "message": (
                    f"{canonical} is running but unmanaged"
                    if running
                    else f"{canonical} already stopped"
                ),
            }

        if proc.poll() is not None:
            self._processes.pop(canonical, None)
            return {
                "success": True,
                "surface_id": canonical,
                "status": "stopped",
                "port": spec.port,
                "managed": True,
                "message": f"{canonical} already exited",
            }

        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)

        self._processes.pop(canonical, None)
        return {
            "success": True,
            "surface_id": canonical,
            "status": "stopped",
            "port": spec.port,
            "managed": True,
            "message": f"Stopped {canonical}",
        }

    def restart(self, surface_id: str) -> dict | None:
        canonical = self._canonical_id(surface_id)
        if canonical not in self._specs:
            return None
        self.stop(canonical)
        return self.start(canonical)


_runtime_manager: SurfaceRuntimeManager | None = None


def get_surface_runtime_manager() -> SurfaceRuntimeManager:
    global _runtime_manager
    if _runtime_manager is None:
        _runtime_manager = SurfaceRuntimeManager()
    return _runtime_manager
