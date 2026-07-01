"""daily_backup — Scheduled daily backup skill.

Runs backup skill at 3 AM with comprehensive data preservation.

Usage:
  POST /api/skills/daily_backup/run
  Body: { "type": "full" | "config" | "database" }
"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.daily_backup")

BACKUP_DIR = Path.home() / ".ucore/backups"
RETENTION_DAYS = 14


class DailyBackup(BaseSkill):
    meta = SkillMeta(
        id="daily_backup",
        name="Daily Backup",
        description="Scheduled daily backup of uCore data, config, and secrets",
        category="maintenance",
        timeout=120,
        params=[
            SkillParam(
                name="type",
                type="string",
                required=False,
                default="full",
                description="Backup type: full, database, config, secrets",
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        backup_type = kwargs.get("type", "full").strip().lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {}

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        if backup_type in ("full", "database"):
            results["database"] = self._backup_database(timestamp)
        if backup_type in ("full", "config"):
            results["config"] = self._backup_config(timestamp)
        if backup_type in ("full", "secrets"):
            results["secrets"] = self._backup_secrets(timestamp)

        self._cleanup_old_backups()

        return {
            "success": True,
            "timestamp": timestamp,
            "backup_dir": str(BACKUP_DIR),
            "type": backup_type,
            "results": results,
        }

    def _backup_database(self, timestamp: str) -> dict:
        from app.core.settings import settings
        db_path = settings.data_dir
        backup_file = BACKUP_DIR / f"database_{timestamp}.sqlite"

        if not db_path.exists():
            return {"status": "skipped", "reason": "No database directory found"}

        db_file = db_path / "ucore.db"
        if db_file.exists():
            shutil.copy2(db_file, backup_file)
            size_kb = backup_file.stat().st_size / 1024
            return {"status": "ok", "file": str(backup_file), "size_kb": round(size_kb, 1)}
        return {"status": "skipped", "reason": "No database file"}

    def _backup_config(self, timestamp: str) -> dict:
        from app.core.settings import settings
        config_dirs = [
            settings.config_dir,
            settings.udos_root / "uCore/config",
        ]
        backup_file = BACKUP_DIR / f"config_{timestamp}.tar.gz"

        files_to_backup = []
        for d in config_dirs:
            if d.exists():
                for f in d.rglob("*"):
                    if f.is_file():
                        files_to_backup.append(str(f))

        if not files_to_backup:
            return {"status": "skipped", "reason": "No config files found"}

        import tarfile
        with tarfile.open(backup_file, "w:gz") as tar:
            for f in files_to_backup:
                path = Path(f)
                try:
                    arcname = str(path.relative_to(Path.home()))
                except ValueError:
                    arcname = path.name
                tar.add(f, arcname=arcname)

        size_kb = backup_file.stat().st_size / 1024
        return {
            "status": "ok",
            "file": str(backup_file),
            "size_kb": round(size_kb, 1),
            "files": len(files_to_backup),
        }

    def _backup_secrets(self, timestamp: str) -> dict:
        from app.core.settings import settings
        secrets_file = settings.secrets_file
        key_file = settings.secret_key_file
        backup_file = BACKUP_DIR / f"secrets_{timestamp}"

        if not secrets_file.exists():
            return {"status": "skipped", "reason": "No secrets file found"}

        backup_file.mkdir(exist_ok=True)
        (backup_file / "secrets.enc").write_bytes(secrets_file.read_bytes())
        if key_file.exists():
            (backup_file / ".store_key").write_bytes(key_file.read_bytes())

        size_kb = sum(f.stat().st_size for f in backup_file.rglob("*")) / 1024
        return {"status": "ok", "dir": str(backup_file), "size_kb": round(size_kb, 1)}

    def _cleanup_old_backups(self):
        """Remove backups older than RETENTION_DAYS."""
        import time
        cutoff = time.time() - (RETENTION_DAYS * 86400)
        removed = 0
        for f in BACKUP_DIR.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
            elif f.is_dir() and f.stat().st_mtime < cutoff:
                shutil.rmtree(f)
                removed += 1
        if removed:
            log.info(f"Cleaned up {removed} old backups")
