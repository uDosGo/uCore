# Task Template for .tasker.dev-flow.yaml

```yaml
- uid: "task.{lane}.{NN}"
  title: "Brief title"
  description: "Full description with context and acceptance criteria"
  status: "pending"
  priority: "high|medium|low|backlog"
  lane: "dev-flow|maintenance|infrastructure|research|ui|backend|docs"
  tags:
    - "p0|p1|p2"
    - "feature|bug|tech-debt|task"
    - "{component}"
  source:
    file: "/path/to/source"
    line: 42
    type: "kanban|copilot|markdown|tasker|snackbar|hivemind"
  created: "2026-06-28T10:00:00Z"
  updated: "2026-06-28T10:00:00Z"
  mcp_optimized: true|false
```

## Required Fields

- `uid` - Unique identifier (format: `task.{lane}.{NN}`)
- `title` - Brief, actionable title
- `status` - One of: pending, in-progress, blocked, review, done
- `priority` - One of: high, medium, low, backlog
- `lane` - One of: dev-flow, maintenance, infrastructure, research, ui, backend, docs

## Optional Fields

- `tags` - Array of classification tags
- `source` - Origin tracking for audit trail
- `mcp_optimized` - Flag for MCP-ready skills