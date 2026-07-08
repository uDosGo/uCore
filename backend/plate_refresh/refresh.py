"""Plate Refresh Engine -- Render, validate, detect drift, and rebuild from plates.

Usage:
    python -m plate_refresh.refresh --render
    python -m plate_refresh.refresh --validate skill.recover_port_conflict
    python -m plate_refresh.refresh --drift-detect all
    python -m plate_refresh.refresh --destroy skill.recover_port_conflict
    python -m plate_refresh.refresh --spool-list
"""
from __future__ import annotations

import gzip
import json
import logging
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from string import Template
from typing import Any

import yaml

from plate_refresh.models import (
    DriftReport,
    PlateMeta,
    RebuildResult,
    SpoolArchiveConfig,
)

log = logging.getLogger("ucore.plate_refresh")

ROOT = Path(__file__).resolve().parents[2]  # /Users/fredbook/Code/uCore
PLATES_ROOT = ROOT / "plates"
BACKUP_ROOT = ROOT / "plates" / ".backups"
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".next",
                ".obsidian", ".vscode", ".venv", ".mypy_cache"}


# ─── Plate Discovery ──────────────────────────────────────

def discover_plates() -> dict[str, Path]:
    """Discover all plate YAML files in plates/ directory."""
    plates: dict[str, Path] = {}
    for f in sorted(PLATES_ROOT.rglob("*.yaml")):
        if ".backups" in f.parts:
            continue
        try:
            with open(f) as fh:
                data = yaml.safe_load(fh)
            if data and "plate" in data:
                pid = data["plate"].get("id", "")
                if pid:
                    plates[pid] = f
        except Exception as exc:
            log.warning("Failed to parse plate %s: %s", f, exc)
    return plates


def load_plate(plate_id: str) -> tuple[PlateMeta, dict[str, Any], Path] | None:
    """Load a plate by ID. Returns (meta, raw_data, path) or None."""
    plates = discover_plates()
    path = plates.get(plate_id)
    if not path:
        return None
    with open(path) as f:
        raw = yaml.safe_load(f)
    meta = PlateMeta(**raw["plate"])
    return meta, raw, path


# ─── Rendering ────────────────────────────────────────────

def render_plates(context: dict[str, str] | None = None) -> list[str]:
    """Render all plates with context substitution.

    Args:
        context: Dict of template variables (e.g. {"DATE": "2026-06-30"})

    Returns:
        List of rendered output paths
    """
    ctx = context or {
        "DATE": time.strftime("%Y-%m-%d"),
        "VERSION": "1.0.0",
        "YEAR": time.strftime("%Y"),
    }

    rendered: list[str] = []
    plates = discover_plates()

    for plate_id, path in plates.items():
        loaded = load_plate(plate_id)
        if not loaded:
            continue
        meta, raw, _ = loaded

        # Render the raw YAML content
        content = path.read_text()
        rendered_content = Template(content).safe_substitute(ctx)

        # Write rendered output to plates/.rendered/
        output_dir = PLATES_ROOT / ".rendered" / meta.domain
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{plate_id}.yaml"
        output_path.write_text(rendered_content)

        # Update checksum
        new_checksum = meta.compute_checksum(rendered_content)
        log.info(
            "Rendered plate %s (v%s) -> %s [checksum: %s]",
            plate_id, meta.version, output_path, new_checksum[:12],
        )
        rendered.append(str(output_path))

    return rendered


# ─── Validation ───────────────────────────────────────────

def validate_plate(plate_id: str) -> dict[str, Any]:
    """Validate a plate against its Pydantic schema.

    Args:
        plate_id: The plate ID to validate

    Returns:
        Validation report dict
    """
    result = load_plate(plate_id)
    if not result:
        return {"plate_id": plate_id, "valid": False, "error": "Plate not found"}

    meta, raw, path = result
    errors: list[str] = []

    # Validate PlateMeta fields
    if not meta.id:
        errors.append("plate.id is required")
    if not meta.version:
        errors.append("plate.version is required")
    if meta.domain not in ("skill", "snack", "mcp", "hivemind", "secret", "css", "vault"):
        errors.append(f"Invalid domain: {meta.domain}")

    # Validate file exists
    if not path.exists():
        errors.append(f"Plate file not found: {path}")

    return {
        "plate_id": plate_id,
        "version": meta.version,
        "domain": meta.domain,
        "valid": len(errors) == 0,
        "errors": errors,
        "path": str(path),
        "checksum": meta.checksum,
    }


