"""ContainerManager — runtime environment lifecycle for uCore.

Supports both in-memory and SQLite persistence backends.
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone

from app.models.container import Container, ContainerRuntime, ContainerStatus
from app.core.database import get_db, container_from_row, now_iso, to_json, from_json


class ContainerManager:
    """Manages the lifecycle of runtime containers with optional SQLite persistence."""

    def __init__(self, persist: bool = True) -> None:
        self._persist = persist
        self._cache: dict[str, Container] = {}

    # ─── SQL Helpers ─────────────────────────────────────────────

    def _load_from_db(self, container_id: str) -> Optional[Container]:
        if not self._persist:
            return self._cache.get(container_id)
        with get_db() as db:
            cursor = db.execute("SELECT * FROM containers WHERE id = ?", (container_id,))
            row = cursor.fetchone()
            return Container(**container_from_row(row)) if row else None

    def _load_all_from_db(self, status: Optional[ContainerStatus] = None) -> list[Container]:
        if not self._persist:
            containers = list(self._cache.values())
            if status:
                containers = [c for c in containers if c.status == status]
            return containers
        with get_db() as db:
            if status:
                cursor = db.execute(
                    "SELECT * FROM containers WHERE status = ? ORDER BY created_at ASC",
                    (status.value,),
                )
            else:
                cursor = db.execute("SELECT * FROM containers ORDER BY created_at ASC")
            return [Container(**container_from_row(row)) for row in cursor.fetchall()]

    def _save_to_db(self, container: Container) -> None:
        if not self._persist:
            self._cache[container.id] = container
            return
        with get_db() as db:
            db.execute(
                """INSERT OR REPLACE INTO containers
                   (id, name, runtime, status, image,
                    dependencies_json, env_vars_json, ports_json, volumes_json,
                    command, logs_json, metadata_json,
                    created_at, updated_at, started_at, stopped_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    container.id,
                    container.name,
                    container.runtime.value,
                    container.status.value,
                    container.image,
                    to_json(container.dependencies),
                    to_json(container.env_vars),
                    to_json(container.ports),
                    to_json(container.volumes),
                    container.command,
                    to_json(container.logs),
                    to_json(container.metadata),
                    container.created_at.isoformat(),
                    container.updated_at.isoformat(),
                    container.started_at.isoformat() if container.started_at else None,
                    container.stopped_at.isoformat() if container.stopped_at else None,
                ),
            )

    def _delete_from_db(self, container_id: str) -> bool:
        if not self._persist:
            if container_id in self._cache:
                del self._cache[container_id]
                return True
            return False
        with get_db() as db:
            cursor = db.execute("DELETE FROM containers WHERE id = ?", (container_id,))
            return cursor.rowcount > 0

    # ─── Public API ──────────────────────────────────────────────

    def create_container(
        self,
        name: str,
        runtime: ContainerRuntime = ContainerRuntime.PYTHON,
        image: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
        env_vars: Optional[dict[str, str]] = None,
        command: Optional[str] = None,
    ) -> Container:
        container = Container(
            name=name,
            runtime=runtime,
            image=image,
            dependencies=dependencies or [],
            env_vars=env_vars or {},
            command=command,
        )
        self._save_to_db(container)
        return container

    def get_container(self, container_id: str) -> Optional[Container]:
        return self._load_from_db(container_id)

    def list_containers(self, status: Optional[ContainerStatus] = None) -> list[Container]:
        return self._load_all_from_db(status)

    def start_container(self, container_id: str) -> Optional[Container]:
        container = self._load_from_db(container_id)
        if container is None:
            return None
        container.start()
        self._save_to_db(container)
        return container

    def stop_container(self, container_id: str) -> Optional[Container]:
        container = self._load_from_db(container_id)
        if container is None:
            return None
        container.stop()
        self._save_to_db(container)
        return container

    def delete_container(self, container_id: str) -> bool:
        return self._delete_from_db(container_id)

    def get_container_logs(self, container_id: str, tail: Optional[int] = None) -> Optional[list[str]]:
        container = self._load_from_db(container_id)
        if container is None:
            return None
        return container.get_logs(tail=tail)

    def count(self) -> int:
        return len(self.list_containers())

    def count_by_status(self, status: ContainerStatus) -> int:
        return len(self.list_containers(status=status))
