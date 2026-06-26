"""Tests for SnackbarOrchestrator service."""
from __future__ import annotations

from app.models.snack import SnackPriority, SnackStatus, SnackType
from app.services.snackbar_orchestrator import SnackbarOrchestrator


class TestSnackbarOrchestrator:
    def setup_method(self):
        self.orch = SnackbarOrchestrator(persist=False)

    def test_queue_snack(self):
        sn = self.orch.queue_snack(SnackType.TASK, {"cmd": "test"}, SnackPriority.HIGH)
        assert sn.type == SnackType.TASK
        assert sn.priority == SnackPriority.HIGH
        assert sn.status == SnackStatus.QUEUED
        assert self.orch.pending_count() == 1

    def test_get_queue_priority_order(self):
        self.orch.queue_snack(SnackType.TASK, {}, SnackPriority.LOW)
        self.orch.queue_snack(SnackType.TASK, {}, SnackPriority.HIGH)
        self.orch.queue_snack(SnackType.TASK, {}, SnackPriority.CRITICAL)
        queue = self.orch.get_queue()
        assert queue[0].priority == SnackPriority.CRITICAL
        assert queue[1].priority == SnackPriority.HIGH
        assert queue[2].priority == SnackPriority.LOW

    def test_deliver_next(self):
        self.orch.queue_snack(SnackType.MESSAGE, {"msg": "hi"}, SnackPriority.NORMAL)
        delivered = self.orch.deliver_next()
        assert delivered is not None
        assert delivered.status == SnackStatus.DELIVERED
        assert self.orch.pending_count() == 0
        assert len(self.orch.get_history()) == 1

    def test_deliver_next_empty(self):
        assert self.orch.deliver_next() is None

    def test_deliver_specific(self):
        sn = self.orch.queue_snack(SnackType.EVENT, {"evt": "test"})
        delivered = self.orch.deliver_snack(sn.id)
        assert delivered is not None
        assert delivered.status == SnackStatus.DELIVERED
        assert self.orch.pending_count() == 0

    def test_deliver_nonexistent(self):
        assert self.orch.deliver_snack("nope") is None

    def test_fail_snack(self):
        sn = self.orch.queue_snack(SnackType.TASK, {"task": "fail_me"})
        failed = self.orch.fail_snack(sn.id)
        assert failed is not None
        assert failed.status == SnackStatus.FAILED

    def test_retry_snack(self):
        sn = self.orch.queue_snack(SnackType.TASK, {"task": "retry_me"})
        self.orch.fail_snack(sn.id)
        retried = self.orch.retry_snack(sn.id)
        assert retried is not None
        assert retried.status == SnackStatus.QUEUED
        assert retried.retry_count == 1

    def test_clear_queue(self):
        self.orch.queue_snack(SnackType.MESSAGE, {})
        self.orch.queue_snack(SnackType.MESSAGE, {})
        self.orch.queue_snack(SnackType.MESSAGE, {})
        assert self.orch.clear_queue() == 3
        assert self.orch.pending_count() == 0

    def test_history_limit(self):
        for i in range(5):
            sn = self.orch.queue_snack(SnackType.MESSAGE, {"i": i})
            self.orch.deliver_snack(sn.id)
        history = self.orch.get_history(limit=2)
        assert len(history) == 2

    def test_persistent_queue_survives_restart(self):
        """Test that persistent mode preserves snacks across instances."""
        from app.core.database import migrate_db
        migrate_db()
        orch = SnackbarOrchestrator(persist=True)
        sn = orch.queue_snack(SnackType.TASK, {"cmd": "test"}, SnackPriority.HIGH)
        orch2 = SnackbarOrchestrator(persist=True)
        queue = orch2.get_queue()
        assert len(queue) >= 1
        assert queue[0].id == sn.id
        assert queue[0].type == SnackType.TASK
        orch2.clear_queue()

    def test_persistent_history(self):
        """Test that delivered snacks persist across instances."""
        orch = SnackbarOrchestrator(persist=True)
        sn = orch.queue_snack(SnackType.MESSAGE, {"msg": "persist"})
        orch.deliver_snack(sn.id)
        orch2 = SnackbarOrchestrator(persist=True)
        history = orch2.get_history()
        assert len(history) >= 1
        assert history[0].id == sn.id
        assert history[0].status == SnackStatus.DELIVERED
        # Clean up
