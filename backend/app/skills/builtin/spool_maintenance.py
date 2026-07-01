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
PROJECT_ROOT = settings.udos_root / "uCore"


class SpoolMaintenance(BaseSkill):
    meta = SkillMeta(
        id="spool_maintenance",
        name="Spool Maintenance",
        description="Rotate, prune, and archive spool logs and completed tasks",
        category="maintenance",
        timeout=60,
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
            SkillParam(
                name="archive_completed_tasks",
                type="boolean",
                required=False,
                default=True,
                description="Archive completed tasks from .tasker to .tasker.archived",
            ),
            SkillParam(
                name="tasker_dir",
                type="string",
                required=False,
                default=str(PROJECT_ROOT / ".tasker"),
                description="Path to .tasker directory",
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
        archive_completed_tasks = bool(kwargs.get("archive_completed_tasks", True))
        tasker_dir = Path(kwargs.get("tasker_dir", PROJECT_ROOT / ".tasker")).expanduser()

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

        archived_tasks = 0
        if archive_completed_tasks and tasker_dir.exists():
            archived_tasks = self._archive_completed_tasks(tasker_dir)

        return {
            "success": True,
            "logs_dir": str(logs_dir),
            "rotated": rotated,
            "removed_old": removed_old,
            "archived_tasks": archived_tasks,
            "max_bytes": max_bytes,
            "backup_count": backup_count,
            "max_age_days": max_age_days,
        }

    def _archive_completed_tasks(self, tasker_dir: Path) -> int:
        """Archive completed tasks from .tasker to .tasker.archived."""
        archived_dir = tasker_dir.parent / ".tasker.archived"
        archived_dir.mkdir(parents=True, exist_ok=True)
        archived_count = 0

        for task_file in tasker_dir.rglob("*.md"):
            if task_file.name == "README.md":
                continue
            try:
                content = task_file.read_text(encoding="utf-8")
                if "status: done" in content or "status: completed" in content:
                    relative = task_file.relative_to(tasker_dir)
                    dest = archived_dir / relative
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    task_file.unlink(missing_ok=True)
                    archived_count += 1
            except Exception:
                continue

        return archived_count

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
