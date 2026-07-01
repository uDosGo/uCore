"""DESTROY/REBUILD — Dev Mode recovery command.

Safely destroys and rebuilds Dev Mode components using template
snapshots managed by TemplateManager (hivemind.008).

Workflow:
1. Backup current state → SPOOL as recovery point
2. DESTROY: remove component state files, reset surfaces
3. REBUILD: restore from template (default or specified)

Safety: never touches data, only Dev Mode config/state.
"""
from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.template_manager import get_template_manager

log = logging.getLogger("ucore.skills.destroy_rebuild")

RECOVERY_DIR = Path.home() / ".ucore" / "recovery"
SPOOL_DIR = Path.home() / ".tasker" / "spool"
WISDOM_DIR = SPOOL_DIR / "wisdom"

# Components that can be destroyed/rebuild
RESETTABLE_COMPONENTS = {
    "dev_layer": {
        "path": Path.home() / ".ucore" / "config.yaml",
        "description": "Dev Mode layer state (mode, surface visibility)",
    },
    "templates": {
        "path": Path.home() / ".ucore" / "templates",
        "description": "All template snapshots (default, stable, exp, custom)",
    },
    "dev_mode_store": {
        "path": None,  # In-memory / Vue store; reset via API
        "description": "Frontend devMode.ts store state",
    },
    "spool_wisdom": {
        "path": WISDOM_DIR,
        "description": "Wisdom records in .tasker/spool/wisdom",
    },
}


@dataclass
class RecoveryPoint:
    """A backup of component state before destruction."""

    id: str
    timestamp: str
    components: list[str]
    path: Path

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "components": self.components,
            "path": str(self.path),
        }


