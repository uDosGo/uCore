# Fieldnotes — Inquisitive Agent Notebook

Real-time tests, observations, and archived code snippets for future
development reference. Updated at the end of each dev flow round.

---

## 2026-07-01 — Feed System Round

### What We Built

Implemented the unified Feed System — a Pod/Nugget/Seed/Slate/Spool
architecture for ingesting user activity into uCore. Seven new files
across backend MCP, API, services, schema, seeds, and frontend store.

### Key Decisions

- **FeedServer as standalone class**: Not a BaseSkill subclass because
  it manages its own SQLite connection lifecycle. Skills are stateless
  by convention; FeedServer needs persistent Pod access.
- **Lazy singleton in feed_api.py**: Avoids database connection at
  import time; only connects on first request.
- **FeedConsumer pattern**: Keyword-based triggers are placeholders.
  Full AI-powered analysis belongs in the Nugget runtime scripts
  (to be built in future rounds).
- **Seeds as JSON config**: Browser/email/messages paths point to
  real macOS paths. Disabled clipboard by default for privacy.
- **Frontend store mirrors devMode.ts**: Same patterns (API_BASE,
  try/catch fallback) for consistency across all Pinia stores.

### Observations

- SQLite in-memory with `row_factory = sqlite3.Row` gives clean
  dict-accessible rows without ORM overhead. Good for MCP tool output.
- The FeedConsumer `consume_activity()` hook is called from the API
  handler, not from FeedServer methods. This keeps the server
  concerned only with data and the consumer concerned with side effects
  (spool writing, task triggers).
- The `binder_suggestions` query groups by source with `HAVING cnt >= 3`
  which prevents noise from single-activity sources.

### Archived Code Snippets

```python
# feed_server.py — schema bootstrap pattern
if SCHEMA_PATH.exists():
    ddl = SCHEMA_PATH.read_text(encoding="utf-8")
    self._conn.executescript(ddl)
    self._conn.commit()
```

```python
# feed_consumer.py — keyword trigger pattern (placeholder for Nugget AI)
keywords = []
combined = f"{title} {content}".lower()
if any(w in combined for w in ("bug", "crash", "error", "broken")):
    keywords.append("bug-report")
```

### Future Notes

- Nugget runtime scripts (`ingest_browser.py`, `ingest_email.py`,
  `ingest_messages.py`) should read directly from macOS SQLite DBs
  and call `/api/feed/ingest` in batches.
- FeedPanel.vue will need WebSocket support for real-time updates
  (currently poll-based in the store).
- AI binder suggestions should use actual embedding clustering
  rather than simple source-based grouping.
- Consider `processed` flag lifecycle: activities marked processed
  on task link, but what about activities that never get linked?
  Add TTL-based auto-archive (e.g., 90 days per seed config).

---

## Round Completion Checklist

- [x] Stage & commit dev flow changes
- [x] Implement feature (Feed System)
- [x] Bump version patch (4.0.0 → 4.0.1)
- [x] Create feature spec doc
- [x] Archive completed sprint plan
- [x] Update devlog
- [x] Update fieldnotes
- [x] Update .clinerules
- [x] Push to origin

## Legacy Structure Shims (Purge 2026-07-01)

Hidden dot-folders removed from git. Contents moved to `docs/archive/`:

| Legacy Dot-Path | Current Visible Path |
|-----------------|---------------------|
| `.tasker.archived/` | `docs/archive/tasker/` |
| `.episodic/` | `docs/archive/episodic/` |
| `.dev/` | `docs/archive/dev-config/` |
| `.continue/` | `docs/archive/continue-config/` |

Active dot-folders kept (essential):
- `.tasker/` — active tasker items (kanban source of truth)
- `.vscode/` — IDE config
- `.git/` — version control
- `.github/` — CI/CD workflows
- `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/` — tooling caches (.gitignored)

## Legacy External Archives

Previous project snapshots live in `~/Code/Archived/`:
- DevStudio-2026-06-21
- HomeNest-console-git-backup-2026-06-21
- uCode1/2/3/4-2026-06-21
- uConnect-2026-06-21
- uServer-2026-06-21

## Lessons Learned

- Always create the spec doc alongside the code, not after. It forces
  thinking through integration points before writing implementation.
- The `try/except ImportError` lazy wiring pattern in routes.py is
  battle-tested: zero import-time failures across 15+ optional modules.
- Pinia stores should always have fallback paths (try/catch on API calls)
  so the UI degrades gracefully when the backend is unreachable.
- Hidden dot-folders accumulate cruft. Purge them to visible `docs/archive/`
  at the end of each phase so the repo stays clean and navigable.
