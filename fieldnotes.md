# Fieldnotes — Inquisitive Agent Notebook

Real-time tests, observations, and archived code snippets for future
development reference. Updated at the end of each dev flow round.

## 2026-07-02 — Control Panel + Agentic Execution Pipeline Delivered

### Context
Completed a massive implementation sprint across 2 lanes:
- **Lane A: Catalogue & Assess** — 4 skills for ecosystem audit, health scoring, and enhancement planning
- **Lane B: Agentic Execution** — 6 skills for multi-model consensus, parallel agent dispatch, Cline CLI bridge, unified Dev Mode executor, and GitHub workflow bridge

### What Changed
- 22 files: 12 created, 10 modified
- Backend: aggregation service + API endpoint for unified ecosystem status
- Frontend: Control Panel tab (8 Vue files) replacing 11 scattered panels
- All existing panels now wired to real backend APIs
- Ecosystem audit: 173 items at 99.4% health

### Key Decisions
- Control tab as default Developer Surface landing
- dev-mode-executor (B4) chains: analyze → route → consensus → execute → log
- Hivemind consensus defaults to weighted mode with architect + dev + reviewer models
- Roundtable dispatches specialized agents based on task content keywords
- Cline invoke supports both yolo and interactive modes
- All new skills follow BaseSkill pattern with SkillMeta registration

---

## 2026-07-01 — Backend Debug Note (launchd / snackbar 500)

### Issue
Backend (`python3 -m app`) returns 500 on all endpoints including
`/api/health`. Process managed by `launchd` as `com.udos.ucore-server`
(runs `app.core.snackbar --port 8484 --auto-start`).

### Symptoms
- Starts, initializes (database migration v1, maintenance scheduler with
  6 jobs), then immediately stops with "Maintenance scheduler stopped"
- launchd auto-restarts the dead process, creating a crash/restart loop
- Kill attempts fail because launchd respawns immediately

### Root Cause Suspect
The "Maintenance scheduler stopped" without an error suggests the async
event loop exits prematurely. Check:
1. `app/core/snackbar.py` line ~507 — `web.run_app()` completion
2. Maintenance scheduler signal handling / graceful shutdown path
3. Python 3.12 compatibility — downgraded from 3.14 to fix aiohttp keepalive OSError

### Fix Required
- Stop, debug, and fix the scheduler exit logic
- Update launchd plist if module paths changed (note: package.json says
  `python -m app.main` but actual is `python3 -m app` via `__main__.py`)
- Consider pip-installable snackbar + MCP daemon pattern for macOS

### Workaround
Frontend on localhost:5175 connects to backend — when backend is down,
Pinia stores gracefully degrade with `try/catch` fallback.
Surface registry skill works independently via Python CLI.

---

## 2026-07-01 — GridCore vs GridSmith Audit

### What Exists (GridCore in uCore)
- `frontend-vue/src/grid-core/` — TypeScript library
  - `types.ts` — GridAlgebra, GridCoreState, Plate types
  - `algebra.ts` — Grid calculations
  - `buffer.ts` — Buffer utilities
  - `gridui-canvas.ts` — Canvas renderer
  - `palette.ts` — Color/theme palette
  - `index.ts` — Public API exports
  - `GridCoreUI.vue` — Vue grid component
  - `MultiColumnViewer.vue` — Multi-column prose viewer
  - `ProseViewer.vue` — Prose display
  - `SlideViewer.vue` — Slide navigation
- `backend/app/api/gridsmith_api.py` — Existing REST endpoints:
  - `gridsmith_status` — GET status
  - `gridsmith_tools` — GET available tools
  - `gridsmith_grid_create` — POST create grid
  - `gridsmith_import_basic` — POST import BASIC
  - `gridsmith_latlon_to_ucode` — POST lat/lon → uCode
  - `gridsmith_ucode_to_latlon` — POST uCode → lat/lon

### What the GridSmith Plan Wants (Node.js Agent)
- Node.js CLI agent in `~/Code/uDosGo/uCode/agents/gridsmith/`
- npm-based with `commander`, `chalk`, `ora` for CLI
- External packages: `@udos/gridcore`, `@udos/viewport-renderer`, `@udos/ucore-client`
- MCP server for Cline integration
- Script-based (not Python skill-based)

### Gap Analysis
| Capability | GridCore (Vue/TS) | GridSmith Plan (Node) | Status |
|------------|-------------------|----------------------|--------|
| World creation | ❌ | ✅ CLI command | Missing |
| Grid creation | ✅ API endpoint | ✅ CLI + core | Needs bridge |
| BASIC import | ✅ POST endpoint | ✅ Built-in parser | Good |
| AMOS import | ❌ | ✅ CLI + parser | Missing |
| Cell editing | ❌ | ✅ CLI + core | Missing |
| Layer composition | ❌ | ✅ CLI + core | Missing |
| Pathfinding | ❌ | ✅ CLI + MCP | Missing |
| UVOX export/import | ❌ | ✅ CLI + core | Missing |
| MCP server | ❌ | ✅ Dedicated | Missing |
| uCore agent reg | ❌ | ✅ Script | Missing |
| npm packaging | ❌ | ✅ npm init | Missing |

### Recommendation
The existing GridCore Vue library is a **frontend renderer** — it handles
display, not world management. The GridSmith plan is a **backend agent**
with CLI, MCP, and program import. These are complementary:

1. GridCore Vue = display surfaces + viewer components
2. GridSmith Node = world builder CLI + MCP tools for Cline

Build GridSmith as the agent, wire it to the existing `gridsmith_api.py`
endpoints via `@udos/ucore-client`, and use `GridCoreUI.vue` for the
frontend preview. Don't rebuild what already works in Python.

---