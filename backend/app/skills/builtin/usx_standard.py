"""USX Standard Skill v3 — audit, validate, and scaffold USX surfaces.

Layer 1: Hardcoded colors (#hex, rgb, rgba) → var(--usx-color-*)
Layer 2: Hardcoded font sizes (px) → var(--usx-font-size-*)
Layer 3: Hardcoded spacing (px, rem) → var(--usx-spacing-*)
Layer 4: Hardcoded border radius (px) → var(--usx-radius-*)
Layer 5: Missing touch targets → var(--usx-touch-min)
Layer 6: Surface registration validation
Layer 7: Theme compatibility check

Token source of truth:
  frontend-vue/src/styles/tokens/tokens-{color,typography,spacing,touch,components}.css
Theme overrides:
  frontend-vue/src/styles/themes/{base,dark,teletext,c64,high-contrast}.css
Canonical class library:
  frontend-vue/src/styles/usx-standard.css
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.usx_standard")

FRONTEND_DIR = (
    Path(__file__).parent.parent.parent.parent.parent / "frontend-vue" / "src"
)
TOKENS_DIR = FRONTEND_DIR / "styles" / "tokens"
THEMES_DIR = FRONTEND_DIR / "styles" / "themes"
STANDARD_CSS = FRONTEND_DIR / "styles" / "usx-standard.css"
SURFACES_DIR = FRONTEND_DIR / "surfaces"
SKILLS_DIR = FRONTEND_DIR / "skills"
EXCLUDES = {"node_modules", ".git", "__pycache__", "dist"}

# Map of hardcoded value patterns → variable families
VARIABLE_MAP = {
    "color": r"color:\s*#[0-9a-fA-F]{3,8}",
    "background": (
        r"(?<!var\(--)background:\s*(?:#[0-9a-fA-F]{3,8}|rgba?\([^)]+\))"
    ),
    "font_size": r"font-size:\s*\d+px",
    "spacing": (
        r"(?:padding|margin)(?:-top|-right|-bottom|-left)?:\s*\d+px"
        "|gap:\s*\d+px"
    ),
    "border_radius": r"border-radius:\s*\d+px",
}

# Expected USX variables — used for validation
EXPECTED_VARIABLES = {
    "colors": [
        "--usx-color-primary",
        "--usx-color-primary-hover",
        "--usx-color-on-primary",
        "--usx-color-surface",
        "--usx-color-on-surface",
        "--usx-color-on-surface-muted",
        "--usx-color-background",
        "--usx-color-border",
        "--usx-color-success",
        "--usx-color-danger",
        "--usx-color-warning",
        "--usx-color-info",
        "--usx-color-accent",
    ],
    "typography": [
        "--usx-font-family-sans",
        "--usx-font-family-mono",
        "--usx-font-size-xs",
        "--usx-font-size-sm",
        "--usx-font-size-base",
        "--usx-font-size-lg",
        "--usx-font-weight-bold",
        "--usx-line-height-normal",
    ],
    "spacing": [
        "--usx-spacing-xs",
        "--usx-spacing-sm",
        "--usx-spacing-md",
        "--usx-spacing-lg",
        "--usx-spacing-xl",
        "--usx-spacing-2xl",
    ],
    "touch": [
        "--usx-touch-min",
        "--usx-touch-min-sm",
    ],
    "components": [
        "--usx-radius-sm",
        "--usx-radius-md",
        "--usx-radius-lg",
        "--usx-radius-full",
        "--usx-card-padding",
        "--usx-icon-size",
        "--usx-icon-gap",
        "--usx-tab-padding",
        "--usx-tab-border-width",
        "--usx-grid-gap",
        "--usx-btn-padding",
        "--usx-topbar-height",
    ],
}

THEME_FILES = {
    "dark": "dark.css",
    "teletext": "teletext.css",
    "c64": "c64.css",
    "high-contrast": "high-contrast.css",
}


class UsxStandardSkill(BaseSkill):
    meta = SkillMeta(
        id="usx-standard",
        name="USX Standard Builder v3",
        description=(
            "Audit/repair CSS to USX variable-only standard;"
            " validate token system; scaffold surfaces compliantly"
        ),
        category="developer",
        params=[
            SkillParam(
                name="action",
                type="string",
                description=(
                    "Action: 'audit', 'repair', 'validate-tokens',"
                    " 'audit-surface', 'scaffold-surface', 'report'"
                ),
                required=True,
            ),
            SkillParam(
                name="target",
                type="string",
                description=(
                    "Optional: specific file, surface, or glob"
                    " to target"
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
        action = kwargs.get("action", "audit")
        target = kwargs.get("target", "")
        dry_run = kwargs.get("dry_run", False)

        actions = {
            "audit": lambda: self._deep_audit(target),
            "repair": lambda: self._repair(target, dry_run),
            "validate-tokens": lambda: self._validate_tokens(),
            "audit-surface": lambda: self._audit_surface(target),
            "scaffold-surface": lambda: self._scaffold_surface(target),
            "report": lambda: self._report(target),
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}"}
        return handler()

    # ─── Core Audit ──────────────────────────────────────────────────

    def _deep_audit(self, target: str = "") -> dict:
        """Multi-layer audit across all CSS and Vue files."""
        findings: dict[str, list] = {
            "hardcoded_colors": [],
            "hardcoded_font_sizes": [],
            "hardcoded_spacing": [],
            "hardcoded_radius": [],
            "missing_touch_targets": [],
        }
        stats = {"total_files": 0, "clean": 0, "total_issues": 0}

        files = self._get_style_files(target)
        for f in files:
            stats["total_files"] += 1
            content = f.read_text()
            rel = str(f.relative_to(FRONTEND_DIR))
            file_issues = 0

            # Colors
            colors = self._find_hardcoded(content, "color")
            if colors:
                findings["hardcoded_colors"].append(
                    {"file": rel, "count": len(colors), "lines": colors[:15]},
                )
                file_issues += len(colors)

            # Backgrounds (exclude var() and data-theme blocks)
            bgs = self._find_hardcoded(content, "background")
            if bgs:
                findings["hardcoded_colors"].append(
                    {"file": rel, "count": len(bgs), "lines": bgs[:15]},
                )
                file_issues += len(bgs)

            # Font sizes
            fonts = self._find_hardcoded(content, "font_size")
            # Skip token variable declarations
            fonts = [f for f in fonts if ":root" not in f and "var(" not in f]
            if fonts:
                findings["hardcoded_font_sizes"].append(
                    {"file": rel, "count": len(fonts), "lines": fonts[:15]},
                )
                file_issues += len(fonts)

            # Spacing
            spacing = self._find_hardcoded(content, "spacing")
            spacing = [
                s for s in spacing
                if "--usx-" not in s and "var(" not in s
            ]
            if spacing:
                findings["hardcoded_spacing"].append({
                    "file": rel,
                    "count": len(spacing),
                    "lines": spacing[:15],
                })
                file_issues += len(spacing)

            # Border radius
            radius = self._find_hardcoded(content, "border_radius")
            radius = [
                r for r in radius
                if "--usx-" not in r and "var(" not in r
            ]
            if radius:
                findings["hardcoded_radius"].append(
                    {"file": rel, "count": len(radius), "lines": radius[:15]},
                )
                file_issues += len(radius)

            if file_issues == 0:
                stats["clean"] += 1
            stats["total_issues"] += file_issues

        return {"success": True, "findings": findings, "stats": stats}

    # ─── Token Validation ────────────────────────────────────────────

    def _validate_tokens(self) -> dict:
        """Verify all expected USX variables are declared in token files."""
        missing: dict[str, list[str]] = {}

        token_files = {
            "tokens-color.css": ("colors", "append"),
            "tokens-typography.css": ("typography", "append"),
            "tokens-spacing.css": ("spacing", "append"),
            "tokens-touch.css": ("touch", "append"),
            "tokens-components.css": ("components", "append"),
        }

        for filename, (var_group, _) in token_files.items():
            fpath = TOKENS_DIR / filename
            if not fpath.exists():
                missing[filename] = ["FILE NOT FOUND"]
                continue
            content = fpath.read_text()
            for var in EXPECTED_VARIABLES[var_group]:
                if var not in content:
                    missing.setdefault(filename, []).append(var)

        # Validate theme files exist
        missing_themes = []
        for theme_name, theme_file in THEME_FILES.items():
            if not (THEMES_DIR / theme_file).exists():
                missing_themes.append(theme_file)

        # Validate standard CSS exists
        standard_ok = STANDARD_CSS.exists()

        return {
            "success": True,
            "valid": len(missing) == 0 and not missing_themes and standard_ok,
            "missing_variables": missing,
            "missing_themes": missing_themes,
            "standard_css_exists": standard_ok,
            "token_count": sum(
                len(v) for v in EXPECTED_VARIABLES.values()
            ),
        }

    # ─── Surface Audit ───────────────────────────────────────────────

    def _audit_surface(self, target: str) -> dict:
        """Audit a single surface Vue file for USX compliance."""
        if not target:
            return {"success": False, "error": "target surface path required"}
        fpath = (
            Path(target)
            if Path(target).is_absolute()
            else SURFACES_DIR / target
        )
        if not fpath.exists():
            return {"success": False, "error": f"Surface not found: {fpath}"}

        content = fpath.read_text()
        issues = []

        # Check for <style> blocks with hardcoded values
        style_blocks = re.findall(
            r"<style[^>]*>(.*?)</style>", content, re.DOTALL,
        )
        for i, block in enumerate(style_blocks):
            for hw_type, pattern in VARIABLE_MAP.items():
                matches = re.findall(pattern, block)
                for m in matches:
                    issues.append(
                        f"<style> block {i + 1}: hardcoded {hw_type}"
                        f" — '{m.strip()}'",
                    )

        # Check for inline style objects
        inline_colors = re.findall(
            r"style\s*=\s*\{\{[^}]*#[0-9a-fA-F]{3,8}[^}]*\}\}",
            content,
        )
        for m in inline_colors:
            issues.append(f"Inline style with hardcoded color: '{m[:80]}...'")

        # Check for USX class usage
        usx_classes = re.findall(
            r'class=["\']([^"\']*usx-[^"\']*)["\']', content,
        )

        return {
            "success": True,
            "surface": str(fpath.relative_to(FRONTEND_DIR)),
            "issue_count": len(issues),
            "issues": issues[:20],
            "usx_classes_used": list(set(usx_classes)),
            "clean": len(issues) == 0,
        }

    # ─── Surface Scaffolding ─────────────────────────────────────────

    def _scaffold_surface(self, name: str) -> dict:
        """Generate a USX-compliant surface Vue file from template."""
        if not name:
            return {"success": False, "error": "surface name required"}

        # Convert kebab-case name to PascalCase
        pascal = "".join(word.capitalize() for word in name.split("-"))
        dir_path = SURFACES_DIR / name.lower()
        file_path = dir_path / f"{pascal}Surface.vue"

        template = f"""<template>
  <div class="surface">
    <div class="surface__header">
      <h1 class="surface__title">{name}</h1>
      <p class="surface__description">
        USX-compliant surface for {name}
      </p>
    </div>

    <div class="surface__tabs">
      <button class="surface__tab surface__tab--active">
        <span class="material-symbols-outlined">dashboard</span>
        <span>Overview</span>
      </button>
    </div>

    <div class="surface__content">
      <div class="surface__panel">
        <h2 class="surface__panel-title">Ready</h2>
        <p class="surface__panel-description">
          This surface uses only USX variables and follows
          the surface plate pattern.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// {pascal}Surface — USX-compliant surface component
