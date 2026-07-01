"""Tests for workflow persistence across manager instances."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.services.workflow_manager import WorkflowManager


class WorkflowPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_workflows.db"

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_workflow_persists_across_instances(self):
        """Verify that workflows saved to DB are readable by new instances."""
        with mock.patch(
            "app.core.settings.settings.data_dir",
            Path(self.temp_dir),
        ):
            # Create first manager and save a workflow
            manager1 = WorkflowManager()
            manager1.create_workflow(
                workflow_id="wf-test-001",
                name="Test Workflow",
                steps=[
                    {"type": "skill", "skill_id": "hello-world", "params": {}},
                ],
                description="A test workflow",
            )

            # Create second manager instance and verify workflow exists
            manager2 = WorkflowManager()
            retrieved = manager2.get_workflow("wf-test-001")

            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved["name"], "Test Workflow")
            self.assertEqual(len(retrieved["steps"]), 1)

    def test_logs_persist_across_instances(self):
        """Verify that workflow logs persist to DB."""
        with mock.patch(
            "app.core.settings.settings.data_dir",
            Path(self.temp_dir),
        ):
            manager1 = WorkflowManager()
            manager1.create_workflow(
                workflow_id="wf-log-test",
                name="Log Test",
                steps=[
                    {"type": "skill", "skill_id": "test", "params": {}},
                ],
            )
            manager1.record_log(
                workflow_id="wf-log-test",
                event="workflow-created",
                message="Test log entry",
                level="info",
            )

            manager2 = WorkflowManager()
            logs = manager2.get_logs("wf-log-test")
            self.assertGreater(len(logs), 0)
            self.assertEqual(logs[-1]["event"], "workflow-created")

    def test_run_history_persists(self):
        """Verify that workflow run results persist."""
        with mock.patch(
            "app.core.settings.settings.data_dir",
            Path(self.temp_dir),
        ):
            manager1 = WorkflowManager()
            manager1.create_workflow(
                workflow_id="wf-run-test",
                name="Run Test",
                steps=[
                    {"type": "skill", "skill_id": "test", "params": {}},
                ],
            )
            manager1.save_run(
                run_id="run-001",
                workflow_id="wf-run-test",
                workflow_name="Run Test",
                started_at="2026-06-23T10:00:00Z",
                finished_at="2026-06-23T10:00:05Z",
                status="completed",
                steps=[{"index": 1, "success": True}],
            )

            manager2 = WorkflowManager()
            runs = manager2.get_run_history("wf-run-test")
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["run_id"], "run-001")
            self.assertEqual(runs[0]["status"], "completed")
