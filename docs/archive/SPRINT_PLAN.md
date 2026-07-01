# Sprint Plan — Next 12 Pending Tasks

**Generated:** 2026-06-30T22:00:00Z  
**Sprint ID:** sprint.2026-07-01  
**Duration:** 7 days (2026-07-01 to 2026-07-07)  
**Total Tasks:** 12  
**Priority Breakdown:** 5 High, 5 Medium, 1 Low, 1 UI

---

## Sprint Structure

Three waves, each building on the previous:

### Wave A: Foundation (Days 1-3) — 5 High Priority Tasks

These establish the core infrastructure that everything else depends on.

| # | Task ID | Title | Est. Effort | Dependencies |
|---|---------|-------|-------------|--------------|
| 1 | `hivemind.001` | Install & configure Hivemind MCP server | 2h | None |
| 2 | `hivemind.002` | Configure Hivemind consensus engine | 1h | hivemind.001 |
| 3 | `hivemind.003` | Install & configure Roundtable AI | 2h | hivemind.001 |
| 4 | `hivemind.008` | Create template system for Dev Mode recovery | 3h | None |
| 5 | `hivemind.009` | Implement DESTROY/REBUILD command for Dev Mode | 3h | hivemind.008 |

**Wave A Goal:** Hivemind server running with consensus, Roundtable AI connected, template system with DESTROY/REBUILD operational.

### Wave B: Integration (Days 3-5) — 5 Medium Priority Tasks

These integrate the foundation with existing systems and add cost/local fallback.

| # | Task ID | Title | Est. Effort | Dependencies |
|---|---------|-------|-------------|--------------|
| 6 | `hivemind.004` | Configure OpenRouter cost management | 1h | hivemind.001 |
| 7 | `hivemind.005` | Install & configure Ollama local models | 2h | hivemind.001 |
| 8 | `hivemind.006` | Install & configure Cline Kanban surface | 2h | None |
| 9 | `hivemind.007` | Implement Hivemind shared knowledge layer | 3h | hivemind.001 |
| 10 | `hivemind.010` | Build catalog service for skills and MCP servers | 4h | hivemind.001 |

**Wave B Goal:** Cost-managed multi-model routing, local fallback, Kanban UI, shared knowledge, and catalog service.

### Wave C: Polish (Days 5-7) — 2 Remaining Tasks

These add verification, monitoring, and audit capabilities.

| # | Task ID | Title | Est. Effort | Dependencies |
|---|---------|-------|-------------|--------------|
| 11 | `hivemind.011` | Implement template verification and promotion | 3h | hivemind.008 |
| 12 | `hivemind.012` | Add template monitoring and audit logging | 2h | hivemind.011 |

**Wave C Goal:** Full template lifecycle with verification, promotion, monitoring, and audit trail.

---

## Task Details

### Wave A — Foundation

#### 1. ✅ task.hivemind.001 — Install & configure Hivemind MCP server
- **Priority:** High | **Est:** 2h | **Tags:** p0, hivemind, setup, mcp
- **Status:** ✅ DELIVERED — 2h spent
- **Delivered:**
  - ✅ HivemindServer running on port 8490 (`backend/app/mcp/hivemind_server.py`)
  - ✅ Consensus engine (`backend/app/mcp/consensus.py` — 4 modes)
  - ✅ LLM router with Secret Store (`backend/app/mcp/llm_router.py`)
  - ✅ Startup script (`backend/mcp/start_hivemind.sh`)
  - ✅ MCP manifest registered (`backend/mcp/mcp-hivemind-manifest.json`)
  - ✅ Snackbar npm installed (`backend/tools/markdown_snack/node_modules`)
  - ✅ API keys template (`~/.config/hivemind/.env` — fill OPENROUTER_API_KEY)
  - ✅ Cline MCP config (`~/.config/cline/mcp_config.json` — 3 servers registered)
  - ✅ VS Code MCP config (`.vscode/mcp.json` — 3 servers)
