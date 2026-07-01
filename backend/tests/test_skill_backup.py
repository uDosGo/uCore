"""Tests for Backup and DailyBackup skills."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_backup_creates_file(tmp_path: Path, monkeypatch):
    """Backup skill copies the database to the destination."""
    from app.skills.builtin.backup import BackupData

    # Create a fake database to back up
    fake_db = tmp_path / "ucore.db"
    fake_db.write_text("fake sqlite content", encoding="utf-8")

    # Patch get_db_path inside the BackupData.run method
    import app.core.database as db_mod
    monkeypatch.setattr(db_mod, "get_db_path", lambda: str(fake_db))

    dest = tmp_path / "backups"
    dest.mkdir()

    skill = BackupData()
    result = await skill.run(destination=str(dest))
    assert result["success"] is True
    assert result["count"] > 0
    assert any("ucore-backup" in f["file"] for f in result["files"])


@pytest.mark.asyncio
async def test_daily_backup_full(tmp_path: Path, monkeypatch):
    """Daily backup runs without error."""
    from app.skills.builtin.daily_backup import DailyBackup

    monkeypatch.setattr("app.skills.builtin.daily_backup.BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr("app.skills.builtin.daily_backup.RETENTION_DAYS", 999)

    skill = DailyBackup()
    result = await skill.run(type="full")
    assert result["success"] is True
    assert result["type"] == "full"


@pytest.mark.asyncio
async def test_daily_backup_database_only(tmp_path: Path, monkeypatch):
    from app.skills.builtin.daily_backup import DailyBackup

    monkeypatch.setattr("app.skills.builtin.daily_backup.BACKUP_DIR", tmp_path / "backups")

    skill = DailyBackup()
    result = await skill.run(type="database")
    assert result["success"] is True
    assert result["type"] == "database"
