# uCore Wisdom

Date: 2026-07-02T01:30:08Z
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
- backend/app/api/flow_router/__init__.py
- backend/app/api/surface_registry_api.py
- backend/app/core/snackbar.py
- backend/app/api/routes.py
- backend/app/skills/builtin/.mypy_cache/3.11/@plugins_snapshot.json
- backend/app/skills/builtin/skill_ecosystem_audit.py
- backend/app/api/.mypy_cache/missing_stubs
- backend/app/api/.mypy_cache/3.11/@plugins_snapshot.json
- backend/app/api/.mypy_cache/3.11/inspect.meta.json
- backend/app/api/.mypy_cache/3.11/inspect.data.json
- backend/app/api/.mypy_cache/3.11/dis.meta.json
- backend/app/api/.mypy_cache/3.11/dis.data.json
- backend/app/api/.mypy_cache/3.11/app/skills/builtin/__init__.meta.json
- backend/app/api/.mypy_cache/3.11/app/skills/builtin/__init__.data.json
- backend/app/api/.mypy_cache/3.11/importlib/util.meta.json
- backend/app/api/.mypy_cache/3.11/importlib/util.data.json
- backend/app/api/.mypy_cache/3.11/opcode.meta.json
- backend/app/api/.mypy_cache/3.11/opcode.data.json
- backend/app/skills/builtin/skill_surface_registry.py
- backend/app/skills/builtin/usx_standard.py

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

## Next Synthesis Targets
- Migration checklist status and canonical doc destinations.
- Snackbar/system orchestration refinements and tray workflows.
- UI view wiring across frontend surfaces and system pages.
- DocLang-style structured export for AI-efficient document context.

## Spool Activity (last 24h)

Total entries: 500
Errors: 0
Warnings: 0

### By Module
- ucore-popcorn-stderr: 461 entries (0 errors)
- stdout: 29 entries (0 errors)
- ucore-menu-stderr: 5 entries (0 errors)
- ucore-menu: 5 entries (0 errors)

### Recent Activity
- ℹ️ 2026-07-02T09:29:51  stdout  [2026-07-02 09:29:51] WARNING  ucore.skills.registry — Skill load fail skill_dev_destroy_rebuild.py:
- ℹ️ 2026-07-02T09:29:51  stdout  [2026-07-02 09:29:51] WARNING  ucore.skills.registry — Skill load fail skill_hardcoded_path_detector
- ✅ 2026-07-02T09:29:51  stdout  [2026-07-02 09:29:51] INFO     ucore — Maintenance job ran: daily_backup success=True
- ✅ 2026-07-02T09:29:51  stdout  [2026-07-02 09:29:51] INFO     ucore — Maintenance job ran: vault_sync success=False
- ✅ 2026-07-02T09:29:51  stdout  [2026-07-02 09:29:51] INFO     ucore — Maintenance job ran: tasker_sync success=False
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] INFO     ucore.api.github — GitHub API routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Spool activity feed routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Identity routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Ceefax Teletext surface registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — BBCSDL surface registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Dashboard surface registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Library index routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore.vault_api — Vault topology routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Vault topology routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Catalog API routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Hivemind knowledge layer routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore.api.dev_layer — Dev Layer API routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Dev Layer API routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Tasker API routes registered (incl. /api/workflow/tasks)
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] INFO     ucore.api.feed — Feed API routes registered: ingest, query, suggest, 
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Feed API routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] INFO     ucore.api.surface_registry — Surface registry routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Surface Registry API routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — API module routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] DEBUG    ucore — Catalog routes registered
- ℹ️ 2026-07-02T09:29:50  stdout  [2026-07-02 09:29:50] INFO     ucore — Maintenance scheduler started with 6 jobs
- ℹ️ 2026-07-02T09:29:48  ucore-menu-stderr  ucore-menu: Starting backend...
- ℹ️ 2026-07-02T09:29:48  ucore-menu  ucore-menu: Starting backend...
- ℹ️ 2026-07-02T09:29:48  ucore-menu-stderr  ucore-menu: Backend not running, attempting auto-start...
- ℹ️ 2026-07-02T09:29:48  ucore-menu  ucore-menu: Backend not running, attempting auto-start...

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
