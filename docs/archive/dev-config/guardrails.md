# uCore Developer Guardrails

## Task Management Rules

### 1. Single Source of Truth
- All active tasks live in `.tasker.dev-flow.yaml`
- No parallel task lists in markdown files
- Archive completed tasks via `spool_maintenance` skill

### 2. Task Lifecycle
```
pending → in-progress → review → done → archived
```
- Update status immediately when starting work
- Mark done only after verification
- Archive happens automatically via spool process

### 3. Priority Classification
- **P0** - Blocking, must complete this round
- **P1** - High priority, next round
- **P2** - Medium priority, backlog
- **backlog** - Low priority, future consideration

### 4. Lane Assignment
- `dev-flow` - Active feature development
- `maintenance` - Bug fixes, refactoring, tech debt
- `infrastructure` - DevOps, MCP servers, deployment
- `research` - Tool evaluation, skill development
- `ui` - Frontend, Developer Surface
- `backend` - API, services, data layer
- `docs` - Documentation, standards, templates

## Skill Development Rules

### 1. MCP Optimization
- Skills that support MCP have `mcp_optimized: true`
- Skills should be idempotent (safe to re-run)
- Use structured return values for programmatic consumption

### 2. Spool Integration
- Skills should log to spool via `spool_event()`
- Include relevant metadata in spool entries
- Use appropriate log levels (INFO, WARNING, ERROR)

### 3. Error Handling
- Return `{"success": False, "error": "..."}` on failure
- Use `validate()` for parameter checking
- Include actionable error messages

## Documentation Rules

### 1. Structured Format
- Use YAML frontmatter for MCP-formatted docs
- Stable headings for AI context extraction
- Link to tasks instead of duplicating

### 2. Archive Policy
- Archive docs older than 30 days with no activity
- Add `archived_date` and `archived_reason` to archived docs
- Move to `docs/archive/` or `.tasker.archived/`

## Configuration Rules

### 1. Settings Hierarchy
- `.env` - Local overrides (not committed)
- `config/*.example.yaml` - Template configs
- `.dev/config.yaml` - Dev defaults
- `backend/app/core/settings.py` - Runtime settings

### 2. Secrets Management
- Never commit secrets
- Use `mcp-secrets` server for secret access
- Reference via environment variables