def validate_all_plates() -> list[dict[str, Any]]:
    """Validate all discovered plates."""
    plates = discover_plates()
    return [validate_plate(pid) for pid in plates]


# ─── Drift Detection ──────────────────────────────────────

def detect_drift(plate_id: str) -> DriftReport:
    """Detect drift between a plate and its rendered output.

    Args:
        plate_id: The plate ID to check

    Returns:
        DriftReport with differences
    """
    result = load_plate(plate_id)
    if not result:
        return DriftReport(
            plate_id=plate_id,
            version="unknown",
            drift_detected=True,
            differences=["Plate not found"],
        )

    meta, raw, path = result
    rendered_path = PLATES_ROOT / ".rendered" / meta.domain / f"{plate_id}.yaml"

    differences: list[str] = []

    if not rendered_path.exists():
        differences.append("No rendered output found (run --render first)")
        return DriftReport(
            plate_id=plate_id,
            version=meta.version,
            drift_detected=True,
            differences=differences,
            checksum_match=False,
        )

    rendered_content = rendered_path.read_text()
    checksum_match = meta.validate_checksum(rendered_content)

    if not checksum_match:
        differences.append("Checksum mismatch -- content has drifted from plate")

    # Compare keys between plate and rendered output
    rendered_raw = yaml.safe_load(rendered_content) or {}
    plate_keys = set(raw.get("plate", {}).keys())
    rendered_keys = set(rendered_raw.get("plate", {}).keys())

    missing = plate_keys - rendered_keys
    extra = rendered_keys - plate_keys

    if missing:
        differences.append(f"Missing keys in rendered output: {missing}")
    if extra:
        differences.append(f"Extra keys in rendered output: {extra}")

    return DriftReport(
        plate_id=plate_id,
        version=meta.version,
        drift_detected=len(differences) > 0,
        differences=differences,
        checksum_match=checksum_match,
        missing_keys=list(missing),
        extra_keys=list(extra),
    )


def detect_all_drift() -> list[DriftReport]:
    """Detect drift across all plates."""
    plates = discover_plates()
    return [detect_drift(pid) for pid in plates]


# ─── SPOOL Archive ────────────────────────────────────────

def _resolve_spool_dir(spool_cfg: SpoolArchiveConfig) -> Path:
    """Resolve spool directory, expanding ~ to home."""
    spool_path = Path(spool_cfg.spool_dir).expanduser()
    spool_path.mkdir(parents=True, exist_ok=True)
    return spool_path