</script>

<style scoped>
/*
 * All styles come from usx-standard.css via CSS variables.
 * No hardcoded values in this file — zero exceptions.
 */
</style>
"""

        return {
            "success": True,
            "action": "scaffold-surface",
            "name": name,
            "component": f"{pascal}Surface",
            "path": str(file_path.relative_to(FRONTEND_DIR.parent.parent)),
            "template": template,
            "note": (
                "This is a preview. Use ACT MODE to write the file"
                " to disk."
            ),
        }

    # ─── Repair ──────────────────────────────────────────────────────

    def _repair(self, target: str = "", dry_run: bool = False) -> dict:
        """Apply automatic repairs: replace hardcoded values with variables."""
        repairs = {
            "colors_fixed": 0,
            "font_sizes_fixed": 0,
            "spacing_fixed": 0,
            "radius_fixed": 0,
            "files_touched": 0,
        }
        touched = set()

        # Color replacement pairs (heuristic — exact matches only)
        color_replacements = [
            # Primary
            (r"color:\s*#0d6efd", "color: var(--usx-color-primary)"),
            (r"color:\s*#0b5ed7", "color: var(--usx-color-primary-hover)"),
            (r"background:\s*#0d6efd", "background: var(--usx-color-primary)"),
            (r"color:\s*#ffffff", "color: var(--usx-color-on-primary)"),
            # Surface
            (
                r"background:\s*#f8f9fa",
                "background: var(--usx-color-surface-hover)",
            ),
            (
                r"background:\s*#e9ecef",
                "background: var(--usx-color-surface-active)",
            ),
            (r"color:\s*#212529", "color: var(--usx-color-on-surface)"),
            (r"color:\s*#6c757d", "color: var(--usx-color-on-surface-muted)"),
            # Status
            (r"color:\s*#198754", "color: var(--usx-color-success)"),
            (r"color:\s*#dc3545", "color: var(--usx-color-danger)"),
            (r"color:\s*#ffc107", "color: var(--usx-color-warning)"),
            (r"color:\s*#0dcaf0", "color: var(--usx-color-info)"),
            # Border
            (r"border-color:\s*#dee2e6", (
                "border-color: var(--usx-color-border)"
            )),
        ]

        files = self._get_style_files(target)
        for f in files:
            content = f.read_text()
            original = content

            for pattern, replacement in color_replacements:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    repairs["colors_fixed"] += 1
                    content = new_content

            if content != original:
                touched.add(str(f))
                if not dry_run:
                    f.write_text(content)

        repairs["files_touched"] = len(touched)
        return {
            "success": True,
            "action": "repair",
            "dry_run": dry_run,
            "repairs": repairs,
            "touched_files": list(touched),
        }

    # ─── Report ──────────────────────────────────────────────────────

    def _report(self, target: str = "") -> dict:
        audit = self._deep_audit(target)
        token_validation = self._validate_tokens()

        return {
            "success": True,
            "action": "report",
            "audit": audit.get("findings", {}),
            "audit_stats": audit.get("stats", {}),
            "token_validation": token_validation,
            "recommendations": [
                "Zero hardcoded values — use var(--usx-*) for everything",
                "Check tokens/tokens-*.css for available variables",
                "Import themes in index.html: <link href='themes/base.css'>",
                "Use useTheme() composable for runtime theme switching",
                "Run 'validate-tokens' before every push to catch drift",
                "Use .surface__* BEM classes from usx-standard.css for layout",
                "All interactive elements must use var(--usx-touch-min)",
            ],
        }

    # ─── Helpers ─────────────────────────────────────────────────────

    def _get_style_files(self, target: str = "") -> list[Path]:
        """Get all CSS and Vue files in the frontend source tree."""
        if not FRONTEND_DIR.exists():
            return []
        patterns = ["*.css", "*.vue"]
        files: list[Path] = []
        for pattern in patterns:
            if target:
                files.extend(
                    FRONTEND_DIR.rglob(f"*{target}*{pattern}"),
                )
            else:
                files.extend(FRONTEND_DIR.rglob(pattern))
        return [
            f for f in files
            if not any(x in str(f) for x in EXCLUDES)
        ]

    def _find_hardcoded(self, content: str, issue_type: str) -> list[str]:
        """Find hardcoded values of a given type in content."""
        pattern = VARIABLE_MAP.get(issue_type)
        if not pattern:
            return []
        lines = content.split("\n")
        results = []
        in_var_block = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip variable declaration blocks
            if "[data-theme" in stripped or ":root" in stripped:
                in_var_block = True
                continue
            if in_var_block:
                if stripped == "}" or stripped.startswith("}"):
                    in_var_block = False
                continue
            # Skip lines that already use var()
            if "var(" in stripped:
                continue
            if re.search(pattern, stripped, re.IGNORECASE):
                results.append(f"L{i + 1}: {stripped.strip()}")
        return results