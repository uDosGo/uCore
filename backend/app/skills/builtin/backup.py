from __future__ import annotations
from app.core.settings import settings
import asyncio, time
from pathlib import Path
from app.skills.base import BaseSkill, SkillMeta, SkillParam
from app.core.logging import log

class BackupData(BaseSkill):
    meta = SkillMeta(id="backup", name="Backup Data",
        description="Backup uCore database, config, secrets, wisdom.md, and user data",
        category="maintenance", timeout=120,
        params=[SkillParam(name="destination", type="string", default="~/.ucore/backups")])
    async def run(self, **kwargs) -> dict:
        dest = Path(kwargs.get("destination", "~/.ucore/backups")).expanduser()
        dest.mkdir(parents=True, exist_ok=True)
        from app.core.database import get_db_path
        db_path = get_db_path()
        ts = time.strftime("%Y%m%d-%H%M%S")

        backup_entries = []
        import shutil

        # 1. Database
        if db_path and Path(db_path).exists():
            backup_file = dest / f"ucore-backup-{ts}.db"
            shutil.copy2(db_path, backup_file)
            backup_entries.append({"file": str(backup_file), "size": backup_file.stat().st_size})

        # 2. wisdom.md
        wisdom_path = settings.udos_root / "uCore/wisdom.md"
        if wisdom_path.exists():
            wisdom_backup = dest / f"wisdom-{ts}.md"
            shutil.copy2(wisdom_path, wisdom_backup)
            backup_entries.append({"file": str(wisdom_backup), "size": wisdom_backup.stat().st_size})

        # 3. Secrets
        secrets_path = settings.secrets_file
        if secrets_path.exists():
            secrets_backup = dest / f"secrets-{ts}.enc"
            shutil.copy2(secrets_path, secrets_backup)
            backup_entries.append({"file": str(secrets_backup), "size": secrets_backup.stat().st_size})

        log.info("Backup completed: %d files backed up to %s", len(backup_entries), dest)
        return {
            "success": True,
            "backup_dir": str(dest),
            "files": backup_entries,
            "count": len(backup_entries),
        }
