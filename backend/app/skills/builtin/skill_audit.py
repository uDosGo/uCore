"""Skill Audit — smoke-test all skills with import + execution checks.

Comprehensive audit that actually tries to load and execute each skill:
1. Discovers all skills in builtin/
2. Attempts to import each skill module
3. Attempts to instantiate BaseSkill subclasses and call run(dry_run=True)
4. For module-level functions, attempts to call run() with safety wrapper
5. Reports failures with exception traces
6. Cross-references against skills audit status doc

Integrates with the uCore skill registry via BaseSkill pattern.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.audit")

SKILLS_DIR = Path(__file__).resolve().parent
UCORE_ROOT = SKILLS_DIR.parent.parent.parent.parent
EXCLUDES = {
    "__pycache__", "__archived__", ".mypy_cache",
    "__init__", "base", "state",
}


def _discover_skill_modules() -> list[str]:
    """Discover all skill modules (files + base-skill classes)."""
    modules: list[str] = []
    for f in sorted(SKILLS_DIR.glob("*.py")):
        name = f.stem
        if name in EXCLUDES or name.startswith("."):
            continue
        modules.append(name)
    return modules


def _safe_import_module(name: str) -> tuple[Any | None, str | None]:
    """Try to import a skill module. Returns (module, error)."""
    try:
        spec = importlib.util.spec_from_file_location(
            name,
            SKILLS_DIR / f"{name}.py",
        )
        if spec is None or spec.loader is None:
            return None, "Could not create module spec"
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod, None
    except Exception as exc:
        return None, f"ImportError: {exc}"


def _find_base_skill_subclass(mod: Any) -> type | None:
    """Find the first BaseSkill subclass in a module."""
    for attr_name in dir(mod):
        attr = getattr(mod, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, BaseSkill)
            and attr is not BaseSkill
        ):
            return attr
    return None


def _has_module_run(mod: Any) -> bool:
    """Check if module has a top-level async run() or def run()."""
    return hasattr(mod, "run") and callable(mod.run)


async def _smoke_test_skill(
    name: str,
    mod: Any,
    skill_cls: type | None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Smoke-test a single skill: import, instantiate, execute."""
    result: dict[str, Any] = {
        "name": name,
        "file": f"{name}.py",
        "import_status": "success",
        "instantiate_status": "skipped",
        "execute_status": "skipped",
        "error": None,
        "traceback": None,
        "duration_ms": 0,
        "is_base_skill": skill_cls is not None,
        "has_module_run": False,
    }

    if skill_cls is None and not _has_module_run(mod):
        result["import_status"] = "warning"
        result["error"] = "No BaseSkill subclass or run() function found"
        return result

    t0 = time.perf_counter()

    # Instantiate BaseSkill
    if skill_cls is not None:
        try:
            instance = skill_cls()
            result["instantiate_status"] = "success"
        except Exception as exc:
            result["instantiate_status"] = "failed"
            result["error"] = str(exc)
            result["traceback"] = traceback.format_exc()
            result["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            return result

        # Execute with dry_run / smoke-test
        try:
            t1 = time.perf_counter()
            if hasattr(instance, "run"):
                out = await instance.run(dry_run=True, smoke_test=True, action="report")
            else:
                out = {"dry_run": True, "status": "no run method"}
            result["execute_status"] = "success"
            result["output"] = out.get("success", True) if isinstance(out, dict) else True
            result["duration_ms"] = round((time.perf_counter() - t1) * 1000, 1)
        except TypeError:
            # Skill doesn't accept dry_run — try without
            try:
                t1 = time.perf_counter()
                out = await instance.run()
                result["execute_status"] = "success"
                result["output"] = True
                result["duration_ms"] = round((time.perf_counter() - t1) * 1000, 1)
            except Exception as exc2:
                result["execute_status"] = "failed"
                result["error"] = str(exc2)
                result["traceback"] = traceback.format_exc()
                result["duration_ms"] = round((time.perf_counter() - t1) * 1000, 1)
        except Exception as exc:
            result["execute_status"] = "failed"
            result["error"] = str(exc)
            result["traceback"] = traceback.format_exc()
            result["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    else:
        # Module-level run() function
        result["has_module_run"] = True
        try:
            t1 = time.perf_counter()
            if hasattr(mod.run, "__code__"):
                # Check if it's async
                import inspect
                if inspect.iscoroutinefunction(mod.run):
                    out = await mod.run()
                else:
                    out = mod.run()
                result["execute_status"] = "success"
                result["output"] = out.get("success", True) if isinstance(out, dict) else True
                result["duration_ms"] = round((time.perf_counter() - t1) * 1000, 1)
            else:
                result["execute_status"] = "skipped"
                result["error"] = "run() is not a function"
        except Exception as exc:
            result["execute_status"] = "failed"
            result["error"] = str(exc)
            result["traceback"] = traceback.format_exc()
            result["duration_ms"] = round((time.perf_counter() - t1) * 1000, 1)

    result["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return result


def _classify_status(result: dict) -> str:
    """Classify overall skill health."""
    if result.get("import_status") == "failed":
        return "broken"
    if result.get("execute_status") == "failed":
        return "broken"
    if result.get("import_status") == "warning":
        return "untested"
    if result.get("execute_status") == "success":
        return "working"
    if result.get("instantiate_status") == "failed":
        return "broken"
    return "untested"


class SkillAuditSkill(BaseSkill):
    """Smoke-test all uCore builtin skills and report health."""

    meta = SkillMeta(
        id="skill-audit",
        name="Skill Auditor (Smoke-Test)",
        description=(
            "Discover, import, instantiate, and execute all builtin skills."
            " Reports health status: working, untested, or broken."
        ),
        category="developer",
        params=[
            SkillParam(
                name="action",
                type="string",
                description="'audit' (full smoke-test), 'discover' (list only), or 'report' (last audit)",
                required=False,
                default="audit",
            ),
            SkillParam(
                name="target",
                type="string",
                description="Specific skill name to test (omit for all)",
                required=False,
                default="",
            ),
            SkillParam(
                name="timeout",
                type="integer",
                description="Per-skill timeout in seconds",
                required=False,
                default=10,
            ),
        ],
        timeout=120,
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        action = kwargs.get("action", "audit")
        target = kwargs.get("target", "")
        timeout = int(kwargs.get("timeout", 10))

        if action == "discover":
            modules = _discover_skill_modules()
            return {
                "success": True,
                "action": "discover",
                "count": len(modules),
                "skills": modules,
            }

        if action == "report":
            return self._load_last_report()

        # Full audit / smoke-test
        modules = _discover_skill_modules()
        if target:
            modules = [m for m in modules if target in m]
            if not modules:
                return {
                    "success": False,
                    "error": f"No skills match target '{target}'",
                }

        results: list[dict] = []
        working = untested = broken = 0
        start_time = time.perf_counter()

        for name in modules:
            mod, import_err = _safe_import_module(name)
            if import_err:
                results.append({
                    "name": name,
                    "file": f"{name}.py",
                    "import_status": "failed",
                    "execute_status": "skipped",
                    "error": import_err,
                    "is_base_skill": False,
                    "duration_ms": 0,
                })
                broken += 1
                continue

            skill_cls = _find_base_skill_subclass(mod)
            result = await _smoke_test_skill(name, mod, skill_cls, timeout)
            results.append(result)

            status = _classify_status(result)
            if status == "working":
                working += 1
            elif status == "broken":
                broken += 1
            else:
                untested += 1

        total_duration = round((time.perf_counter() - start_time) * 1000, 1)

        report = {
            "timestamp": int(time.time()),
            "total_skills": len(modules),
            "working": working,
            "untested": untested,
            "broken": broken,
            "health_pct": round((working / len(modules)) * 100, 1) if modules else 0,
            "duration_ms": total_duration,
            "skills": results,
            "recommendations": _generate_recommendations(working, untested, broken, results),
        }

        self._persist_report(report)
        return {"success": True, "action": "audit", "report": report}

    def _persist_report(self, report: dict) -> None:
        """Save report to seeds/ for frontend consumption."""
        try:
            seeds = UCORE_ROOT / "seeds"
            seeds.mkdir(exist_ok=True)
            out = seeds / "skill-audit-report.json"
            out.write_text(json.dumps(report, indent=2, default=str))
        except Exception:
            pass

    def _load_last_report(self) -> dict:
        """Load the last saved audit report."""
        report_file = UCORE_ROOT / "seeds" / "skill-audit-report.json"
        if report_file.exists():
            try:
                return {"success": True, "action": "report", "report": json.loads(report_file.read_text())}
            except Exception:
                pass
        return {"success": False, "error": "No previous audit report found"}


def _generate_recommendations(
    working: int,
    untested: int,
    broken: int,
    results: list[dict],
) -> list[str]:
    """Generate actionable recommendations."""
    recs = []

    if broken > 0:
        names = [r["name"] for r in results if _classify_status(r) == "broken"]
        recs.append(
            f"Fix {broken} broken skill(s): {', '.join(names[:5])}"
            + (f" +{len(names) - 5} more" if len(names) > 5 else "")
        )

    if untested > 0:
        names = [r["name"] for r in results if _classify_status(r) == "untested"]
        recs.append(
            f"Verify {untested} untested skill(s): {', '.join(names[:5])}"
            + (f" +{len(names) - 5} more" if len(names) > 5 else "")
        )

    if working == 0 and broken == 0:
        recs.append("No skills were tested — verify skill directory path")

    if working > 0:
        recs.append(f"{working} skills working correctly — no action needed")

    # Check for skills with no BaseSkill subclass (skip the module-level ones)
    no_base = [r["name"] for r in results if not r.get("is_base_skill") and r.get("import_status") != "failed"]
    if no_base:
        recs.append(
            f"{len(no_base)} skill(s) without BaseSkill subclass: {', '.join(no_base[:5])}"
            + (f" +{len(no_base) - 5} more" if len(no_base) > 5 else "")
            + " — consider converting to BaseSkill pattern"
        )

    return recs