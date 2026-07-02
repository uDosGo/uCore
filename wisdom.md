# uCore Wisdom

Date: 2026-07-02T12:02:46Z
Status: Refreshed by brain_sync

## Durable Lessons
- Keep one canonical implementation path per subsystem; remove split-file remnants once a stable abstraction exists.
- Prefer local-first flows for AppFlowy, Snackbar spool, and clipboard workflows so offline operation remains the default.
- Treat the tray menu, clipboard buffer, and system snacks as one orchestration surface, not separate side features.
- Use explicit, structured docs with stable headings, tables, and low ambiguity so they can be transformed into DocLang-style agent context later.
- **Cline CLI is the single orchestrator**: Both interactive TUI (pair programming) and headless `--yolo` mode (automation). Avoid separate CLI wrappers; Cline already has all modes.
- **Firewatch MCP + Playwright for UI automation**: Zen Browser (Firefox) + Firewatch MCP tools directly available to agents. Lightpanda for high-scale headless only.
- **AppFlowy integration is multi-path**: CLI for data sync, n8n for workflows, Zapier for broad integrations. No single "configure everything" panel; compose tools based on use case.
- **Playwright Python/JS API is standardized**: Whether connecting to Zen, Lightpanda CDP, or headless Firefox, same Playwright code works. Switch backend, keep same interface.
- **UI Refinement = Multiple Tabs + Shared Components**: S320 tabbed interface reduces cognitive load. TaskDetailDrawer reusable across surfaces. Progressive disclosure pattern works well.
- **Consolidation Dashboard mirrors progress**: Checkbox-based checklist + metric tracking builds confidence. Visual progress bars (coverage %) are more compelling than raw numbers.
- **⛔ Prevent skill loops with convergence guards**: USX surface rebuild skills that run audit→repair→re-audit cycles MUST have a `max_iterations` guard (default 3) and a surface-level cooldown tracker (5 min TTL). Without this, orchestration agents can infinite-loop on surfaces that never converge to zero issues. `skill_surface_rebuild` has this guard; add it to any new multi-step pipeline skill.
- **launchd KeepAlive traps**: Deprecated launchd configs with `KeepAlive <true/>` respawn killed processes immediately. Use `launchctl bootout` to stop, not just `kill`. Distinguish between "stop for debugging" and "disable until reboot."
- **`except` nesting bug in snackbar_menu.py**: A `release_lock()` function had a bare `except` nested inside `try:` at the wrong indentation level, causing `SyntaxError: invalid syntax` on line 1122. Always run `flake8` or `py_compile` on changed files; this error only surfaced in `stderr.log` after launchd restart.

## Recent Change Scan
- backend/app/skills/builtin/skill_enhancement_planner.py
- backend/app/skills/builtin/skill_gh_workflow_bridge.py
- backend/app/skills/builtin/skill_dev_mode_executor.py
- backend/app/skills/builtin/skill_cline_invoke.py
- backend/app/skills/builtin/skill_hivemind_consensus.py
- backend/app/skills/builtin/skill_audit.py
- backend/app/skills/builtin/skill_roundtable_dispatch.py
- backend/app/skills/builtin/route_task.py
- backend/app/skills/builtin/skill_ucore_index.py
- backend/app/skills/builtin/skill_ecosystem_audit.py
- backend/app/api/routes.py
- backend/app/api/control_api.py

## Memory Architecture
- Short-term: active AI/chat session context.
- Long-term: AppFlowy, vault, and canonical docs.
- Episodic: wisdom.md, spool logs, and recent change summaries.

## Synthesis Inputs
- Window: last 24h
- Spool summary: included
- AppFlowy activity: not included
- Test failures: 10 signals
- Episodic log: not included

## Durable Lessons (2026-07-02 — Agentic Execution Pipeline)

- **Smoke-testing skills on import + dry-run catches broken dependencies** before they cause runtime failures. The `skill-audit` rewrites does this systematically.
- **Health scoring ecosystem items** (working/untested/broken/orphaned) gives a clear, actionable picture of what needs attention. `ecosystem-audit assess` proved this at 99.4% health across 173 items.
- **The `dev-mode-executor` pipeline pattern** (fetch → analyze → route → consensus → execute → log) is reusable for any task workflow. Keep it as the canonical agentic execution pattern.
- **Route tasks to specialized agents based on content keywords**, not user selection. `roundtable-dispatch` auto-selects architect/dev/reviewer/debugger/docgen from the task description.
- **Hivemind consensus defaults to weighted mode** with architect + dev + reviewer models for balanced deliberation. Majority mode for quick decisions, deliberative for deep analysis.
- **Cline invoke should default to interactive mode** for safety, with `--yolo` opt-in for pre-approved autonomous tasks.
- **Flake8 unused imports are the #1 lint issue** in new skill files — run `flake8 --select=F841` before every commit.
- **Aggregation endpoints should run checks concurrently** — `control_service.py` uses `asyncio.gather` for all 8 status probes, keeping the `/api/control/status` response under 3 seconds.

