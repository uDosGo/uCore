# uCore — Unified Development OS

## 1. Project Purpose
uCore is a unified daemon that provides a local-first API server orchestrating AI chat providers, surfaces (UI apps), skills (automation), tools (environment detection), and a knowledge bridge to AppFlowy. It replaces uConnect (frontend), uServer (services), and DevStudio (tools) into one system.

**Repo:** https://github.com/uDosGo/uCore  
**Port:** 8484  
**Stack:** Python 3.14, aiohttp, SQLite, React (Vite + TypeScript)

## 2. Architecture

```
uCore/
├── backend/                    # Python aiohttp server
│   ├── app/
│   │   ├── api/                # HTTP route handlers
│   │   │   ├── routes.py       # All route registrations
│   │   │   ├── skills.py       # GET /api/skills, POST /api/skills/{id}/run
│   │   │   ├── tools.py        # GET /api/tools, GET /api/tools/{id}/status
│   │   │   ├── knowledge.py    # GET /api/knowledge/* (AppFlowy bridge)
│   │   │   └── secret_store_api.py  # GET/POST/DELETE /api/secrets/*
│   │   ├── core/
│   │   │   ├── snackbar.py     # Main server entry, CORS, middleware
│   │   │   └── database.py     # SQLite (surfaces, snacks, containers)
│   │   ├── skills/             # Automation skills
│   │   │   ├── registry.py     # Auto-discovers builtin/ + ~/.ucore/skills/
│   │   │   ├── base.py         # BaseSkill class with metadata
│   │   │   ├── builtin/        # 7 built-in skills
│   │   │   └── templates/      # Skill templates
│   │   ├── tools/              # Environment tool detectors
│   │   │   ├── registry.py     # Auto-discovers tool classes
│   │   │   ├── base.py         # BaseTool class
│   │   │   └── *_tool.py       # 7 detectors (docker, git, python, node, etc.)
│   │   ├── knowledge/          # AppFlowy integration
│   │   │   └── appflowy.py     # Reads AppFlowy SQLite + vector DB
│   │   ├── secret/             # Encrypted secret store
│   │   │   └── store.py        # AES-256-GCM key-value store
│   │   └── services/
│   │       ├── provider_router.py  # AI provider routing (Ollama, OpenRouter)
│   │       ├── surface_manager.py # Surface lifecycle
│   │       └── mcp/            # MCP tool server
│   └── app/__main__.py         # CLI entry point
├── frontend/                   # React TypeScript SPA
│   └── src/surfaces/system/    # System surface (settings, secrets, pages)
└── CONTEXT.md                  # This file
```

## 3. Key API Endpoints

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Health check |
| GET | /api/version | Version info |
| GET | /api/system | System info |
| POST | /api/exec | Run shell command |

### Skills & Tools
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/skills | List all skills (builtin + user) |
| POST | /api/skills/{id}/run | Execute a skill by ID |
| POST | /api/skills/run | Execute by name+params |
| GET | /api/tools | List installed tools with versions |
| GET | /api/tools/{id}/status | Check specific tool |

### Knowledge (AppFlowy)
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/knowledge/workspaces | List AppFlowy workspaces |
| GET | /api/knowledge/documents | List documents |
| GET | /api/knowledge/documents/{id} | Get document metadata |
| GET | /api/knowledge/documents/{id}/content | Get document text |
| GET | /api/knowledge/search?q=... | Semantic search |

### Secret Store
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
| GET | /api/models | List AI providers |
| GET | /api/chat/prompts | List prompt templates |
| POST | /api/chat | Send chat message |
| POST | /api/chat/stream | Stream chat response |

### Others
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | /api/surfaces | List/create surfaces |
| POST | /api/surfaces/{id}/{start,stop,restart,repair,debug} | Surface ops |
| GET | /api/docker/ps | List Docker containers |

## 4. Configuration

### User Files
| File | Purpose |
|------|---------|
| `~/.ucore/skills/` | User-defined skills (auto-discovered) |
| `~/.ucore/secrets.enc` | Encrypted secret store (AES-256-GCM) |
| `~/.ucore/.store_key` | 256-bit secret store key |
| `~/.ucore/data/` | Database, surfaces, containers |
| `~/.config/udos/config.yaml` | uDOS ecosystem config |
| `~/.config/udos/models.yaml` | AI provider configuration |
| `~/.ucore/logs/` | Server logs |

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `OPENROUTER_API_KEY` | OpenRouter AI provider |
| `GITHUB_TOKEN` | GitHub API access |
| `UCORE_PORT` | Server port (default: 8484) |
| `UCORE_DEBUG` | Enable debug mode |
| `UCORE_DATA_DIR` | Data directory override |

## 5. Skills System

Built-in skills live in `backend/app/skills/builtin/`. Each skill extends `BaseSkill`:

```python
from app.skills.base import BaseSkill, SkillMeta, SkillParam

class MySkill(BaseSkill):
    meta = SkillMeta(id="my-skill", name="My Skill", timeout=30)
    async def run(self, **kwargs) -> dict:
        return {"success": True, "result": ...}
```

User skills go in `~/.ucore/skills/` with the same pattern.
Available skills: backup, container_start, container_stop, export, import, surface_repair, surface_restart, hello-world.

## 6. Secret Store

All secrets encrypted with AES-256-GCM. Key derived from 256-bit random key in `~/.ucore/.store_key`. On first load, auto-imports `OPENROUTER_API_KEY` and `GITHUB_TOKEN` from environment. Secrets can be managed through the UI at `/system?tab=secrets`.

## 7. Running & Testing

```bash
# Start server
cd backend && source .venv/bin/activate && python -m app --port 8484 --debug

# Start frontend
cd frontend && npm run dev

# Test health
curl http://localhost:8484/api/health

# List skills
curl http://localhost:8484/api/skills

# List tools
curl http://localhost:8484/api/tools

# List AppFlowy workspaces
curl http://localhost:8484/api/knowledge/workspaces

# List secrets
curl http://localhost:8484/api/secrets
```

## 8. Important Rules for Coding

1. **All imports use absolute paths** — no `from .base import`, use `from app.skills.base import`
2. **All tool/asset detection is async** — tool `.check()` is async, registry uses `await`
3. **Skill registry auto-discovers** both `builtin/` and `~/.ucore/skills/`
4. **Frontend uses `SNACKBAR_API = 'http://localhost:8484'`** for all API calls
5. **Secrets are NEVER logged** — masked values only in API responses
6. **File-splitter destroys imports** — verify type defs and constants exist after splitting
7. **New endpoints go in `backend/app/api/routes.py`** via `register_routes()`

## 9. GitHub Repositories

| Repo | Status |
|------|--------|
| uDosGo/uCore | ✅ Active — consolidated |
| uDosGo/uConnect-archived | 📦 Archived |
| uDosGo/uServer-archived | 📦 Archived |
| uDosGo/uCode1-archived | 📦 Archived |
| uDosGo/uCode2-archived | 📦 Archived |
| uDosGo/uCode3-archived | 📦 Archived |
