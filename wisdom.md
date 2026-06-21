# uCore Wisdom

Date: 2026-06-21T12:11:15Z
Status: Refreshed by brain_sync

## Durable Lessons
- Keep one canonical implementation path per subsystem; remove split-file remnants once a stable abstraction exists.
- Prefer local-first flows for AppFlowy, Snackbar spool, and clipboard workflows so offline operation remains the default.
- Treat the tray menu, clipboard buffer, and system snacks as one orchestration surface, not separate side features.
- Use explicit, structured docs with stable headings, tables, and low ambiguity so they can be transformed into DocLang-style agent context later.

## Recent Change Scan
- backend/tests/test_spool_reader.py
- backend/.pytest_cache/v/cache/lastfailed
- backend/.pytest_cache/v/cache/nodeids
- docs/SPOOL_SPEC.md
- backend/app/api/spool.py
- backend/app/services/spool_reader.py
- backend/app/services/maintenance_scheduler.py
- backend/app/api/routes.py
- backend/app/skills/builtin/backup.py
- backend/app/skills/builtin/brain_sync.py
- .tasker/phases/in-progress-phase-5-memory-brain-a17f3b2d.md
- .tasker/phases/done-phase-4-docs-4f9fe0c7.md
- docs/TASKER_MARKDOWN_WORKFLOW.md
- docs/GITHUB_SKILLS_SUMMARY.md
- docs/GITHUB_AUTOMATION.md
- backend/app/skills/builtin/route_task.py
- .tasker/backlog/todo-cline-orchestration-c901d2e3.md
- .tasker/backlog/todo-ucore-cli-b567d890.md
- .tasker/backlog/todo-ai-provider-manager-a12b34c5.md
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
- stdout: 180 entries (0 errors)
- stderr: 168 entries (0 errors)
- popcorn: 116 entries (0 errors)
- ucore-menu-stderr: 26 entries (0 errors)
- ucore-popcorn-stderr: 8 entries (0 errors)
- ucore-menu: 2 entries (0 errors)

### Recent Activity
- ℹ️ 2026-06-21T12:11:15  ucore-popcorn-stderr  ModuleNotFoundError: No module named 'objc'
- ℹ️ 2026-06-21T12:11:15  ucore-popcorn-stderr      import objc
- ℹ️ 2026-06-21T12:11:15  ucore-popcorn-stderr    File "/Users/fredbook/Code/uCore/backend/app/ui/popcorn.py", line 29, in <module>
- ℹ️ 2026-06-21T12:11:15  ucore-popcorn-stderr  Traceback (most recent call last):
- ℹ️ 2026-06-21T12:11:15  ucore-popcorn-stderr  ModuleNotFoundError: No module named 'objc'
- ℹ️ 2026-06-21T12:11:15  ucore-popcorn-stderr      import objc
- ℹ️ 2026-06-21T12:11:15  ucore-popcorn-stderr    File "/Users/fredbook/Code/uCore/backend/app/ui/popcorn.py", line 29, in <module>
- ℹ️ 2026-06-21T12:11:15  ucore-popcorn-stderr  Traceback (most recent call last):
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr  objc.BadPrototypeError: 'focusClipboardTable:' expects 1 arguments, <function SnackbarMenuDelegate.f
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr      raise objc.BadPrototypeError(
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr    File "/Users/fredbook/Library/Python/3.9/lib/python/site-packages/objc/_transform.py", line 538, i
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr      new_value = transformAttribute(key, value, class_object, protocols)
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr    File "/Users/fredbook/Library/Python/3.9/lib/python/site-packages/objc/_transform.py", line 113, i
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr      class SnackbarMenuDelegate(NSObject):
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr    File "/Users/fredbook/Code/uCore/backend/app/menu/snackbar_menu.py", line 269, in <module>
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr  Traceback (most recent call last):
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr  objc.BadPrototypeError: 'focusClipboardTable:' expects 1 arguments, <function SnackbarMenuDelegate.f
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr      raise objc.BadPrototypeError(
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr    File "/Users/fredbook/Library/Python/3.9/lib/python/site-packages/objc/_transform.py", line 538, i
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr      new_value = transformAttribute(key, value, class_object, protocols)
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr    File "/Users/fredbook/Library/Python/3.9/lib/python/site-packages/objc/_transform.py", line 113, i
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr      class SnackbarMenuDelegate(NSObject):
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr    File "/Users/fredbook/Code/uCore/backend/app/menu/snackbar_menu.py", line 269, in <module>
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr  Traceback (most recent call last):
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr  ModuleNotFoundError: No module named 'objc'
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr      import objc
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr    File "/Users/fredbook/Code/uCore/backend/app/menu/snackbar_menu.py", line 28, in <module>
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr  Traceback (most recent call last):
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr  ModuleNotFoundError: No module named 'objc'
- ℹ️ 2026-06-21T12:11:15  ucore-menu-stderr      import objc
