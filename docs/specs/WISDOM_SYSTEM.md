# Wisdom System

Status: Active local-memory contract

## Purpose

The Wisdom system gives agents durable project context without committing personal or machine-specific learnings to public git.

## Storage Model

| Layer | Path | Git status | Purpose |
|---|---|---|---|
| Context | `CONTEXT.md` | tracked | Public project architecture and working conventions |
| Wisdom template | `docs/templates/wisdom.md` | tracked | Sanitized seed for local installs |
| Fieldnotes template | `docs/templates/fieldnotes.md` | tracked | Sanitized seed for local installs |
| Private wisdom | `~/.ucore/memory/uCore/wisdom.md` | untracked | Generated durable lessons and local synthesis |
| Private fieldnotes | `~/.ucore/memory/uCore/fieldnotes.md` | untracked | Optional developer notebook |
| Legacy local files | `wisdom.md`, `fieldnotes.md` | ignored | Local-only compatibility files if they already exist |

## Runtime Flow

1. `brain_sync` reads existing private wisdom, recent project changes, spool activity, test failure signals, and episodic entries.
2. `brain_sync` writes refreshed wisdom to `~/.ucore/memory/uCore/wisdom.md`.
3. `attach_context` injects `CONTEXT.md` plus private wisdom when available.
4. `backup` includes private wisdom in local backups.
5. `tasker_ingest` appends durable lessons to private wisdom, not to the repository root.

## Fallbacks

Readers prefer private wisdom first, then legacy local `wisdom.md`, then `docs/templates/wisdom.md`.

This lets existing local files keep working while new generated memory no longer appears as public repository churn.

## Fieldnotes Guidance

Fieldnotes are useful as a scratch notebook for observations that have not earned canonical status. They should not be used as a second source of truth. Promote stable material into specs, `CONTEXT.md`, or docs; keep personal notes local.
