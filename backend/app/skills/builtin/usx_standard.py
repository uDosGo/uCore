"""USX Standard Skill v2 — audit, detect overrides, and repair surfaces.

Layer 1: Hardcoded colors → CSS variables
Layer 2: Hardcoded font sizes → Pico variables
Layer 3: Competing icon sizing rules → delegate to usx-icons.css
Layer 4: Duplicate USX base class definitions → remove from surface CSS
Layer 5: Duplicate surface layout classes → use USX equivalents
Layer 6: TSX inline style audit
"""
from __future__ import annotations
import logging
import re
from pathlib import Path
from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.usx_standard")

USX_STANDARD_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "frontend"
    / "src"
    / "styles"
)
USX_SURFACES_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "frontend"
    / "src"
    / "surfaces"
)
USX_EXCLUDES = {"node_modules", ".git", "__pycache__"}

# Canonical USX files — the only source of truth for these classes
CANONICAL_FILES = {
    "usx-base.css": [
        ".usx-surface-body",
        ".usx-surface-main",
        ".usx-header-btn",
        ".hub-status-badge",
        ".content-grid",
    ],
    "usx-typography.css": [".prose"],
    "usx-icons.css": [".material-symbols-outlined"],
}

# Surface-specific layout classes that should use USX equivalents
SURFACE_LAYOUT_MAP = {
    ".developer-surface-body": ".usx-surface-body",
    ".developer-surface-main": ".usx-surface-main",
    ".workflow-surface-main": ".usx-surface-main",
    ".ucode-main": ".usx-surface-main",
    ".assistui-surface": ".usx-surface-layout",
    # GridCore specific layout classes
    ".gridcore-settings-panel": ".system-panel",
    #   Example: Map GridCore panel to System panel
    # System specific layout classes
    ".system-panel": ".system-panel",
    #   Already System, no change needed — explicit mapping
}


