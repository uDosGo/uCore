from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
from pathlib import Path

from app.skills.base import BaseSkill

log = logging.getLogger("ucore.skills.registry")
_registry: dict[str, BaseSkill] = {}
_loaded = False
SKILL_PATHS = [
    Path(__file__).parent / "builtin",
    Path.home() / ".ucore/skills",
]

def _discover():
    skills = {}
    for sd in SKILL_PATHS:
        if not sd.exists(): continue
        sys.path.insert(0, str(sd.parent))
        for f in sd.iterdir():
            if f.suffix != ".py" or f.name.startswith("_"): continue
            try:
                spec = importlib.util.spec_from_file_location(f"skills_{f.stem}", f)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    for _, obj in inspect.getmembers(mod):
                        if inspect.isclass(obj) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                            inst = obj(); skills[inst.meta.id] = inst
            except Exception as e:
                log.warning(f"Skill load fail {f.name}: {e}")
        sys.path.pop(0)
    return skills

def _ensure():
    global _registry, _loaded
    if not _loaded: _registry = _discover(); _loaded = True

def list_skills() -> list[dict]:
    _ensure()
    return [{"id": s.meta.id, "name": s.meta.name, "description": s.meta.description,
             "category": s.meta.category, "timeout": s.meta.timeout,
             "requires_confirmation": getattr(s.meta, "requires_confirmation", False),
             "category_priority": _get_category_priority(s.meta.category)} for s in _registry.values()]


def _get_category_priority(category: str) -> int:
    """Return priority for sorting categories in UI."""
    priorities = {
        "system": 1,
        "mutating": 2,
        "destructive": 3,
        "maintenance": 4,
        "surfaces": 5,
        "containers": 6,
        "general": 7,
    }
    return priorities.get(category, 7)

def get_skill(skill_id: str) -> BaseSkill | None:
    _ensure(); return _registry.get(skill_id)

async def run_skill_by_id(skill_id: str, **kwargs) -> dict:
    skill = get_skill(skill_id)
    if not skill: return {"success": False, "error": f"Skill '{skill_id}' not found"}
    errors = skill.validate(**kwargs)
    if errors: return {"success": False, "errors": errors}
    return await skill.run(**kwargs)
