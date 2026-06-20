"""Tests for ContainerManager service."""
from __future__ import annotations

import pytest
from app.models.container import ContainerRuntime, ContainerStatus
from app.services.container_manager import ContainerManager


class TestContainerManager:
    def setup_method(self):
        self.mgr = ContainerManager(persist=False)

    def test_create_container(self):
        c = self.mgr.create_container("Test", ContainerRuntime.PYTHON)
        assert c.name == "Test"
        assert c.runtime == ContainerRuntime.PYTHON
        assert c.status == ContainerStatus.CREATED
        assert len(c.id) > 0

    def test_get_container(self):
        c = self.mgr.create_container("Find Me", ContainerRuntime.NODE)
        found = self.mgr.get_container(c.id)
        assert found is not None
        assert found.name == "Find Me"

    def test_get_nonexistent(self):
        assert self.mgr.get_container("nope") is None

    def test_list_containers(self):
        self.mgr.create_container("A", ContainerRuntime.PYTHON)
        self.mgr.create_container("B", ContainerRuntime.NODE)
        self.mgr.create_container("C", ContainerRuntime.BASH)
        assert len(self.mgr.list_containers()) == 3

    def test_list_by_status(self):
        c1 = self.mgr.create_container("A", ContainerRuntime.PYTHON)
        c2 = self.mgr.create_container("B", ContainerRuntime.NODE)
        self.mgr.start_container(c1.id)
        self.mgr.start_container(c2.id)
        self.mgr.stop_container(c1.id)
        running = self.mgr.list_containers(ContainerStatus.RUNNING)
        stopped = self.mgr.list_containers(ContainerStatus.STOPPED)
        assert len(running) == 1
        assert len(stopped) == 1

    def test_start_stop_cycle(self):
        c = self.mgr.create_container("Cycle", ContainerRuntime.PYTHON)
        assert c.status == ContainerStatus.CREATED
        self.mgr.start_container(c.id)
        assert self.mgr.get_container(c.id).status == ContainerStatus.RUNNING
        self.mgr.stop_container(c.id)
        assert self.mgr.get_container(c.id).status == ContainerStatus.STOPPED

    def test_start_nonexistent(self):
        assert self.mgr.start_container("nope") is None

    def test_stop_nonexistent(self):
        assert self.mgr.stop_container("nope") is None

    def test_delete_container(self):
        c = self.mgr.create_container("Delete Me", ContainerRuntime.PYTHON)
        assert self.mgr.count() == 1
        assert self.mgr.delete_container(c.id) is True
        assert self.mgr.count() == 0
        assert self.mgr.delete_container("nope") is False

    def test_get_logs(self):
        c = self.mgr.create_container("Logger", ContainerRuntime.BASH)
        self.mgr.start_container(c.id)
        self.mgr.stop_container(c.id)
        logs = self.mgr.get_container_logs(c.id)
        assert logs is not None
        assert len(logs) == 2
        assert "Started" in logs[0]
        assert "Stopped" in logs[1]

    def test_get_logs_tail(self):
        c = self.mgr.create_container("Tail Test", ContainerRuntime.PYTHON)
        self.mgr.start_container(c.id)
        self.mgr.stop_container(c.id)
        logs = self.mgr.get_container_logs(c.id, tail=1)
        assert logs is not None
        assert len(logs) == 1
        assert "Stopped" in logs[0]

    def test_count_by_status(self):
        c1 = self.mgr.create_container("A", ContainerRuntime.PYTHON)
        c2 = self.mgr.create_container("B", ContainerRuntime.NODE)
        c3 = self.mgr.create_container("C", ContainerRuntime.DOCKER)
        self.mgr.start_container(c1.id)
        self.mgr.start_container(c2.id)
        self.mgr.start_container(c3.id)
        self.mgr.stop_container(c1.id)
        assert self.mgr.count_by_status(ContainerStatus.RUNNING) == 2
        assert self.mgr.count_by_status(ContainerStatus.STOPPED) == 1

    def test_persistent_lifecycle(self):
        """Test that containers persist across instances."""
        from app.core.database import migrate_db
        migrate_db()  # Ensure tables exist
        mgr = ContainerManager(persist=True)
        c = mgr.create_container("Persist", ContainerRuntime.PYTHON)
        mgr.start_container(c.id)
        mgr2 = ContainerManager(persist=True)
        loaded = mgr2.get_container(c.id)
        assert loaded is not None
        assert loaded.status == ContainerStatus.RUNNING
        mgr2.stop_container(c.id)
        stopped = mgr2.get_container(c.id)
        assert stopped is not None
        assert stopped.status == ContainerStatus.STOPPED
        mgr2.delete_container(c.id)
