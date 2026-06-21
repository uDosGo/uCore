"""Focused tests for maintenance scheduler and vault sync skill."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_maintenance_scheduler_runs_jobs_once_in_order(tmp_path: Path, monkeypatch):
    import app.services.maintenance_scheduler as mod

    calls: list[str] = []

    async def fake_run_skill_by_id(skill_id: str, **kwargs):
        calls.append(skill_id)
        return {"success": True, "skill_id": skill_id, "params": kwargs}

    monkeypatch.setattr(mod, "run_skill_by_id", fake_run_skill_by_id)

    jobs = (
        mod.MaintenanceJob("daily_backup", "03:00", {"type": "full"}),
        mod.MaintenanceJob("vault_sync", "04:00", {"summary_only": True}),
        mod.MaintenanceJob("brain_sync", "04:15", {"hours": 24}),
    )
    scheduler = mod.MaintenanceScheduler(
        state_path=tmp_path / "maintenance-state.json",
        jobs=jobs,
        interval_seconds=60,
    )

    first = await scheduler.run_due(now=datetime(2026, 6, 21, 4, 20))
    second = await scheduler.run_due(now=datetime(2026, 6, 21, 4, 55))

    assert [entry["skill_id"] for entry in first] == ["daily_backup", "vault_sync", "brain_sync"]
    assert second == []
    assert calls == ["daily_backup", "vault_sync", "brain_sync"]


@pytest.mark.asyncio
async def test_vault_sync_skips_without_config(tmp_path: Path, monkeypatch):
    import app.skills.builtin.vault_sync as mod

    script = tmp_path / "appflowy_vault_sync.py"
    script.write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setattr(mod, "SCRIPT_PATH", script)
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)

    missing_config = tmp_path / "missing.yaml"
    result = await mod.VaultSync().run(config=str(missing_config), summary_only=True)

    assert result["success"] is True
    assert result["status"] == "skipped"
    assert "config not found" in result["reason"]
