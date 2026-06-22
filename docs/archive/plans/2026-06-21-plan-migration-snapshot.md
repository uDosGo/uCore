# Plan Migration Snapshot

Archived: 2026-06-21
Purpose: Preserve pre-consolidation plan content after migration into .tasker/UNIFIED_DEV_TASK_WORKFLOW.md.

## Canonical Active Workflow

- .tasker/UNIFIED_DEV_TASK_WORKFLOW.md

## Snapshot A: HANDOVER.md Remaining Plan and Backlog

### Phase 6: Snackbar / System Orchestration

| Task | Status | Description |
|------|--------|-------------|
| T6.1 Clipboard maintenance | Todo | Wire S310 capture/cleanup to overnight schedule |
| T6.2 Spool log rotation | Todo | Add to maintenance scheduler |
| T6.3 Tray menu state | Todo | Surface state in maintenance model |

### Phase 7: MCP + Tasker Integration

| Task | Status | Description |
|------|--------|-------------|
| T7.1 Clipboard MCP tool | Todo | capture/get/delete via /api/mcp |
| T7.2 Knowledge MCP tools | Todo | workspace list, doc list, search |
| T7.3 Tasker MCP ops | Todo | .tasker/ read/write/list boards |
| T7.4 Auto-sync .tasker/ | Todo | From AppFlowy in maintenance chain |

### Backlog

| Task | Priority | Description |
|------|----------|-------------|
| AI Provider Manager UI | Low | System page for provider config |
| Cline + Roundtable | Medium | Replace Continue, parallel MCP execution |
| uCore CLI (uc) | Low | Terminal control, skill execution |

## Snapshot B: NEXT_ROUNDS_CHECKLIST.md

### Open items at migration time

- Define a DocLang bridge export format for AppFlowy, vault, and canonical docs.
- Add a transform step that produces AI-efficient structured context from selected docs.
- Extend synthesis inputs to include spool events, AppFlowy local activity, and recurring test failures.
- Add a dedicated episodic-log folder/runbook for durable correction history.
- Add global shortcut opening for the clipboard panel.
- Extend overnight orchestration to spool cleanup and richer maintenance tasks.
- Add orchestration status visibility in a system-facing UI view using /api/system/maintenance.
- Move active Snackbar, clipboard, and AppFlowy operational docs into canonical uDocs destinations.
- Replace duplicate or legacy docs with canonical pointers.
- Update repo README entry points to point to uDocs and current runtime surfaces.
- Add a clipboard/system orchestration system page.
- Add a knowledge-local/AppFlowy tools system page.
- Add a migration/consolidation dashboard view.
- Keep route naming aligned to backend API groups.
- Add direct launch/health actions for local Kanban from the UI.
- Add task detail and board actions in S300/DevStudio.

## Snapshot C: HANDOVER_UDOS_LOCAL_MODEL_PERFORMANCE.md Action Plan

1. Keep Qwen Q4 as local default.
2. Route medium and complex tasks to OpenRouter by default.
3. Add SQLite chat cache for extension/tooling path.
4. Keep OpenRouter -> local fallback behavior.
5. Monitor latency and cache hit ratio regularly.

## Notes

- All snapshot items are normalized into UDW-001 through UDW-026.
- New planning should not be added to source snapshot docs.
- Update status only in .tasker/UNIFIED_DEV_TASK_WORKFLOW.md and underlying .tasker phase/backlog files.

## Canonical Link Map

- Developer Surface rename: [frontend/src/surfaces/developer/DeveloperSurface.tsx](../../../frontend/src/surfaces/developer/DeveloperSurface.tsx) and route `/developer`
- Legacy DevStudio alias: `/devstudio` now redirects to `/developer`
- User/System/Installation variables: [backend/app/core/settings.py](../../../backend/app/core/settings.py), [backend/app/api/config_api.py](../../../backend/app/api/config_api.py), and [frontend/src/surfaces/system/SettingsPanel.tsx](../../../frontend/src/surfaces/system/SettingsPanel.tsx)
- Secret Store tab in uServer: [frontend/src/surfaces/system/SecretStorePanel.tsx](../../../frontend/src/surfaces/system/SecretStorePanel.tsx) and [frontend/src/surfaces/userver/UServerSurface.tsx](../../../frontend/src/surfaces/userver/UServerSurface.tsx)
- Encrypted secret store context and `.env` notes: [CONTEXT.md](../../../CONTEXT.md)
- P100-P899 fallback states: [frontend/src/SystemPage.tsx](../../../frontend/src/SystemPage.tsx) and [frontend/src/pages/SystemPageFallback.tsx](../../../frontend/src/pages/SystemPageFallback.tsx)
- Story Builder + shared NestFrame styles: [frontend/src/pages/S101StoryBuilder.tsx](../../../frontend/src/pages/S101StoryBuilder.tsx) and [frontend/src/styles/nestframe.css](../../../frontend/src/styles/nestframe.css)
- Concrete S100+ pages: [frontend/src/pages/S100ToolBuilder.tsx](../../../frontend/src/pages/S100ToolBuilder.tsx), [frontend/src/pages/S300WorkflowBuilder.tsx](../../../frontend/src/pages/S300WorkflowBuilder.tsx), [frontend/src/pages/S310ClipboardOrchestration.tsx](../../../frontend/src/pages/S310ClipboardOrchestration.tsx), [frontend/src/pages/S320KnowledgeTools.tsx](../../../frontend/src/pages/S320KnowledgeTools.tsx), [frontend/src/pages/S330MigrationDashboard.tsx](../../../frontend/src/pages/S330MigrationDashboard.tsx), [frontend/src/pages/S600Learning.tsx](../../../frontend/src/pages/S600Learning.tsx)
- Legacy DevStudio docs URLs are archival-only; current documentation surface entry point is [frontend/src/surfaces/documentation/DocumentationSurface.tsx](../../../frontend/src/surfaces/documentation/DocumentationSurface.tsx)