def write_spool_archive(
    plate_id: str,
    meta: PlateMeta,
    raw: dict[str, Any],
    salvaged: dict[str, Any],
    backup_path: str,
    rebuild_output: str,
    errors: list[str],
) -> str | None:
    """Compress a destroyed component's essence into an MCP-formatted SPOOL record.

    The SPOOL record is a gzip-compressed JSON blob written to ~/.ucore/logs/
    that preserves:
    - Plate metadata (id, version, domain, description)
    - Salvaged state (keys preserved from corruption)
    - Lessons learned (from plate.lessons field)
    - Backup reference (path to full backup)
    - Rebuild output (stdout from rebuild command)
    - Timestamp and event type

    This enables:
    1. Legacy/archival records that dont consume lots of space like .git can
    2. Avoiding re-developing the same deprecated skill
    3. Learning/wisdom from previous failures and upgrades

    Args:
        plate_id: The plate ID being destroyed
        meta: PlateMeta instance
        raw: Raw plate YAML data
        salvaged: State salvaged before destruction
        backup_path: Path to backup file
        rebuild_output: Output from rebuild command
        errors: Any errors encountered

    Returns:
        Path to the spool archive file, or None if archiving is disabled
    """
    spool_cfg = meta.destroy.spool_archive
    if not spool_cfg.enabled:
        log.info("SPOOL archiving disabled for %s", plate_id)
        return None

    spool_dir = _resolve_spool_dir(spool_cfg)

    # Build the MCP-formatted spool record
    now = datetime.now(timezone.utc)
    spool_record = {
        "event": "plate.destroy",
        "timestamp": now.isoformat(),
        "plate": {
            "id": plate_id,
            "version": meta.version,
            "domain": meta.domain,
            "description": meta.description,
            "source": meta.source,
            "checksum": meta.checksum,
            "dependencies": meta.dependencies,
        },
        "salvaged": salvaged if spool_cfg.compress_metadata else {},
        "lessons": meta.lessons if spool_cfg.include_lessons else [],
        "backup": backup_path if backup_path else None,
        "rebuild_output": rebuild_output if rebuild_output else None,
        "errors": errors if errors else [],
        "schema": raw.get("plate", {}).get("schema", {}),
    }

    # Compress to gzip
    spool_filename = (
        f"plate_{plate_id}_{now.strftime('%Y%m%d_%H%M%S')}.spool.json.gz"
    )
    spool_path = spool_dir / spool_filename

    with gzip.open(spool_path, "wt", encoding="utf-8") as f:
        json.dump(spool_record, f, indent=2, default=str)

    log.info(
        "SPOOL archive written: %s (%d keys, %d lessons)",
        spool_path,
        len(spool_record["salvaged"]),
        len(spool_record["lessons"]),
    )
    return str(spool_path)


def list_spool_archives(domain: str | None = None) -> list[dict[str, Any]]:
    """List all SPOOL archive records in ~/.ucore/logs/.

    Args:
        domain: Optional domain filter (skill, snack, mcp, etc.)

    Returns:
        List of spool record summaries
    """
    spool_dir = Path("~/.ucore/logs").expanduser()
    if not spool_dir.exists():
        return []

    archives: list[dict[str, Any]] = []
    for f in sorted(spool_dir.glob("plate_*.spool.json.gz"), reverse=True):
        try:
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                record = json.load(fh)
            if domain and record.get("plate", {}).get("domain") != domain:
                continue
            archives.append({
                "file": str(f),
                "timestamp": record.get("timestamp", ""),
                "plate_id": record.get("plate", {}).get("id", ""),
                "version": record.get("plate", {}).get("version", ""),
                "domain": record.get("plate", {}).get("domain", ""),
                "salvaged_keys": list(record.get("salvaged", {}).keys()),
                "lesson_count": len(record.get("lessons", [])),
                "has_errors": len(record.get("errors", [])) > 0,
            })
        except Exception as exc:
            log.warning("Failed to read spool archive %s: %s", f, exc)

    return archives


def read_spool_archive(spool_path: str) -> dict[str, Any] | None:
    """Read and decompress a single SPOOL archive record.

    Args:
        spool_path: Path to the .spool.json.gz file

    Returns:
        Decompressed record dict, or None on failure
    """
    path = Path(spool_path).expanduser()
    if not path.exists():
        log.warning("SPOOL archive not found: %s", spool_path)
        return None
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log.warning("Failed to read spool archive %s: %s", spool_path, exc)
        return None


# ─── DESTROY/REBUILD Protocol ─────────────────────────────

