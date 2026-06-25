"""vault_sync — Run the local AppFlowy/Vault markdown sync script.

Usage:
  POST /api/skills/vault_sync/run
  Body: { "config": "config/vault-sync.yaml", "dry_run": false, "summary_only": true }
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from app.core.settings import settings

from app.skills.base import BaseSkill, SkillMeta, SkillParam

PROJECT_ROOT = settings.udos_root / "uCore"
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "vault-sync.yaml"
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "appflowy_vault_sync.py"


class VaultSync(BaseSkill):
    meta = SkillMeta(
        id="vault_sync",
        name="Vault Sync",
        description="Run the AppFlowy/Vault bidirectional markdown sync",
        category="maintenance",
        timeout=300,
        params=[
            SkillParam(
                name="config",
                type="string",
                required=False,
                default=str(DEFAULT_CONFIG),
                description="Path to vault sync YAML config",
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                required=False,
                default=False,
                description="Only report actions without writing files",
            ),
            SkillParam(
                name="summary_only",
                type="boolean",
                required=False,
                default=True,
                description="Print condensed action counts",
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        config_path = Path(kwargs.get("config", str(DEFAULT_CONFIG))).expanduser()
        dry_run = bool(kwargs.get("dry_run", False))
        summary_only = bool(kwargs.get("summary_only", True))

        if not SCRIPT_PATH.exists():
            return {
                "success": False,
                "error": f"sync script not found: {SCRIPT_PATH}",
            }

        if not config_path.exists():
            return {
                "success": True,
                "status": "skipped",
                "reason": f"config not found: {config_path}",
                "script": str(SCRIPT_PATH),
            }

        cmd = [sys.executable, str(SCRIPT_PATH), "--config", str(config_path)]
        if dry_run:
            cmd.append("--dry-run")
        if summary_only:
            cmd.append("--summary-only")

        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=self.meta.timeout,
        )
        success = proc.returncode == 0
        return {
            "success": success,
            "status": "ok" if success else "error",
            "config": str(config_path),
            "script": str(SCRIPT_PATH),
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "exit_code": proc.returncode,
            "dry_run": dry_run,
            "summary_only": summary_only,
        }
