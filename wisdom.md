# uCore Wisdom

Date: 2026-06-25T20:29:32Z
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
- **Popcorn polling interval matters**: The popcorn tray app polled Ollama every 5 seconds, generating 500 spool entries/day. Raised to 30 seconds. Keep daemon polling intervals ≥30s unless latency-critical. Use `NSTimer` or `threading.Timer` with cooldown, not raw loops.
- **launchd KeepAlive traps**: `com.udos.ucore-popcorn.plist` had `KeepAlive <true/>` — killing the process just spawned another immediately. Use `launchctl bootout` to stop, not just `kill`. Distinguish between "stop for debugging" and "disable until reboot."
- **`except` nesting bug in snackbar_menu.py**: A `release_lock()` function had a bare `except` nested inside `try:` at the wrong indentation level, causing `SyntaxError: invalid syntax` on line 1122. Always run `flake8` or `py_compile` on changed files; this error only surfaced in `stderr.log` after launchd restart.

## Recent Change Scan
- backend/app/surfaces/ceefax.py
- backend/app/tools/ollama_tool.py
- backend/app/surfaces/dashboard.py
- backend/app/tools/node_tool.py
- backend/app/tools/github_cli_tool.py
- backend/app/tools/docker_tool.py
- backend/app/tools/git_tool.py
- backend/app/tools/base.py
- backend/app/tools/__init__.py
- backend/app/tools/python_tool.py
- backend/app/ui/popcorn.py
- backend/app/tools/registry.py
- backend/app/tools/vscode_tool.py
- backend/app/skills/builtin/route_task.py
- backend/app/services/mcp/__init__.py
- backend/app/services/mcp/github_tools.py
- backend/app/services/mcp/github_client.py
- backend/app/services/identity.py
- backend/app/services/maintenance_scheduler.py
- backend/app/services/gridsmith_bridge.py

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
- popcorn: 500 entries (0 errors)

### Recent Activity
- ℹ️ 2026-06-26T04:29:29  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T04:29:29  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T04:00:55  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T04:00:55  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T02:32:52  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T02:32:52  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T01:50:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T01:50:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:48:52  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:48:52  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:04:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:04:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:04:20  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:04:20  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:03:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:03:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:03:20  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:03:20  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:02:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:02:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:02:20  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:02:20  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:01:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:01:50  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:01:19  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:01:19  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:00:49  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:00:49  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:00:19  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-26T00:00:19  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-

## Test Failure Signals (last 24h)

- pytest-cache: tests/test_api_containers.py::test_create_container
- pytest-cache: tests/test_api_containers.py::test_create_container_no_name
- pytest-cache: tests/test_api_containers.py::test_create_container_invalid_runtime
- pytest-cache: tests/test_api_containers.py::test_list_containers
- pytest-cache: tests/test_api_containers.py::test_list_containers_filter_status
- pytest-cache: tests/test_api_containers.py::test_get_container
- pytest-cache: tests/test_api_containers.py::test_get_container_not_found
- pytest-cache: tests/test_api_containers.py::test_start_stop_container
- pytest-cache: tests/test_api_containers.py::test_get_logs
- pytest-cache: tests/test_api_containers.py::test_get_logs_tail
