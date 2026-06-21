# Next Rounds Checklist

Date: 2026-06-21  
Status: Active roadmap scaffold

## 1. DocLang and Knowledge Foundation

- [x] Establish `CONTEXT.md` as the baseline architecture prompt.
- [x] Establish `wisdom.md` as the episodic memory layer.
- [x] Add `brain_sync` and extend `attach_context` to include `wisdom.md`.
- [ ] Define a DocLang bridge export format for AppFlowy, vault, and canonical docs.
- [ ] Add a transform step that produces AI-efficient structured context from selected docs.

## 2. Brain and Memory Architecture

- [x] Add a local `brain_sync` skill to synthesize recent project changes.
- [x] Store synthesized memory in `wisdom.md`.
- [ ] Extend synthesis inputs to include spool events, AppFlowy local activity, and recurring test failures.
- [ ] Add overnight scheduling integration for `brain_sync` after vault sync.
- [ ] Add a dedicated episodic-log folder/runbook for durable correction history.

## 3. Snackbar / System Orchestration

- [x] Restore macOS tray menu.
- [x] Add system snacks API and tray execution path.
- [x] Add clipboard buffer, search, panel, and keyboard controls.
- [ ] Add global shortcut opening for the clipboard panel.
- [ ] Unify overnight maintenance orchestration across backup, vault sync, brain sync, and spool cleanup.
- [ ] Add orchestration status visibility in a system-facing UI view.

## 4. Migration / Consolidation

- [x] Create docs consolidation baseline.
- [x] Add AppFlowy local-first checklist and snacks system spec.
- [ ] Move active Snackbar, clipboard, and AppFlowy operational docs into canonical uDocs destinations.
- [ ] Replace duplicate or legacy docs with canonical pointers.
- [ ] Update repo README entry points to point to uDocs and current runtime surfaces.

## 5. UI View Wiring

Backend/UI wiring targets:

- `frontend/src/SystemPage.tsx`
- `frontend/src/UIHubManager.tsx`
- `frontend/src/UIHubManager_other.tsx`
- `frontend/src/UIHubManager_surfaces.tsx`
- `frontend/src/surfaces/system/`

Next wiring goals:

- [ ] Add a clipboard/system orchestration system page.
- [ ] Add a knowledge-local/AppFlowy tools system page.
- [ ] Add a migration/consolidation dashboard view.
- [ ] Add a maintenance/overnight tasks status view.
- [ ] Keep route naming aligned to backend API groups.

## 6. Immediate Execution Order

1. Add overnight `brain_sync` scheduling and spool-aware synthesis.
2. Wire first system UI pages for clipboard/orchestration visibility.
3. Move canonical docs into uDocs and replace local duplicates with pointers.
4. Add global shortcut support and stronger popover anchoring.