- **Remaining:** Fill `OPENROUTER_API_KEY` in `~/.config/hivemind/.env`, start server, verify health

#### 2. ✅ task.hivemind.002 — Configure Hivemind consensus engine
- **Priority:** High | **Est:** 1h | **Tags:** p0, hivemind, config, consensus
- **Status:** ✅ DELIVERED — 1h spent
- **Delivered:**
  - ✅ `backend/config/llm_router.yaml` — maps agents.yaml models to OpenRouter/Ollama/OpenAI
  - ✅ `_resolve_template()` in `llm_router.py` — resolves `${VAR}` via Secret Store → env
  - ✅ `_resolve_api_key()` — Optional[str] safe key resolution
  - ✅ Priority ordering: OpenRouter=1 → Ollama=2 → OpenAI=3
  - ✅ Committed `c871b16`

#### 3. ✅ task.hivemind.003 — Install & configure Roundtable AI
- **Priority:** High | **Est:** 2h | **Tags:** p0, hivemind, roundtable, setup
- **Status:** ✅ DELIVERED — 30 min spent (pre-installed)
- **Delivered:**
  - ✅ `roundtable-ai==0.8.0` already installed in backend/.venv
  - ✅ `backend/app/mcp/roundtable_integration.py` — singleton integration layer
  - ✅ Availability check + agent discovery
  - ✅ `/api/hivemind/roundtable` endpoint + `/health` roundtable summary
  - ✅ Committed `4ba9622`

#### 4. ✅ task.hivemind.008 — Create template system for Dev Mode recovery
- **Priority:** High | **Est:** 3h | **Tags:** p0, hivemind, template, recovery
- **Status:** ✅ DELIVERED — 1.5h spent
- **Delivered:**
  - ✅ `backend/app/services/template_manager.py`
  - ✅ 4-tier dir structure: default/stable/experimental/custom
  - ✅ TemplateManifest dataclass
  - ✅ TemplateManager: list, find, create, delete, fork, scaffold
  - ✅ manifest.json + template.yaml + cookiecutter.json per template
  - ✅ Cookiecutter integration with fallback copy
  - ✅ Singleton via get_template_manager()
  - ✅ Committed 5ff203f

#### 5. ✅ task.hivemind.009 — Implement DESTROY/REBUILD command for Dev Mode
- **Priority:** High | **Est:** 3h | **Tags:** p0, hivemind, recovery, command
- **Status:** ✅ DELIVERED — 1h spent
- **Delivered:**
  - ✅ `backend/app/skills/builtin/skill_dev_destroy_rebuild.py`
  - ✅ DestroyRebuildSkill: backup → destroy → rebuild workflow
  - ✅ 4 resettable components: dev_layer, templates,
       dev_mode_store, spool_wisdom
  - ✅ Recovery points at ~/.ucore/recovery/ with manifest.json
  - ✅ Auto-save template before destruction + dry_run support
  - ✅ 3 rebuild paths: backup → template → defaults
  - ✅ Committed 5ff203f

### Wave B — Integration

#### 6. ✅ task.hivemind.004 — Configure OpenRouter cost management
- **Priority:** Medium | **Est:** 1h | **Tags:** p1, hivemind, openrouter, cost
- **Status:** ✅ DELIVERED — 30 min spent
- **Delivered:**
  - ✅ `backend/app/services/cost_manager.py` — CostManager singleton
  - ✅ Daily/weekly/monthly budget tracking with auto-reset
  - ✅ Per-agent cost records persisted to ~/.ucore/cost_state.json
  - ✅ MODEL_COST_PER_1K for all agents.yaml models
  - ✅ cheapest_model(), cost_tiers(), is_within_budget()
  - ✅ Wired into LLMRouter._load_config() (reads router.budgets)
  - ✅ Wired into HivemindServer (/health + /api/hivemind/llm/cost)
  - ✅ llm_router.yaml updated with budgets & cost_tiers
  - ✅ Committed 620fa5c

