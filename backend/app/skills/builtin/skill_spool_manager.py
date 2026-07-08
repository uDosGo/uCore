#!/usr/bin/env python3
"""Skill: SPOOL Manager — ARCHIVE, BACKUP, DESTROY, UNFURL, and NUGGET.

This skill provides the unified SPOOL lifecycle plus the Nugget concept:

1. ARCHIVE  — Compress legacy content into gzip'd MCP-formatted SPOOL records.
              Strips runtime code, preserves metadata, schema, and lessons.
              Enables tiny archival records that dont consume space like .git can.

2. BACKUP   — Timelined/diff-based backups that also get SPOOLed.
              Backups are stored as small, timestamped chunks in ~/.ucore/backups/
              and automatically SPOOLed so they dont accumulate indefinitely.
              Old backups are pruned based on max_age_days.

3. DESTROY  — Component destruction with full SPOOL preservation.
              SALVAGE -> BACKUP -> ARCHIVE -> DESTROY -> REBUILD -> VERIFY.
              The SPOOL record is the recovery point for UNFURL.

4. UNFURL   — Reverse operation: SPOOL -> reconstruct component from archived essence.
              Reads a .spool.json.gz file and materializes the component from
              its plate definition with salvaged state. This is the recovery path
              after a DESTROY or for restoring legacy components.

5. NUGGET   — A Nugget (or Nug) is a compressed legacy relic that contains useful
              data and can be redeployed/reborn. Unlike a SPOOL (which is a system
              by-product of Destroy/Backup), a Nugget is intentionally created and
              left by a user, or may be a by-product of a Destroy and System Plate
              Reset. Nuggets are stored in ~/.ucore/nuggets/ and can be:
              - Intentionally created by a user to preserve something valuable
              - By-product of a DESTROY and System Plate Reset
              - Redeployed/reborn via unfurl back into a living component
              - Left behind as a legacy artifact for future discovery

Registered skills:
  - spool_archive:   Compress legacy content into SPOOL record
  - spool_backup:    Timelined/diff-based backup with SPOOL integration
  - spool_destroy:   DESTROY/REBUILD with full SPOOL preservation
  - spool_unfurl:    Reverse SPOOL -> reconstruct component from archive
  - spool_list:      List and search SPOOL archives
  - spool_prune:     Prune old backups and SPOOL records by age
  - nugget_create:   Intentionally create a Nugget from a component
  - nugget_list:     List and search Nuggets
  - nugget_redeploy: Redeploy/reborn a Nugget back into a living component
  - nugget_discover: Discover Nuggets left by other users or systems
"""

from __future__ import annotations

import gzip
import json
import logging
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.spool_manager")

# ─── Paths ─────────────────────────────────────────────────

SPOOL_DIR = Path("~/.ucore/logs").expanduser()
BACKUP_DIR = Path("~/.ucore/backups").expanduser()
NUGGET_DIR = Path("~/.ucore/nuggets").expanduser()
PLATES_ROOT = Path(__file__).resolve().parents[4] / "plates"  # uCore/plates/


# ─── Helpers ───────────────────────────────────────────────

