# uCore — Unified Development OS

## 1. Project Purpose
uCore is a unified daemon providing a local-first API server orchestrating AI chat providers, surfaces (UI apps), skills (automation), tools (environment detection), knowledge bridge to AppFlowy, and encrypted secret store. Replaces uConnect (frontend), uServer (services), and DevStudio (tools) into one system.

**Repo:** https://github.com/uDosGo/uCore  
**Port:** 8484  
**Stack:** Python 3.14, aiohttp, SQLite, React (Vite + TypeScript)  
**Auto-start:** launchd `com.udos.ucore-server` (boot + crash recovery)  
**Schedules:** Daily backup 3:00 AM, vault sync 4:00 AM, brain sync 4:15 AM via in-process maintenance scheduler

## 2. Architecture

```
uCore/
├── backend/
│   ├── app/
│   │   ├── api/                    # HTTP route handlers
│   │   │   ├── routes.py           # All route registrations
│   │   │   ├── mcp.py              # MCP protocol (18 tools for VS Code)
│   │   │   ├── skills.py           # /api/skills/* — skill execution
│   │   │   ├── tools.py            # /api/tools/* — tool detection
│   │   │   ├── knowledge.py        # /api/knowledge/* — AppFlowy bridge
│   │   │   └── secret_store_api.py # /api/secrets/* — encrypted store
│   │   ├── core/snackbar.py        # Main server, CORS, middleware
│   │   ├── skills/builtin/         # 15 built-in skills
│   │   ├── tools/                  # 7 environment detectors
│   │   ├── knowledge/appflowy.py   # AppFlowy SQLite + vector DB
│   │   ├── secret/store.py         # AES-256-GCM key-value store
│   │   └── services/
│   │       ├── provider_router.py  # AI provider routing
│   │       ├── maintenance_scheduler.py # Overnight job orchestration
│   │       └── surface_manager.py  # Surface lifecycle
│   └── __main__.py
├── frontend/                       # React/TypeScript SPA
│   └── src/surfaces/system/        # System surface (settings, secrets, pages)
└── CONTEXT.md                      # This file
```

## 3. Available Skills (15 total)

| Skill | ID | What It Does | Cost |
|-------|-----|-------------|------|
| **Backup** | `backup` | Backup database, config, secrets (14-day retention) | — |
| **Container Start** | `container_start` | Start a Docker container | — |
| **Container Stop** | `container_stop` | Stop a Docker container | — |
| **Export** | `export` | Export surface configuration | — |
| **Import** | `import` | Import surface configuration | — |
| **Surface Repair** | `surface_repair` | Repair a surface | — |
| **Surface Restart** | `surface_restart` | Restart a surface | — |
| **Hello World** | `hello-world` | Example skill template | — |
| **Ask Vault** | `ask_vault` | Query AppFlowy knowledge base | — |
| **Attach Context** | `attach_context` | Inject CONTEXT.md as AI system prompt | — |
| **Brain Sync** | `brain_sync` | Refresh `wisdom.md` from recent project changes | — |
| **Tasker Sync** | `tasker_sync` | Export AppFlowy/local rows into Markdown-first task files | — |
| **Vault Sync** | `vault_sync` | Run AppFlowy/Vault bidirectional markdown sync | — |
| **Route Task** | `route_task` | Route tasks to optimal AI provider | — |
| **Daily Backup** | `daily_backup` | Scheduled backup (config/database/secrets) | — |

## 3A. Memory Architecture

uCore now follows a three-layer local-first memory model:

| Memory Layer | Storage | Purpose |
|-------------|---------|---------|
| **Short-term** | Active AI/chat session | Immediate task context and working state |
| **Long-term** | AppFlowy, Vault, canonical docs | Durable project knowledge and specifications |
| **Episodic** | `wisdom.md`, spool logs, recent change summaries | What worked, what changed, and lessons learned |

Key files:
- `CONTEXT.md` — architecture and operational baseline
- `wisdom.md` — synthesized project memory refreshed by `brain_sync`
- `docs/CONSOLIDATION_PLAN.md` — migration and canonical-doc execution plan

