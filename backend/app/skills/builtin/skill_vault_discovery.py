"""Vault Discovery Skill — Identify all user uCode data across vault layers.

Scans all vault layers (User, Shared, Global, Code, Public) and reports:
- File counts, sizes, and structure per layer
- uCore-specific data (configs, logs, plates, spool archives)
- Dry-run mode for safe identification
- Nugget extraction for reusable components

Usage:
    # Dry-run: identify everything
    result = await skill.run(dry_run=True)

    # Full scan with Nugget extraction
    result = await skill.run(
        dry_run=False,
        extract_nuggets=True,
        nugget_output_dir="~/Nuggets/"
    )
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.vault_discovery")

# Vault topology from vault_file_discovery.py
VAULT_PATHS = {
    "user": Path("~/Vault/").expanduser(),
    "shared": Path("~/Shared/").expanduser(),
    "global": Path("~/Public/global-knowledge/").expanduser(),
    "code": Path("~/Code/").expanduser(),
    "public": Path("~/Public/doc-sites/").expanduser(),
}

UCORE_PATHS = {
    "config": Path("~/.ucore/").expanduser(),
    "logs": Path("~/.ucore/logs/").expanduser(),
    "plates": Path("plates/").resolve(),
}

SUPPORTED_EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".txt", ".csv", ".py", ".ts", ".tsx", ".css", ".html"}
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".next", ".obsidian", ".vscode", ".venv", ".mypy_cache"}


class VaultDiscoverySkill(BaseSkill):
    """Discover and report all user uCode data across vault layers."""

    meta = SkillMeta(
        id="vault_discovery",
        name="Vault Discovery",
        description="Scan all vault layers and identify uCode data, "
        "with dry-run and Nugget extraction support",
        category="system",
        params=[
            SkillParam(
                name="dry_run",
                type="boolean",
                description="If true, only identify without destructive actions",
                required=False,
                default=True,
            ),
            SkillParam(
                name="extract_nuggets",
                type="boolean",
                description="If true, extract reusable components as Nuggets",
                required=False,
                default=False,
            ),
            SkillParam(
                name="nugget_output_dir",
                type="string",
                description="Directory to write extracted Nuggets",
                required=False,
                default="~/Nuggets/",
            ),
            SkillParam(
                name="vault_layers",
                type="string",
                description="Comma-separated list of vault layers to scan "
                "(user,shared,global,code,public) or 'all'",
                required=False,
                default="all",
            ),
        ],
        timeout=120,
    )

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        """Execute vault discovery.

        Args:
            dry_run: If True, only identify without destructive actions
            extract_nuggets: If True, extract reusable components as Nuggets
            nugget_output_dir: Directory to write extracted Nuggets
            vault_layers: Comma-separated list of layers or 'all'

        Returns:
            Discovery report with vault stats, uCore data, and Nuggets
        """
        dry_run = kwargs.get("dry_run", True)
        extract_nuggets = kwargs.get("extract_nuggets", False)
        nugget_output_dir = Path(
            kwargs.get("nugget_output_dir", "~/Nuggets/")
        ).expanduser()
        vault_layers_str = kwargs.get("vault_layers", "all")

        # Determine which layers to scan
        if vault_layers_str == "all":
            layers_to_scan = list(VAULT_PATHS.keys())
        else:
            layers_to_scan = [
                layer.strip() for layer in vault_layers_str.split(",")
                if layer.strip() in VAULT_PATHS
            ]

        log.info(
            "Vault discovery: dry_run=%s, layers=%s, nuggets=%s",
            dry_run, layers_to_scan, extract_nuggets,
        )

        # Scan each vault layer
        vaults: dict[str, dict[str, Any]] = {}
        total_files = 0
        total_size = 0

        for layer in layers_to_scan:
            vault_path = VAULT_PATHS[layer]
            stats = self._scan_vault_layer(vault_path, layer)
            vaults[layer] = stats
            total_files += stats["files"]
            total_size += stats["size_bytes"]

        # Scan uCore-specific data
        ucore_data = self._scan_ucore_data()

        # Extract Nuggets if requested
        nuggets: list[dict[str, Any]] = []
        if extract_nuggets and not dry_run:
            nuggets = self._extract_nuggets(
                vaults, nugget_output_dir,
            )

        report = {
            "vaults": vaults,
            "ucore_data": ucore_data,
            "nuggets": nuggets,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "dry_run": dry_run,
            "scanned_at": datetime.now(UTC).isoformat(),
            "layers_scanned": layers_to_scan,
        }

        log.info(
            "Vault discovery complete: %d files, %d bytes, %d nuggets",
            total_files, total_size, len(nuggets),
        )

        return report

    def _scan_vault_layer(
        self, vault_path: Path, layer: str,
    ) -> dict[str, Any]:
        """Scan a single vault layer and return stats."""
        if not vault_path.exists():
            return {
                "path": str(vault_path),
                "exists": False,
                "files": 0,
                "size_bytes": 0,
                "structure": [],
            }

        import os

        files_count = 0
        size_bytes = 0
        structure: dict[str, int] = {}
        extensions: dict[str, int] = {}

        for dirpath, dirnames, filenames in os.walk(vault_path):
            dirpath_obj = Path(dirpath)

            # Skip excluded dirs
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

            rel_parts = dirpath_obj.relative_to(vault_path).parts

            for filename in filenames:
                filepath = dirpath_obj / filename
                ext = filepath.suffix.lower()

                if ext in SUPPORTED_EXTENSIONS:
                    files_count += 1
                    try:
                        size_bytes += filepath.stat().st_size
                    except OSError:
                        pass
                    extensions[ext] = extensions.get(ext, 0) + 1

                    # Track top-level directory structure
                    top_dir = rel_parts[0] if rel_parts else "."
                    structure[top_dir] = structure.get(top_dir, 0) + 1

        return {
            "path": str(vault_path),
            "exists": True,
            "files": files_count,
            "size_bytes": size_bytes,
            "extensions": extensions,
            "structure": [
                {"dir": d, "files": c}
                for d, c in sorted(structure.items())
            ],
        }

    def _scan_ucore_data(self) -> dict[str, Any]:
        """Scan uCore-specific data directories."""
        results: dict[str, Any] = {}

        for name, path in UCORE_PATHS.items():
            if not path.exists():
                results[name] = {
                    "path": str(path),
                    "exists": False,
                    "files": 0,
                }
                continue

            files = []
            for f in sorted(path.rglob("*")):
                if f.is_file() and ".git" not in f.parts:
                    files.append({
                        "name": f.name,
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            f.stat().st_mtime, tz=UTC,
                        ).isoformat(),
                    })

            results[name] = {
                "path": str(path),
                "exists": True,
                "files": len(files),
                "file_list": files[:50],  # Limit to 50 entries
            }

        # Also scan for spool archives specifically
        spool_dir = Path("~/.ucore/logs").expanduser()
        spool_archives = list(spool_dir.glob("plate_*.spool.json.gz"))
        results["spool_archives"] = {
            "path": str(spool_dir),
            "count": len(spool_archives),
            "archives": [str(f.name) for f in spool_archives],
        }

        return results

    def _extract_nuggets(
        self,
        vaults: dict[str, dict[str, Any]],
        output_dir: Path,
    ) -> list[dict[str, Any]]:
        """Extract reusable components from vaults as Nuggets.

        A Nugget is a self-contained, reusable component extracted from
        vault data that can be redeployed in another context.
        """
        nuggets: list[dict[str, Any]] = []
        output_dir.mkdir(parents=True, exist_ok=True)

        nugget_id = 0
        for layer, stats in vaults.items():
            if not stats.get("exists"):
                continue

            vault_path = Path(stats["path"])
            for struct in stats.get("structure", []):
                dir_path = vault_path / struct["dir"]
                if not dir_path.exists() or not dir_path.is_dir():
                    continue

                # Only extract directories with meaningful content
                if struct["files"] < 3:
                    continue

                nugget_id += 1
                nugget = {
                    "id": f"nugget.vault.{layer}.{nugget_id:03d}",
                    "source": str(dir_path),
                    "layer": layer,
                    "files": struct["files"],
                    "exported_to": str(output_dir / f"{layer}_{struct['dir'].replace('/', '_')}"),
                }

                # Write Nugget manifest
                manifest_path = output_dir / f"{layer}_{struct['dir'].replace('/', '_')}.nugget.json"
                manifest_path.write_text(
                    json.dumps(nugget, indent=2),
                    encoding="utf-8",
                )

                nuggets.append(nugget)
                log.info("Extracted Nugget: %s", nugget["id"])

        return nuggets