def _ensure_dirs() -> None:
    """Ensure SPOOL and BACKUP directories exist."""
    SPOOL_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _build_spool_record(
    event: str,
    component_id: str,
    component_type: str,
    version: str,
    metadata: dict[str, Any],
    salvaged: dict[str, Any] | None = None,
    lessons: list[str] | None = None,
    backup_path: str | None = None,
    rebuild_output: str | None = None,
    errors: list[str] | None = None,
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standardized MCP-formatted SPOOL record."""
    now = datetime.now(timezone.utc)
    return {
        "event": event,
        "timestamp": now.isoformat(),
        "component": {
            "id": component_id,
            "type": component_type,
            "version": version,
            **metadata,
        },
        "salvaged": salvaged or {},
        "lessons": lessons or [],
        "backup": backup_path,
        "rebuild_output": rebuild_output,
        "errors": errors or [],
        "schema": schema or {},
    }


def _write_spool_file(record: dict[str, Any]) -> str:
    """Write a SPOOL record to gzip'd JSON file.

    Returns:
        Path to the written spool file
    """
    _ensure_dirs()
    cid = record.get("component", {}).get("id", "unknown")
    ts = record.get("timestamp", datetime.now(timezone.utc).isoformat())
    # Sanitize timestamp for filename
    ts_safe = ts.replace(":", "-").replace("+", "_").replace(".", "_")
    filename = f"spool_{cid}_{ts_safe}.json.gz"
    spool_path = SPOOL_DIR / filename

    with gzip.open(spool_path, "wt", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str)

    log.info("SPOOL record written: %s (%s)", spool_path, record.get("event"))
    return str(spool_path)


def _read_spool_file(spool_path: str) -> dict[str, Any] | None:
    """Read and decompress a SPOOL archive file."""
    path = Path(spool_path).expanduser()
    if not path.exists():
        return None
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log.warning("Failed to read spool %s: %s", spool_path, exc)
        return None


def _list_spool_files(
    component_type: str | None = None,
    event: str | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """List SPOOL files with optional filters."""
    _ensure_dirs()
    results: list[dict[str, Any]] = []
    for f in sorted(SPOOL_DIR.glob("spool_*.json.gz"), reverse=True):
        try:
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                record = json.load(fh)
            if component_type and record.get("component", {}).get("type") != component_type:
                continue
            if event and record.get("event") != event:
                continue
            results.append({
                "file": str(f),
                "timestamp": record.get("timestamp", ""),
                "event": record.get("event", ""),
                "component_id": record.get("component", {}).get("id", ""),
                "component_type": record.get("component", {}).get("type", ""),
                "version": record.get("component", {}).get("version", ""),
                "salvaged_keys": list(record.get("salvaged", {}).keys()),
                "lesson_count": len(record.get("lessons", [])),
                "has_errors": len(record.get("errors", [])) > 0,
                "has_backup": bool(record.get("backup")),
            })
            if len(results) >= max_results:
                break
        except Exception:
            continue
    return results


def _compute_diff(source: str, target: str) -> dict[str, Any]:
    """Compute a simple diff between two text contents.

    Returns a dict with added/removed line counts and a summary.
    """
    src_lines = source.splitlines(keepends=True)
    tgt_lines = target.splitlines(keepends=True)

    # Simple line-level diff
    src_set = set(src_lines)
    tgt_set = set(tgt_lines)

    added = tgt_set - src_set
    removed = src_set - tgt_set

    return {
        "added_lines": len(added),
        "removed_lines": len(removed),
        "total_source": len(src_lines),
        "total_target": len(tgt_lines),
        "summary": f"{len(added)} added, {len(removed)} removed",
    }


# ─── Skill: spool_archive ──────────────────────────────────

class SpoolArchiveSkill(BaseSkill):
    """ARCHIVE — Compress legacy content into SPOOL record.

    Strips runtime code, preserves metadata, schema, and lessons.
    The original file is optionally removed after archiving.
    """

    meta = SkillMeta(
        id="spool_archive",
        name="SPOOL Archive",
        description="Compress legacy content into gzip'd MCP-formatted SPOOL record",
        category="maintenance",
        params=[
            SkillParam(
                name="component_id",
                type="string",
                description="Unique identifier for the component",
                required=True,
            ),
            SkillParam(
                name="component_type",
                type="string",
                description="Type: skill, snack, mcp, hivemind, secret, css, legacy",
                default="legacy",
            ),
            SkillParam(
                name="version",
                type="string",
                description="SemVer version string",
                default="0.0.0",
            ),
            SkillParam(
                name="source_path",
                type="string",
                description="Path to the file/directory to archive",
                required=True,
            ),
            SkillParam(
                name="metadata",
                type="object",
                description="Additional metadata to preserve",
                default={},
            ),
            SkillParam(
                name="lessons",
                type="array",
                description="Lessons learned from this component",
                default=[],
            ),
            SkillParam(
                name="schema",
                type="object",
                description="JSON schema of the component",
                default={},
            ),
            SkillParam(
                name="remove_source",
                type="boolean",
                description="Remove the source file after archiving",
                default=False,
            ),
        ],
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        component_id = kwargs.get("component_id", "")
        component_type = kwargs.get("component_type", "legacy")
        version = kwargs.get("version", "0.0.0")
        source_path = kwargs.get("source_path", "")
        extra_metadata = kwargs.get("metadata", {})
        lessons = kwargs.get("lessons", [])
        schema = kwargs.get("schema", {})
        remove_source = kwargs.get("remove_source", False)

        if not component_id or not source_path:
            return {
                "success": False,
                "message": "component_id and source_path are required",
            }

        src = Path(source_path).expanduser()
        if not src.exists():
            return {
                "success": False,
                "message": f"Source path not found: {source_path}",
            }

        # Read source content for metadata extraction
        source_content = ""
        if src.is_file():
            try:
                source_content = src.read_text()
            except Exception:
                source_content = f"[binary file: {src.name}]"

        # Build metadata from source
        metadata = {
            "source_path": str(src),
            "source_size_bytes": src.stat().st_size if src.exists() else 0,
            "source_modified": datetime.fromtimestamp(
                src.stat().st_mtime, tz=timezone.utc
            ).isoformat() if src.exists() else "",
            **extra_metadata,
        }

        # Build the SPOOL record
        record = _build_spool_record(
            event="archive",
            component_id=component_id,
            component_type=component_type,
            version=version,
            metadata=metadata,
            salvaged={"source_summary": source_content[:500]},
            lessons=lessons,
            schema=schema,
        )

        spool_path = _write_spool_file(record)

        # Optionally remove source
        if remove_source:
            if src.is_file():
                src.unlink()
                log.info("Removed source file: %s", src)
            elif src.is_dir():
                shutil.rmtree(src)
                log.info("Removed source directory: %s", src)

        return {
            "success": True,
            "message": f"Archived {component_id} (v{version}) to SPOOL",
            "spool_path": spool_path,
            "component_id": component_id,
            "component_type": component_type,
            "version": version,
            "source_removed": remove_source,
            "lesson_count": len(lessons),
        }


# ─── Skill: spool_backup ───────────────────────────────────

class SpoolBackupSkill(BaseSkill):
    """BACKUP — Timelined/diff-based backup with SPOOL integration.

    Creates timestamped backups in ~/.ucore/backups/ and writes a
    SPOOL record referencing the backup. Supports diff-based backups
    (only store changes from previous backup) and automatic pruning
    of old backups based on max_age_days.

    Backups are small, timelined chunks that can be SPOOLed themselves
    so they dont accumulate indefinitely.
    """

    meta = SkillMeta(
        id="spool_backup",
        name="SPOOL Backup",
        description="Timelined/diff-based backup with SPOOL integration",
        category="maintenance",
        params=[
            SkillParam(
                name="component_id",
                type="string",
                description="Unique identifier for the component",
                required=True,
            ),
            SkillParam(
                name="source_path",
                type="string",
                description="Path to the file/directory to backup",
                required=True,
            ),
            SkillParam(
                name="component_type",
                type="string",
                description="Type: skill, snack, mcp, hivemind, secret, css, legacy",
                default="legacy",
            ),
            SkillParam(
                name="version",
                type="string",
                description="Version string for the backup",
                default="",
            ),
            SkillParam(
                name="diff_mode",
                type="boolean",
                description="Only store diff from previous backup",
                default=False,
            ),
            SkillParam(
                name="max_age_days",
                type="integer",
                description="Prune backups older than this many days",
                default=90,
            ),
            SkillParam(
                name="lessons",
                type="array",
                description="Lessons to include in SPOOL record",
                default=[],
            ),
        ],
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        component_id = kwargs.get("component_id", "")
        source_path = kwargs.get("source_path", "")
        component_type = kwargs.get("component_type", "legacy")
        version = kwargs.get("version", "")
        diff_mode = kwargs.get("diff_mode", False)
        max_age_days = kwargs.get("max_age_days", 90)
        lessons = kwargs.get("lessons", [])

        if not component_id or not source_path:
            return {
                "success": False,
                "message": "component_id and source_path are required",
            }

        src = Path(source_path).expanduser()
        if not src.exists():
            return {
                "success": False,
                "message": f"Source path not found: {source_path}",
            }

        _ensure_dirs()

        # Create component backup directory
        comp_backup_dir = BACKUP_DIR / component_id
        comp_backup_dir.mkdir(parents=True, exist_ok=True)

        # Timestamp for this backup
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_suffix = f"_v{version}" if version else ""

        if diff_mode and src.is_file():
            # Find the most recent backup for diff comparison
            existing_backups = sorted(comp_backup_dir.glob(f"{component_id}_*.bak"))
            if existing_backups:
                prev_backup = existing_backups[-1]
                prev_content = prev_backup.read_text()
                current_content = src.read_text()
                diff = _compute_diff(prev_content, current_content)

                # Store only the diff
                backup_name = f"{component_id}_{ts}{version_suffix}.diff.bak"
                backup_path = comp_backup_dir / backup_name
                backup_path.write_text(json.dumps(diff, indent=2))
                backup_type = "diff"
            else:
                # No previous backup, store full content
                backup_name = f"{component_id}_{ts}{version_suffix}.full.bak"
                backup_path = comp_backup_dir / backup_name
                shutil.copy2(str(src), str(backup_path))
                backup_type = "full"
        else:
            # Full backup
            backup_name = f"{component_id}_{ts}{version_suffix}.full.bak"
            backup_path = comp_backup_dir / backup_name
            if src.is_file():
                shutil.copy2(str(src), str(backup_path))
            elif src.is_dir():
                shutil.make_archive(
                    str(backup_path).replace(".bak", ""),
                    "gztar",
                    root_dir=src.parent,
                    base_dir=src.name,
                )
                backup_path = Path(str(backup_path) + ".tar.gz")
            backup_type = "full"

        # Write SPOOL record for this backup
        record = _build_spool_record(
            event="backup",
            component_id=component_id,
            component_type=component_type,
            version=version,
            metadata={
                "backup_path": str(backup_path),
                "backup_type": backup_type,
                "source_path": source_path,
            },
            lessons=lessons,
        )
        spool_path = _write_spool_file(record)

        # Prune old backups
        pruned = 0
        cutoff = datetime.now() - timedelta(days=max_age_days)
        for old_backup in comp_backup_dir.iterdir():
            if old_backup.is_file():
                mtime = datetime.fromtimestamp(old_backup.stat().st_mtime)
                if mtime < cutoff:
                    old_backup.unlink()
                    pruned += 1

        return {
            "success": True,
            "message": f"Backup created for {component_id}",
            "backup_path": str(backup_path),
            "backup_type": backup_type,
            "spool_path": spool_path,
            "pruned_old_backups": pruned,
            "max_age_days": max_age_days,
        }


# ─── Skill: spool_destroy ──────────────────────────────────

class SpoolDestroySkill(BaseSkill):
    """DESTROY — Component destruction with full SPOOL preservation.

    Executes the full DESTROY/REBUILD protocol:
    SALVAGE -> BACKUP -> ARCHIVE -> DESTROY -> REBUILD -> VERIFY

    The SPOOL record is the recovery point for UNFURL.
    """

    meta = SkillMeta(
        id="spool_destroy",
        name="SPOOL Destroy",
        description="DESTROY/REBUILD with full SPOOL preservation",
        category="destructive",
        params=[
            SkillParam(
                name="component_id",
                type="string",
                description="Unique identifier for the component",
                required=True,
            ),
            SkillParam(
                name="component_type",
                type="string",
                description="Type: skill, snack, mcp, hivemind, secret, css",
                default="skill",
            ),
            SkillParam(
                name="version",
                type="string",
                description="Version string",
                default="",
            ),
            SkillParam(
                name="salvage_keys",
                type="array",
                description="Keys to preserve from the component state",
                default=[],
            ),
            SkillParam(
                name="salvage_state",
                type="object",
                description="Pre-extracted state to preserve",
                default={},
            ),
            SkillParam(
                name="rebuild_command",
                type="string",
                description="Command to rebuild the component",
                default="",
            ),
            SkillParam(
                name="source_path",
                type="string",
                description="Path to the component source to destroy",
                default="",
            ),
            SkillParam(
                name="lessons",
                type="array",
                description="Lessons learned from this component",
                default=[],
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                description="Only simulate, dont actually destroy",
                default=True,
            ),
        ],
        timeout=120,
    )

    async def run(self, **kwargs) -> dict:
        component_id = kwargs.get("component_id", "")
        component_type = kwargs.get("component_type", "skill")
        version = kwargs.get("version", "")
        salvage_keys = kwargs.get("salvage_keys", [])
        salvage_state = kwargs.get("salvage_state", {})
        rebuild_command = kwargs.get("rebuild_command", "")
        source_path = kwargs.get("source_path", "")
        lessons = kwargs.get("lessons", [])
        dry_run = kwargs.get("dry_run", True)

        if not component_id:
            return {
                "success": False,
                "message": "component_id is required",
            }

        steps: list[dict[str, Any]] = []
        errors: list[str] = []
        salvaged: dict[str, Any] = {}
        backup_path = ""
        rebuild_output = ""

        # Step 1: SALVAGE
        if salvage_state:
            salvaged = salvage_state
        elif salvage_keys and source_path:
            src = Path(source_path).expanduser()
            if src.exists():
                try:
                    content = src.read_text()
                    for key in salvage_keys:
                        if key in content:
                            salvaged[key] = "[found in source]"
                except Exception:
                    pass

        steps.append({
            "step": "salvage",
            "status": "ok",
            "salvaged_keys": list(salvaged.keys()),
        })

        # Step 2: BACKUP
        if source_path and not dry_run:
            src = Path(source_path).expanduser()
            if src.exists():
                _ensure_dirs()
                comp_backup_dir = BACKUP_DIR / component_id
                comp_backup_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{component_id}_{ts}.pre_destroy.bak"
                backup_path = str(comp_backup_dir / backup_name)
                if src.is_file():
                    shutil.copy2(str(src), backup_path)
                elif src.is_dir():
                    shutil.make_archive(
                        str(comp_backup_dir / f"{component_id}_{ts}.pre_destroy"),
                        "gztar",
                        root_dir=src.parent,
                        base_dir=src.name,
                    )
                    backup_path = str(
                        comp_backup_dir / f"{component_id}_{ts}.pre_destroy.tar.gz"
                    )

        steps.append({
            "step": "backup",
            "status": "ok" if backup_path else "skipped",
            "backup_path": backup_path,
        })

        # Step 3: ARCHIVE (write SPOOL record)
        record = _build_spool_record(
            event="destroy",
            component_id=component_id,
            component_type=component_type,
            version=version,
            metadata={
                "salvage_keys": salvage_keys,
                "rebuild_command": rebuild_command,
                "source_path": source_path,
                "dry_run": dry_run,
            },
            salvaged=salvaged,
            lessons=lessons,
            backup_path=backup_path,
        )
        spool_path = _write_spool_file(record)

        steps.append({
            "step": "archive",
            "status": "ok",
            "spool_path": spool_path,
        })

        # Step 4: DESTROY (skip in dry_run)
        if not dry_run and source_path:
            src = Path(source_path).expanduser()
            if src.exists():
                if src.is_file():
                    src.unlink()
                elif src.is_dir():
                    shutil.rmtree(src)
                steps.append({
                    "step": "destroy",
                    "status": "ok",
                    "removed": str(src),
                })
            else:
                steps.append({
                    "step": "destroy",
                    "status": "skipped",
                    "reason": "Source not found",
                })
        else:
            steps.append({
                "step": "destroy",
                "status": "dry_run",
                "would_remove": source_path,
            })

        # Step 5: REBUILD
        if rebuild_command and not dry_run:
            try:
                cmd = rebuild_command
                for k, v in salvaged.items():
                    cmd = cmd.replace(f"${{{k}}}", str(v))
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=120,
                )
                rebuild_output = result.stdout
                if result.returncode != 0:
                    errors.append(f"Rebuild failed: {result.stderr}")
                steps.append({
                    "step": "rebuild",
                    "status": "ok" if result.returncode == 0 else "failed",
                    "output": rebuild_output[:200],
                })
            except subprocess.TimeoutExpired:
                errors.append("Rebuild timed out")
                steps.append({"step": "rebuild", "status": "timeout"})
            except Exception as exc:
                errors.append(f"Rebuild error: {exc}")
                steps.append({"step": "rebuild", "status": "error"})
        else:
            steps.append({
                "step": "rebuild",
                "status": "dry_run" if dry_run else "skipped",
                "command": rebuild_command,
            })

        # Step 6: VERIFY
        steps.append({
            "step": "verify",
            "status": "ok" if not errors else "failed",
            "errors": errors,
        })

        success = len(errors) == 0
        return {
            "success": success,
            "message": (
                f"DESTROY/REBUILD simulation for {component_id}"
                if dry_run
                else f"DESTROY/REBUILD {'completed' if success else 'failed'} for {component_id}"
            ),
            "dry_run": dry_run,
            "steps": steps,
            "spool_path": spool_path,
            "salvaged": salvaged,
            "backup_path": backup_path,
            "errors": errors,
        }


# ─── Skill: spool_unfurl ───────────────────────────────────

class SpoolUnfurlSkill(BaseSkill):
    """UNFURL — Reverse SPOOL: reconstruct component from archived essence.

    Reads a .spool.json.gz file and materializes the component from
    its plate definition with salvaged state. This is the recovery path
    after a DESTROY or for restoring legacy components.

    The unfurl process:
    1. Read the SPOOL record
    2. Check if a plate exists for this component
    3. If plate exists, rebuild from plate with salvaged state
    4. If no plate, reconstruct from the SPOOL metadata and schema
    5. Write the reconstructed component to the target path
    """

    meta = SkillMeta(
        id="spool_unfurl",
        name="SPOOL Unfurl",
        description="Reverse SPOOL: reconstruct component from archived essence",
        category="recovery",
        params=[
            SkillParam(
                name="spool_path",
                type="string",
                description="Path to the .spool.json.gz file to unfurl",
                required=True,
            ),
            SkillParam(
                name="target_path",
                type="string",
                description="Where to write the reconstructed component",
                default="",
            ),
            SkillParam(
                name="use_plate",
                type="boolean",
                description="Try to use a plate for reconstruction",
                default=True,
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                description="Only show what would be reconstructed",
                default=False,
            ),
        ],
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        spool_path = kwargs.get("spool_path", "")
        target_path = kwargs.get("target_path", "")
        use_plate = kwargs.get("use_plate", True)
        dry_run = kwargs.get("dry_run", False)

        if not spool_path:
            return {
                "success": False,
                "message": "spool_path is required",
            }

        # Read the SPOOL record
        record = _read_spool_file(spool_path)
        if not record:
            return {
                "success": False,
                "message": f"Failed to read SPOOL archive: {spool_path}",
            }

        component = record.get("component", {})
        component_id = component.get("id", "unknown")
        component_type = component.get("type", "unknown")
        version = component.get("version", "0.0.0")
        salvaged = record.get("salvaged", {})
        lessons = record.get("lessons", [])
        schema = record.get("schema", {})
        event = record.get("event", "unknown")

        # Determine target path
        if not target_path:
            target_path = f"./reconstructed_{component_id}"

        target = Path(target_path).expanduser()

        # Try to find a plate
        plate_found = False
        plate_content = ""
        if use_plate:
            # Search plates/ for matching plate
            for plate_file in PLATES_ROOT.rglob("*.yaml"):
                try:
                    import yaml as yl
                    with open(plate_file) as f:
                        data = yl.safe_load(f)
                    if data and data.get("plate", {}).get("id") == component_id:
                        plate_found = True
                        plate_content = plate_file.read_text()
                        break
                except Exception:
                    continue

        # Build reconstruction plan
        reconstruction = {
            "component_id": component_id,
            "component_type": component_type,
            "version": version,
            "event": event,
            "timestamp": record.get("timestamp", ""),
            "plate_found": plate_found,
            "salvaged_keys": list(salvaged.keys()),
            "lesson_count": len(lessons),
            "has_schema": bool(schema),
        }

        if dry_run:
            return {
                "success": True,
                "message": f"UNFURL simulation for {component_id} (from {event} SPOOL)",
                "dry_run": True,
                "reconstruction": reconstruction,
                "spool_path": spool_path,
                "target_path": str(target),
            }

        # Perform reconstruction
        output_lines: list[str] = []
        output_lines.append(f"# Reconstructed: {component_id}")
        output_lines.append(f"# Source SPOOL: {spool_path}")
        output_lines.append(f"# Event: {event} @ {record.get('timestamp', '')}")
        output_lines.append(f"# Version: {version}")
        output_lines.append(f"# Type: {component_type}")
        output_lines.append("")

        if plate_found:
            output_lines.append("# Plate found — using plate definition")
            output_lines.append(plate_content)
        else:
            output_lines.append("# No plate found — reconstructing from SPOOL metadata")
            output_lines.append(f"# Salvaged state: {json.dumps(salvaged, indent=2)}")
            if schema:
                output_lines.append(f"# Schema: {json.dumps(schema, indent=2)}")

        output_lines.append("")
        output_lines.append("# Lessons learned:")
        for i, lesson in enumerate(lessons, 1):
            output_lines.append(f"#   {i}. {lesson}")

        output_lines.append("")
        output_lines.append("# --- Reconstruction metadata ---")
        output_lines.append("# To fully restore, run:")
        if plate_found:
            output_lines.append(f"#   python -m plate_refresh.refresh --destroy {component_id}")
        output_lines.append("# Or use the plate directly from plates/")

        # Write reconstruction
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(output_lines))

        return {
            "success": True,
            "message": f"UNFURL completed for {component_id}",
            "reconstruction": reconstruction,
            "spool_path": spool_path,
            "target_path": str(target),
            "output_lines": len(output_lines),
        }


# ─── Skill: spool_list ─────────────────────────────────────

class SpoolListSkill(BaseSkill):
    """List and search SPOOL archives.

    Supports filtering by component type, event type, and text search.
    """

    meta = SkillMeta(
        id="spool_list",
        name="SPOOL List",
        description="List and search SPOOL archives",
        category="information",
        params=[
            SkillParam(
                name="component_type",
                type="string",
                description="Filter by type: skill, snack, mcp, hivemind, secret, css, legacy",
                default="",
            ),
            SkillParam(
                name="event",
                type="string",
                description="Filter by event: archive, backup, destroy",
                default="",
            ),
            SkillParam(
                name="search",
                type="string",
                description="Text search in component_id",
                default="",
            ),
            SkillParam(
                name="max_results",
                type="integer",
                description="Maximum results to return",
                default=50,
            ),
        ],
        timeout=10,
    )

    async def run(self, **kwargs) -> dict:
        component_type = kwargs.get("component_type", "") or None
        event = kwargs.get("event", "") or None
        search = kwargs.get("search", "")
        max_results = kwargs.get("max_results", 50)

        archives = _list_spool_files(
            component_type=component_type,
            event=event,
            max_results=max_results,
        )

        # Apply text search filter
        if search:
            search_lower = search.lower()
            archives = [
                a for a in archives
                if search_lower in a["component_id"].lower()
            ]

        return {
            "success": True,
            "total": len(archives),
            "archives": archives,
            "filters": {
                "component_type": component_type,
                "event": event,
                "search": search,
            },
        }


# ─── Skill: spool_prune ────────────────────────────────────

class SpoolPruneSkill(BaseSkill):
    """Prune old backups and SPOOL records by age.

    Automatically removes SPOOL records and backups older than
    max_age_days. This prevents indefinite accumulation while
    preserving recent history for recovery.
    """

    meta = SkillMeta(
        id="spool_prune",
        name="SPOOL Prune",
        description="Prune old backups and SPOOL records by age",
        category="maintenance",
        params=[
            SkillParam(
                name="max_age_days",
                type="integer",
                description="Remove records older than this many days",
                default=365,
            ),
            SkillParam(
                name="component_type",
                type="string",
                description="Only prune records of this type",
                default="",
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                description="Only show what would be pruned",
                default=True,
            ),
        ],
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        max_age_days = kwargs.get("max_age_days", 365)
        component_type = kwargs.get("component_type", "") or None
        dry_run = kwargs.get("dry_run", True)

        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        pruned_spools = 0
        pruned_backups = 0
        errors: list[str] = []

        # Prune SPOOL records
        _ensure_dirs()
        for f in SPOOL_DIR.glob("spool_*.json.gz"):
            try:
                with gzip.open(f, "rt", encoding="utf-8") as fh:
                    record = json.load(fh)
                ts_str = record.get("timestamp", "")
                if ts_str:
                    ts = datetime.fromisoformat(ts_str)
                    if ts < cutoff:
                        if component_type:
                            rec_type = record.get("component", {}).get("type", "")
                            if rec_type != component_type:
                                continue
                        if not dry_run:
                            f.unlink()
                        pruned_spools += 1
            except Exception as exc:
                errors.append(f"Error processing {f.name}: {exc}")

        # Prune old backups
        for backup_dir in BACKUP_DIR.iterdir():
            if backup_dir.is_dir():
                for f in backup_dir.iterdir():
                    if f.is_file():
                        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                        if mtime < cutoff:
                            if not dry_run:
                                f.unlink()
                            pruned_backups += 1

        return {
            "success": True,
            "message": (
                f"Would prune {pruned_spools} SPOOL records and "
                f"{pruned_backups} backups older than {max_age_days} days"
                if dry_run
                else f"Pruned {pruned_spools} SPOOL records and "
                f"{pruned_backups} backups older than {max_age_days} days"
            ),
            "dry_run": dry_run,
            "pruned": {
                "spool_records": pruned_spools,
                "backups": pruned_backups,
            },
            "errors": errors,
        }


# ─── Nugget Helpers ────────────────────────────────────────

def _ensure_nugget_dir() -> None:
    """Ensure the Nugget directory exists."""
    NUGGET_DIR.mkdir(parents=True, exist_ok=True)


def _generate_cookiecutter_template(
    component_id: str,
    component_type: str,
    source_content: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Generate a Cookiecutter template from a component's source.

    Creates a Cookiecutter-compatible template structure that can be
    used to re-instantiate the component anywhere. The template includes:
    - cookiecutter.json with prompts derived from the schema
    - A {{cookiecutter.component_id}}/ directory with the source
    - Jinja2 template variables for all schema properties

    Returns:
        Dict with 'template_dir' (path to temp dir) and 'context' (defaults)
    """
    import tempfile

    # Build Cookiecutter context from schema properties
    context = {"component_id": component_id}
    if schema and "properties" in schema:
        for prop_name, prop_def in schema["properties"].items():
            context[prop_name] = prop_def.get("default", "")

    # Create a temporary Cookiecutter template directory
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"nugget_cc_{component_id}_"))
    template_dir = tmp_dir / "{{cookiecutter.component_id}}"
    template_dir.mkdir(parents=True, exist_ok=True)

    # Write cookiecutter.json
    cc_json = {
        "component_id": component_id,
        "component_type": component_type,
        **{k: v for k, v in context.items() if k not in ("component_id",)},
    }
    with open(tmp_dir / "cookiecutter.json", "w") as f:
        json.dump(cc_json, f, indent=2)

    # Write the source as a Jinja2 template (with variable substitution)
    # Replace actual values with Cookiecutter template variables
    template_content = source_content
    for key, value in context.items():
        if isinstance(value, (str, int, float)):
            template_content = template_content.replace(
                str(value), f"{{{{cookiecutter.{key}}}}}"
            )

    # Write the main template file
    main_file = template_dir / "main.py"
    main_file.write_text(template_content)

    # Write a README template
    readme = template_dir / "README.md"
    readme.write_text(
        "# {{cookiecutter.component_id}}\n\n"
        "Type: {{cookiecutter.component_type}}\n\n"
        "Reborn from a Nugget. Run `cookiecutter` to re-instantiate.\n"
    )

    return {"template_dir": str(tmp_dir), "context": context}


