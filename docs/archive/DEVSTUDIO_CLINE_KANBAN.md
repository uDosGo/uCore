# DevStudio Workflow Consolidation

Date: 2026-06-21  
Status: Active local-first direction

## Goal

Consolidate the Developer UI / DevStudio workflow surface around Cline Kanban as
its visual orchestration engine while keeping task state, guardrails, and
knowledge flows local and inspectable.

## Chosen Architecture

### 1. Visual Workflow Engine

Cline Kanban is the preferred orchestration layer for uCode development because it provides:

- a local board for active development tasks,
- isolated git worktrees per card,
- inline feedback on diffs,
- dependency chaining and automation hooks.

Recommended local launch model:

- command: `npx kanban`
- bind: `127.0.0.1:3484`
- access: localhost only

### 2. Markdown Workflow Substrate

Kanban is not the durable task store.

Durable task state should remain in repo-adjacent Markdown under `.tasker/`, with:

- AppFlowy/local rows as upstream planning input,
- `tasker_sync` as the export bridge,
- Git as the durable audit/history layer.

### 3. Orchestration Layer

uCore provides the surrounding local orchestration:

- `/api/system/workflow` for workflow surface status,
- `/api/system/maintenance` for overnight maintenance chain status,
- `vault_sync`, `brain_sync`, and `daily_backup` for scheduled maintenance.

## Guardrails Against Dev Creep

1. Keep Kanban bound to localhost only.
2. Do not expose the workflow board via public host, tunnel, or broad LAN bind in the default setup.
3. Use ephemeral git worktrees to isolate card execution from the main branch.
4. Treat remote access as opt-in and only through a secure mechanism such as SSH tunnel or Tailscale.
5. Keep task state readable in Markdown so workflow logic is auditable outside the UI.

## Surface Wiring

The first live system-facing workflow surface is:

- `frontend/src/pages/S300WorkflowBuilder.tsx`

It currently presents:

- Cline Kanban engine role and guardrails,
- `.tasker/` board counts,
- overnight maintenance chain visibility,
- next workflow wiring actions.

## Next Steps

1. Add direct task actions in S300 for `tasker_sync`, `vault_sync`, and board refresh.
2. Add task detail views for `.tasker` Markdown cards.
3. Add optional launch/health checks for a local Kanban service.
4. Connect richer DevStudio tabs to the same workflow status model.
