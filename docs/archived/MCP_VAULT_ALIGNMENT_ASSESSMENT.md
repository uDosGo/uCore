# MCP & Vault Alignment Assessment

**Version:** 1.0.0
**Date:** 2026-06-30
**Status:** Active Assessment
**Owner:** Developer Productivity Team

---

## Executive Summary

This document assesses the uCore/snackbar MCP tools for Vault docs and Code dev ops, evaluates the current Vault structure and AppFlowy Snack integration/doc mirror, compiles specs relating to Docs and Vault permissions/Workspaces, and assesses MCP skills including the ability to repair MCP when corruption happens (DESTROY/REBUILD).

**Key Findings:**
- ✅ MCP layer is functional with 22 registered tools + dynamic skill tools
- ✅ DESTROY/REBUILD capability exists via `skill_mcp_self_heal` + `mcp_guardrails`
- ✅ AppFlowy integration is functional (local-first SQLite access)
- ⚠️ Vault path misalignment across 3 files (`vault_file_discovery.py`, `vault-sync.example.yaml`, `sync_config.yaml`)
- ⚠️ Snackbar `server.py` modularization incomplete (25 missing module imports)
- ⚠️ `/api/mcp/diagnostics` endpoint spec'd but not implemented

---

## 1. MCP Tools Assessment

### 1.1 MCP API Surface

The MCP layer lives in three files under `backend/app/api/`:

| File | Role | Lines |
|------|------|-------|
| `mcp.py` | Discovery (`GET /api/mcp/tools`) + Call (`POST /api/mcp/call`) | 338 |
| `mcp_handlers.py` | 22 tool handlers + `dispatch_tool()` router | 640 |
| `mcp_guardrails.py` | Integrity validation (6 checks) | 231 |

### 1.2 Registered MCP Tools (22)

| Domain | Tools | Vault/DevOps Relevance |
|--------|-------|----------------------|
| **Knowledge** | `knowledge_search`, `knowledge_list_workspaces`, `knowledge_list_documents` | ✅ Direct Vault docs access via AppFlowy SQLite |
| **Clipboard** | `clipboard_capture`, `clipboard_get`, `clipboard_delete` | DevOps copy buffer |
| **Tasker** | `tasker_list_boards`, `tasker_read_task`, `tasker_write_task`, `tasker_sync_export` | Code dev ops task management |
| **Flow Router** | `flow_router_route`, `flow_router_analytics`, `flow_router_history` | AI model routing for dev tasks |
| **Gridsmith** | `gridsmith_tools_list`, `gridsmith_create_grid`, `gridsmith_latlon_to_ucode`, `gridsmith_ucode_to_latlon`, `gridsmith_import_basic_program` | Low relevance to docs/vault |
| **TOON** | `toon_encode`, `toon_stats`, `toon_clear` | Token optimization for context |
| **System** | `autostart_health_check` | Service lifecycle |
| **Skills** | Dynamic `skill_*` tools (all discovered skills) | Extensible dev ops |

### 1.3 MCP Services

| Service | Location | Status |
|---------|----------|--------|
| TOON Context Server | `backend/app/mcp/toon/server.py` | ✅ SQLite-backed token-optimization cache (30-60% compression) |
| GitHub MCP | `backend/app/services/mcp/github_client.py`, `github_tools.py` | 🟨 Partial (Phase 5 of upgrade checklist) |

### 1.4 MCP Discovery & Call Flow

```
Client (VS Code/Continue/Cline)
  ↓
GET /api/mcp/tools → handle_mcp_discover()
  Returns: { tools: [...], protocolVersion, serverInfo }
  ↓
POST /api/mcp/call → handle_mcp_call() → dispatch_tool(body)
  Body: { "name": "tool_name", "arguments": {...} }
  ↓
TOOL_HANDLERS[tool_name](arguments, request_id)
  ↓
JSON-RPC 2.0 response
```

---

## 2. Vault Structure Assessment