## 3B. DocLang Principles

All new documentation should be structured for efficient AI ingestion before any future cloud path:

1. Prefer stable headings, explicit tables, and low-ambiguity sections.
2. Keep architecture, runbooks, and checklists split into predictable documents.
3. Favor normalized Markdown that can be transformed into DocLang-style JSON/XML later.
4. Avoid burying operational rules in narrative prose when a checklist or table is clearer.

## 3C. Workflow Foundation

uCore's current workflow direction is Markdown-first and local-first:

1. AppFlowy/local SQLite remains the planning source.
2. `tasker_sync` exports workflow rows into repo-adjacent `.tasker/` Markdown files.
3. Cline Kanban is the preferred visual orchestration layer for DevStudio/uCode work.
4. Richer Python automation can be layered later without replacing the Markdown task substrate.

## 4. Cost Strategy (Task Router)

| Complexity | Provider | Model | Cost | When to Use |
|-----------|----------|-------|------|-------------|
| **Simple** | Ollama | qwen2.5-coder:7b | **$0.00** (local) | Typos, boilerplate, formatting |
| **Medium** | OpenRouter/Codex | o3-mini | **~$0.01/task** | Daily work, features, endpoints |
| **Complex** | OpenRouter/Claude | claude-sonnet-4 | **~$0.15/task** | Security, architecture, concurrency |
| **Large Context** | OpenRouter/Gemini | gemini-2.5-flash | **~$0.02/100K tokens** | Repo-wide refactoring, analysis |

**Strategy:** 15% Ollama, 70% Codex, 5% Claude, 10% Gemini. Always auto-detect from task description.

## 5. MCP Integration (VS Code / Continue)

uCore exposes 18 tools via the Model Context Protocol for IDE integration:

```
VS Code → Continue → MCP Bridge → uCore (port 8484) → Skills + Knowledge
```

**Available MCP tools:**
- 15 skill tools: `skill_backup`, `skill_ask_vault`, `skill_brain_sync`, `skill_tasker_sync`, `skill_vault_sync`, `skill_route_task`, etc.
- 3 knowledge tools: `knowledge_search`, `knowledge_list_workspaces`, `knowledge_list_documents`

**MCP Bridge** (`~/.continue/mcp-udos.py`):
- Python stdio bridge translating MCP JSON-RPC ↔ uCore HTTP API
- Used by **both** Continue and Cline

**Continue 2.0.0** (uses YAML in `.continue/mcpServers/*.yaml`):
```yaml
# .continue/mcpServers/udos.yaml
name: uCore MCP
version: 4.0.0
schema: v1
mcpServers:
  - name: uCore
    command: python3
    args:
      - /Users/fredbook/.continue/mcp-udos.py
    description: uCore MCP — 18 tools + skills + AppFlowy knowledge
    env: {}
```
**Cline** (`~/.cline/mcp_settings.json`):
```json
{
  "mcpServers": {
    "uCore": {
      "command": "python3",
      "args": ["/Users/fredbook/.continue/mcp-udos.py"],
      "disabled": false,
      "alwaysAllow": ["skill_ask_vault", "skill_route_task", "skill_attach_context", "knowledge_search", "knowledge_list_workspaces", "knowledge_list_documents"]
    }
  }
}
```

## 6. Key API Endpoints

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Health check |
| GET | /api/version | Version info |
| GET | /api/system | System info |
| GET | /api/system/maintenance | Overnight scheduler status |
| GET | /api/system/workflow | Workflow surface status and guardrails |
| POST | /api/exec | Run shell command |

### Skills
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/skills | List all 15 skills |
| POST | /api/skills/{id}/run | Execute a skill |
| POST | /api/skills/run | Execute by path/name |

### MCP Protocol
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/mcp/tools | List all 18 MCP tools |
| POST | /api/mcp/call | Call a tool via JSON-RPC |

