# Plan: Server/System/Workflow Surface Split

## Issues Found
1. UServerSurface is 1892-line monolithic file with 14 tabs mixing backend ops and admin config
2. WorkflowSurface has mock/static data, needs real API wiring
3. No workflow-specific tasker API endpoint
4. No deduplicated SystemSurface

## Plan
1. **Backend**: Add `/api/workflow/tasks` endpoint filtering `.tasker/workflow/` and `.tasker/gridsmith/`
2. **SystemSurface**: Extract `pages`, `tools`, `secrets`, `settings` tabs from UServerSurface into new top-level `/system` surface
3. **UServerSurface**: Cleaned to 10 tabs (dashboard, ingest, story, services, logs, workflows, budget, agents, snacks)
4. **WorkflowSurface**: Wire up with real API calls, add detail panel, add right-panel editor