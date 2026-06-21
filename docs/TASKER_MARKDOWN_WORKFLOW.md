# Markdown-First Workflow Foundation

Date: 2026-06-21  
Status: Active local-first scaffold

## Goal

Close the workflow gap with a lite, human-readable foundation that keeps task
state near code and remains compatible with AppFlowy-driven planning.

## Chosen Direction

Primary fit for current uCore iteration:

1. Tasker-style Markdown tasks as the default local workflow substrate.
2. AppFlowy/local SQLite as the upstream planning source.
3. AI/agent access through uCore skills and MCP, not through a heavy workflow UI first.

## Implemented Foundation

### 1. Task Markdown Bridge

- Service: `backend/app/services/tasker_bridge.py`
- Skill: `backend/app/skills/builtin/tasker_sync.py`
- CLI: `scripts/appflowy_tasker_sync.py`

This bridge:

- runs a read-only SQL query against local AppFlowy SQLite,
- maps rows into readable Markdown task files,
- writes them into a repo-local `.tasker/<board>/` structure.

### 2. Output Shape

Each task is written as plain Markdown with:

- task title
- status
- source metadata
- synced timestamp
- summary/body fields
- extra metadata lines

This keeps tasks readable in Git and easy to inspect without a dedicated UI.

## Example

```bash
cd /Users/fredbook/Code/uCore
python scripts/appflowy_tasker_sync.py \
  --db database \
  --sql "SELECT * FROM row_table LIMIT 20" \
  --tasker-dir .tasker \
  --board inbox \
  --dry-run
```

## Why This Fits Now

- It is Markdown-first and repo-adjacent.
- It works offline against local AppFlowy data.
- It gives future UI views a simple file-backed workflow layer.
- It leaves room for more advanced orchestration later.

## Planned Complements

### Tasker / MCP path

- Map `.tasker/` output to a Tasker-compatible layout where useful.
- Add MCP-facing workflow operations on top of task Markdown files.

### Zrb / Python automation path

- Use Python-native workflow logic for richer automation chains, diagram generation, or task execution.
- Treat this as a complementary automation layer, not the default task representation.

### UI path

- Surface `.tasker/` boards in the S300 Workflow Builder page.
- Show maintenance status and task sync runs together.
- Add AppFlowy-to-Markdown sync controls in system workflow views.