def _write_nugget_file(
    record: dict[str, Any],
    cookiecutter_template: str | None = None,
) -> str:
    """Write a Nugget record to gzip'd JSON file.

    Nuggets use the same gzip'd JSON format as SPOOLs but are stored
    in ~/.ucore/nuggets/ and have a 'nugget' event type. They are
    intentionally created artifacts meant to be discovered and reborn.

    If cookiecutter_template is provided, the Nugget is stored as a
    gzip'd tar archive containing both the JSON record and the
    Cookiecutter template directory, making it fully redeployable.

    Returns:
        Path to the written nugget file
    """
    _ensure_nugget_dir()
    cid = record.get("component", {}).get("id", "unknown")
    ts = record.get("timestamp", datetime.now(timezone.utc).isoformat())
    ts_safe = ts.replace(":", "-").replace("+", "_").replace(".", "_")
    filename = f"nugget_{cid}_{ts_safe}.json.gz"

    if cookiecutter_template:
        # Store as gzip'd tar: record.json + cookiecutter template dir
        import io as _io
        import tarfile
        nugget_path = NUGGET_DIR / filename.replace(".json.gz", ".tar.gz")
        cc_dir = Path(cookiecutter_template)
        with tarfile.open(nugget_path, "w:gz") as tar:
            # Add the JSON record
            record_json = json.dumps(record, indent=2, default=str).encode()
            record_tarinfo = tarfile.TarInfo(name="record.json")
            record_tarinfo.size = len(record_json)
            tar.addfile(record_tarinfo, _io.BytesIO(record_json))

            # Add the Cookiecutter template directory
            tar.add(str(cc_dir), arcname="cookiecutter_template")

        # Clean up temp dir
        shutil.rmtree(str(cc_dir.parent), ignore_errors=True)
        log.info("Nugget with Cookiecutter template written: %s", nugget_path)
    else:
        # Simple gzip'd JSON
        nugget_path = NUGGET_DIR / filename
        with gzip.open(nugget_path, "wt", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)
        log.info("Nugget written: %s", nugget_path)

    return str(nugget_path)