### Knowledge (AppFlowy)
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/knowledge/workspaces | List AppFlowy workspaces |
| GET | /api/knowledge/documents | List documents |
| GET | /api/knowledge/documents/{id} | Get document metadata |
| GET | /api/knowledge/documents/{id}/content | Get document text |
| GET | /api/knowledge/search?q=... | Semantic search |

### Secret Store (Encrypted)
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/secrets | List stored secrets (masked) |
| GET | /api/secrets/{name} | Get secret value |
| POST | /api/secrets/{name} | Set a secret |
| DELETE | /api/secrets/{name} | Delete a secret |
| GET | /api/secrets/env | List available env vars |
| POST | /api/secrets/import-env | Import from environment |

### AI Chat
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/models | List AI providers (4) |
| GET | /api/chat/prompts | List prompt templates |
| POST | /api/chat | Send chat message |
| POST | /api/chat/stream | Stream chat response |

### Tools & Others
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/tools | List 7 installed tools |
| GET | /api/tools/{id}/status | Check specific tool |
| GET/POST | /api/surfaces | List/create surfaces |
| GET | /api/docker/ps | List Docker containers |

## 7. Configuration

### User Files
| File | Purpose |
|------|---------|
| `~/.ucore/skills/` | User-defined skills (auto-discovered) |
| `~/.ucore/secrets.enc` | Encrypted secret store (AES-256-GCM) |
| `~/.ucore/.store_key` | 256-bit secret store key |
| `~/.ucore/backups/` | Daily backup archives (14-day retention) |
| `~/.ucore/data/` | Database, surfaces, containers |
| `~/.config/udos/config.yaml` | uDOS ecosystem config |
| `~/.config/udos/models.yaml` | AI provider configuration (4 providers) |
| `~/.ucore/logs/` | Server logs |

### Environment Variables
| Variable | Purpose | Currently Set |
|----------|---------|--------------|
| `OPENROUTER_API_KEY` | OpenRouter AI provider | ✅ Imported + encrypted |
| `GITHUB_TOKEN` | GitHub API access | ✅ Imported + encrypted |
| `UCORE_PORT` | Server port (default: 8484) | — |
| `UCORE_DEBUG` | Enable debug mode | ✅ (via launchd) |

## 8. Running & Testing

```bash
# Start server (via launchd auto-start)
launchctl start com.udos.ucore-server

# Or manual
cd backend && source .venv/bin/activate && python -m app --port 8484 --debug

# Start frontend
cd frontend && npm run dev

# Test everything
curl http://localhost:8484/api/health
curl http://localhost:8484/api/skills                  # 15 skills
curl http://localhost:8484/api/tools                   # 7 tools
curl http://localhost:8484/api/models                  # 4 providers
curl http://localhost:8484/api/secrets                 # Secret store
curl http://localhost:8484/api/mcp/tools               # 18 MCP tools
curl http://localhost:8484/api/knowledge/workspaces    # AppFlowy
```

## 9. Important Rules for Coding

1. **All imports use absolute paths** — `from app.skills.base import BaseSkill`
2. **All async** — tool `.check()`, skill `.run()` are awaitable
3. **Skill registry auto-discovers** both `builtin/` and `~/.ucore/skills/`
4. **Frontend uses `SNACKBAR_API = 'http://localhost:8484'`** for all API calls
5. **Secrets are NEVER logged** — masked values only in API responses
6. **New endpoints go in `backend/app/api/routes.py`** via `register_routes()`
7. **File-splitter destroys imports** — verify type defs after splitting
8. **Parameters in skill body** can be flat (`{"task": "..."}`) or `{"params": {"task": "..."}}`

## 10. GitHub Repositories

| Repo | Status |
|------|--------|
| uDosGo/uCore | ✅ Active — consolidated |
| uDosGo/uConnect-archived | 📦 Archived |
| uDosGo/uServer-archived | 📦 Archived |
| uDosGo/uCode1-archived | 📦 Archived |
| uDosGo/uCode2-archived | 📦 Archived |
| uDosGo/uCode3-archived | 📦 Archived |