def destroy_and_rebuild(
    plate_id: str,
    salvage_state: dict[str, Any] | None = None,
) -> RebuildResult:
    """Execute DESTROY/REBUILD protocol for a plate.

    Steps:
    1. SALVAGE -- Extract key state from corrupted instance
    2. BACKUP  -- Backup current instance
    3. ARCHIVE -- Compress essence into MCP-formatted SPOOL record
    4. DESTROY -- Remove corrupted instance
    5. REBUILD -- Materialize from plate with salvaged state
    6. VERIFY  -- Run validation checks

    Args:
        plate_id: The plate ID to rebuild
        salvage_state: Optional pre-extracted state to preserve

    Returns:
        RebuildResult with outcome
    """
    result = load_plate(plate_id)
    if not result:
        return RebuildResult(
            plate_id=plate_id,
            success=False,
            errors=["Plate not found"],
        )

    meta, raw, path = result
    errors: list[str] = []
    salvaged: dict[str, Any] = {}
    backup_path = ""

    # Step 1: SALVAGE

    if salvage_state:
        salvaged = salvage_state
    else:
        for key in meta.destroy.salvage_keys:
            if key in raw.get("plate", {}):
                salvaged[key] = raw["plate"][key]

    # Step 2: BACKUP
    if meta.destroy.backup_before_destroy:
        backup_dir = BACKUP_ROOT / meta.domain
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_name = (
            f"{plate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        )
        backup_path = str(backup_dir / backup_name)
        shutil.copy2(str(path), backup_path)
        log.info("Backed up %s to %s", plate_id, backup_path)

    # Step 3: ARCHIVE -- compress essence into SPOOL record
    # (before destroy, while we still have the full data)

    # Step 4: DESTROY (remove rendered output)
    rendered_path = PLATES_ROOT / ".rendered" / meta.domain / f"{plate_id}.yaml"
    if rendered_path.exists():
        rendered_path.unlink()
        log.info("Removed rendered output for %s", plate_id)

    # Step 5: REBUILD
    rebuild_output = ""
    if meta.destroy.rebuild_command:
        try:
            cmd = meta.destroy.rebuild_command
            # Substitute salvage keys into command
            for k, v in salvaged.items():
                cmd = cmd.replace(f"${{{k}}}", str(v))
            result_proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=120,
            )
            rebuild_output = result_proc.stdout
            if result_proc.returncode != 0:
                errors.append(f"Rebuild command failed: {result_proc.stderr}")
        except subprocess.TimeoutExpired:
            errors.append("Rebuild command timed out after 120s")
        except Exception as exc:
            errors.append(f"Rebuild command error: {exc}")

    # Step 6: VERIFY
    validation = validate_plate(plate_id)
    if not validation.get("valid", False):
        for err in validation.get("errors", []):
            errors.append(f"Validation after rebuild: {err}")

    # Write SPOOL archive (after rebuild so we can include rebuild_output)
    spool_path = write_spool_archive(
        plate_id=plate_id,
        meta=meta,
        raw=raw,
        salvaged=salvaged,
        backup_path=backup_path,
        rebuild_output=rebuild_output,
        errors=errors,
    )

    success = len(errors) == 0
    log.info(
        "DESTROY/REBUILD for %s: %s",
        plate_id, "SUCCESS" if success else "FAILED",
    )

    return RebuildResult(
        plate_id=plate_id,
        success=success,
        salvaged=salvaged,
        rebuild_output=rebuild_output,
        errors=errors,
        backup_path=backup_path,
    )


# ─── Vault Discovery (for DESTROY interactive menu) ──────

VAULT_PATHS = {
    "user": Path("~/Vault/").expanduser(),
    "shared": Path("~/Shared/").expanduser(),
    "global": Path("~/Public/global-knowledge/").expanduser(),
    "code": Path("~/Code/").expanduser(),
    "public": Path("~/Public/doc-sites/").expanduser(),
}

UCORE_DIRS = {
    "config": Path("~/.ucore/").expanduser(),
    "logs": Path("~/.ucore/logs/").expanduser(),
    "plates": ROOT / "plates",
}


