# uCore — Context

## What This Is

uCore is the unified backend daemon + Vue 3 frontend for the uDos platform. It provides:

- macOS menu bar tray with snack plugins
- REST API on port 8484
- MCP server bridge for AI tool integration
- Vue 3 frontend at http://localhost:5175
- DESTROY/REBUILD plate system for component recovery

## Repository Structure (After Modularization)

```
uCore/
├── backend/
│   ├── app/
│   │   ├── api/          # REST API routes
│   │   ├── clipboard/    # macOS clipboard watcher
│   │   ├── core/         # Settings, database, logging
│   │   ├── mcp/          # Hivemind MCP server + consensus
│   │   ├── menu/         # macOS menu bar + tray snacks
│   │   ├── secret/       # AES-256-GCM secret store
│   │   ├── services/     # uCore-specific services
│   │   ├── snackbar/     # Modular snackbar server
│   │   ├── surfaces/     # uCode surface definitions
│   │   └── ...
├── frontend-vue/         # Vue 3 + Pinia + Vite
├── plates/               # DESTROY/REBUILD blueprints
├── vendor/               # Distribution sources
└── docs/                 # Active specs & audits
```

## Extracted Pip Packages

| Package | GitHub | Purpose |
|---|---|---|
| snackmachine | uDosGo/snackmachine | Snack registry, scheduler, spool, MCP knowledge conduit |
| udos-budget | uDosGo/udos-budget | Spending limits with circuit breaker |
| udos-agents | uDosGo/udos-agents | Task-to-agent routing |
| udos-identity | uDosGo/udos-identity | UDos unique identity system |

## Open Source Replacements

| Old | New | Why |
|---|---|---|
| provider_router.py (632 lines) | LiteLLM | Multi-provider LLM routing, 100+ providers |
| Hivemind agent execution | LangGraph | Multi-agent orchestration |
| Playwright MCP server | Community MCP server | Dev tool, not core |

## Key Files

- `backend/pyproject.toml` — Python dependencies
- `backend/app/snackbar/server.py` — Modular route loader
- `frontend-vue/src/skills/organisms/GlobalToolbar.vue` — Unified toolbar
- `vendor/sources.yaml` — Distribution source definitions
- `docs/PLATES_SYSTEM_SPEC.md` — DESTROY/REBUILD protocol
- `docs/VAULT_PLATES_AND_DESTROY_SPEC.md` — Vault plate system

## Data

All mutable data lives in `~/.ucore/`:
- `~/.ucore/indices/library.db` — FTS5 search index
- `~/.ucore/knowledge/shared.db` — Multi-agent memory
- `~/.ucore/logs/` — Spool files
- `~/.ucore/secrets.enc` — Encrypted secrets