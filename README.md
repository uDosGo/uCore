# uCore — Unified Development OS

[![Python](https://img.shields.io/badge/Python-3.14-blue)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-green)]()
[![Tests](https://img.shields.io/badge/Tests-301%20passing-brightgreen)]()

uCore is a **local-first, AI-powered development daemon** that unifies syntax, automation, and runtime management.

**Port:** 8484 | **Stack:** Python 3.14 + aiohttp + SQLite + React/Vite + TypeScript

## Quick Start

```bash
git clone https://github.com/uDosGo/uCore.git
cd uCore
./scripts/setup.sh

# Start server
launchctl start com.udos.ucore-server

# Start frontend
cd frontend && npm run dev
# → http://localhost:5173

# Verify
curl http://localhost:8484/api/health
```

## Architecture

```
VS Code (Cline) → MCP Bridge → uCore (port 8484)
  ├── Skills (15 built-in) — backup, sync, route, ask vault
  ├── Knowledge — AppFlowy SQLite + vector DB bridge
  ├── Secrets — AES-256-GCM encrypted store
  ├── Chat — AI providers via OpenRouter/Ollama/Gemini
  ├── Surfaces — AssistUI, GridUI, BrowserUI, System, UServer
  ├── TOON Context Optimization — Token-optimized context encoding (30-60% token savings)
  └── Flow-LLM Router — Cost-optimized routing with analytics and visualization

→ Roundtable MCP → parallel Claude/Gemini/OpenRouter execution
```

## Optimized Workflow Features ✅

uCore now includes advanced optimization features to reduce token waste and improve cost efficiency:

### 🎯 TOON Context Optimization ✅
- Converts structured data (JSON, CSV, Markdown) to TOON format for 30-60% token efficiency

### 🛡️ System Workflow Management ✅
- `workflow_guard`: Enforce workflow safety policies and prevent dangerous automation loops
- `workflow_audit`: Audit workflow execution history and detect potential loops or anomalies
- `workflow_pause`: Pause or resume workflow execution to prevent runaway automation
- Caches and compresses API responses, file contents, and build outputs
- Available via MCP tools: `toon_encode`, `toon_stats`, `toon_clear`
- REST API: `/api/toon/encode`, `/api/toon/stats`, `/api/toon/clear`
- Configuration: `config/toon.example.yaml`

### 🧠 Flow-LLM Router ✅
- Smart, cost-optimized routing to the best model for each task
- Detailed analytics showing cost savings, token savings, and latency improvements
- Visualizable routing history for debugging and optimization
- Available via MCP tools: `flow_router_route`, `flow_router_analytics`, `flow_router_history`
- REST API: `/api/flow-router/route`, `/api/flow-router/analytics`, `/api/flow-router/history`
- Configuration: `config/flow-router.example.yaml`

### 🎮 Developer Surface Integration ✅
- Cline Kanban UI shows real-time routing decisions, model selection, and cost savings
- Visual feedback for each agent run with estimated cost and token usage
- Automatic review and PR creation with context-aware feedback
- Analytics dashboard for monitoring cost savings and token efficiency

## Quick Start

1. Start uCore backend: `cd backend && python3 -m app`
2. Start frontend: `cd frontend && npm run dev`
3. Run quick start script: `scripts/start_optimized_workflow.sh`
4. Access Cline Kanban UI at `http://localhost:5173`

## Documentation

Canonical docs live in **[uDocs](https://github.com/uDosGo/uDocs)**:

| Section | Description |
|---------|-------------|
| [Architecture](https://github.com/uDosGo/uDocs/blob/main/architecture/overview.md) | System topology, data flow, security |
| [API Reference](https://github.com/uDosGo/uDocs/blob/main/api/rest-api.md) | All endpoints with examples |
| [Runbooks](https://github.com/uDosGo/uDocs/blob/main/runbooks/development.md) | Setup, deploy, backup, troubleshooting |
| [Surfaces](https://github.com/uDosGo/uDocs/tree/main/surfaces) | AssistUI, Ceefax, GridUI, System, more |
| [Cline Guide](https://github.com/uDosGo/uDocs/blob/main/guides/cline-roundtable-setup.md) | Cline + Roundtable orchestration |
| [Consolidation Plan](docs/CONSOLIDATION_PLAN.md) | Current docs consolidation status |

## Dev Plan

Active development tracked in `.tasker/`:

Single source of truth:

- `.tasker/UNIFIED_DEV_TASK_WORKFLOW.md`

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 4 | 🏗️ In progress | Docs consolidation → uDocs |
| Phase 5 | 📋 Todo | Memory/brain layer upgrade |
| Phase 6 | 📋 Todo | Clipboard + system orchestration |
| Phase 7 | 📋 Todo | MCP + tasker integration |
| Backlog | 📋 Todo | Cline/Roundtable, CLI, provider UI |

## Key Endpoints

```bash
curl http://localhost:8484/api/health          # Health check
curl http://localhost:8484/api/skills          # 15 skills
curl http://localhost:8484/api/tools           # 7 tools
curl http://localhost:8484/api/models          # 4 providers
curl http://localhost:8484/api/secrets         # Encrypted store
curl http://localhost:8484/api/mcp/tools       # 18 MCP tools
curl http://localhost:8484/api/knowledge/workspaces  # AppFlowy
curl http://localhost:8484/api/knowledge/index/status # AppFlowy index coverage

# Import configured vaults into AppFlowy workspaces + local index
python scripts/appflowy_import_workspaces.py --config ~/.ucore/sync_config.yaml

# Map source workspace hints to discovered AppFlowy workspace IDs
python scripts/appflowy_workspace_map.py --config ~/.ucore/sync_config.yaml --write

# Install recurring launchd import job (macOS)
bash scripts/install_appflowy_import_launchd.sh --interval-seconds 1800
```

## Status

- **301 backend tests** — all passing
- **0 TypeScript errors** — clean build
- **15 built-in skills** — auto-discovered
- **4 AI providers** — Ollama, OpenRouter, Claude, Gemini
- **7 surfaces** — AssistUI, GridUI, BrowserUI, System, UServer, Mission Control, Developer

## Configuration

Unified configuration lives in:
- `frontend/src/config/merged-config.ts`
- `backend/app/core/config.py`

See `docs/CONSOLIDATION_PLAN.md` for current consolidation status.

## License

Apache 2.0 — see LICENSE.