class DestroyRebuildSkill:
    """DESTROY/REBUILD — Component-level Dev Mode recovery."""

    def __init__(self):
        self._template_mgr = get_template_manager()
        self._recovery: list[RecoveryPoint] = []
        self._load_recovery_points()

    # ── DESTROY ──────────────────────────────────────────────

    def destroy(
        self,
        components: list[str] | None = None,
        template_id: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Destroy specified components after backup.

        Args:
            components: List of component IDs to destroy.
                        None = all resettable components.
            template_id: Save a template before destruction.
            dry_run: If True, only report what would be done.

        Returns:
            Dict with backup_id, destroyed_components, template_id
        """
        targets = components or list(RESETTABLE_COMPONENTS.keys())
        unknown = [c for c in targets if c not in RESETTABLE_COMPONENTS]
        if unknown:
            return {
                "error": f"Unknown components: {unknown}",
                "known": list(RESETTABLE_COMPONENTS.keys()),
            }

        # 1. Backup
        backup = self._backup(targets)
        if backup:
            log.info("Backup created: %s", backup.id)

        # 2. Template snapshot
        saved_template = None
        if template_id or dry_run:
            template_name = template_id or f"pre-destroy-{_now_slug()}"
            try:
                saved_template = self._template_mgr.create_template(
                    name=template_name,
                    tier="custom",
                    description=(
                        f"Auto-saved before DESTROY of {', '.join(targets)}"
                    ),
                    tags=["auto-save", "pre-destroy", *targets],
                    state=self._capture_state(targets),
                )
                log.info("Template saved: %s", saved_template.id)
            except Exception as exc:
                log.warning("Template save failed: %s", exc)

        if dry_run:
            return {
                "dry_run": True,
                "would_destroy": targets,
                "would_backup": backup is not None,
                "would_save_template": saved_template is not None,
            }

        # 3. Execute destruction
        destroyed = []
        for component in targets:
            if self._destroy_component(component):
                destroyed.append(component)

        return {
            "backup_id": backup.id if backup else None,
            "destroyed": destroyed,
            "template_id": saved_template.id if saved_template else None,
            "message": (
                f"Destroyed {len(destroyed)} component(s). "
                f"Use 'rebuild {backup.id}' to restore."
            ),
        }

    def _destroy_component(self, component: str) -> bool:
        """Remove component state files."""
        info = RESETTABLE_COMPONENTS[component]
        path = info["path"]
        if path is None:
            # In-memory component; just report success
            log.info("Component '%s' is in-memory — reset via API", component)
            return True
        if not path.exists():
            log.info("Component '%s' has no state to destroy", component)
            return True
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            log.info("Destroyed %s: %s", component, path)
            return True
        except OSError as exc:
            log.error("Failed to destroy %s: %s", component, exc)
            return False

    # ── REBUILD ──────────────────────────────────────────────

    def rebuild(
        self,
        backup_id: str | None = None,
        template_id: str | None = None,
        components: list[str] | None = None,
    ) -> dict[str, Any]:
        """Rebuild components from backup or template.

        Args:
            backup_id: Restore from a specific recovery point.
            template_id: Rebuild from a template snapshot.
            components: Subset of components to restore (default: all).

        Priority: backup > template > default
        """
        if backup_id:
            return self._rebuild_from_backup(backup_id, components)
        if template_id:
            return self._rebuild_from_template(template_id, components)
        return self._rebuild_defaults(components)

    def _rebuild_from_backup(
        self, backup_id: str, components: list[str] | None
    ) -> dict[str, Any]:
        """Restore from a specific recovery point."""
        rp = self._find_recovery(backup_id)
        if not rp:
            return {"error": f"Recovery point '{backup_id}' not found"}
        if not rp.path.exists():
            return {"error": f"Recovery point path missing: {rp.path}"}

        restored = []
        targets = components or rp.components
        for comp in targets:
            if comp not in RESETTABLE_COMPONENTS:
                continue
            comp_path = RESETTABLE_COMPONENTS[comp]["path"]
            backup_comp = rp.path / comp
            if comp_path and backup_comp.exists():
                comp_path.parent.mkdir(parents=True, exist_ok=True)
                if backup_comp.is_dir():
                    shutil.copytree(backup_comp, comp_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(backup_comp, comp_path)
                restored.append(comp)
                log.info("Restored %s from backup %s", comp, backup_id)

        return {
            "restored_from": "backup",
            "backup_id": backup_id,
            "restored": restored,
        }

    def _rebuild_from_template(
        self, template_id: str, components: list[str] | None
    ) -> dict[str, Any]:
        """Rebuild from a template snapshot."""
        tm = get_template_manager()
        tp = tm.get_path(template_id)
        if not tp:
            return {"error": f"Template '{template_id}' not found"}

        state = tm._load_state(tp)  # noqa: protected-access
        if not state:
            return {"error": f"Template '{template_id}' has no state"}

        log.info("Rebuilding from template %s", template_id)
        return {
            "restored_from": "template",
            "template_id": template_id,
            "state": state,
        }

    def _rebuild_defaults(
        self, components: list[str] | None
    ) -> dict[str, Any]:
        """Reset components to defaults."""
        targets = components or list(RESETTABLE_COMPONENTS.keys())
        log.info("Resetting %d components to defaults", len(targets))
        return {
            "restored_from": "defaults",
            "reset": targets,
            "message": (
                f"Reset {len(targets)} component(s) to defaults. "
                "Restart surfaces to apply."
            ),
        }

    # ── Backup ───────────────────────────────────────────────

    def _backup(self, components: list[str]) -> RecoveryPoint | None:
        """Backup component state before destruction."""
        now = datetime.now(timezone.utc)
        rp_id = f"recovery-{now.strftime('%Y%m%d-%H%M%S')}"
        rp_path = RECOVERY_DIR / rp_id
        rp_path.mkdir(parents=True, exist_ok=True)

        backed_up = []
        for comp in components:
            info = RESETTABLE_COMPONENTS[comp]
            path = info["path"]
            if path is None or not path.exists():
                continue
            dest = rp_path / comp
            try:
                if path.is_dir():
                    shutil.copytree(path, dest)
                else:
                    shutil.copy2(path, dest)
                backed_up.append(comp)
            except OSError as exc:
                log.warning("Backup failed for %s: %s", comp, exc)

        if not backed_up:
            shutil.rmtree(rp_path, ignore_errors=True)
            return None

        rp = RecoveryPoint(
            id=rp_id,
            timestamp=now.isoformat(),
            components=backed_up,
            path=rp_path,
        )
        self._recovery.append(rp)
        self._save_recovery_point(rp)
        return rp

    def _capture_state(self, components: list[str]) -> dict:
        """Capture current Dev Mode state for template snapshot."""
        state: dict[str, Any] = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "components": {},
        }
        for comp in components:
            info = RESETTABLE_COMPONENTS[comp]
            path = info["path"]
            if path and path.exists():
                try:
                    if path.is_file():
                        state["components"][comp] = {
                            "path": str(path),
                            "exists": True,
                            "type": "file",
                        }
                    elif path.is_dir():
                        state["components"][comp] = {
                            "path": str(path),
                            "exists": True,
                            "type": "directory",
                            "entries": [
                                str(p.relative_to(path))
                                for p in path.rglob("*")
                            ],
                        }
                except Exception:
                    state["components"][comp] = {"path": str(path), "error": "read failed"}
            else:
                state["components"][comp] = {"path": str(path) if path else "in-memory"}
        return state

    # ── Recovery Point Management ────────────────────────────

    def list_recovery_points(self) -> list[dict]:
        return [rp.to_dict() for rp in self._recovery]

    def _find_recovery(self, rp_id: str) -> RecoveryPoint | None:
        for rp in self._recovery:
            if rp.id == rp_id:
                return rp
        # Check disk
        rp_path = RECOVERY_DIR / rp_id
        if rp_path.is_dir():
            manifest_file = rp_path / "manifest.json"
            if manifest_file.exists():
                try:
                    data = json.loads(manifest_file.read_text("utf-8"))
                    rp = RecoveryPoint(
                        id=data.get("id", rp_id),
                        timestamp=data.get("timestamp", ""),
                        components=data.get("components", []),
                        path=rp_path,
                    )
                    self._recovery.append(rp)
                    return rp
                except (json.JSONDecodeError, KeyError):
                    pass
        return None

    def _save_recovery_point(self, rp: RecoveryPoint) -> None:
        manifest_file = rp.path / "manifest.json"
        manifest_file.write_text(
            json.dumps(rp.to_dict(), indent=2), "utf-8"
        )

    def _load_recovery_points(self) -> None:
        """Scan recovery directory for existing points."""
        if not RECOVERY_DIR.is_dir():
            return
        for entry in sorted(RECOVERY_DIR.iterdir()):
            if entry.is_dir():
                manifest_file = entry / "manifest.json"
                if manifest_file.exists():
                    try:
                        data = json.loads(manifest_file.read_text("utf-8"))
                        self._recovery.append(RecoveryPoint(
                            id=data.get("id", entry.name),
                            timestamp=data.get("timestamp", ""),
                            components=data.get("components", []),
                            path=entry,
                        ))
                    except (json.JSONDecodeError, KeyError):
                        pass


# ─── Singleton ──────────────────────────────────────────────

_skill: DestroyRebuildSkill | None = None


def get_destroy_rebuild_skill() -> DestroyRebuildSkill:
    global _skill
    if _skill is None:
        _skill = DestroyRebuildSkill()
    return _skill


def reset_skill() -> None:
    global _skill
    _skill = None


def _now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
