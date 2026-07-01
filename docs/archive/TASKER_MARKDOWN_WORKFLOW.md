> **SUPERSEDED** — See `.tasker.dev-flow.yaml` and `.dev/` for current workflow.

# Markdown-First Workflow Foundation (Archived)

Date: 2026-06-21  
Status: **SUPERSEDED** — All tasks migrated to `.tasker.dev-flow.yaml`

## Migration Notice

This workflow specification has been superseded by the consolidated task system:

- **Active tasks:** `.tasker.dev-flow.yaml` (25 tasks)
- **Dev Mode templates:** `.dev/templates/`
- **Recovery scripts:** `.dev/scripts/`

All UDW-001 through UDW-034 tasks are archived in `.tasker.archived/`.
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
