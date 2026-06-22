# Phase 8: UI Refinement — Knowledge & Workflow Integration
- status: done
- source: ucore-dev
- source_id: phase-8
- synced_at: 2026-06-22T14:00:00Z
- completed: 2026-06-22T14:00:00Z

## Summary
Complete S320 Knowledge Tools UI, add migration dashboard, wire board actions in S300, and implement task detail panels. Consolidate workflow orchestration visibility with AppFlowy integration.

## Metadata
- area: ux
- priority: high
- depends_on: phase-7, UDW-024-026 (Cline CLI, Firewatch, AppFlowy toolchain)
- orchestrator: Cline + Roundtable (parallel UI implementation)

## Sub-tasks

### T8.1: S320 Knowledge Tools Completion (UDW-020)
- status: done
- **Completed**: Tabbed interface with 4 tabs (Workspaces, LocalDB, Coverage, Actions)
  - Workspace browser and document list (existing) ✅
  - Document detail drawer with preview ✅
  - Local AppFlowy SQLite DB browser with SQL query editor ✅
  - Index coverage metrics per source with progress bars ✅
  - Action buttons: Vault Sync, AppFlowy Import ✅
- **UI Components**:
  - DocumentDetailDrawer (inline in S320)
  - LocalDBBrowser (LocalDB tab)
  - KnowledgeToolbar (Actions tab)
- **Endpoints wired**:
  - `GET /api/knowledge/workspaces` ✅
  - `GET /api/knowledge/documents` ✅
  - `GET /api/knowledge/documents/{id}/content` ✅
  - `GET /api/knowledge/search` ✅
  - `GET /api/knowledge/local/databases` ✅
  - `POST /api/knowledge/local/query` ✅
  - `GET /api/knowledge/index/status` ✅
  - `POST /api/knowledge/import` ✅
  - `POST /api/skills/vault_sync/run` ✅

### T8.2: Migration & Consolidation Dashboard (UDW-021)
- status: done
- **Completed**: S330 migration dashboard with full metrics and checklist
  - New page: `/s330` ✅
  - Import job progress tracker ✅
  - Per-source index coverage with visual progress bars ✅
  - Consolidation checklist with 12 items (4 docs, 3 repo, 4 ui, 1 integration) ✅
  - Checkbox state management for checklist ✅
  - Category tags and progress tracking ✅
- **Routes registered**: 
  - Added to main.tsx pageMap ✅
  - Added to USystemSurface S_PAGES array ✅
  - Added to SystemToolsSurface tools list ✅

### T8.3: Board Launch & Health Actions (UDW-022)
- status: done
- **Completed**: S300 board action handlers
  - Board list now displays as interactive cards ✅
  - "View" button opens board file in file explorer ✅
  - "Health" button runs simulated health check ✅
  - "Launch Kanban" button shows command to run ✅
  - Refreshable board status display ✅

### T8.4: Task Detail & Board Actions (UDW-023)
- status: done
- **Completed**: Reusable TaskDetailDrawer component
  - Created TaskDetailDrawer.tsx with full CRUD UI ✅
  - Full task metadata editing (title, status, priority, board, assignee, date) ✅
  - Description editor with markdown support ✅
  - Status dropdown (todo, in-progress, done, blocked) ✅
  - Priority selector (low, medium, high, critical) ✅
  - Date picker for due dates ✅
  - Tag display ✅
  - Save/Cancel buttons with backend API integration ✅
  - Read-only mode support ✅
  - Slide-in animation ✅

## Execution Order

1. **T8.1**: Complete S320 by adding detail drawer, DB browser, action buttons
2. **T8.2**: Build S330 migration dashboard (depends on S320 data)
3. **T8.3**: Wire S300 board actions (launch Kanban, health check)
4. **T8.4**: Implement task detail drawer and status management

## Testing Strategy

- **Unit Tests**: TaskDetailDrawer component with mock task data
- **Integration Tests**: S320 → AppFlowy → detail drawer flow
- **E2E Tests** (via Cline CLI + Firewatch):
  - Navigate to S320 → select workspace → open document → edit metadata
  - Launch board from S300 → validate board health → navigate to task
  - Import AppFlowy vault → watch progress on S330 → verify index coverage

## Definition of Done

- ✅ S320 fully featured (browse, detail, import, sync)
- ✅ S330 migration dashboard live with coverage metrics
- ✅ S300 board actions wired (launch, health, task detail)
- ✅ Developer surface wired to task context via query params
- ✅ All workflows testable via Cline CLI + Firewatch
- ✅ Spool logs capture all import/sync events
