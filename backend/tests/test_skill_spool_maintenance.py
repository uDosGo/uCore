from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_spool_maintenance_rotates_and_prunes(
    tmp_path: Path,
    monkeypatch,
):
    from app.core.settings import settings
    from app.skills.builtin.spool_maintenance import SpoolMaintenance

    monkeypatch.setattr(settings, "logs_dir", tmp_path)

    active = tmp_path / "snackbar.log"
    active.write_text("X" * 32, encoding="utf-8")

    rotated_1 = tmp_path / "snackbar.log.1"
    rotated_1.write_text("old-1", encoding="utf-8")

    rotated_3 = tmp_path / "snackbar.log.3"
    rotated_3.write_text("old-3", encoding="utf-8")

    old_ts = (datetime.now(timezone.utc) - timedelta(days=30)).timestamp()
    rotated_3.touch()
    rotated_3.chmod(0o644)
    import os
    os.utime(rotated_3, (old_ts, old_ts))

    result = await SpoolMaintenance().run(
        max_bytes=8,
        backup_count=2,
        max_age_days=14,
    )

    assert result["success"] is True
    assert result["rotated"] == 1
    assert result["removed_old"] >= 1
    assert active.exists()
    assert (tmp_path / "snackbar.log.1").exists()


@pytest.mark.asyncio
async def test_spool_maintenance_creates_logs_dir(
    tmp_path: Path,
    monkeypatch,
):
    from app.core.settings import settings
    from app.skills.builtin.spool_maintenance import SpoolMaintenance

    logs_dir = tmp_path / "logs"
    monkeypatch.setattr(settings, "logs_dir", logs_dir)

    result = await SpoolMaintenance().run(max_bytes=1024)

    assert result["success"] is True
    assert logs_dir.exists()
    assert result["rotated"] == 0
