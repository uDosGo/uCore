# 📋 uCore Dev Plan — Tasker Boards

Master source: `/Users/fredbook/Code/uCore/.tasker/`

Canonical workflow: `.tasker/UNIFIED_DEV_TASK_WORKFLOW.md`

Use the unified workflow file as the single plan, handover, and backlog index.

## Boards

| Board | Description |
|-------|-------------|
| `phases/` | Active development phases, organized as Markdown tasks |
| `backlog/` | Future work, ideas, and deferred tasks |

## Task Format

Each task follows the Tasker Markdown schema:

```markdown
# Task Title
- status: todo | in-progress | done | blocked
- source: ucore-dev
- source_id: unique-id
- synced_at: 2026-06-21T...

## Summary
Brief description and context.

## Metadata
- area: phase-4-docs
- priority: high
- depends_on: task-id
```