def _discover_vaults() -> dict[str, Any]:
    """Quick vault discovery for the DESTROY interactive menu."""
    import os

    vaults: dict[str, Any] = {}
    total_files = 0

    for layer, path in VAULT_PATHS.items():
        if not path.exists():
            vaults[layer] = {"path": str(path), "exists": False, "files": 0}
            continue

        count = 0
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames
                           if d not in EXCLUDE_DIRS]
            count += len(filenames)

        vaults[layer] = {
            "path": str(path), "exists": True, "files": count,
        }
        total_files += count

    ucore_data: dict[str, Any] = {}
    for name, path in UCORE_DIRS.items():
        if not path.exists():
            ucore_data[name] = {"path": str(path), "files": 0}
            continue
        count = sum(1 for _ in path.rglob("*") if _.is_file())
        ucore_data[name] = {"path": str(path), "files": count}

    # Spool archives
    spool_dir = Path("~/.ucore/logs").expanduser()
    spool_count = len(list(spool_dir.glob("plate_*.spool.json.gz")))
    ucore_data["spool_archives"] = {
        "path": str(spool_dir), "count": spool_count,
    }

    return {
        "vaults": vaults,
        "ucore_data": ucore_data,
        "total_files": total_files,
    }


def _destroy_user_vault() -> RebuildResult:
    """Destroy user vault data (~/Vault/) with backup and SPOOL archive."""
    vault_path = Path("~/Vault/").expanduser()
    errors: list[str] = []
    backup_path = ""

    if not vault_path.exists():
        return RebuildResult(
            plate_id="vault.user_vault_seed",
            success=True,
            errors=[],
            rebuild_output="User vault does not exist. Nothing to destroy.",
        )

    # Backup
    backup_dir = BACKUP_ROOT / "vault"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_name = f"user_vault_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    backup_path = str(backup_dir / backup_name)

    import tarfile
    try:
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(vault_path, arcname="Vault")
        log.info("Backed up user vault to %s", backup_path)
    except Exception as exc:
        errors.append(f"Backup failed: {exc}")

    # Write SPOOL archive
    spool_record = {
        "event": "vault.destroy.user",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vault": {
            "layer": "user",
            "path": str(vault_path),
            "backup": backup_path,
        },
        "errors": errors,
    }
    spool_dir = Path("~/.ucore/logs").expanduser()
    spool_dir.mkdir(parents=True, exist_ok=True)
    spool_path = spool_dir / (
        f"vault_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ".spool.json.gz"
    )
    import gzip
    with gzip.open(spool_path, "wt", encoding="utf-8") as f:
        json.dump(spool_record, f, indent=2, default=str)

    # Remove vault contents (keep directory)
    import shutil
    for item in vault_path.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as exc:
            errors.append(f"Failed to remove {item}: {exc}")

    success = len(errors) == 0
    return RebuildResult(
        plate_id="vault.user_vault_seed",
        success=success,
        errors=errors,
        backup_path=backup_path,
        rebuild_output=(
            f"User vault destroyed. Backup at {backup_path}. "
            f"SPOOL archive at {spool_path}."
        ),
    )


