# uCore Wisdom

Date: 2026-06-21T21:30:47Z
Status: Refreshed by brain_sync

## Durable Lessons
- Keep one canonical implementation path per subsystem; remove split-file remnants once a stable abstraction exists.
- Prefer local-first flows for AppFlowy, Snackbar spool, and clipboard workflows so offline operation remains the default.
- Treat the tray menu, clipboard buffer, and system snacks as one orchestration surface, not separate side features.
- Use explicit, structured docs with stable headings, tables, and low ambiguity so they can be transformed into DocLang-style agent context later.

## Recent Change Scan
- .tasker/UNIFIED_DEV_TASK_WORKFLOW.md
- backend/.pytest_cache/v/cache/nodeids
- backend/app/skills/builtin/attach_context.py
- backend/app/skills/builtin/brain_sync.py
- backend/tests/test_skills_memory.py
- backend/.pytest_cache/v/cache/lastfailed
- docs/DOCLANG_BRIDGE_EXPORT_SPEC.md
- scripts/export_doclang_context.py
- backend/tests/test_doclang_bridge.py
- backend/app/services/doclang_bridge.py
- docs/APPFLOWY_BIDIRECTIONAL_SYNC.md
- scripts/ai_stack_health_check.sh
- backend/tests/test_provider_router.py
- backend/tests/test_chat_cache.py
- backend/tests/test_api_metadata.py
- backend/app/services/chat_cache.py
- backend/app/api/metadata.py
- backend/app/services/provider_router.py
- backend/app/core/settings.py
- .tasker/phases/todo-phase-7-mcp-tasker-d6e779f1.md

## Memory Architecture
- Short-term: active AI/chat session context.
- Long-term: AppFlowy, vault, and canonical docs.
- Episodic: wisdom.md, spool logs, and recent change summaries.

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
- popcorn: 498 entries (0 errors)
- stdout: 2 entries (0 errors)

### Recent Activity
- ℹ️ 2026-06-22T05:30:45  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T05:30:45  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T05:30:40  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T05:30:40  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T05:30:35  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T05:30:35  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T05:30:30  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T05:30:30  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T05:12:35  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T05:12:35  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:54:47  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:54:47  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:38:56  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:38:56  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:22:47  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:22:47  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:18:12  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:18:12  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:02:41  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:02:41  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:02:36  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:02:36  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:02:31  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:02:31  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ✅ 2026-06-22T04:02:29  stdout  [2026-06-22 04:02:29] INFO     ucore — Maintenance job ran: daily_backup success=True
- ✅ 2026-06-22T04:02:29  stdout  [2026-06-22 04:02:29] INFO     ucore — Maintenance job ran: vault_sync success=True
- ℹ️ 2026-06-22T04:02:25  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:02:25  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:02:20  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
- ℹ️ 2026-06-22T04:02:20  popcorn  Ollama status: running, models: ['qwen2.5-coder:7b-instruct-q4_K_M', 'nomic-embed-text:latest', 'qwe
