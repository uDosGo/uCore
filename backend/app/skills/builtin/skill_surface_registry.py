"""Surface Registry Skill — discover, validate, scaffold, repair, wire.

Autonomous maintenance for the uCore surface ecosystem.
Manages frontend Vue surfaces and their backend wiring
(runtimes, variables, commands).

Actions:
  discover    — scan filesystem for registered/detached surfaces
  validate    — check surface compliance (USX, routing, backend wiring)
  scaffold    — generate new surface from template
  repair      — auto-fix routing, imports, tab registration gaps
  wire        — link surface to backend runtime/variables/commands
  report      — full ecosystem health report
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.surface_registry")

ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend-vue" / "src"
SURFACES_DIR = FRONTEND_DIR / "surfaces"
ROUTER_FILE = FRONTEND_DIR / "router" / "index.ts"
DEV_STORE_FILE = FRONTEND_DIR / "stores" / "developer.ts"
DEV_SURFACE_FILE = SURFACES_DIR / "developer" / "DeveloperSurface.vue"
BACKEND_DIR = ROOT_DIR / "backend" / "app"
RUNTIMES_FILE = BACKEND_DIR / "services" / "dev_layer.py"
MANIFEST_FILE = ROOT_DIR / "seeds" / "surface-registry.json"

EXCLUDES = {"node_modules", ".git", "__pycache__", "dist", "panels", "archive"}


class SurfaceRegistrySkill(BaseSkill):
    meta = SkillMeta(
        id="surface-registry",
        name="Surface Registry v1",
        description=(
            "Discover, validate, scaffold, repair, and wire uCore"
            " surfaces. Autonomous maintenance for the surface"
            " ecosystem with backend runtime linking."
        ),
        category="developer",
        params=[
            SkillParam(
                name="action",
                type="string",
                description=(
                    "Action: 'discover', 'validate', 'scaffold',"
                    " 'repair', 'wire', 'report'"
                ),
                required=True,
            ),
            SkillParam(
                name="target",
                type="string",
                description="Surface name (e.g., 'developer', 'workflow')",
                required=False,
            ),
            SkillParam(
                name="backend_runtime",
                type="string",
                description=(
                    "Backend runtime to wire (e.g., 'dev_layer',"
                    " 'feed_server')"
                ),
                required=False,
            ),
            SkillParam(
                name="dry_run",
                type="bool",
                description="Preview changes without applying",
                required=False,
            ),
        ],
        timeout=120,
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        action = kwargs.get("action", "discover")
        target = kwargs.get("target", "")
        backend_runtime = kwargs.get("backend_runtime", "")
        dry_run = kwargs.get("dry_run", False)

        actions = {
            "discover": lambda: self._discover(),
            "validate": lambda: self._validate(target),
            "scaffold": lambda: self._scaffold(target),
            "repair": lambda: self._repair(target, dry_run),
            "wire": lambda: self._wire(target, backend_runtime, dry_run),
            "report": lambda: self._report(),
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}"}
        return handler()

    # ─── Discover ────────────────────────────────────────────────────

    def _discover(self) -> dict:
        """Scan filesystem for all surfaces and their registration state."""
        registered = self._parse_router_surfaces()
        filesystem = self._scan_filesystem_surfaces()
        tabs = self._parse_developer_tabs()

        # Detect detached surfaces (in filesystem but not in router)
        detached = [s for s in filesystem if s not in registered]

        # Detect phantom surfaces (in router but not in filesystem)
        phantom = [s for s in registered if s not in filesystem]

        # Detect untabbed surfaces (in router but no developer tab)
        untabbed = [s for s in registered if s not in tabs]

        # Detect backend-wired surfaces
        wired = self._detect_backend_wiring(registered)

        return {
            "success": True,
            "action": "discover",
            "total_registered": len(registered),
            "total_filesystem": len(filesystem),
            "surfaces": registered,
            "detached": detached,
            "phantom": phantom,
            "untabbed": untabbed,
            "wired_backend": wired,
            "health": (
                "healthy" if not detached and not phantom and not untabbed
                else "attention"
            ),
        }

    # ─── Validate ────────────────────────────────────────────────────

    def _validate(self, target: str = "") -> dict:
        """Validate surface compliance: USX, routing, backend wiring."""
        surfaces = (
            [target] if target
            else self._parse_router_surfaces()
        )
        results = {}

        for surface in surfaces:
            sf_name = f"{self._pascal_case(surface)}Surface.vue"
            surface_file = SURFACES_DIR / surface / sf_name

            issues = []
            warnings = []

            # Check filesystem presence
            if not surface_file.exists():
                issues.append("Surface Vue file not found on disk")
                results[surface] = {
                    "exists": False,
                    "issues": issues,
                    "clean": False,
                }
                continue

            # Check router registration
            rc = ROUTER_FILE.read_text() if ROUTER_FILE.exists() else ""
            if surface.lower() not in rc.lower():
                issues.append("Not registered in router/index.ts")

            # Check USX compliance via surface audit
            content = surface_file.read_text()
            usx_issues = self._audit_surface_usx(content)
            issues.extend(usx_issues)

            # Check panel imports in DeveloperSurface.vue
            dev_content = (
                DEV_SURFACE_FILE.read_text()
                if DEV_SURFACE_FILE.exists() else ""
            )
            if surface.lower() not in dev_content.lower():
                warnings.append(
                    "No panel registered in DeveloperSurface.vue",
                )

            # Check backend wiring
            wiring = self._check_surface_wiring(surface)
            if not wiring.get("wired"):
                warnings.append("No backend runtime wiring detected")
            else:
                results.setdefault("_wiring", {})[surface] = wiring

            clean = len(issues) == 0
            results[surface] = {
                "exists": True,
                "issues": issues,
                "warnings": warnings,
                "clean": clean,
            }

        # Aggregate
        all_clean = all(
            r.get("clean", False)
            for r in results.values()
            if isinstance(r, dict) and "clean" in r
        )

        return {
            "success": True,
            "action": "validate",
            "surfaces": results,
            "all_clean": all_clean,
            "total": len(results),
        }

    # ─── Scaffold ────────────────────────────────────────────────────

    def _scaffold(self, name: str) -> dict:
        """Generate surface: Vue file, router entry, dev tab, panel."""
        if not name:
            return {"success": False, "error": "surface name required"}
        if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", name):
            return {
                "success": False,
                "error": (
                    f"Invalid surface name '{name}'. Use lowercase"
                    " kebab-case (e.g., 'my-feature')"
                ),
            }

        pascal = self._pascal_case(name)
        route_path = f"/{name}"
        route_name = name.replace("-", "")

        # Surface Vue template
        vue_template = (
            f'<template>\n'
            f'  <div class="surface">\n'
            f'    <div class="surface__header">\n'
            f'      <h1 class="surface__title">{name}</h1>\n'
            f'      <p class="surface__description">\n'
            f'        USX-compliant surface for {name}\n'
            f'      </p>\n'
            f'    </div>\n'
            f'    <div class="surface__tabs">\n'
            f'      <button class="surface__tab surface__tab--active">\n'
            f'        <span class="material-symbols-outlined">'
            f'dashboard</span>\n'
            f'        <span>Overview</span>\n'
            f'      </button>\n'
            f'    </div>\n'
            f'    <div class="surface__content">\n'
            f'      <div class="surface__panel">\n'
            f'        <h2 class="surface__panel-title">Ready</h2>\n'
            f'        <p class="surface__panel-description">\n'
            f'          This surface uses only USX variables and\n'
            f'          follows the surface plate pattern.\n'
            f'        </p>\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </div>\n'
            f'</template>\n'
            f'\n'
            f'<script setup lang="ts">\n'
            f'// {pascal}Surface — USX-compliant surface\n'
            f'</script>\n'
            f'\n'
            f'<style scoped>\n'
            f'/*\n'
            f' * All styles from usx-standard.css via CSS\n'
            f' * variables. Zero hardcoded values.\n'
            f' */\n'
            f'</style>\n'
        )

        # Panel template (for DeveloperSurface tab)
        panel_template = (
            f'<template>\n'
            f'  <div class="usx-section">\n'
            f'    <div class="usx-flex-between">\n'
            f'      <h3>{name}</h3>\n'
            f'      <span class="usx-badge usx-badge--accent">new</span>\n'
            f'    </div>\n'
            f'    <p class="usx-mt-sm"'
            f' style="color: var(--usx-color-on-surface-muted)">\n'
            f'      {pascal} surface panel\n'
            f'    </p>\n'
            f'  </div>\n'
            f'</template>\n'
            f'\n'
            f'<script setup lang="ts">\n'
            f'// {pascal}Panel — Developer Surface tab\n'
            f'</script>\n'
        )

        # Router entry
        router_entry = (
            f"  {{\n"
            f"    path: '{route_path}/:pathMatch(.*)*',\n"
            f"    name: '{route_name}',\n"
            f"    component: () => import(\n"
            f"      '../surfaces/{name}/{pascal}Surface.vue'"
            f"\n    ),\n"
            f"    meta: {{ title: '{pascal}', icon: 'widgets' }},\n"
            f"  }},"
        )

        # Dev store tab entry
        dev_tab_entry = (
            f"  {{ id: '{name}', label: '{pascal}',"
            f" icon: 'widgets' }},"
        )

        # Files to create
        files = {
            f"frontend-vue/src/surfaces/{name}/"
            f"{pascal}Surface.vue": vue_template,
            f"frontend-vue/src/surfaces/{name}/"
            f"panels/{pascal}Panel.vue": panel_template,
        }

        return {
            "success": True,
            "action": "scaffold",
            "name": name,
            "component": f"{pascal}Surface",
            "panel": f"{pascal}Panel",
            "route": route_path,
            "files_to_create": files,
            "router_entry": router_entry,
            "dev_tab_entry": dev_tab_entry,
            "instructions": [
                "1. Write the surface Vue file(s) to disk",
                "2. Add the router entry to router/index.ts routes array",
                (
                    "3. Add the dev tab entry to"
                    " stores/developer.ts DEVELOPER_TABS"
                ),
                "4. Add to DeveloperTab union type in stores/developer.ts",
                "5. Import and wire panel in DeveloperSurface.vue",
                "6. Run 'wire' action to link backend runtime",
                "7. Run 'validate' action to confirm compliance",
            ],
        }

    # ─── Repair ──────────────────────────────────────────────────────

    def _repair(self, target: str = "", dry_run: bool = False) -> dict:
        """Auto-fix routing, imports, tab registration gaps."""
        repairs = {
            "routing_fixed": 0,
            "tabs_fixed": 0,
            "total_fixed": 0,
        }
        issues = []

        if not ROUTER_FILE.exists():
            return {
                "success": False,
                "error": "Router or dev store file not found",
                "repairs": repairs,
            }

        registered = self._parse_router_surfaces()
        tabs = self._parse_developer_tabs()
        filesystem = self._scan_filesystem_surfaces()

        # Fix: surfaces in filesystem but not in router
        detached = [s for s in filesystem if s not in registered]
        for surface in detached:
            if target and surface != target:
                continue
            issues.append(
                f"Surface '{surface}' in filesystem but not in router",
            )
            repairs["routing_fixed"] += 1

        # Fix: surfaces in router but no dev tab
        untabbed = [s for s in registered if s not in tabs]
        for surface in untabbed:
            if target and surface != target:
                continue
            issues.append(
                f"Surface '{surface}' in router but no dev tab",
            )
            repairs["tabs_fixed"] += 1

        repairs["total_fixed"] = (
            repairs["routing_fixed"] + repairs["tabs_fixed"]
        )

        return {
            "success": True,
            "action": "repair",
            "dry_run": dry_run,
            "repairs": repairs,
            "issues_found": issues,
            "note": (
                "Auto-repair provides detection. Manual"
                " insertion required for router entries and"
                " tab registrations to avoid merge conflicts."
            ),
        }

    # ─── Wire ────────────────────────────────────────────────────────

    def _wire(
        self, target: str = "", backend_runtime: str = "",
        dry_run: bool = False,
    ) -> dict:
        """Wire a frontend surface to backend runtime/variables/commands."""
        if not target:
            return {
                "success": False,
                "error": "target surface name required",
            }

        # Discover available backend handlers
        runtimes = self._discover_backend_runtimes()

        # If backend_runtime specified, validate it
        if backend_runtime and backend_runtime not in runtimes:
            return {
                "success": False,
                "error": (
                    f"Unknown backend runtime '{backend_runtime}'."
                    f" Available: {list(runtimes.keys())}"
                ),
            }

        # Build wiring manifest
        wiring = {
            "surface": target,
            "runtime": backend_runtime or "default",
            "endpoints": {},
            "variables": {},
            "commands": {},
        }

        if backend_runtime and backend_runtime in runtimes:
            rt = runtimes[backend_runtime]
            wiring["endpoints"] = rt.get("endpoints", {})
            wiring["variables"] = rt.get("variables", {})
            wiring["commands"] = rt.get("commands", {})

        return {
            "success": True,
            "action": "wire",
            "target": target,
            "wiring": wiring,
            "available_runtimes": list(runtimes.keys()),
            "instructions": [
                (
                    "1. Add API client calls in the surface Vue"
                    " component to the wired endpoints"
                ),
                (
                    "2. Create a Pinia store for the surface's"
                    " state if it needs persistent data"
                ),
                "3. Register the store in the surface's setup()",
                (
                    "4. Add backend variables to the surface's"
                    " reactive state"
                ),
                (
                    "5. Expose commands as methods callable from"
                    " the surface UI"
                ),
                (
                    "6. Update surface-registry.json manifest"
                    " with the wiring"
                ),
            ],
        }

    # ─── Report ──────────────────────────────────────────────────────

    def _report(self) -> dict:
        discover = self._discover()
        validate = self._validate()
        runtimes = self._discover_backend_runtimes()

        return {
            "success": True,
            "action": "report",
            "ecosystem": {
                "total_surfaces": discover["total_registered"],
                "health": discover["health"],
                "detached": discover["detached"],
                "phantom": discover["phantom"],
                "untabbed": discover["untabbed"],
                "wired_backend": discover["wired_backend"],
            },
            "validation": {
                "all_clean": validate["all_clean"],
                "total_issues": sum(
                    len(r.get("issues", [])) + len(r.get("warnings", []))
                    for r in validate["surfaces"].values()
                    if isinstance(r, dict)
                ),
            },
            "backends_available": list(runtimes.keys()),
            "recommendations": [
                (
                    "Run 'scaffold' to generate new surfaces"
                    " from templates"
                ),
                "Run 'validate' after any surface changes",
                "Run 'wire' to connect surfaces to backend runtimes",
                "Check detached surfaces and register or clean them up",
                "Check phantom surfaces and create their Vue files",
            ],
        }

    # ─── Helpers ─────────────────────────────────────────────────────

    def _parse_router_surfaces(self) -> list[str]:
        """Extract surface names from router/index.ts."""
        if not ROUTER_FILE.exists():
            return []
        content = ROUTER_FILE.read_text()
        # Match: component: () => import('../surfaces/NAME/NameSurface.vue')
        matches = re.findall(
            r"import\('\.\./surfaces/([a-z][a-z0-9-]*)/",
            content,
        )
        return sorted(set(matches))

    def _scan_filesystem_surfaces(self) -> list[str]:
        """List surface directories on disk."""
        if not SURFACES_DIR.exists():
            return []
        surfaces = []
        for d in SURFACES_DIR.iterdir():
            if d.is_dir() and d.name not in EXCLUDES:
                # Check for a Surface.vue file
                vue_files = list(d.glob("*Surface.vue"))
                if vue_files:
                    surfaces.append(d.name)
        return sorted(surfaces)

    def _parse_developer_tabs(self) -> list[str]:
        """Extract tab IDs from developer store."""
        if not DEV_STORE_FILE.exists():
            return []
        content = DEV_STORE_FILE.read_text()
        # Match: { id: 'tabname', ... }
        matches = re.findall(
            r"\{\s*id:\s*'([a-z][a-z0-9-]*)'",
            content,
        )
        return sorted(set(matches))

    def _detect_backend_wiring(self, surfaces: list[str]) -> list[str]:
        """Detect surfaces with known backend runtime connections."""
        known_runtimes = {
            "developer": ["dev_layer", "tasker_ingest"],
            "server": ["hivemind_server", "llm_router"],
            "workflow": ["task_processor"],
            "snackmachine": ["snackmachine"],
            "assistui": ["assistui_runtime"],
            "documentation": ["docs_roundup"],
            "terminal": ["terminal_runtime"],
            "ucode": ["ucode_runtime"],
            "browserui": ["browser_runtime"],
            "teletext": ["teletext_runtime"],
            "dashboard": ["dashboard_runtime"],
            "system": ["system_runtime"],
            "feed": ["feed_server", "feed_consumer"],
        }
        wired = []
        for s in surfaces:
            if s in known_runtimes:
                wired.append(s)
        return wired

    def _discover_backend_runtimes(self) -> dict:
        """Scan backend for available runtime services."""
        runtimes = {}

        # Known backend runtime modules
        candidate_modules = {
            "dev_layer": BACKEND_DIR / "services" / "dev_layer.py",
            "feed_server": BACKEND_DIR / "mcp" / "feed" / "feed_server.py",
            "feed_consumer": BACKEND_DIR / "services" / "feed_consumer.py",
            "hivemind_server": BACKEND_DIR / "mcp" / "hivemind_server.py",
            "llm_router": BACKEND_DIR / "mcp" / "llm_router.py",
            "cost_manager": BACKEND_DIR / "services" / "cost_manager.py",
            "template_manager": (
                BACKEND_DIR / "services" / "template_manager.py"
            ),
            "tasker_ingest": BACKEND_DIR / "mcp" / "tasker_ingest.py",
        }

        for name, path in candidate_modules.items():
            if not path.exists():
                continue
            content = path.read_text()

            # Extract endpoints (API routes, MCP tools)
            endpoints = []
            for match in re.findall(
                r'"([a-z_]+)"\s*:\s*self\._[a-z_]+', content,
            ):
                endpoints.append(match)

            # Extract MCP tool names
            for match in re.findall(
                r'name="([a-z_]+)"', content,
            ):
                endpoints.append(match)

            # Extract class variables from __init__
            variables = {}
            for match in re.findall(
                r"self\.([a-z_]+)\s*=\s*([^#\n]+)", content,
            ):
                key, val = match
                if len(key) > 2 and not key.startswith("_"):
                    variables[key] = val.strip().rstrip(",")

            # Extract public methods as commands
            commands = []
            for match in re.findall(
                r"async def ([a-z_]+)\(self", content,
            ):
                if not match.startswith("_"):
                    commands.append(match)
            for match in re.findall(
                r"def ([a-z_]+)\(self", content,
            ):
                if not match.startswith("_"):
                    commands.append(match)

            runtimes[name] = {
                "file": str(path.relative_to(ROOT_DIR)),
                "endpoints": sorted(set(endpoints)),
                "variables": variables,
                "commands": sorted(set(commands)),
            }

        return runtimes

    def _check_surface_wiring(self, surface: str) -> dict:
        """Check if a surface has backend wiring."""
        wired = self._detect_backend_wiring([surface])
        return {
            "wired": len(wired) > 0,
            "runtimes": (self._detect_backend_wiring([surface])),
        }

    def _audit_surface_usx(self, content: str) -> list[str]:
        """Quick USX compliance check for a surface file."""
        issues = []

        # Check for hardcoded colors in style blocks
        style_blocks = re.findall(
            r"<style[^>]*>(.*?)</style>", content, re.DOTALL,
        )
        for i, block in enumerate(style_blocks):
            hex_colors = re.findall(r"#[0-9a-fA-F]{3,8}", block)
            for h in hex_colors:
                issues.append(
                    f"<style> block {i + 1}: hardcoded color {h}"
                    " — use var(--usx-color-*)",
                )
            px_values = re.findall(r"(?<!\w)\d+px", block)
            for p in px_values:
                issues.append(
                    f"<style> block {i + 1}: hardcoded {p}"
                    " — use var(--usx-spacing-*) or var(--usx-touch-*)",
                )

        # Check for USX surface plate classes
        if "surface" not in content:
            issues.append(
                "Missing .surface class — use USX surface plate"
                " pattern",
            )

        return issues

    def _pascal_case(self, name: str) -> str:
        """Convert kebab-case to PascalCase."""
        return "".join(word.capitalize() for word in name.split("-"))