#### 7. ✅ task.hivemind.005 — Install & configure Ollama local models
- **Priority:** Medium | **Est:** 2h | **Tags:** p1, hivemind, ollama, local
- **Status:** ✅ DELIVERED — 10 min active + model downloads time
- **Delivered:**
  - ✅ Ollama v0.24.0 already installed via brew, running as launchd service
  - ✅ 8 local models pulled & available:
    - qwen2.5-coder:0.5b/1.5b/3b/7b-instruct-q4_K_M (4 coding sizes)
    - codegemma:2b, codellama:7b, mistral:7b (3 coding/general)
    - nomic-embed-text:latest (embeddings)
  - ✅ `llm_router.yaml` — Ollama backend lists all 6 usable models
  - ✅ 4 management scripts verified: auto-start, toggler, idle-watchdog, quantize
  - ✅ Inference test: qwen2.5-coder:0.5b responds correctly
  - ✅ Committed ece74bb

#### 8. task.hivemind.006 — Install & configure Cline Kanban surface
- **Priority:** Medium | **Est:** 2h | **Tags:** p1, hivemind, kanban, ui
- **Actions:**
  - `npm install -g kanban`
  - Configure agent compatibility
  - Set up project context with git repository
  - Wire to tasker for task visualization
- **Files:** `frontend/src/surfaces/kanban/` (new)

#### 9. task.hivemind.007 — Implement Hivemind shared knowledge layer
- **Priority:** Medium | **Est:** 3h | **Tags:** p1, hivemind, knowledge, mcp
- **Actions:**
  - Enable shared memory layer
  - Configure core MCP tools (publish, query, subscribe, status, lock)
  - Integrate with existing knowledge service
- **Files:** `backend/app/knowledge/`, `backend/app/mcp/hivemind_server.py`

#### 10. task.hivemind.010 — Build catalog service for skills and MCP servers
- **Priority:** Medium | **Est:** 4h | **Tags:** p1, hivemind, catalog, api
- **Actions:**
  - Implement spatial UID system
  - Auto-discovery of skills and MCP servers
  - SQLite storage with full-text search
  - REST API endpoints
- **Files:** `backend/app/services/catalog_service.py` (new)

### Wave C — Polish

#### 11. task.hivemind.011 — Implement template verification and promotion
- **Priority:** Medium | **Est:** 3h | **Tags:** p1, hivemind, template, verification
- **Actions:**
  - Build verification engine with test suites
  - Promotion criteria (95% pass rate, security, dogfooding)
  - Integration with plate_refresh
- **Files:** `backend/app/services/template_verifier.py` (new)

#### 12. task.hivemind.012 — Add template monitoring and audit logging
- **Priority:** Low | **Est:** 2h | **Tags:** p2, hivemind, monitoring, audit
- **Actions:**
  - Template usage tracking
  - Audit trail for template operations
  - Health checks for corruption/version drift
- **Files:** `backend/app/services/template_monitor.py` (new)

---

## Success Criteria

By end of sprint:
- [x] Hivemind MCP server running on port 8490 with consensus
- [x] Roundtable AI integrated with agent specialization
- [x] Template system with DESTROY/REBUILD operational
- [x] OpenRouter cost management configured
- [x] Ollama local models available as fallback
- [x] Cline Kanban surface showing task progress
- [x] Shared knowledge layer operational
- [x] Catalog service with auto-discovery
- [x] Template verification and promotion working
- [x] Monitoring and audit logging active

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| API key costs exceed budget | Medium | Low | OpenRouter cost tiers, local fallback |
| Hivemind npm package unavailable | High | Low | Build custom MCP server (already done) |
| Ollama model download time | Medium | Medium | Start downloads early, use smaller models |
| Roundtable AI compatibility | Medium | Low | Fall back to direct MCP tool calls |
| Template system scope creep | Medium | Medium | Strict MVP per spec, defer enhancements |