## Next Synthesis Targets
- Migration checklist status and canonical doc destinations.
- Snackbar/system orchestration refinements and tray workflows.
- UI view wiring across frontend surfaces and system pages.
- DocLang-style structured export for AI-efficient document context.

## Spool Activity (last 24h)

Total entries: 500
Errors: 0
Warnings: 2

### By Module
- stdout: 480 entries (0 errors)
- ucore-menu-stderr: 10 entries (0 errors)
- ucore-menu: 10 entries (0 errors)

### Recent Warnings
- [2026-07-02T19:20:10] ucore-menu: Backend failed to start within 8.0 seconds
- [2026-07-02T19:20:10] ucore-menu: Backend failed to start within 8.0 seconds

### Recent Activity
- ℹ️ 2026-07-02T19:26:22  stdout  [2026-07-02 19:26:22] WARNING  ucore.skills.registry — Skill load fail skill_dev_destroy_rebuild.py:
- ℹ️ 2026-07-02T19:26:22  stdout  [2026-07-02 19:26:22] WARNING  ucore.skills.registry — Skill load fail skill_hardcoded_path_detector
- ℹ️ 2026-07-02T19:20:46  ucore-menu-stderr  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-02T19:20:46  ucore-menu  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-02T19:20:46  ucore-menu-stderr  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-02T19:20:46  ucore-menu  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-02T19:20:10  ucore-menu-stderr  ucore-menu: Global clipboard shortcut registered: Ctrl+Cmd+V
- ℹ️ 2026-07-02T19:20:10  ucore-menu  ucore-menu: Global clipboard shortcut registered: Ctrl+Cmd+V
- ℹ️ 2026-07-02T19:20:10  ucore-menu-stderr  ucore-menu: Registered snack: clipboard-buffer (clipboard)
- ℹ️ 2026-07-02T19:20:10  ucore-menu  ucore-menu: Registered snack: clipboard-buffer (clipboard)
- ⚠️ 2026-07-02T19:20:10  ucore-menu-stderr  ucore-menu: Backend failed to start within 8.0 seconds
- ⚠️ 2026-07-02T19:20:10  ucore-menu  ucore-menu: Backend failed to start within 8.0 seconds
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] INFO     ucore.api.github — GitHub API routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Spool activity feed routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Identity routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Ceefax Teletext surface registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — BBCSDL surface registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Dashboard surface registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Library index routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore.vault_api — Vault topology routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Vault topology routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Catalog API routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Hivemind knowledge layer routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore.api.dev_layer — Dev Layer API routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Dev Layer API routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Tasker API routes registered (incl. /api/workflow/tasks)
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] INFO     ucore.api.feed — Feed API routes registered: ingest, query, suggest, 
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Feed API routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] INFO     ucore.api.surface_registry — Surface registry routes registered
- ℹ️ 2026-07-02T19:20:00  stdout  [2026-07-02 19:20:00] DEBUG    ucore — Surface Registry API routes registered

## Test Failure Signals (last 24h)

- pytest-cache: backend/tests/test_chat_cache.py::test_provider_router_chat_uses_cache
- pytest-cache: backend/tests/test_core_snackbar.py::test_shutdown_handler
- pytest-cache: backend/tests/test_episodic_log.py::test_episodic_log_skill_writes_entry
- pytest-cache: backend/tests/test_episodic_log.py::test_episodic_log_skill_rejects_invalid_type
- pytest-cache: backend/tests/test_episodic_log.py::test_episodic_log_skill_requires_description
- pytest-cache: backend/tests/test_episodic_log.py::test_episodic_log_accepts_comma_separated_tags
- pytest-cache: backend/tests/test_episodic_log.py::test_brain_sync_includes_episodic_summary
- pytest-cache: backend/tests/test_flow_router.py::test_flow_router_basic
- pytest-cache: backend/tests/test_flow_router.py::test_flow_router_analytics
- pytest-cache: backend/tests/test_flow_router.py::test_flow_router_clear
