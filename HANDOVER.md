# uCore — Handover Note for Copilot

**Date:** 2026-06-21  
**Last commit:** `64b7254` — Rename DevStudio → Developer surface + clean dead paths

---

## What's Changed

### Rename: DevStudio → Developer
- Surface route: `/devstudio/*` → `/developer/*`
- Component: `DevStudioSurface` → `DeveloperSurface`
- Directory: `frontend/src/surfaces/devstudio/` → `frontend/src/surfaces/developer/`
- CSS: `devstudio.css` → `developer.css`
- All CSS class names: `devstudio-*` → `developer-*`
- API agent key: `"devstudio"` kept for backward compat (Mission Control map devstudio → Developer)
- UIHubManager surface entry: `id: 'developer', name: 'Developer'`

### Dead Paths Removed
- `SKILL_PATHS` → `DevStudio/skills/` (doesn't exist — skills are all in builtin/)
- `provider_router.py` → `/Users/fredbook/Code/DevStudio/config/models.yaml` (doesn't exist)
- Guide links to `localhost:5185/DevStudio/guide/*` (dead port/service)
- `~/Code/DevStudio/` refs → moved to `~/Code/uCore/`
- Stale backup files (`*_other.tsx`, `*_surfaces.tsx`, etc.) — deleted
- `.zshrc` aliases pointing to `~/Code/DevStudio/` → updated

### New $ROOT System Variable
- `settings.udos_root` in `backend/app/core/settings.py` — reads `$ROOT` → `$UDOS_CODE` → `~/Code`
- All skills use `settings.udos_root / "uCore"` instead of `Path.home() / "Code/uCore"`
- `.zshrc`: `export ROOT="$HOME/Code"`
- Scripts: `scripts/install-root.sh`, `scripts/root-env.sh`

### Skills = Universal, Snacks = macOS, Spices = Linux
- **Skills:** Python in `backend/app/skills/builtin/` — universal, OS-agnostic
- **Snacks:** macOS-specific shell scripts in `scripts/` (Ollama togglers, appflowy sync)
- **Spices:** Linux-specific tooling (future)

### Ollama Management
- `scripts/ollama-toggler.sh` — start/stop/status
- `scripts/ollama-idle-watchdog.sh` — auto-stop after 15min idle
- `scripts/ollama-auto-start.sh` — on-demand start
- `scripts/ollama-quantize-all.sh` — quantization check
- Crontab: stop 23:00, start 08:00, watchdog every 5min

---

## Remaining Plan

### Phase 6: Snackbar / System Orchestration (IN PROGRESS)
| Task | Status | Description |
|------|--------|-------------|
| T6.1 Clipboard maintenance | Todo | Wire S310 capture/cleanup to overnight schedule |
| T6.2 Spool log rotation | Todo | Add to maintenance scheduler |
| T6.3 Tray menu state | Todo | Surface state in maintenance model |

### Phase 7: MCP + Tasker Integration (TODO)
| Task | Status | Description |
|------|--------|-------------|
| T7.1 Clipboard MCP tool | Todo | capture/get/delete via /api/mcp |
| T7.2 Knowledge MCP tools | Todo | workspace list, doc list, search |
| T7.3 Tasker MCP ops | Todo | .tasker/ read/write/list boards |
| T7.4 Auto-sync .tasker/ | Todo | From AppFlowy in maintenance chain |

### Backlog
| Task | Priority | Description |
|------|----------|-------------|
| AI Provider Manager UI | Low | System page for provider config |
| Cline + Roundtable | Medium | Replace Continue, parallel MCP execution |
| uCore CLI (uc) | Low | Terminal control, skill execution |

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/core/settings.py` | Central settings (udos_root, ports, paths) |
| `backend/app/services/provider_router.py` | AI provider routing (Ollama, OpenRouter) |
| `backend/app/skills/builtin/` | 15 universal Python skills |
| `backend/app/snackbar/server.py` | Main aiohttp server (port 8484) |
| `frontend/src/surfaces/developer/DeveloperSurface.tsx` | Developer surface |
| `frontend/src/main.tsx` | Route definitions |
| `frontend/src/UIHubManager.tsx` | Surface registry |
| `CONTEXT.md` | Full architecture documentation |
| `scripts/` | macOS snacks |
| `.tasker/` | Dev plan board |
