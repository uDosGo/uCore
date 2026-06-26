from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.settings import settings
from app.skills.base import BaseSkill, SkillMeta, SkillParam

ROTATED_SUFFIX_RE = re.compile(r"^(?P<name>.+\.log)\.(?P<index>\d+)$")
DEFAULT_MAX_BYTES = 2 * 1024 * 1024
DEFAULT_BACKUP_COUNT = 5
DEFAULT_MAX_AGE_DAYS = 14


class SpoolMaintenance(BaseSkill):
    meta = SkillMeta(
        id="spool_maintenance",
        name="Spool Maintenance",
        description="Rotate and prune spool log files under ~/.ucore/logs",
        category="maintenance",
        timeout=30,
        params=[
            SkillParam(
                name="max_bytes",
                type="number",
                required=False,
                default=DEFAULT_MAX_BYTES,
            ),
            SkillParam(
                name="backup_count",
                type="number",
                required=False,
                default=DEFAULT_BACKUP_COUNT,
            ),
            SkillParam(
                name="max_age_days",
                type="number",
                required=False,
                default=DEFAULT_MAX_AGE_DAYS,
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        logs_dir = settings.logs_dir
        max_bytes = int(kwargs.get("max_bytes", DEFAULT_MAX_BYTES))
        backup_count = max(
            1,
            int(kwargs.get("backup_count", DEFAULT_BACKUP_COUNT)),
        )
        max_age_days = max(
            1,
            int(kwargs.get("max_age_days", DEFAULT_MAX_AGE_DAYS)),
        )

        logs_dir.mkdir(parents=True, exist_ok=True)

        rotated = 0
        removed_old = 0
        active_files = sorted(logs_dir.glob("*.log"))

        for log_file in active_files:
            if not log_file.is_file():
                continue
            if log_file.stat().st_size <= max_bytes:
                continue
            self._rotate_file(log_file, backup_count)
            rotated += 1

        cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
        for path in sorted(logs_dir.iterdir()):
            if not path.is_file():
                continue
            if not ROTATED_SUFFIX_RE.match(path.name):
                continue
            if self._is_older_than(path, cutoff):
                path.unlink(missing_ok=True)
                removed_old += 1

        return {
            "success": True,
            "logs_dir": str(logs_dir),
            "rotated": rotated,
            "removed_old": removed_old,
            "max_bytes": max_bytes,
            "backup_count": backup_count,
            "max_age_days": max_age_days,
        }

    def _rotate_file(self, log_file: Path, backup_count: int) -> None:
        oldest = log_file.with_name(f"{log_file.name}.{backup_count}")
        oldest.unlink(missing_ok=True)

        for idx in range(backup_count - 1, 0, -1):
            src = log_file.with_name(f"{log_file.name}.{idx}")
            dst = log_file.with_name(f"{log_file.name}.{idx + 1}")
            if src.exists():
                src.rename(dst)

        first = log_file.with_name(f"{log_file.name}.1")
        if first.exists():
            first.unlink(missing_ok=True)
        log_file.rename(first)
        log_file.touch()

    def _is_older_than(self, path: Path, cutoff: datetime) -> bool:
        modified = datetime.fromtimestamp(
            path.stat().st_mtime,
            tz=UTC,
        )
        return modified < cutoff
