from __future__ import annotations
import asyncio, time
from pathlib import Path
from app.skills.base import BaseSkill, SkillMeta, SkillParam

class BackupData(BaseSkill):
    meta = SkillMeta(id="backup", name="Backup Data",
        description="Backup uCore database and user data",
        category="maintenance", timeout=120,
        params=[SkillParam(name="destination", type="string", default="~/.ucore/backups")])
    async def run(self, **kwargs) -> dict:
        dest = Path(kwargs.get("destination", "~/.ucore/backups")).expanduser()
        dest.mkdir(parents=True, exist_ok=True)
        from app.core.database import get_db_path
        db_path = get_db_path()
        ts = time.strftime("%Y%m%d-%H%M%S")
        backup_file = dest / f"ucore-backup-{ts}.db"
        import shutil
        shutil.copy2(db_path, backup_file)
        return {"success": True, "backup_path": str(backup_file), "size": backup_file.stat().st_size}