def _read_nugget_file(
    nugget_path: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Read a Nugget file, extracting the record and optional Cookiecutter template.

    Supports both simple .json.gz and .tar.gz (with Cookiecutter template).

    Returns:
        Tuple of (record_dict_or_None, cookiecutter_template_dir_or_None)
    """
    import tarfile
    import tempfile

    path = Path(nugget_path).expanduser()
    if not path.exists():
        return None, None

    if ".tar" in path.suffixes and path.suffix == ".gz":
        # Tar.gz with Cookiecutter template
        try:
            with tarfile.open(path, "r:gz") as tar:
                # Extract record.json
                record_member = tar.extractfile("record.json")
                if record_member:
                    record = json.loads(record_member.read().decode())
                else:
                    return None, None

                # Extract Cookiecutter template to temp dir
                try:
                    tar.getmember("cookiecutter_template")
                    tmp_dir = Path(tempfile.mkdtemp(
                        prefix=f"nugget_extract_"
                        f"{record.get('component', {}).get('id', 'unknown')}_"
                    ))
                    tar.extractall(path=tmp_dir)
                    cc_path = str(tmp_dir / "cookiecutter_template")
                    return record, cc_path
                except KeyError:
                    return record, None
        except Exception as exc:
            log.warning("Failed to read tar nugget %s: %s", nugget_path, exc)
            return None, None
    else:
        # Simple gzip'd JSON
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                record = json.load(f)
            return record, None
        except Exception as exc:
            log.warning("Failed to read nugget %s: %s", nugget_path, exc)
            return None, None


def _list_nugget_files(
    component_type: str | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """List Nugget files with optional filters."""
    _ensure_nugget_dir()
    results: list[dict[str, Any]] = []
    for f in sorted(NUGGET_DIR.glob("nugget_*.json.gz"), reverse=True):
        try:
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                record = json.load(fh)
            if component_type and record.get("component", {}).get("type") != component_type:
                continue
            results.append({
                "file": str(f),
                "timestamp": record.get("timestamp", ""),
                "component_id": record.get("component", {}).get("id", ""),
                "component_type": record.get("component", {}).get("type", ""),
                "version": record.get("component", {}).get("version", ""),
                "description": record.get("component", {}).get("description", ""),
                "salvaged_keys": list(record.get("salvaged", {}).keys()),
                "lesson_count": len(record.get("lessons", [])),
                "has_schema": bool(record.get("schema")),
                "created_by": record.get("component", {}).get("created_by", ""),
                "legacy": record.get("component", {}).get("legacy", False),
            })
            if len(results) >= max_results:
                break
        except Exception:
            continue
    return results


# ─── Skill: nugget_create ──────────────────────────────────

class NuggetCreateSkill(BaseSkill):
    """NUGGET CREATE — Intentionally create a Nugget from a component.

    A Nugget (or Nug) is a compressed legacy relic that contains useful
    data and can be redeployed/reborn. Unlike a SPOOL (which is a system
    by-product of Destroy/Backup), a Nugget is intentionally created and
    left by a user, or may be a by-product of a Destroy and System Plate
    Reset.

    Nuggets are stored in ~/.ucore/nuggets/ and can be:
    - Intentionally created by a user to preserve something valuable
    - By-product of a DESTROY and System Plate Reset
    - Redeployed/reborn via unfurl back into a living component
    - Left behind as a legacy artifact for future discovery
    """

    meta = SkillMeta(
        id="nugget_create",
        name="Nugget Create",
        description="Intentionally create a Nugget from a component",
        category="creation",
        params=[
            SkillParam(
                name="component_id",
                type="string",
                description="Unique identifier for the component",
                required=True,
            ),
            SkillParam(
                name="component_type",
                type="string",
                description="Type: skill, snack, mcp, hivemind, secret, css, legacy",
                default="legacy",
            ),
            SkillParam(
                name="version",
                type="string",
                description="SemVer version string",
                default="0.0.0",
            ),
            SkillParam(
                name="source_path",
                type="string",
                description="Path to the file/directory to nuggetize",
                required=True,
            ),
            SkillParam(
                name="description",
                type="string",
                description="Human-readable description of this nugget",
                default="",
            ),
            SkillParam(
                name="created_by",
                type="string",
                description="Who created this nugget (user, system, skill)",
                default="user",
            ),
            SkillParam(
                name="legacy",
                type="boolean",
                description="Mark as a legacy relic (left behind intentionally)",
                default=False,
            ),
            SkillParam(
                name="metadata",
                type="object",
                description="Additional metadata to preserve",
                default={},
            ),
            SkillParam(
                name="lessons",
                type="array",
                description="Lessons learned from this component",
                default=[],
            ),
            SkillParam(
                name="schema",
                type="object",
                description="JSON schema of the component",
                default={},
            ),
            SkillParam(
                name="remove_source",
                type="boolean",
                description="Remove the source file after nuggetizing",
                default=False,
            ),
        ],
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        component_id = kwargs.get("component_id", "")
        component_type = kwargs.get("component_type", "legacy")
        version = kwargs.get("version", "0.0.0")
        source_path = kwargs.get("source_path", "")
        description = kwargs.get("description", "")
        created_by = kwargs.get("created_by", "user")
        legacy = kwargs.get("legacy", False)
        extra_metadata = kwargs.get("metadata", {})
        lessons = kwargs.get("lessons", [])
        schema = kwargs.get("schema", {})
        remove_source = kwargs.get("remove_source", False)

        if not component_id or not source_path:
            return {
                "success": False,
                "message": "component_id and source_path are required",
            }

        src = Path(source_path).expanduser()
        if not src.exists():
            return {
                "success": False,
                "message": f"Source path not found: {source_path}",
            }

        # Read source content
        source_content = ""
        if src.is_file():
            try:
                source_content = src.read_text()
            except Exception:
                source_content = f"[binary file: {src.name}]"

        # Build metadata
        metadata = {
            "source_path": str(src),
            "source_size_bytes": src.stat().st_size if src.exists() else 0,
            "description": description,
            "created_by": created_by,
            "legacy": legacy,
            **extra_metadata,
        }

        # Build the Nugget record (same format as SPOOL but with nugget event)
        record = _build_spool_record(
            event="nugget",
            component_id=component_id,
            component_type=component_type,
            version=version,
            metadata=metadata,
            salvaged={"source_summary": source_content[:1000]},
            lessons=lessons,
            schema=schema,
        )

        nugget_path = _write_nugget_file(record)

        # Optionally remove source
        if remove_source:
            if src.is_file():
                src.unlink()
                log.info("Removed source after nuggetizing: %s", src)
            elif src.is_dir():
                shutil.rmtree(src)
                log.info("Removed source directory after nuggetizing: %s", src)

        return {
            "success": True,
            "message": f"Nugget created: {component_id} (v{version})",
            "nugget_path": nugget_path,
            "component_id": component_id,
            "component_type": component_type,
            "version": version,
            "description": description,
            "created_by": created_by,
            "legacy": legacy,
            "source_removed": remove_source,
            "lesson_count": len(lessons),
        }


# ─── Skill: nugget_list ────────────────────────────────────

class NuggetListSkill(BaseSkill):
    """NUGGET LIST — List and search Nuggets.

    Supports filtering by component type and text search.
    """

    meta = SkillMeta(
        id="nugget_list",
        name="Nugget List",
        description="List and search Nuggets",
        category="information",
        params=[
            SkillParam(
                name="component_type",
                type="string",
                description="Filter by type: skill, snack, mcp, hivemind, secret, css, legacy",
                default="",
            ),
            SkillParam(
                name="search",
                type="string",
                description="Text search in component_id or description",
                default="",
            ),
            SkillParam(
                name="legacy_only",
                type="boolean",
                description="Only show legacy Nuggets",
                default=False,
            ),
            SkillParam(
                name="max_results",
                type="integer",
                description="Maximum results to return",
                default=50,
            ),
        ],
        timeout=10,
    )

    async def run(self, **kwargs) -> dict:
        component_type = kwargs.get("component_type", "") or None
        search = kwargs.get("search", "")
        legacy_only = kwargs.get("legacy_only", False)
        max_results = kwargs.get("max_results", 50)

        nuggets = _list_nugget_files(
            component_type=component_type,
            max_results=max_results,
        )

        # Apply text search filter
        if search:
            search_lower = search.lower()
            nuggets = [
                n for n in nuggets
                if search_lower in n["component_id"].lower()
                or search_lower in n.get("description", "").lower()
            ]

        # Filter legacy only
        if legacy_only:
            nuggets = [n for n in nuggets if n.get("legacy")]

        return {
            "success": True,
            "total": len(nuggets),
            "nuggets": nuggets,
            "filters": {
                "component_type": component_type,
                "search": search,
                "legacy_only": legacy_only,
            },
        }


# ─── Skill: nugget_redeploy ────────────────────────────────

class NuggetRedeploySkill(BaseSkill):
    """NUGGET REDEPLOY — Redeploy/reborn a Nugget back into a living component.

    Reads a Nugget file from ~/.ucore/nuggets/ and materializes the
    component from its plate definition with salvaged state. This is
    the rebirth path for Nuggets — taking a compressed legacy relic
    and bringing it back to life.

    The redeploy process:
    1. Read the Nugget record
    2. Check if a plate exists for this component
    3. If plate exists, rebuild from plate with salvaged state
    4. If no plate, reconstruct from the Nugget metadata and schema
    5. Write the reborn component to the target path
    """

    meta = SkillMeta(
        id="nugget_redeploy",
        name="Nugget Redeploy",
        description="Redeploy/reborn a Nugget back into a living component",
        category="recovery",
        params=[
            SkillParam(
                name="nugget_path",
                type="string",
                description="Path to the nugget file to redeploy",
                required=True,
            ),
            SkillParam(
                name="target_path",
                type="string",
                description="Where to write the reborn component",
                default="",
            ),
            SkillParam(
                name="use_plate",
                type="boolean",
                description="Try to use a plate for reconstruction",
                default=True,
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                description="Only show what would be redeployed",
                default=False,
            ),
        ],
        timeout=30,
    )

    async def run(self, **kwargs) -> dict:
        nugget_path = kwargs.get("nugget_path", "")
        target_path = kwargs.get("target_path", "")
        use_plate = kwargs.get("use_plate", True)
        dry_run = kwargs.get("dry_run", False)

        if not nugget_path:
            return {
                "success": False,
                "message": "nugget_path is required",
            }

        # Read the Nugget record
        path = Path(nugget_path).expanduser()
        if not path.exists():
            return {
                "success": False,
                "message": f"Nugget not found: {nugget_path}",
            }

        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                record = json.load(f)
        except Exception as exc:
            return {
                "success": False,
                "message": f"Failed to read Nugget: {exc}",
            }

        component = record.get("component", {})
        component_id = component.get("id", "unknown")
        component_type = component.get("type", "unknown")
        version = component.get("version", "0.0.0")
        salvaged = record.get("salvaged", {})
        lessons = record.get("lessons", [])
        schema = record.get("schema", {})
        description = component.get("description", "")

        # Determine target path
        if not target_path:
            target_path = f"./reborn_{component_id}"

        target = Path(target_path).expanduser()

        # Try to find a plate
        plate_found = False
        plate_content = ""
        if use_plate:
            for plate_file in PLATES_ROOT.rglob("*.yaml"):
                try:
                    import yaml as yl
                    with open(plate_file) as f:
                        data = yl.safe_load(f)
                    if data and data.get("plate", {}).get("id") == component_id:
                        plate_found = True
                        plate_content = plate_file.read_text()
                        break
                except Exception:
                    continue

        # Build redeployment plan
        redeployment = {
            "component_id": component_id,
            "component_type": component_type,
            "version": version,
            "description": description,
            "timestamp": record.get("timestamp", ""),
            "plate_found": plate_found,
            "salvaged_keys": list(salvaged.keys()),
            "lesson_count": len(lessons),
            "has_schema": bool(schema),
        }

        if dry_run:
            return {
                "success": True,
                "message": f"Nugget redeploy simulation for {component_id}",
                "dry_run": True,
                "redeployment": redeployment,
                "nugget_path": nugget_path,
                "target_path": str(target),
            }

        # Perform redeployment
        output_lines: list[str] = []
        output_lines.append(f"# Reborn: {component_id}")
        output_lines.append(f"# Source Nugget: {nugget_path}")
        output_lines.append(f"# Timestamp: {record.get('timestamp', '')}")
        output_lines.append(f"# Version: {version}")
        output_lines.append(f"# Type: {component_type}")
        output_lines.append(f"# Description: {description}")
        output_lines.append("")

        if plate_found:
            output_lines.append("# Plate found -- using plate definition")
            output_lines.append(plate_content)
        else:
            output_lines.append("# No plate found -- reconstructing from Nugget")
            output_lines.append(f"# Salvaged state: {json.dumps(salvaged, indent=2)}")
            if schema:
                output_lines.append(f"# Schema: {json.dumps(schema, indent=2)}")

        output_lines.append("")
        output_lines.append("# Lessons learned:")
        for i, lesson in enumerate(lessons, 1):
            output_lines.append(f"#   {i}. {lesson}")

        output_lines.append("")
        output_lines.append("# --- Redeployment metadata ---")
        output_lines.append("# This component was reborn from a Nugget.")
        output_lines.append("# To fully restore, run:")
        if plate_found:
            output_lines.append(
                f"#   python -m plate_refresh.refresh --destroy {component_id}"
            )
        output_lines.append("# Or use the plate directly from plates/")

        # Write reborn component
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(output_lines))

        return {
            "success": True,
            "message": f"Nugget redeployed: {component_id} reborn at {target}",
            "redeployment": redeployment,
            "nugget_path": nugget_path,
            "target_path": str(target),
            "output_lines": len(output_lines),
        }


# ─── Skill: nugget_discover ────────────────────────────────

class NuggetDiscoverSkill(BaseSkill):
    """NUGGET DISCOVER — Discover Nuggets left by other users or systems.

    Scans ~/.ucore/nuggets/ for Nuggets that were left behind as legacy
    artifacts. This is the discovery mechanism for finding useful relics
    that may contain valuable data, schemas, or lessons.

    Discovery can be filtered by:
    - Component type (skill, snack, mcp, etc.)
    - Legacy status (intentionally left behind)
    - Age (recent vs ancient)
    - Text search in description or component_id
    """

    meta = SkillMeta(
        id="nugget_discover",
        name="Nugget Discover",
        description="Discover Nuggets left by other users or systems",
        category="information",
        params=[
            SkillParam(
                name="component_type",
                type="string",
                description="Filter by type: skill, snack, mcp, hivemind, secret, css, legacy",
                default="",
            ),
            SkillParam(
                name="search",
                type="string",
                description="Text search in component_id or description",
                default="",
            ),
            SkillParam(
                name="legacy_only",
                type="boolean",
                description="Only show legacy Nuggets (left behind intentionally)",
                default=True,
            ),
            SkillParam(
                name="max_age_days",
                type="integer",
                description="Only show Nuggets newer than this many days",
                default=0,
            ),
            SkillParam(
                name="max_results",
                type="integer",
                description="Maximum results to return",
                default=50,
            ),
        ],
        timeout=15,
    )

    async def run(self, **kwargs) -> dict:
        component_type = kwargs.get("component_type", "") or None
        search = kwargs.get("search", "")
        legacy_only = kwargs.get("legacy_only", True)
        max_age_days = kwargs.get("max_age_days", 0)
        max_results = kwargs.get("max_results", 50)

        nuggets = _list_nugget_files(
            component_type=component_type,
            max_results=max_results * 2,  # Get extra for filtering
        )

        # Apply text search
        if search:
            search_lower = search.lower()
            nuggets = [
                n for n in nuggets
                if search_lower in n["component_id"].lower()
                or search_lower in n.get("description", "").lower()
            ]

        # Filter legacy only
        if legacy_only:
            nuggets = [n for n in nuggets if n.get("legacy")]

        # Filter by age
        if max_age_days > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            nuggets = [
                n for n in nuggets
                if n.get("timestamp", "") and
                datetime.fromisoformat(n["timestamp"]) >= cutoff
            ]

        # Limit results
        nuggets = nuggets[:max_results]

        return {
            "success": True,
            "total": len(nuggets),
            "nuggets": nuggets,
            "filters": {
                "component_type": component_type,
                "search": search,
                "legacy_only": legacy_only,
                "max_age_days": max_age_days,
            },
            "discovery_note": (
                "Nuggets are compressed legacy relics that can be "
                "redeployed/reborn via nugget_redeploy. They may contain "
                "useful data, schemas, or lessons from past components."
            ),
        }

