# ⚠️ ARCHIVED — React Frontend

**Date:** 2026-06-28  
**Status:** Fully migrated to Vue 3 — all surfaces ported  
**New location:** `frontend-vue/` (active)  
**Archive:** `frontend/archive/` (reference only)

---

## What happened

This React frontend has been **fully migrated** to a **Vue 3 + Pinia + Vite** architecture.

All 12 surfaces are now live in `frontend-vue/`:
- **Dashboard** (Mission Control) — surface hub with cards
- **AssistUI** — AI chat with streaming, agents, models, conversations
- **Developer** — tabbed dev lane (models, agents, kanban, repos, review, skills, workflows, MCP, settings)
- **Server** — operations dashboard (services, logs, budget, runtime agents)
- **Workflow** — mission control, tasks kanban, binder, publish
- **System** — pages, tools, services, variables, secrets, settings
- **SnackMachine** — snacks, workflows, MCP bridge, vault sync, scheduler
- **BrowserUI** — search, bookmark card stacks, research
- **Documentation** — learning hub, guide iframe, API reference
- **UCode/GridCore** — canvas engine (Wave 4)
- **Teletext** — canvas engine (Wave 4)
- **Terminal** — canvas engine (Wave 4)

## Access the new dashboard

```bash
# From repo root (pnpm workspace)
pnpm --filter frontend-vue dev

# Or directly
cd frontend-vue && pnpm run dev
```

The Vue dashboard runs at: **http://localhost:5175**

## Migration status

| Wave | Status | Surfaces |
|------|--------|----------|
| Wave 0 | ✅ Complete | Foundation (router, shell, stores, API, tokens) |
| Wave 1 | ✅ Complete | Dashboard, AssistUI, Developer, Server |
| Wave 2 | ✅ Complete | Workflow, System, SnackMachine, UCode |
| Wave 3 | ✅ Complete | BrowserUI, Documentation, Teletext, Terminal |
| Wave 4 | 🔲 Remaining | Canvas engine, Vitest tests, Storybook, a11y |

## Why archive instead of delete?

The React code is kept for:
1. **Reference** — canvas engine patterns (GridUI grid-algebra) still being ported
2. **History** — git history preserves the full React implementation
3. **Fallback** — can be temporarily restored if critical regression found
