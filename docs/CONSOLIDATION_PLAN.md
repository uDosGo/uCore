# Docs Consolidation Plan

> **Superseded for active task tracking by `.tasker.dev-flow.yaml`.**
> **Canonical docs destination: `/Users/fredbook/Code/uDocs`.**
> This file is kept as a historical migration tracker only.

Date: 2026-06-21
Owner: uDosGo maintainers
Status: Milestone A started; docs cleanup in progress

## Objective

Consolidate distributed documentation into uDocs so architecture, API, and operational knowledge have one canonical home.

## Canonical Repository

uDocs path: /Users/fredbook/Code/uDocs

Canonical sections:
- architecture/
- api/
- runbooks/
- guides/
- surfaces/
- runtimes/
- changelog/

## Source Inventory Summary

Discovered and reviewed sources:
- /Users/fredbook/Code/uCore/CONTEXT.md
- /Users/fredbook/Code/uCore/docs/GITHUB_AUTOMATION.md
- /Users/fredbook/Code/uCore/docs/GITHUB_SKILLS_SUMMARY.md
- /Users/fredbook/Code/uCode/README.md
- /Users/fredbook/Code/global-knowledge/README.md
- /Users/fredbook/Code/ARCHIVED/uDosGo.code-workspace

Missing expected sources:
- /Users/fredbook/Code/uConnect (repo missing)
- /Users/fredbook/Code/uServer (repo missing)
- /Users/fredbook/Code/HomeNest/README.md (missing)
- /Users/fredbook/Code/uCore/README.md (missing)

## Keep / Merge / Archive

Keep and normalize into uDocs:
- uCore CONTEXT content for architecture and API baseline
- uCore GitHub automation docs for runbooks and MCP bridge docs
- uCode runtime map for runtime docs

Merge:
- GITHUB_SKILLS_SUMMARY.md into broader automation docs to remove duplication
- Workspace role comments into onboarding guide

Archive or deprecate in-place:
- Legacy repo docs should point to uDocs after migration completion

## Milestone A Deliverables Completed

1. uDocs structure scaffolded.
2. uDocs CONTEXT.md drafted.
3. ADR-001 and ADR-002 drafted.
4. Source inventory and decisions documented in /Users/fredbook/Code/uDocs/migration-source-inventory.md.
5. Configuration consolidation:
   - `frontend/src/config/merged-config.ts`
   - `backend/app/core/config.py`
   - `backend/tests/test_core_config.py` added and passing.

## Next Milestone A Actions

1. Populate architecture/overview.md and api/rest-api.md directly from current uCore routes and handlers.
2. Populate runbooks/development.md from current backend/frontend setup commands.
3. Populate surfaces/ceefax.md and surfaces/developer.md from current uCore surfaces and frontend modules.
4. Populate runtimes/basic.md from uCode runtime docs.
5. Update repository README files to point to uDocs.

## Next Rounds Checklist

### 1. Migration Checklist

- Add canonical uDocs destinations for Snackbar system docs, clipboard buffer docs, and AppFlowy local-first docs.
- Normalize active docs using DocLang-friendly structure: explicit headings, tables, API lists, and stable identifiers.
- Create README pointers in active repos back to uDocs canonical sections.

### 2. Snackbar / System Orchestration

- Keep system snacks, tray menu, clipboard buffer, and spool logging under one orchestration model.
- Add `brain_sync` to overnight maintenance alongside backup and vault sync.
- Track popover/global-shortcut work as part of system surface orchestration, not as isolated menu hacks.

### 3. Memory / Brain Layer

- `brain_sync` refreshes `wisdom.md` from recent project changes.
- `attach_context` injects both `CONTEXT.md` and `wisdom.md`.
- Next iteration should synthesize spool events, recent docs, and AppFlowy local activity into more durable lessons.

### 4. UI View Wiring

- Map backend orchestration features to concrete UI destinations in `frontend/src/SystemPage.tsx`, `frontend/src/UIHubManager*.tsx`, and `frontend/src/surfaces/system/`.
- Add explicit system-page targets for clipboard buffer, knowledge/local AppFlowy tools, and orchestration status.
- Keep page/view wiring aligned to backend route groups so API, tray, and UI surfaces converge.

## Definition of Done for Consolidation

- All active architecture and API docs exist in uDocs.
- Every repo README links to uDocs canonical sections.
- Duplicate detailed docs outside uDocs are archived or replaced with pointers.
- AI context files reference uDocs as source of truth.
- Unified configuration files added and validated on both frontend and backend.

## 2026-06-22 Progress Update

- Completed ingest orchestration wiring (mission/binder/files context) for `/api/knowledge/import` and UServer Drop Ingest UI flow.
- Consolidated server tabs now exclude legacy tabs from active nav while retaining compatibility routing.
- Mission Control global toolbar removed legacy ProseUI-era tabs and now keeps only canonical navigation (`Dashboard`, `Missions`).
- Archived legacy frontend remnants removed from codebase:
	- `frontend/src/surfaces/gridcore/GridCoreSurface.tsx`
	- `frontend/src/pages/S800Labs.tsx`