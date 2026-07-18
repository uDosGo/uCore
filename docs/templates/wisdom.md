# uCore Wisdom Template

Status: Seed template for local project wisdom

## Durable Lessons
- Keep durable project lessons short, actionable, and reusable.
- Prefer architecture decisions and operational gotchas over raw session logs.
- Store personal or machine-specific observations only in the private local wisdom file.

## Memory Architecture
- Public repo: this template and documentation only.
- Private local state: `~/.ucore/memory/uCore/wisdom.md`.
- Runtime integration: `brain_sync` refreshes private wisdom; `attach_context` injects it with `CONTEXT.md` when available.

## Synthesis Inputs
- Recent project changes
- Spool summaries
- Test failure signals
- Episodic correction log entries

## Next Synthesis Targets
- Replace this template with private generated content only in local state.
