"""Slate — Dev Mode recovery template system (renamed from Plate).

>>>>>>> renamed: Plate → Slate across the uCore ecosystem. 
>>>>>>> Slate now hosts versioned, verifiable Dev Mode templates
>>>>>>> organized in four tiers: default, stable, experimental, custom.

Manages application state templates stored in ~/.ucode/templates/
across four tiers: default, stable, experimental, custom.

Templates capture surface visibility, feature flags, masonry layout,
grid state, and spool config — enabling DESTROY/REBUILD recovery.

Integrates with Cookiecutter for scaffolding new templates.
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.services.template_manager")

TEMPLATE_DIR = Path.home() / ".ucore" / "templates"
TIERS = ["default", "stable", "experimental", "custom"]


@dataclass
class TemplateManifest:
    """Metadata for a single template."""

    id: str
    name: str
    tier: str
    description: str
    created: str
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    parent: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> TemplateManifest:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            tier=data.get("tier", "custom"),
            description=data.get("description", ""),
            created=data.get("created", _now_iso()),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            parent=data.get("parent"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier,
            "description": self.description,
            "created": self.created,
            "version": self.version,
            "tags": self.tags,
            "parent": self.parent,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TemplateManager:
    """Template discovery, creation, and management.

    Layout:
        ~/.ucode/templates/
        ├── default/<id>/manifest.json + template.yaml
        ├── stable/<id>/...
        ├── experimental/<id>/...
        └── custom/<id>/...
    """

    def __init__(self, template_dir: str | Path | None = None):
        self._dir = Path(template_dir) if template_dir else TEMPLATE_DIR
        self._ensure_dirs()

    # ── Directory ──────────────────────────────────────────────

    def _ensure_dirs(self) -> None:
        for tier in TIERS:
            (self._dir / tier).mkdir(parents=True, exist_ok=True)

    def get_path(self, template_id: str) -> Path | None:
        for tier in TIERS:
            path = self._dir / tier / template_id
            if path.is_dir():
                return path
        return None

    # ── Discovery ─────────────────────────────────────────────

    def list_templates(
        self, tier: str | None = None
    ) -> list[TemplateManifest]:
        results: list[TemplateManifest] = []
        tiers = [tier] if tier else TIERS
        for t in tiers:
            d = self._dir / t
            if not d.is_dir():
                continue
            for entry in d.iterdir():
                if entry.is_dir():
                    m = self._load_manifest(entry)
                    if m:
                        results.append(m)
        return results

    def find_template(
        self, query: str, tier: str | None = None
    ) -> list[TemplateManifest]:
        q = query.lower()
        return [
            t for t in self.list_templates(tier)
            if q in t.name.lower()
            or q in t.description.lower()
            or any(q in tag.lower() for tag in t.tags)
        ]

    def count_by_tier(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for tier in TIERS:
            d = self._dir / tier
            counts[tier] = (
                len([p for p in d.iterdir() if p.is_dir()])
                if d.is_dir() else 0
            )
        return counts

    # ── Creation ──────────────────────────────────────────────

    def create_template(
        self,
        name: str,
        tier: str = "custom",
        description: str = "",
        tags: list[str] | None = None,
        state: dict | None = None,
        parent: str | None = None,
    ) -> TemplateManifest:
        if tier not in TIERS:
            raise ValueError(
                f"Invalid tier '{tier}'. Use: {', '.join(TIERS)}"
            )

        template_id = self._slugify(name)
        tdir = self._dir / tier / template_id
        counter = 1
        while tdir.exists():
            template_id = f"{self._slugify(name)}-{counter}"
            tdir = self._dir / tier / template_id
            counter += 1
        tdir.mkdir(parents=True)

        manifest = TemplateManifest(
            id=template_id,
            name=name,
            tier=tier,
            description=description,
            created=_now_iso(),
            version="1.0.0",
            tags=tags or [],
            parent=parent,
        )
        self._write_manifest(tdir, manifest)
        if state:
            self._write_state(tdir, state)
        self._write_cookiecutter_config(tdir, manifest)
        log.info("Template created: %s/%s", tier, template_id)
        return manifest

    def fork_template(
        self,
        source_id: str,
        new_name: str,
        target_tier: str = "custom",
        description: str | None = None,
    ) -> TemplateManifest:
        sp = self.get_path(source_id)
        if not sp:
            raise ValueError(f"Template '{source_id}' not found")
        sm = self._load_manifest(sp)
        if sm is None:
            raise ValueError(
                f"Template '{source_id}' has no valid manifest"
            )
        ss = self._load_state(sp)
        return self.create_template(
            name=new_name,
            tier=target_tier,
            description=description or sm.description,
            tags=sm.tags,
            state=ss,
            parent=source_id,
        )

    # ── Deletion ──────────────────────────────────────────────

    def delete_template(self, template_id: str) -> bool:
        path = self.get_path(template_id)
        if not path:
            return False
        shutil.rmtree(path)
        log.info("Template deleted: %s", template_id)
        return True

    # ── Persistence ───────────────────────────────────────────

    def _load_manifest(self, tdir: Path) -> TemplateManifest | None:
        f = tdir / "manifest.json"
        if not f.exists():
            return None
        try:
            return TemplateManifest.from_dict(
                json.loads(f.read_text("utf-8"))
            )
        except (json.JSONDecodeError, KeyError) as exc:
            log.warning("Corrupt manifest %s: %s", tdir, exc)
            return None

    def _write_manifest(self, tdir: Path, m: TemplateManifest) -> None:
        (tdir / "manifest.json").write_text(
            json.dumps(m.to_dict(), indent=2), "utf-8"
        )

    def _load_state(self, tdir: Path) -> dict | None:
        f = tdir / "template.yaml"
        if not f.exists():
            return None
        try:
            import yaml
            return yaml.safe_load(f.read_text("utf-8"))
        except Exception as exc:
            log.warning("State load failed %s: %s", f, exc)
            return None

    def _write_state(self, tdir: Path, state: dict) -> None:
        import yaml
        (tdir / "template.yaml").write_text(
            yaml.dump(state, default_flow_style=False, sort_keys=False),
            "utf-8",
        )

    def _write_cookiecutter_config(
        self, tdir: Path, m: TemplateManifest
    ) -> None:
        (tdir / "cookiecutter.json").write_text(
            json.dumps({
                "template_id": m.id,
                "template_name": m.name,
                "tier": m.tier,
                "version": m.version,
                "description": m.description,
                "_template": m.parent or "",
            }, indent=2),
            "utf-8",
        )

    # ── Cookiecutter Integration ──────────────────────────────

    def has_cookiecutter(self) -> bool:
        return shutil.which("cookiecutter") is not None

    def scaffold_from_template(
        self,
        template_id: str,
        output_dir: str | Path,
        extra_context: dict | None = None,
    ) -> Path | None:
        tp = self.get_path(template_id)
        if not tp:
            log.error("Template not found: %s", template_id)
            return None
        if not self.has_cookiecutter():
            log.warning(
                "Cookiecutter not installed — using copy fallback"
            )
            return self._scaffold_fallback(tp, output_dir)
        try:
            r = subprocess.run(
                ["cookiecutter", "--no-input", str(tp),
                 "-o", str(output_dir)],
                capture_output=True, text=True, timeout=60,
                env=extra_context or {},
            )
            if r.returncode == 0:
                log.info("Scaffolded %s → %s", template_id, output_dir)
                return Path(output_dir)
            log.error("Cookiecutter failed: %s", r.stderr[:200])
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            log.error("Cookiecutter error: %s", exc)
            return None

    def _scaffold_fallback(
        self, tp: Path, output_dir: str | Path
    ) -> Path:
        out = Path(output_dir) / tp.name
        shutil.copytree(tp, out, dirs_exist_ok=True)
        return out

    # ── Summary ──────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        templates = self.list_templates()
        return {
            "directory": str(self._dir),
            "total_templates": len(templates),
            "by_tier": self.count_by_tier(),
            "has_cookiecutter": self.has_cookiecutter(),
            "templates": [t.to_dict() for t in templates],
        }

    @staticmethod
    def _slugify(name: str) -> str:
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
        return slug.strip("-") or "untitled"


# ─── Singleton ──────────────────────────────────────────────

_manager: TemplateManager | None = None


def get_template_manager() -> TemplateManager:
    global _manager
    if _manager is None:
        _manager = TemplateManager()
    return _manager


def reset_template_manager() -> None:
    global _manager
    _manager = None