def _destroy_installation() -> RebuildResult:
    """Destroy entire uCore installation and user data."""
    errors: list[str] = []

    # 1. Destroy user vault
    vault_result = _destroy_user_vault()
    if not vault_result.success:
        errors.extend(vault_result.errors)

    # 2. Backup and remove ~/.ucore/
    ucore_dir = Path("~/.ucore/").expanduser()
    if ucore_dir.exists():
        backup_dir = BACKUP_ROOT / "installation"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_name = (
            f"ucore_install_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        )
        backup_path = str(backup_dir / backup_name)
        import tarfile
        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(ucore_dir, arcname=".ucore")
            import shutil
            shutil.rmtree(ucore_dir)
        except Exception as exc:
            errors.append(f"Failed to backup/remove ~/.ucore/: {exc}")

    # 3. Write final SPOOL archive
    spool_record = {
        "event": "installation.destroy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "errors": errors,
    }
    spool_dir = Path("~/.ucore/logs").expanduser()
    spool_dir.mkdir(parents=True, exist_ok=True)
    spool_path = spool_dir / (
        f"installation_destroy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ".spool.json.gz"
    )
    import gzip
    with gzip.open(spool_path, "wt", encoding="utf-8") as f:
        json.dump(spool_record, f, indent=2, default=str)

    success = len(errors) == 0
    return RebuildResult(
        plate_id="installation",
        success=success,
        errors=errors,
        rebuild_output=(
            f"Installation destroyed. SPOOL archive at {spool_path}."
        ),
    )


# ─── Interactive DESTROY Menu ────────────────────────────

def interactive_destroy():
    """Present interactive DESTROY/REBUILD options to the user."""
    print()
    print("=" * 58)
    print("  uCore DESTROY/REBUILD UTILITY")
    print("=" * 58)
    print()

    # Run vault discovery (dry-run)
    print("Running vault discovery (dry-run)...")
    discovery = _discover_vaults()
    print()
    for layer, stats in discovery["vaults"].items():
        status = "EXISTS" if stats["exists"] else "NOT FOUND"
        print(f"  {layer:8s} -> {stats['path']:<35s} [{status}] "
              f"{stats['files']} files")
    print()
    print("  uCore data:")
    for name, stats in discovery["ucore_data"].items():
        print(f"    {name:15s}: {stats['path']} "
              f"({stats.get('files', stats.get('count', 0))} files)")
    print()
    print(f"  Total: {discovery['total_files']} files across all vaults")
    print()

    # Present options
    print("Select an option:")
    print()
    print("  [1] Dry-run only (identify everything, no changes)")
    print("  [2] Destroy & Rebuild (reset corrupted components, "
          "keep user data)")
    print("  [3] Destroy User Data Only (remove ~/Vault/, "
          "keep installation)")
    print("  [4] Destroy Installation & Data (complete uninstall)")
    print("  [5] Break off Nuggets (extract reusable components, "
          "then rebuild)")
    print("  [6] Cancel")
    print()

    try:
        choice = input("Enter choice [1-6]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return

    if choice == "1":
        print("\nDry-run complete. No changes made.")
        print(json.dumps(discovery, indent=2, default=str))

    elif choice == "2":
        print("\n[2] Destroy & Rebuild selected.")
        confirm = input(
            "This will reset corrupted components. "
            "User data will be preserved. Continue? [y/N]: "
        ).strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
        plates = discover_plates()
        results = []
        for pid in plates:
            result = destroy_and_rebuild(pid)
            results.append(result)
            status = "OK" if result.success else "FAIL"
            print(f"  {pid}: {status}")
        print(f"\nProcessed {len(results)} plates.")

    elif choice == "3":
        print("\n[3] Destroy User Data Only selected.")
        confirm = input(
            "This will remove all contents of ~/Vault/ "
            "(backup will be created). Continue? [y/N]: "
        ).strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
        result = _destroy_user_vault()
        if result.success:
            print(f"\nUser vault destroyed. Backup: {result.backup_path}")
        else:
            print(f"\nErrors: {result.errors}")

    elif choice == "4":
        print("\n[4] Destroy Installation & Data selected.")
        confirm = input(
            "WARNING: This will remove ALL user data and the "
            "uCore installation. Continue? [y/N]: "
        ).strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
        confirm2 = input(
            "Type 'DESTROY' to confirm complete uninstall: "
        ).strip()
        if confirm2 != "DESTROY":
            print("Cancelled.")
            return
        result = _destroy_installation()
        if result.success:
            print("\nInstallation destroyed.")
        else:
            print(f"\nErrors: {result.errors}")

    elif choice == "5":
        print("\n[5] Break off Nuggets selected.")
        confirm = input(
            "Extract reusable components from vaults as Nuggets? "
            "Continue? [y/N]: "
        ).strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
        # Run vault discovery skill for Nugget extraction
        try:
            from app.skills.builtin.skill_vault_discovery import (
                VaultDiscoverySkill,
            )
            skill = VaultDiscoverySkill()
            import asyncio
            result = asyncio.run(skill.run(
                dry_run=False,
                extract_nuggets=True,
                nugget_output_dir="~/Nuggets/",
            ))
            print(f"\nExtracted {len(result['nuggets'])} Nuggets:")
            for n in result["nuggets"]:
                print(f"  {n['id']}: {n['source']} ({n['files']} files)")
        except Exception as exc:
            print(f"\nNugget extraction failed: {exc}")

    elif choice == "6":
        print("\nCancelled.")

    else:
        print(f"\nInvalid choice: {choice}")


# ─── CLI ──────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Plate Refresh Engine -- Render, validate, "
        "detect drift, rebuild",
    )
    parser.add_argument("--render", action="store_true", help="Render all plates")
    parser.add_argument(
        "--validate", type=str, nargs="?", const="all", default=None,
        help="Validate a specific plate or 'all'",
    )
    parser.add_argument(
        "--drift-detect", type=str, nargs="?", const="all", default=None,
        help="Detect drift for a plate or 'all'",
    )
    parser.add_argument(
        "--destroy", type=str, default=None,
        help="DESTROY/REBUILD a specific plate",
    )
    parser.add_argument(
        "--destroy-interactive", action="store_true",
        help="Interactive DESTROY menu with vault discovery",
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered plates",
    )
    parser.add_argument(
        "--spool-list", action="store_true",
        help="List all SPOOL archive records",
    )
    parser.add_argument(
        "--spool-read", type=str, default=None,
        help="Read and decompress a SPOOL archive file",
    )
    parser.add_argument(
        "--spool-domain", type=str, default=None,
        help="Filter spool list by domain",
    )
    # Add verification and monitoring arguments
    from plate_refresh.monitoring import add_monitoring_args
    from plate_refresh.verification import add_verification_args
    add_verification_args(parser)
    add_monitoring_args(parser)

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.list:
        plates = discover_plates()
        print(f"Discovered {len(plates)} plates:")
        for pid, path in sorted(plates.items()):
            loaded = load_plate(pid)
            if loaded:
                meta, _, _ = loaded
                print(f"  {pid} (v{meta.version}) [{meta.domain}] -> {path}")

    if args.render:
        rendered = render_plates()
        print(f"Rendered {len(rendered)} plates")

    if args.validate:
        if args.validate == "all":
            results = validate_all_plates()
        else:
            results = [validate_plate(args.validate)]
        for r in results:
            status = "VALID" if r["valid"] else "INVALID"
            print(f"  {r['plate_id']}: {status}")
            if not r["valid"]:
                for e in r.get("errors", []):
                    print(f"    - {e}")

    if args.drift_detect:
        if args.drift_detect == "all":
            reports = detect_all_drift()
        else:
            reports = [detect_drift(args.drift_detect)]
        for report in reports:
            status = "DRIFT" if report.drift_detected else "CLEAN"
            print(f"  {report.plate_id} (v{report.version}): {status}")
            for d in report.differences:
                print(f"    - {d}")

    if args.destroy:
        result = destroy_and_rebuild(args.destroy)
        status = "SUCCESS" if result.success else "FAILED"
        print(f"DESTROY/REBUILD {args.destroy}: {status}")
        if result.errors:
            for e in result.errors:
                print(f"  ERROR: {e}")
        if result.backup_path:
            print(f"  Backup: {result.backup_path}")
        if result.salvaged:
            print(f"  Salvaged: {json.dumps(result.salvaged, indent=2)}")

    if args.destroy_interactive:
        interactive_destroy()

    if args.spool_list:
        archives = list_spool_archives(domain=args.spool_domain)
        if not archives:
            print("No SPOOL archives found")
        else:
            print(f"Found {len(archives)} SPOOL archives:")
            for a in archives:
                err_flag = " [ERRORS]" if a["has_errors"] else ""
                print(
                    f"  {a['plate_id']} (v{a['version']}) "
                    f"[{a['domain']}] @ {a['timestamp']}"
                    f"{err_flag}"
                )
                print(f"    salvaged: {a['salvaged_keys']}")
                print(f"    lessons: {a['lesson_count']}")

    if args.spool_read:
        record = read_spool_archive(args.spool_read)
        if record:
            print(json.dumps(record, indent=2, default=str))
        else:
            print(f"Failed to read SPOOL archive: {args.spool_read}")

    # Handle verification and monitoring commands
    from plate_refresh.monitoring import handle_monitoring_commands
    from plate_refresh.verification import handle_verification_commands
    handle_verification_commands(args)
    handle_monitoring_commands(args)


if __name__ == "__main__":
    main()
