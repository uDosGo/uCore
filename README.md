# uCore — Unified Development OS

[![Python](https://img.shields.io/badge/Python-3.12-blue)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-green)]()
[![Tests](https://img.shields.io/badge/Tests-301%20passing-brightgreen)]()

uCore is a **local-first, AI-powered development daemon** that unifies syntax, automation, and runtime management.

**Port:** 8484 | **Stack:** Python 3.12 + aiohttp + SQLite + Vue 3 + TypeScript

## Quick Start

### First Time on macOS (Fresh System)

```bash
curl -fsSL https://raw.githubusercontent.com/uDosGo/uCore/main/scripts/bootstrap.sh | bash
```

This installs Homebrew, Python 3.12, Node.js 22, pnpm, clones uCore, and starts everything.

### Already Have Prerequisites

```bash
git clone https://github.com/uDosGo/uCore.git
cd uCore
./scripts/setup.sh
```

### Verify

```bash
curl http://localhost:8484/api/health
# Look for 🍿 in the macOS menu bar
# Frontend: http://localhost:5175
```

### Uninstall

```bash
./scripts/install.sh --uninstall
```


## Architecture

```
VS Code (Cline) → MCP Bridge → uCore (port 8484)
  ├── Skills (15 built-in) — backup, sync, route, ask vault
  ├── Knowledge — AppFlowy SQLite + vector DB bridge
  ├── Secrets — AES-256-GCM encrypted store
  ├── Chat — AI providers via OpenRouter/Ollama/Gemini
  ├── Surfaces (12) — Dashboard, AssistUI, Server, Developer,
  │                    System, Workflow, SnackMachine, BrowserUI,
  │                    Documentation, Teletext, Terminal, uCode
  ├── Plates — Vault plates, surface templates (Cookiecutter)
  ├── Hivemind — MCP orchestration, template verification, audit
  ├── Distribution — GitHub pull wiring, package management
  ├── TOON Context Optimization — Token-optimized context encoding
  └── Flow-LLM Router — Cost-optimized routing with analytics

→ Roundtable MCP → parallel Claude/Gemini/OpenRouter execution
```

## Repositories

| Repo | Purpose | Location |
|------|---------|----------|
| **uCore** | Development OS daemon (this repo) | `~/Code/uCore` |
| **uCode** | Programming language runtimes (BASIC, AMOS) | `~/Code/uCode` |
| **HomeNest** | Home automation + multimedia runtimes | `~/Code/HomeNest` |
| **uDocs** | Canonical documentation | GitHub |

## Surfaces (12)

| Surface | Route | Description |
|---------|-------|-------------|
| Dashboard | `/` | Main landing, Dev Mode filtering |
| AssistUI | `/assistui` | AI chat assistant |
| Server | `/server` | Server management |
| Developer | `/developer` | Developer tools |
| System | `/system` | System settings |
| Workflow | `/workflow` | Workflow builder |
| SnackMachine | `/snackmachine` | Snack management |
| BrowserUI | `/browserui` | Browser automation |
| Documentation | `/documentation` | Docs viewer |
| Teletext | `/teletext` | Teletext display |
| Terminal | `/terminal` | Terminal emulator |
| uCode | `/ucode` | uCode runtime interface |

## Documentation

Canonical docs live in **[uDocs](https://github.com/uDosGo/uDocs)**:

| Section | Description |
|---------|-------------|
| [Architecture](https://github.com/uDosGo/uDocs/blob/main/architecture/overview.md) | System topology, data flow, security |
| [API Reference](https://github.com/uDosGo/uDocs/blob/main/api/rest-api.md) | All endpoints with examples |
| [Runbooks](https://github.com/uDosGo/uDocs/blob/main/runbooks/development.md) | Setup, deploy, backup, troubleshooting |
| [Surfaces](https://github.com/uDosGo/uDocs/tree/main/surfaces) | All 12 surfaces |
| [Cline Guide](https://github.com/uDosGo/uDocs/blob/main/guides/cline-roundtable-setup.md) | Cline + Roundtable orchestration |

Local docs in `docs/` cover vault plates, USX layout, and system specs.

## Key Endpoints

```bash
curl http://localhost:8484/api/health          # Health check
curl http://localhost:8484/api/skills          # 15 skills
curl http://localhost:8484/api/tools           # 7 tools
curl http://localhost:8484/api/models          # 4 providers
curl http://localhost:8484/api/secrets         # Encrypted store
curl http://localhost:8484/api/mcp/tools       # MCP tools
curl http://localhost:8484/api/knowledge/workspaces  # AppFlowy
```

## Status

- **301 backend tests** — all passing
- **0 TypeScript errors** — clean build
- **15 built-in skills** — auto-discovered
- **4 AI providers** — Ollama, OpenRouter, Claude, Gemini
- **12 surfaces** — Vue 3 + USX layout system
- **Plates system** — Vault plates, surface templates, destroy patterns

## License

Apache 2.0 — see LICENSE.