### 2.1 Confirmed Vault Topology

| Layer | Path | Purpose | Permissions |
|-------|------|---------|-------------|
| **User** | `~/Vault/` | One personal vault (Obsidian-format) | Read/Write |
| **Shared** | `~/Shared/` | Many shared vaults (`uConnect/`, etc.) | Read/Write (permission check) |
| **Global** | `~/Public/global-knowledge/` | Global knowledge bank | Read-only |
| **Public** | `~/Public/doc-sites/` | Published vaults (`DevStudio-docs/`) | Publish-only |
| **Code** | `~/Code/` | Dev repos (uCore, uDocs, uCode, etc.) | Read/Write (dev) |

### 2.2 Actual Filesystem State

```
~/Vault/                    ← User vault (22 items: binders, daily, knowledge, missions, etc.)
~/Shared/                   ← Shared vaults (uConnect/)
~/Public/global-knowledge/  ← Global knowledge bank (33 items)
~/Public/doc-sites/         ← Published sites (DevStudio-docs/)
~/Code/                     ← Dev repos (uCore, uDocs, uCode, etc.)
```

### 2.3 Path Misalignment Analysis

#### Files with CORRECT paths:
- `backend/app/knowledge/appflowy.py` — reads AppFlowy SQLite directly ✅
- `backend/app/knowledge/local_first.py` — local SQLite operations ✅
- `backend/app/api/mcp.py` + `mcp_handlers.py` — MCP tools ✅
- `backend/app/api/mcp_guardrails.py` — integrity validation ✅
- `backend/app/skills/builtin/skill_mcp_self_heal.py` — DESTROY/REBUILD ✅
- `backend/app/menu/snack_registry.py` — snack plugin system ✅

#### Files with MISALIGNED paths (require correction):

| File | Currently References | Should Reference | Status |
|------|---------------------|-----------------|--------|
| `vault_file_discovery.py` | `~/Vaults/User/`, `~/Vaults/Shared/`, `~/Vaults/Global/` | `~/Vault/`, `~/Shared/`, `~/Public/global-knowledge/` | ❌ Fixed |
| `vault-sync.example.yaml` | `~/Vault/Shared`, `~/Vault/Public` | `~/Shared/`, `~/Public/doc-sites/` | ❌ Fixed |
| `af_manager/sync_config.yaml` | `~/Vault/Public`, `~/Vault/Shared` | `~/Shared/`, `~/Public/doc-sites/` | ❌ Fixed |

---

## 3. AppFlowy Snack Integration / Doc Mirror

### 3.1 Knowledge Module (`backend/app/knowledge/`)

| File | Capability | Status |
|------|-----------|--------|
| `appflowy.py` | Direct SQLite read of AppFlowy cloud + local workspaces; `list_workspaces()`, `list_documents()`, `semantic_search()`, `get_document_content()` | ✅ Functional |
| `local_first.py` | Safe read/write SQLite ops with backup + spool logging; `discover_databases()`, `run_query()`, `export_to_vault()` | ✅ Functional |

### 3.2 AF Manager (`backend/app/af_manager/`)

| File | Purpose | Status |
|------|---------|--------|
| `sync.py` (26KB) | Bidirectional sync engine | ✅ Functional |
| `sync_config.yaml` | Maps vault sources to AppFlowy workspaces | ⚠️ Path misalignment (fixed) |
| `cli.py` | CLI for sync operations | ✅ Functional |

### 3.3 Bidirectional Sync Architecture

```
uDocs (canonical) ←→ ~/Vault/CodeDocs
~/Vault/ ←→ uDocs/ingest/user-vault
~/Shared/ ←→ uDocs/ingest/shared
~/Public/doc-sites/ ←→ uDocs/ingest/public
```

**Conflict handling**: `.conflict-left/right.TIMESTAMP.md` copies (no overwrite)

