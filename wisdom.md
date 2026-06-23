# uCore Wisdom

Date: 2026-06-22T20:28:33Z
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

## Recent Change Scan
- frontend/dist/assets/MaterialSymbolsOutlined-Db6aBbE4.ttf
- frontend/dist/assets/Teletext50-B0FE1AIM.otf
- frontend/dist/assets/C64_User_Mono_v1.0-STYLE-BsBxhfAV.ttf
- frontend/dist/assets/press-start-2p-CnAFzuvi.woff2
- frontend/dist/assets/Bedstead-OSqLCfiS.otf
- frontend/dist/assets/index-DjyVuFu2.js
- frontend/dist/assets/C64_User_Mono_v1.0-STYLE-CFnYgsZY.woff
- frontend/dist/index.html
- frontend/dist/assets/index-DRAibU9i.css
- frontend/dist/assets/PetMe128-DUjnzmmV.ttf
- backend/.pytest_cache/v/cache/nodeids
- backend/app/api/secret_store_api.py
- frontend/src/surfaces/system/SecretStorePanel.tsx
- backend/app/api/config_api.py
- backend/app/skills/builtin/route_task.py
- backend/app/services/provider_router.py
- backend/app/core/settings.py
- frontend/src/surfaces/userver/UServerSurface.tsx
- docs/USER_SETUP_VAULT_MCP_WORKSPACES.md
- .tasker/UNIFIED_DEV_TASK_WORKFLOW.md

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
- stdout: 406 entries (0 errors)
- popcorn: 94 entries (0 errors)

### Recent Activity
- ℹ️ 2026-06-23T04:28:31  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-23T04:28:31  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — ╔══════════════════════════════════════════╗
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — ║       uCore v4.0.0 — unified daemon        ║
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — ╚══════════════════════════════════════════╝
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — Host: 0.0.0.0:8484
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — Debug: True
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — Auto-start surfaces: False
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — Starting uCore snackbar on 0.0.0.0:8484
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — Database migration: v1 (surfaces, snacks, containers tables)
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore.api.github — GitHub API routes registered
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] DEBUG    ucore — Spool activity feed routes registered
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] DEBUG    ucore — Identity routes registered
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] DEBUG    ucore — Ceefax Teletext surface registered
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] DEBUG    ucore — BBCSDL surface registered
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] DEBUG    ucore — Dashboard surface registered
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] DEBUG    ucore — API module routes registered
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — Maintenance scheduler started with 6 jobs
- ℹ️ 2026-06-23T04:28:29  stdout  [2026-06-23 04:28:29] INFO     ucore — Maintenance scheduler stopped
- ℹ️ 2026-06-23T04:28:26  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-23T04:28:26  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-23T04:28:21  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-23T04:28:21  popcorn  Ollama status: running, models: ['qwen2.5-coder:0.5b', 'codegemma:2b', 'qwen2.5-coder:3b', 'qwen2.5-
- ℹ️ 2026-06-23T04:28:19  stdout  [2026-06-23 04:28:19] INFO     ucore — ╔══════════════════════════════════════════╗
- ℹ️ 2026-06-23T04:28:19  stdout  [2026-06-23 04:28:19] INFO     ucore — ║       uCore v4.0.0 — unified daemon        ║
- ℹ️ 2026-06-23T04:28:19  stdout  [2026-06-23 04:28:19] INFO     ucore — ╚══════════════════════════════════════════╝
- ℹ️ 2026-06-23T04:28:19  stdout  [2026-06-23 04:28:19] INFO     ucore — Host: 0.0.0.0:8484
- ℹ️ 2026-06-23T04:28:19  stdout  [2026-06-23 04:28:19] INFO     ucore — Debug: True
- ℹ️ 2026-06-23T04:28:19  stdout  [2026-06-23 04:28:19] INFO     ucore — Auto-start surfaces: False
- ℹ️ 2026-06-23T04:28:19  stdout  [2026-06-23 04:28:19] INFO     ucore — Starting uCore snackbar on 0.0.0.0:8484

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