class UsxStandardSkill(BaseSkill):
    meta = SkillMeta(
        id="usx-standard",
        name="USX Standard Builder v2",
        description=(
            "Audit CSS for overrides/duplicates, repair to USX"
            " canonical standard"
        ),
        category="developer",
        params=[
            SkillParam(
                name="action",
                type="string",
                description=(
                    "Action: 'audit', 'repair', 'consolidate',"
                    " 'report'"
                ),
                required=True,
            ),
            SkillParam(
                name="target",
                type="string",
                description=("Optional: specific file or surface to target"),
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

        if action == "audit":
            return self._deep_audit(target)
        elif action == "repair":
            return self._repair(target, dry_run)
        elif action == "consolidate":
            return {
                "success": True,
                "action": "consolidate",
                "message": "Extract shared patterns into usx-base.css",
            }
        elif action == "report":
            audit = self._deep_audit(target)
            return {
                "success": True,
                "action": "report",
                "report": audit,
                "recommendations": self._recommendations(audit),
            }
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def _deep_audit(self, target: str = "") -> dict:
        """Multi-layer CSS audit."""
        findings: dict[str, list] = {
            "colors": [],
            "font_sizes": [],
            "icon_rules": [],
            "usx_duplicates": [],
            "surface_layout": [],
            "unscoped_headings": [],
            "redundant_imports": [],
            "inline_styles_tsx": [],
        }
        stats = {"total_files": 0, "clean": 0, "total_issues": 0}

        css_files = self._get_css_files(target)

        for css_file in css_files:
            stats["total_files"] += 1
            content = css_file.read_text()
            rel = str(css_file.relative_to(USX_STANDARD_DIR))
            file_issues = 0

            # L1: Hardcoded colors
            colors = self._check_hardcoded_colors(content)
            if colors:
                findings["colors"].append({"file": rel, "issues": colors[:10]})
                file_issues += len(colors)

            # L2: Hardcoded font sizes
            fonts = self._check_hardcoded_font_sizes(content, css_file.name)
            if fonts:
                findings["font_sizes"].append(
                    {"file": rel, "issues": fonts[:10]}
                )
                file_issues += len(fonts)

            # L3: Competing icon sizing
            icon_violations = self._check_icon_sizing(content, rel)
            if icon_violations:
                findings["icon_rules"].append(
                    {"file": rel, "issues": icon_violations}
                )
                file_issues += len(icon_violations)

            # L4: USX class duplication outside canon files
            usx_dupes = self._check_usx_duplicates(content, rel)
            if usx_dupes:
                findings["usx_duplicates"].append(
                    {"file": rel, "issues": usx_dupes}
                )
                file_issues += len(usx_dupes)

            # L5: Surface-specific layout classes
            layout_issues = self._check_surface_layout(content, rel)
            if layout_issues:
                findings["surface_layout"].append(
                    {"file": rel, "issues": layout_issues}
                )
                file_issues += len(layout_issues)

            # L6: TSX inline style audit (placeholder)
            # inline_styles = self._check_inline_styles(content)
            # if inline_styles:
            #     findings["inline_styles_tsx"].append(
            #         {"file": rel, "issues": inline_styles}
            #     )
            #     file_issues += len(inline_styles)

            # Headings
            headings = self._check_unscoped_headings(content)
            if headings:
                findings["unscoped_headings"].append(
                    {"file": rel, "issues": headings}
                )
                file_issues += len(headings)

            if file_issues == 0:
                stats["clean"] += 1
            stats["total_issues"] += file_issues

        return {"success": True, "findings": findings, "stats": stats}

    def _repair(self, target: str = "", dry_run: bool = False) -> dict:
        """Apply safe, automatic repairs to CSS files."""
        # audit = self._deep_audit(target) # 'audit' is assigned but never used
        repairs = {
            "colors_fixed": 0,
            "icon_rules_removed": 0,
            "usx_dupes_removed": 0,
            "total_files_touched": 0,
        }
        touched = set()

        for css_file in self._get_css_files(target):
            rel = str(css_file.relative_to(USX_STANDARD_DIR))
            content = css_file.read_text()
            changed = False

            # R1: Fix hardcoded colors
            new_content = self._fix_hardcoded_colors(content)
            if new_content != content:
                diff = self._count_changes(content, new_content)
                repairs["colors_fixed"] += diff
                content = new_content
                changed = True

            # R2: Remove competing icon font-size rules
            new_content = self._fix_icon_sizing(content)
            if new_content != content:
                repairs["icon_rules_removed"] += 1
                content = new_content
                changed = True

            # R3: Remove USX class duplicates outside canon
            new_content = self._fix_usx_duplicates(content)
            if new_content != content:
                repairs["usx_dupes_removed"] += 1
                content = new_content
                changed = True

            if changed:
                touched.add(rel)
                if not dry_run:
                    css_file.write_text(content)

        repairs["total_files_touched"] = len(touched)
        return {
            "success": True,
            "action": "repair",
            "dry_run": dry_run,
            "repairs": repairs,
        }

    def _get_css_files(self, target: str = "") -> list[Path]:
        if not USX_STANDARD_DIR.exists():
            return []
        css_files = (
            list(USX_STANDARD_DIR.rglob("*.css"))
            if not target
            else list(USX_STANDARD_DIR.rglob(f"*{target}*"))
        )
        return [
            f
            for f in css_files
            if not any(x in str(f) for x in USX_EXCLUDES)
        ]

    # ─── Check methods ──────────────────────────────────────────────

    def _check_hardcoded_colors(self, content: str) -> list[str]:
        issues: list[str] = []
        in_var_block = False
        for line in content.split("\n"):
            stripped = line.strip()
            if "[data-theme" in stripped or "[data-palette" in stripped:
                in_var_block = True
                continue
            if in_var_block and stripped == "}":
                in_var_block = False
                continue
            if in_var_block:
                continue
            if "--" in stripped and ":" in stripped and "var(" not in stripped:
                continue
            # Skip lines that already use var() — the hex is a fallback,
            # not a hardcoded value
            if "var(" in stripped:
                continue
            for match in re.findall(r"color:\s*#[0-9a-fA-F]{3,8}", stripped):
                issues.append(
                    f"Hardcoded color: '{match}' → use"
                    " var(--pico-*)"
                )
                break
        return issues

    def _check_hardcoded_font_sizes(
        self, content: str, filename: str
    ) -> list[str]:
        if "gridui-terminal" in filename:
            return []
        matches = re.findall(r"font-size:\s*\d+px", content)
        return [f"Hardcoded font-size: '{m}'" for m in matches]

    def _check_icon_sizing(self, content: str, rel: str) -> list[str]:
        """Detect constraints that prevent icons from matching text size."""
        issues: list[str] = []
        if rel == "usx/usx-icons.css":
            return issues

        # Check for opsz cap that limits optical sizing
        if "opsz" in content:
            issues.append(
                "Has 'opsz' font-variation-setting — removes cap so"
                " icons scale with font-size"
            )

        # Check for display: inline-block on icons (needs inline-flex for
        # heading alignment)
        if (
            "display: inline-block" in content
            and ".material-symbols-outlined" in content
        ):
            issues.append(
                "Uses display: inline-block on icons — should be"
                " inline-flex for heading alignment"
            )

        # Check for competing font-size rules on icons
        for match in re.finditer(
            r"\.material-symbols-outlined[\s\S]*?\{[^}]*font-size[^}]*\}",
            content
        ):
            if (
                "font-size: 1em" not in match.group()
                and "font-size: 1.5rem" not in match.group()
            ):
                lines = match.group().split("\n")
                for line in lines:
                    if "font-size" in line:
                        issues.append(
                            f"Competing icon font-size:"
                            f" '{line.strip()}' → remove, let"
                            " usx-icons.css handle it"
                        )
        return issues

    def _check_usx_duplicates(self, content: str, rel: str) -> list[str]:
        """Find USX class definitions outside canon files."""
        canon_files = [
            "usx-base.css",
            "usx-typography.css",
            "usx-icons.css",
        ]
        if any(c in rel for c in canon_files):
            return []
        issues = []
        for cls_list in CANONICAL_FILES.values():
            for cls in cls_list:
                # Find where the class is defined (not just referenced)
                for match in re.finditer(rf"{re.escape(cls)}\s*\{{", content):
                    issues.append(
                        f"Duplicates USX class '{cls}' → import"
                        " from usx-base.css instead"
                    )
        return issues

    def _check_surface_layout(self, content: str, rel: str) -> list[str]:
        issues: list[str] = []
        for old_cls, new_cls in SURFACE_LAYOUT_MAP.items():
            if old_cls in content:
                issues.append(
                    f"Uses '{old_cls}' instead of canonical '{new_cls}'"
                )
        return issues

    def _check_unscoped_headings(self, content: str) -> list[str]:
        issues: list[str] = []
        for h in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            unscoped = re.findall(
                rf"(?:^|(?<={{))[\s]*{h}\s*\{{", content, re.MULTILINE
            )
            if unscoped:
                issues.append(
                    f"Unscoped '{h}' selector → scope under a class"
                )
        return issues

    # ─── Fix methods ────────────────────────────────────────────────

    def _fix_hardcoded_colors(self, content: str) -> str:
        pairs = [
            (
                r"color:\s*#ffffff",
                "color: var(--pico-primary-inverse, #ffffff)",
            ),
            (
                r"color:\s*#e6edf3",
                "color: var(--pico-color, #e6edf3)",
            ),
            (
                r"color:\s*#c9d1d9",
                "color: var(--pico-color, #c9d1d9)",
            ),
            (
                r"color:\s*#8b949e",
                "color: var(--pico-muted-color, #8b949e)",
            ),
            (
                r"color:\s*#d29922",
                "color: var(--pico-warning-color, #d29922)",
            ),
            (
                r"color:\s*#58a6ff",
                "color: var(--pico-primary, #58a6ff)",
            ),
            (
                r"color:\s*#3fb950",
                "color: var(--pico-ins-color, #3fb950)",
            ),
            (
                r"color:\s*#f85149",
                "color: var(--pico-del-color, #f85149)",
            ),
            (
                r"color:\s*#2f81f7",
                "color: var(--pico-primary, #2f81f7)",
            ),
            (
                r"color:\s*#9ba7b4",
                "color: var(--pico-muted-color, #9ba7b4)",
            ),
            (
                r"color:\s*#a855f7",
                "color: var(--pico-primary, #a855f7)",
            ),
            (r"color:\s*#fff(?!\w)", "color: var(--pico-color-inverse, #fff)"),
        ]
        lines = content.split("\n")
        in_var = False
        for i, line in enumerate(lines):
            s = line.strip()
            if "[data-theme" in s or "[data-palette" in s:
                in_var = True
                continue
            if in_var and s == "}":
                in_var = False
                continue
            if in_var:
                continue
            if "--" in s and ":" in s and "var(" not in s:
                continue
            if "var(" in s:
                continue
            for pat, repl in pairs:
                if re.search(pat, line):
                    lines[i] = re.sub(pat, repl, line)
                    break
        return "\n".join(lines)

    def _fix_icon_sizing(self, content: str) -> str:
        """Remove competing .material-symbols-outlined font-size rules."""
        # Just remove font-size from these rules — the canon handles it
        lines = content.split("\n")
        in_icon_block = False
        new_lines = []
        for line in lines:
            if ".material-symbols-outlined" in line and "{" in line:
                in_icon_block = True
                new_lines.append(line)
                continue
            if in_icon_block:
                if "}" in line:
                    in_icon_block = False
                elif "font-size" in line and "!important" not in line:
                    continue  # strip the competing font-size
            new_lines.append(line)
        return "\n".join(new_lines)

    def _fix_usx_duplicates(self, content: str) -> str:
        """Remove USX class definitions outside canon files."""
        canon_classes = []
        for cls_list in CANONICAL_FILES.values():
            canon_classes.extend(cls_list)
        # Build a pattern that matches the full rule block for these classes
        lines = content.split("\n")
        new_lines = []
        skip_until_brace = 0
        for i, line in enumerate(lines):
            if skip_until_brace > 0:
                skip_until_brace -= 1
                if "}" in line:
                    skip_until_brace = 0
                continue

            stripped = line.strip()
            for cls in canon_classes:
                if stripped.startswith(cls) and "{" in stripped:
                    # Start skipping until we find the closing brace
                    skip_until_brace = 1  # Will count braces
                    brace_count = stripped.count("{") - stripped.count("}")
                    if brace_count > 0:
                        # Find the closing brace
                        for j in range(i + 1, len(lines)):
                            opens = lines[j].count("{")
                            closes = lines[j].count("}")
                            brace_count += opens - closes
                            if brace_count <= 0:
                                skip_until_brace = j - i
                                break
                    break
            else:
                new_lines.append(line)
        return "\n".join(new_lines)

    def _count_changes(self, old: str, new: str) -> int:
        old_lines = old.split("\n")
        new_lines = new.split("\n")
        return sum(1 for o, n in zip(old_lines, new_lines) if o != n)

    def _recommendations(self, audit: dict) -> list[str]:
        recs = [
            "Use CSS variables (--pico-*) instead of hardcoded values",
            (
                "Use `.prose` class for markdown content instead"
                " of per-surface prose styles"
            ),
            (
                "Use USX layout classes from usx-base.css instead"
                " of surface-specific wrappers"
            ),
            (
                "Strip .material-symbols-outlined font-size from"
                " all non-USX CSS files"
            ),
            "Remove duplicate USX class definitions from nestframe.css",
            (
                "Do not redefine .usx-surface-body or"
                " .usx-surface-main in any surface CSS"
            ),
        ]
        findings = audit.get("findings", {})
        for key, label in [
            ("icon_rules", "Competing icon rules"),
            ("usx_duplicates", "Duplicate USX class definitions"),
            ("surface_layout", "Surface-specific layout classes"),
        ]:
            if findings.get(key):
                files = set(f["file"] for f in findings[key])
                recs.append(
                    f"Fix {label} in: {', '.join(sorted(files))}"
                )
        return recs