### 3.4 Doc Mirror Status (from `APPFLOWY_SNACKBAR_LOCAL_FIRST_CHECKLIST.md`)

- ✅ SQLite access, query endpoints, export, spool logging
- 🟨 Partial: typed schema mapping, MCP resource wrappers, trigger wiring
- ⬜ Not done: DB triggers, AppFlowy editor plugin, slash commands

### 3.5 MCP Tools for AppFlowy

| Tool | Function | Backend |
|------|----------|---------|
| `knowledge_search` | Semantic search across workspaces | `appflowy.semantic_search()` |
| `knowledge_list_workspaces` | List all AppFlowy workspaces | `appflowy.list_workspaces()` |
| `knowledge_list_documents` | List documents in workspace | `appflowy.list_documents()` |

---

## 4. Specs Compilation: Docs & Vault Permissions/Workspaces

### 4.1 MCP Permissions Policy (`docs/mcp-policy.md`)

- Tool permissions: `always` | `ask` | `never` | `auto`
- Naming convention: `{domain}_{action}_{target}`
- Spool logs must record tool calls with `source = mcp`
- Security: short-lived tokens, least privilege, audit logging
- Health: `/health` endpoint (HTTP transport)
- Versioning: semantic versioning for server

### 4.2 Vault Guardrails (`docs/APPFLOWY_BIDIRECTIONAL_SYNC.md`)

1. Keep secrets out of Public container
2. Keep ADRs and architecture docs canonical in uDocs
3. Use Shared for team-wide operational runbooks and glossary
4. Keep Personal container for drafts and private notes

### 4.3 Workspace Mapping (Corrected)

| Layer | Path | AppFlowy Workspace | Permissions |
|-------|------|-------------------|-------------|
| User | `~/Vault/` | `Global Vault` | Read/Write |
| Shared | `~/Shared/` | `Shared Vault` | Read/Write (permission check) |
| Global | `~/Public/global-knowledge/` | `Global Knowledge` | Read-only |
| Public | `~/Public/doc-sites/` | `Public Vault` | Publish-only |
| Code | `~/Code/` | (dev repos, not synced to AppFlowy) | Read/Write (dev) |

### 4.4 MCP Diagnostics Spec (`docs/mcp-diagnostics.md`)

- Endpoint: `/api/mcp/diagnostics`
- Returns: tool registry snapshot, recent tool calls, health status, remediation path
- Status: Spec only — **now implemented** in `api/mcp.py`

---

## 5. MCP Skills & DESTROY/REBUILD Capability

### 5.1 Self-Heal Skills (`backend/app/skills/self_heal.py`)

| Skill | Purpose | DESTROY/REBUILD? |
|-------|---------|-----------------|
| `recover_port_conflict` | Detect/resolve port conflicts | No |
| `diagnose_system` | System health diagnostics | No |
| `cleanup_resources` | Kill zombie processes | No |
| `restart_backend` | Graceful restart (CLI-triggered) | Partial |
| `reset_database` | Clear DB and rebuild schema | ✅ Yes (DB DESTROY/REBUILD) |

### 5.2 MCP Guardrails (`backend/app/api/mcp_guardrails.py`)

`validate_mcp_integrity()` runs 6 checks:

1. **Syntax validation** — `mcp.py`, `mcp_handlers.py`, `mcp_guardrails.py` parse as valid Python
2. **Exports validation** — Required functions present in `mcp.py`
3. **Handler signatures** — All 22 handlers match expected `(arguments, request_id)` signature
4. **Tool registry completeness** — `TOOL_HANDLERS` covers all 22 required tools
5. **Dispatch tool** — `dispatch_tool()` exists, is callable, accepts `body`
6. **Frontend port consistency** — No stale 5173/5174 ports (must be 5175)

### 5.3 MCP Self-Heal Skill (`backend/app/skills/builtin/skill_mcp_self_heal.py`)

**This is the MCP DESTROY/REBUILD mechanism.** 248-line skill that:

