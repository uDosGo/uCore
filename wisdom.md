# uCore Wisdom

Date: 2026-06-30T20:15:29Z
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
- backend/app/mcp/hivemind_server.py
- backend/.venv/lib/python3.14/site-packages/snackmachine-1.0.0.dist-info/RECORD
- backend/.venv/lib/python3.14/site-packages/snackmachine-1.0.0.dist-info/REQUESTED
- backend/.venv/lib/python3.14/site-packages/snackmachine-1.0.0.dist-info/direct_url.json
- backend/.venv/lib/python3.14/site-packages/snackmachine-1.0.0.dist-info/INSTALLER
- backend/.venv/bin/snackmachine
- backend/.venv/lib/python3.14/site-packages/snackmachine-1.0.0.dist-info/top_level.txt
- backend/.venv/lib/python3.14/site-packages/snackmachine-1.0.0.dist-info/entry_points.txt
- backend/.venv/lib/python3.14/site-packages/snackmachine-1.0.0.dist-info/WHEEL
- backend/.venv/lib/python3.14/site-packages/snackmachine-1.0.0.dist-info/METADATA
- backend/.venv/lib/python3.14/site-packages/__editable__.snackmachine-1.0.0.pth
- backend/.venv/lib/python3.14/site-packages/__editable___snackmachine_1_0_0_finder.py
- backend/pyproject.toml
- backend/app/services/provider_router.py
- backend/.venv/lib/python3.14/site-packages/langgraph-1.2.7.dist-info/RECORD
- backend/.venv/lib/python3.14/site-packages/langgraph-1.2.7.dist-info/REQUESTED
- backend/.venv/lib/python3.14/site-packages/langgraph-1.2.7.dist-info/INSTALLER
- backend/.venv/lib/python3.14/site-packages/langgraph-1.2.7.dist-info/licenses/LICENSE
- backend/.venv/lib/python3.14/site-packages/langgraph-1.2.7.dist-info/WHEEL
- backend/.venv/lib/python3.14/site-packages/langgraph-1.2.7.dist-info/METADATA

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
- ucore-menu-stderr: 17 entries (0 errors)
- ucore-menu: 17 entries (0 errors)
- stdout: 5 entries (0 errors)

### Recent Activity
- ✅ 2026-07-01T04:05:25  stdout  [2026-07-01 04:05:25] INFO     ucore — Maintenance job ran: tasker_sync success=False
- ✅ 2026-07-01T04:00:25  stdout  [2026-07-01 04:00:25] INFO     ucore — Maintenance job ran: vault_sync success=False
- ✅ 2026-07-01T03:00:32  stdout  [2026-07-01 03:00:32] INFO     ucore — Maintenance job ran: daily_backup success=True
- ℹ️ 2026-07-01T02:18:57  ucore-menu-stderr  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T02:18:57  ucore-menu  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T02:18:57  ucore-menu-stderr  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-01T02:18:57  ucore-menu  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-01T01:27:19  stdout  [2026-07-01 01:27:19] INFO     ucore.chat — Chat request: agent=vault, history_len=3, message=Pick u
- ℹ️ 2026-07-01T01:18:59  ucore-menu-stderr  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T01:18:59  ucore-menu  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T01:18:59  ucore-menu-stderr  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-01T01:18:59  ucore-menu  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-01T01:18:17  ucore-menu-stderr  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T01:18:17  ucore-menu  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T01:18:17  ucore-menu-stderr  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-01T01:18:17  ucore-menu  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-01T00:59:00  ucore-menu-stderr  ucore-menu: Opened URL: http://localhost:5175/s310
- ℹ️ 2026-07-01T00:59:00  ucore-menu  ucore-menu: Opened URL: http://localhost:5175/s310
- ℹ️ 2026-07-01T00:11:42  ucore-menu-stderr  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T00:11:42  ucore-menu  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T00:11:42  ucore-menu-stderr  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-01T00:11:42  ucore-menu  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-01T00:10:37  ucore-menu-stderr  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T00:10:37  ucore-menu  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-07-01T00:10:36  ucore-menu-stderr  ucore-menu: Opening UI Hub
- ℹ️ 2026-07-01T00:10:36  ucore-menu  ucore-menu: Opening UI Hub
- ℹ️ 2026-06-30T23:41:11  ucore-menu-stderr  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-06-30T23:41:11  ucore-menu  ucore-menu: Opened URL: http://localhost:5175
- ℹ️ 2026-06-30T23:41:11  ucore-menu-stderr  ucore-menu: Opening UI Hub
- ℹ️ 2026-06-30T23:41:11  ucore-menu  ucore-menu: Opening UI Hub

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
