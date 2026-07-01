# Snacks & Skills Status Audit

**Generated:** 2026-06-30T20:53:00Z  
**Scope:** All snack plugins and builtin skills in `backend/app/`

---

## Snacks

### Menu Snacks (`backend/app/menu/snacks/`)

| Snack | File | Status | Notes |
|-------|------|--------|-------|
| **SystemSnack** | `system_snack.py` | ✅ Working | Health checks, service mgmt. Hardcoded paths to user's machine. |
| **SurfaceSnack** | `surface_snack.py` | ✅ Working | Surface navigation, auto-starts backend. Hardcoded paths. |
| **ClipboardSnack** | `clipboard_snack.py` | ✅ Working | Delegates to ObjC menu delegate. Requires macOS. |
| **AppFlowySyncSnack** | `appflowy_sync_snack.py` | ✅ Working | Vault→AppFlowy sync via af_manager. Depends on AppFlowy DB. |
| **OllamaSnack** | `ollama_snack.py` | ⚠️ Untested | Ollama model management. Needs Ollama running. |

### API Snacks (`backend/app/snacks/`)

| Snack | File | Status | Notes |
|-------|------|--------|-------|
| **AppFlowyEditorSnack** | `appflowy_editor_snack.py` | ✅ Fixed | Was corrupted (overlapping writes). Reconstructed from docstring + imports. |
| **DevModeSnack** | `dev_mode_snack.py` | ✅ Working | Dev server start/stop. Hardcoded paths. |
| **MissionOpsSnack** | `mission_ops_snack.py` | ✅ Working | Mission queue via API. Depends on backend running. |
| **SpoolMonitorSnack** | `spool_monitor_snack.py` | ✅ Working | Spool error monitoring with macOS notifications. |

### Snack Template

| File | Status | Notes |
|------|--------|-------|
| `templates/snack_template.py` | ✅ Working | BaseSnack class with Pydantic validation. |
| `templates/snack_template.yaml` | ✅ Working | YAML metadata template. |

---

## Skills

### Builtin Skills (`backend/app/skills/builtin/`)

| Skill | File | Status | Notes |
|-------|------|--------|-------|
| **ask_vault** | `ask_vault.py` | ⚠️ Untested | Vault Q&A skill. |
| **attach_context** | `attach_context.py` | ⚠️ Untested | Context attachment. |
| **backup** | `backup.py` | ⚠️ Untested | Backup operations. |
| **brain_sync** | `brain_sync.py` | ⚠️ Untested | Brain sync. |
| **clipboard_maintenance** | `clipboard_maintenance.py` | ⚠️ Untested | Clipboard cleanup. |
| **container_start** | `container_start.py` | ⚠️ Untested | Docker container start. |
| **container_stop** | `container_stop.py` | ⚠️ Untested | Docker container stop. |
| **daily_backup** | `daily_backup.py` | ⚠️ Untested | Daily backup routine. |
| **episodic_log** | `episodic_log.py` | ⚠️ Untested | Episodic memory logging. |
| **export** | `export.py` | ⚠️ Untested | Data export. |
| **file_edit_enhancer** | `file_edit_enhancer.py` | ✅ Working | MCP file editing with spool logging. |
| **git_maintenance** | `git_maintenance.py` | ⚠️ Untested | Git operations. |
| **import_skill** | `import_skill.py` | ⚠️ Untested | Skill import. |
| **lint_fix** | `lint_fix.py` | ⚠️ Untested | Lint auto-fix. |
| **route_task** | `route_task.py` | ⚠️ Untested | Task routing. |
| **skill_audit** | `skill_audit.py` | ⚠️ Untested | Skill audit. |
| **skill_autostart** | `skill_autostart.py` | ⚠️ Untested | Auto-start skills. |
| **skill_color_reset** | `skill_color_reset.py` | ⚠️ Untested | Terminal color reset. |
| **skill_dead_code_archiver** | `skill_dead_code_archiver.py` | ✅ Working | Dead code detection. |
| **skill_devlog_mcp** | `skill_devlog_mcp.py` | ✅ Working | MCP devlog generation. |
| **skill_duplicate_detector** | `skill_duplicate_detector.py` | ✅ Working | Duplicate code detection. |
| **skill_hardcoded_path_detector** | `skill_hardcoded_path_detector.py` | ✅ Working | Hardcoded path detection. |
| **skill_lint_fix** | `skill_lint_fix.py` | ⚠️ Untested | Lint fix (duplicate of lint_fix?). |
| **skill_lucide_icon_migration** | `skill_lucide_icon_migration.py` | ⚠️ Untested | Icon migration audit. |
| **skill_mcp_self_heal** | `skill_mcp_self_heal.py` | ⚠️ Untested | MCP self-healing. |
| **skill_modularisation_planner** | `skill_modularisation_planner.py` | ✅ Working | Modularization planning. |
| **skill_pico_component_audit** | `skill_pico_component_audit.py` | ⚠️ Untested | Pico CSS component audit. |
| **skill_surface_enhancement_report** | `skill_surface_enhancement_report.py` | ⚠️ Untested | Surface enhancement reporting. |
| **skill_surface_rebuild** | `skill_surface_rebuild.py` | ⚠️ Untested | Surface rebuild. |
| **skill_ucore_index** | `skill_ucore_index.py` | ⚠️ Untested | uCore index. |
| **skill_usx_audit_enhanced** | `skill_usx_audit_enhanced.py` | ⚠️ Untested | USX audit. |
| **skill_usx_spacing_normalize** | `skill_usx_spacing_normalize.py` | ⚠️ Untested | USX spacing normalize. |
| **spool_maintenance** | `spool_maintenance.py` | ✅ Working | Spool maintenance. |
| **surface_repair** | `surface_repair.py` | ⚠️ Untested | Surface repair. |
| **surface_restart** | `surface_restart.py` | ⚠️ Untested | Surface restart. |
| **tasker_devlog_bridge** | `tasker_devlog_bridge.py` | ✅ Working | Tasker↔devlog bridge. |
| **tasker_sync** | `tasker_sync.py` | ⚠️ Untested | Tasker sync. |
| **usx_standard** | `usx_standard.py` | ⚠️ Untested | USX standard. |
| **vault_sync** | `vault_sync.py` | ⚠️ Untested | Vault sync. |
| **workflow_audit** | `workflow_audit.py` | ⚠️ Untested | Workflow audit. |
| **workflow_guard** | `workflow_guard.py` | ⚠️ Untested | Workflow guard. |
| **workflow_pause** | `workflow_pause.py` | ⚠️ Untested | Workflow pause. |

