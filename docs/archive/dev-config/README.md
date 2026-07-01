# uCore Developer Standards

**Version:** 1.0.0  
**Status:** Active  
**Purpose:** Dev guardrails, templates, and configuration for uCore development workflow.

---

## Directory Structure

```
.dev/
├── README.md           # This file - dev standards overview
├── templates/          # Dev templates for new tasks, skills, docs
│   ├── task.md         # Task template for .tasker.dev-flow.yaml
│   ├── skill.md        # Skill template for MCP skills
│   ├── doc.md          # Doc template for structured docs
│   ├── default/        # Default reset template
│   │   └── manifest.toml
│   └── fallback/       # OpenRouter fallback template
│       └── openrouter-only.toml
├── scripts/            # Recovery and reset scripts
│   ├── backup-pre-reset.sh
│   ├── reset-to-default.sh
│   └── activate-openrouter-fallback.sh
├── guardrails.md       # Dev workflow guardrails and rules
├── config.yaml         # Dev configuration defaults
└── settings.yaml       # Dev environment settings
```

---

## Recovery System

### Quick Reset Commands

```bash
# Backup current state before reset
~/.ucode/scripts/backup-pre-reset.sh

# Full reset to default template
~/.ucode/scripts/reset-to-default.sh

# Activate OpenRouter fallback (if Hivemind fails)
~/.ucode/scripts/activate-openrouter-fallback.sh
```

### Fallback Chain

1. **Hivemind** (primary) → 2. **Roundtable** → 3. **OpenRouter Direct**

When Hivemind is unavailable, the system automatically falls back to OpenRouter with cost-first routing.

---

## Dev Workflow Guardrails

### Task Management
1. All tasks must be registered in `.tasker.dev-flow.yaml` before work begins
2. Tasks use structured YAML format with uid, title, status, priority, lane, tags
3. Completed tasks are automatically archived by `spool_maintenance` skill
4. Use `devlog_mcp` skill to generate MCP-formatted devlog from completed tasks

### Skill Development
1. Skills extend `BaseSkill` and use `SkillMeta` for metadata
2. Skills are auto-discovered from `backend/app/skills/builtin/`
3. MCP-optimized skills have `mcp_optimized: true` flag
4. Skills should be idempotent and safe to re-run

### Documentation
1. Use structured headings with stable identifiers
2. Link to `.tasker.dev-flow.yaml` instead of carrying parallel task lists
3. Archive old docs to `docs/archive/` with date suffix
4. MCP-formatted docs use YAML frontmatter for AI consumption

---

## Quick Commands

```bash
# Run spool maintenance (archives completed tasks)
python3 -c "from app.skills.builtin.spool_maintenance import SpoolMaintenance; ..."

# Generate MCP devlog
python3 -c "from app.skills.builtin.skill_devlog_mcp import DevlogMCP; ..."

# View active tasks
cat .tasker.dev-flow.yaml | grep -A5 "status: pending"
```

---

## Related Files

- `.tasker.dev-flow.yaml` - Consolidated active task list
- `devlog.mcp.yaml` - MCP-formatted devlog
- `wisdom.md` - Durable lessons and project memory
- `docs/SPOOL_SPEC.md` - Spool system specification
- `docs/DEVMODE_CODE_ANALYSIS_SKILLS.md` - Code analysis skills reference