# uCore Wisdom

Date: 2026-06-21
Status: Bootstrapped local project memory

## Durable Lessons

- Keep one canonical implementation path per subsystem; remove split-file remnants once a stable abstraction exists.
- Prefer local-first flows for AppFlowy, Snackbar spool, and clipboard workflows so offline operation remains the default.
- Treat the tray menu, clipboard buffer, and system snacks as one orchestration surface, not separate side features.
- Use explicit, structured docs with stable headings, tables, and low ambiguity so they can be transformed into DocLang-style agent context later.

## Active Patterns

- `CONTEXT.md` is the main architecture baseline.
- `wisdom.md` is the episodic/project-memory layer synthesized from recent work.
- AppFlowy local access lives behind `/api/knowledge/local/*`.
- Snackbar clipboard history lives behind `/api/snacks/clipboard*`.

## Next Synthesis Targets

- Migration checklist phases for docs consolidation, UI view wiring, and snackbar/system orchestration.
- Reusable DocLang bridge format for vault and AppFlowy documents.
- Overnight memory synthesis from recent code/docs/test changes into concise lessons learned.