- Runs `validate_mcp_integrity()` to detect issues
- Auto-repairs what it can:
  - **Handler signature mismatches** → normalizes to `(arguments, request_id)`
  - **Missing tools in registry** → adds to `TOOL_HANDLERS` if handler exists
  - **Stale frontend ports** → replaces 5173/5174 with 5175
  - **Orphaned code detection** → identifies dead code after last function
- Flags for manual fix:
  - **Syntax errors** → cannot auto-repair
  - **Missing exports** → requires manual code changes

**Invocation:**
```bash
# Dry run (diagnose only)
curl -X POST http://localhost:8484/api/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"name": "skill_mcp_self_heal", "arguments": {"dry_run": true}}'

# Execute repairs
curl -X POST http://localhost:8484/api/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"name": "skill_mcp_self_heal", "arguments": {"dry_run": false}}'
```

### 5.4 Skill Discovery System

Skills are dynamically discovered via `backend/app/skills/registry.py`:
- Scans `backend/app/skills/builtin/` directory
- Scans `~/.ucore/skills/` directory
- Imports all `.py` files, finds `BaseSkill` subclasses, instantiates them
- Registers in `_registry` dict keyed by `meta.id`

This is why `skill_mcp_self_heal` exists but isn't in `self_heal.py`'s `SKILLS` dict — it's a separate dynamically-discovered skill.

---

## 6. Snackbar Modularization Assessment

### 6.1 Snack Plugin System (Functional)

**Plugin system** (`backend/app/menu/snack_registry.py`):
- `SnackPlugin` ABC with `spec`, `execute()`, `is_available()`
- `SnackSpec` dataclass (id, name, icon, kind, category, actions)
- `SnackRegistry` singleton with register/unregister/get_all/get_by_category
- `update_from_backend()` for dynamic snack loading from API

**Snack template** (`backend/app/snacks/templates/snack_template.py`):
- `BaseSnack` class with `SnackMeta` (pydantic model)
- `SnackParam` for typed parameters
- Version tracking, tags, timeout, confirmation support

**Existing snacks** (`backend/app/snacks/`):
- `dev_mode_snack.py` — start/stop/restart dev servers
- `mission_ops_snack.py` — mission operations
- `spool_monitor_snack.py` — spool monitoring
- `clipboard_snack.py` (in `menu/`) — clipboard buffer

### 6.2 Snackbar Server Gap (`backend/app/snackbar/server.py`)

The snackbar `server.py` was intended as a unified daemon with 25 modular imports:
```python
from server_approval import *    # approval
from server_bbcsdl import *      # bbcsdl
from server_bridge import *      # bridge
from server_ceefax import *      # ceefax
from server_chat import *        # chat
from server_containers import *  # containers
from server_dashboard import *   # dashboard
from server_developer import *   # devstudio
from server_events import *      # events
from server_health import *      # health
from server_identity import *    # identity
from server_ingest import *      # ingest
from server_maintenance import * # maintenance
from server_map import *         # map
from server_mcp import *         # mcp
from server_mission_control import * # mission_control
from server_other import *       # other
from server_pages import *       # pages
from server_peers import *       # peers
from server_process import *     # process
from server_scheduler import *   # scheduler
from server_skills import *      # skills
from server_snacks import *      # snacks
from server_surfaces import *    # surfaces
from server_svg import *         # svg
from server_udos import *        # udos
from server_vault import *       # vault
from server_vibe import *        # vibe
```

**These modules don't exist** — modularization is incomplete. The functionality currently lives in:
- `backend/app/api/mcp*.py` (MCP tools)
- `backend/app/services/` (vault_file_discovery, snackbar_orchestrator, etc.)
- `backend/app/skills/` (skill system)
- `backend/app/snacks/` (snack plugins)

