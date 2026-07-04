# uCore Wisdom

Date: 2026-07-04T13:42:00Z
Status: Docs round complete (PyCharm setup + Grid UI polish + handover)

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
- pyproject.toml: version 4.0.3 → 4.0.4
- package.json: version 4.0.3 → 4.0.4
- fieldnotes.md: added 2026-07-04 entry (PyCharm setup, Grid UI, handover)
- devlog.mcp.yaml: updated to v2.2.0 with session changes
- .tasker/handover-pyrchard-2026-07-04.md: new session handover document
- .tasker.dev-flow.yaml: updated completed count and sprint notes

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
- Fix 10 active test failures (episodic_log, flow_router, chat_cache, snackbar)
- Investigate backend snackbar crash loop on launchd
- GridSmith Node.js agent implementation per gap analysis
- DocLang-style structured export for AI-efficient document context
- Migration checklist status and canonical doc destinations

## Spool Activity (last 24h)

Total entries: 500
Errors: 0
Warnings: 0

### By Module
- ucore-popcorn-stderr: 457 entries (0 errors)
- stdout: 31 entries (0 errors)
- ucore-menu-stderr: 5 entries (0 errors)
- ucore-menu: 5 entries (0 errors)
- ucore-server: 2 entries (0 errors)

### Recent Activity
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] INFO     ucore.api.github — GitHub API routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Spool activity feed routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Identity routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Ceefax Teletext surface registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — BBCSDL surface registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Dashboard surface registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Library index routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore.vault_api — Vault topology routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Vault topology routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Catalog API routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Hivemind knowledge layer routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore.api.dev_layer — Dev Layer API routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Dev Layer API routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Tasker API routes registered (incl. /api/workflow/tasks)
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] INFO     ucore.api.feed — Feed API routes registered: ingest, query, suggest, 
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Feed API routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] INFO     ucore.api.control — Control Panel API routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Control Panel API routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] INFO     ucore.api.surface_registry — Surface registry routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Surface Registry API routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — API module routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] DEBUG    ucore — Catalog routes registered
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] INFO     ucore — Maintenance scheduler started with 6 jobs
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] WARNING  ucore.skills.registry — Skill load fail skill_dev_destroy_rebuild.py:
- ℹ️ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] WARNING  ucore.skills.registry — Skill load fail skill_hardcoded_path_detector
- ✅ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] INFO     ucore — Maintenance job ran: daily_backup success=True
- ✅ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] INFO     ucore — Maintenance job ran: vault_sync success=False
- ✅ 2026-07-04T21:28:14  stdout  [2026-07-04 21:28:14] INFO     ucore — Maintenance job ran: tasker_sync success=False
- ℹ️ 2026-07-04T21:28:13  ucore-menu-stderr  ucore-menu: Starting backend...
- ℹ️ 2026-07-04T21:28:13  ucore-menu  ucore-menu: Starting backend...

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