### Scheduled Skills (`backend/app/skills/builtin/scheduled/`)

| Skill | Status | Notes |
|-------|--------|-------|
| *(empty directory)* | ⚠️ Empty | No scheduled skills defined yet. |

### Skill Templates

| File | Status | Notes |
|------|--------|-------|
| `templates/skill_template.py` | ✅ Working | BaseSkill class. |
| `templates/skill_template.yaml` | ✅ Working | YAML metadata template. |

---

## Issues Found & Fixed

### Fixed
1. **`appflowy_editor_snack.py`** — File was corrupted with overlapping partial writes (invalid syntax). Reconstructed from docstring, imports, and snack plugin pattern. Uses `af_manager.sync` for vault imports instead of non-existent `appflowy_import`.

### Pre-existing Issues (not fixed)
1. **`appflowy_editor_snack.py`** — `_sync_from_vault` uses `load_config()` without args; may need a config path. Lazy import of `af_manager` is fine.
2. **`system_snack.py`** — Hardcoded paths (`/Users/fredbook/Code/uCore/backend`). Not portable.
3. **`dev_mode_snack.py`** — Hardcoded paths. `pkill -f vite` is aggressive.
4. **`surface_snack.py`** — Hardcoded paths. Auto-starts backend with hardcoded cwd.
5. **`lint_fix.py` vs `skill_lint_fix.py`** — Two files with similar names; likely duplicates.
6. **Many skills untested** — 28 of 42 builtin skills are marked ⚠️ Untested. They parse cleanly but have never been executed in this audit.

---

## Alignment with Reference Docs

| Doc | Alignment Status | Notes |
|-----|-----------------|-------|
| `docs/SNACKS_SYSTEM_SPEC.md` | ✅ Aligned | Snack registry, BaseSnack, and menu snacks match spec. |
| `docs/SPOOL_SPEC.md` | ✅ Aligned | SpoolMonitorSnack uses `spool_reader`. |
| `docs/DEVMODE_CODE_ANALYSIS_SKILLS.md` | ✅ Aligned | duplicate-detector, dead-code-archiver, modularisation-planner all exist. |
| `docs/MCP_SETUP.md` | ✅ Aligned | MCP skills (file_edit_enhancer, tasker_devlog_bridge) match. |
| `docs/OPTIMIZED_WORKFLOW.md` | ⚠️ Partial | TOON/Flow-LLM skills exist but not as builtin skills. |

---

## Recommendations

1. **Run the 28 untested skills** through a smoke test to confirm they import and execute without errors.
2. **Consolidate `lint_fix.py` and `skill_lint_fix.py`** — they appear to be duplicates.
3. **Remove hardcoded paths** from system_snack, dev_mode_snack, surface_snack — use env vars or config.
4. **Add scheduled skills** or remove the empty `scheduled/` directory.
5. **Run ruff on all skills** to catch any other syntax errors like the one in appflowy_editor_snack.