**Recommendation**: The snack plugin system (`snack_registry.py` + `BaseSnack`) is the correct loading mechanism for new snacks. The `snackbar/server.py` should either be:
1. **Completed** — generate the 25 missing modules as thin wrappers around existing services, OR
2. **Deprecated** — formally mark as dead code and remove, since functionality lives elsewhere

### 6.3 Snack Loading Pattern

New snacks follow this pattern:
```python
from app.menu.snack_registry import SnackPlugin, SnackSpec, register_snack

class MySnack(SnackPlugin):
    @property
    def spec(self) -> SnackSpec:
        return SnackSpec(id="my-snack", name="My Snack", ...)

    def execute(self, action=None, **kwargs):
        # Implementation
        pass

def register(menu_delegate=None):
    plugin = MySnack(menu_delegate)
    register_snack(plugin)
    return plugin
```

---

## 7. Library/Index Recommendation

### 7.1 Current Indexing

`vault_file_discovery.py` provides:
- `discover_files()` — scans all vault layers
- `build_index()` — builds JSON index with file metadata
- `apply_filters()` — workspace/binder/mission/tag/search filtering
- Frontmatter parsing for tags, binder, mission metadata

### 7.2 Recommended Consolidation

All vaults/containers should be consolidated under the confirmed topology with a unified library/index:

```yaml
library:
  user:
    path: ~/Vault/
    permissions: read-write
    index: ~/.ucore/indices/user-vault.json

  shared:
    path: ~/Shared/
    permissions: read-write (permission check)
    index: ~/.ucore/indices/shared-vaults.json

  global:
    path: ~/Public/global-knowledge/
    permissions: read-only
    index: ~/.ucore/indices/global-knowledge.json

  public:
    path: ~/Public/doc-sites/
    permissions: publish-only
    index: ~/.ucore/indices/public-sites.json

  code:
    path: ~/Code/
    permissions: read-write (dev)
    index: ~/.ucore/indices/code-repos.json
```

### 7.3 Index Location

```
~/.ucore/indices/
├── user-vault.json
├── shared-vaults.json
├── global-knowledge.json
├── public-sites.json
└── code-repos.json
```

---

## 8. Alignment Actions Taken

| # | Action | File | Status |
|---|--------|------|--------|
| 1 | Fixed `VAULT_PATHS` to match confirmed topology | `backend/app/services/vault_file_discovery.py` | ✅ Done |
| 2 | Aligned container paths to confirmed topology | `config/vault-sync.example.yaml` | ✅ Done |
| 3 | Aligned source paths to confirmed topology | `backend/app/af_manager/sync_config.yaml` | ✅ Done |
| 4 | Implemented `/api/mcp/diagnostics` endpoint | `backend/app/api/mcp.py` | ✅ Done |
| 5 | Created this assessment document | `docs/MCP_VAULT_ALIGNMENT_ASSESSMENT.md` | ✅ Done |

---

## 9. References

- [MCP Setup Guide](./MCP_SETUP.md)
- [MCP Policy](./mcp-policy.md)
- [MCP Diagnostics Spec](./mcp-diagnostics.md)
- [uCode MCP Upgrade Checklist](./uCode_MCP_First_Developer_Tools_Upgrade_Checklist.md)
- [AppFlowy Integration Methods](./APPFLOWY_INTEGRATION_METHODS.md)
- [AppFlowy Bidirectional Sync](./APPFLOWY_BIDIRECTIONAL_SYNC.md)
- [AppFlowy Snackbar Local-First Checklist](./APPFLOWY_SNACKBAR_LOCAL_FIRST_CHECKLIST.md)
- [User Setup: Vault, MCP, Workspaces](./USER_SETUP_VAULT_MCP_WORKSPACES.md)
- [Filepicker Sidebar Spec](./FILEPICKER_SIDEBAR_SPEC.md)
- [Snacks System Spec](./SNACKS_SYSTEM_SPEC.md)

---

**Last Updated:** 2026-06-30T00:11:00+08:00
**Session:** MCP/Vault Alignment Assessment
**Status:** Complete