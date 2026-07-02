# 🚀 Continue Kick-off — Phases 0–1: Test Coverage

**Context:** uCore is a unified daemon (Python 3.12/aiohttp + React/TypeScript) serving as a local-first API development OS. Full architecture in `CONTEXT.md`.

---

## Current State

### ✅ Existing Tests (13 test files)
| File | Type | What It Covers |
|------|------|----------------|
| `test_health.py` | Smoke | Settings, logging, app creation imports |
| `test_api_containers.py` | Integration | CRUD lifecycle + start/stop/logs/delete |
| `test_api_surfaces.py` | Integration | CRUD lifecycle + start/stop |
| `test_api_snacks.py` | Integration | Queue/deliver/fail/retry/history/clear |
| `test_api_clipboard.py` | Integration | Save/list/search/pin/delete/capture/cleanup |
| `test_api_knowledge_local.py` | Integration | Local DB tables/query/write/rejection |
| `test_snackbar_orchestrator.py` | Unit | Queue/priority/deliver/fail/retry/persistence |
| `test_surface_manager.py` | Unit | Surface lifecycle |
| `test_container_manager.py` | Unit | Container lifecycle |
| `test_workflow_status.py` | Unit | Board scanning + guardrails |
| `test_maintenance_scheduler.py` | Unit | Job order + vault sync skip |
| `test_skills_memory.py` | Unit | AttachContext + BrainSync |
| `test_tasker_sync.py` | Unit | Tasker export |

### ❌ Missing Test Coverage (gaps to fill)

| Route / Handler | File | Priority |
|-----------------|------|----------|
| `GET /api/skills` | `api/skills.py` `handle_list_skills` | **HIGH** |
| `POST /api/skills/{id}/run` | `api/skills.py` `handle_run_skill` | **HIGH** |
| `POST /api/skills/run` | `api/skills.py` `handle_run_named_skill` | **HIGH** |
| `GET /api/tools` | `api/tools.py` `handle_list_tools` | **HIGH** |
| `GET /api/tools/{id}/status` | `api/tools.py` `handle_tool_status` | **HIGH** |
| `GET /api/mcp/tools` | `api/mcp.py` `handle_mcp_discover` | **HIGH** |
| `POST /api/mcp/call` | `api/mcp.py` `handle_mcp_call` | **HIGH** |
| `GET /api/secrets` | `api/secret_store_api.py` `handle_list_secrets` | **MEDIUM** |
| `GET /api/secrets/{name}` | `api/secret_store_api.py` `handle_get_secret` | **MEDIUM** |
| `POST /api/secrets/{name}` | `api/secret_store_api.py` `handle_set_secret` | **MEDIUM** |
| `DELETE /api/secrets/{name}` | `api/secret_store_api.py` `handle_delete_secret` | **MEDIUM** |
| `GET /api/secrets/env` | `api/secret_store_api.py` `handle_list_env_vars` | **LOW** |
| `POST /api/secrets/import-env` | `api/secret_store_api.py` `handle_import_from_env` | **LOW** |
| `GET /api/models` | `api/chat.py` `handle_models` | **MEDIUM** |
| `GET /api/chat/prompts` | `api/chat.py` `handle_chat_prompts` | **LOW** |
| `POST /api/chat` | `api/chat.py` `handle_chat` | **MEDIUM** |
| `GET /api/system` | `api/metadata.py` `system_info_handler` | **HIGH** |
| `GET /api/system/maintenance` | `api/metadata.py` `maintenance_status_handler` | **MEDIUM** |
| `GET /api/system/workflow` | `api/metadata.py` `workflow_status_handler` | **MEDIUM** |
| `POST /api/exec` | `api/exec.py` `handle_exec` | **HIGH** |
| `GET /api/docker/ps` | `api/docker.py` `handle_docker_ps` | **LOW** |
| `GET /api/knowledge/workspaces` | `api/knowledge.py` `handle_list_workspaces` | **MEDIUM** |
| `GET /api/knowledge/documents` | `api/knowledge.py` `handle_list_documents` | **MEDIUM** |
| `GET /api/knowledge/documents/{id}` | `api/knowledge.py` `handle_get_document` | **MEDIUM** |
| `GET /api/knowledge/documents/{id}/content` | `api/knowledge.py` `handle_get_document_content` | **MEDIUM** |
| `GET /api/knowledge/search` | `api/knowledge.py` `handle_search` | **MEDIUM** |
| `GET /api/knowledge/local/databases` | `api/knowledge.py` `handle_local_databases` | **LOW** |
| `GET /api/knowledge/local/tables` | `api/knowledge.py` `handle_local_tables` | **LOW** |
| `POST /api/knowledge/local/export` | `api/knowledge.py` `handle_local_export` | **LOW** |
| `GET /api/surfaces` (list) | `api/surfaces.py` partial | already tested |
| `GET /api/surfaces/{id}` | `api/surfaces.py` partial | already tested |
| `DELETE /api/surfaces/{id}` | `api/surfaces.py` partial | already tested |
| `POST /api/surfaces/{id}/start` | `api/surfaces.py` partial | already tested |
| `POST /api/surfaces/{id}/stop` | `api/surfaces.py` partial | already tested |
| Containers CRUD | `api/containers.py` | already tested |
| Snacks CRUD | `api/snacks.py` | already tested |
| Clipboard | `api/snacks.py` | already tested |

### Missing Unit Tests (Services)
| Service / Module | File | Priority |
|-----------------|------|----------|
| `provider_router.py` | services/ | **HIGH** |
| `surface_manager.py` surfaces/list/detail | services/ (partial coverage) | **MEDIUM** |
| `container_manager.py` error paths | services/ (partial coverage) | **MEDIUM** |
| `secret/store.py` | secret/ | **MEDIUM** |
| `mcp/github_tools.py` | services/mcp/ | **LOW** |
| `mcp/github_client.py` | services/mcp/ | **LOW** |

### Missing Skill Tests
| Skill | File | Priority |
|-------|------|----------|
| `hello-world` | skills/builtin/ | **LOW** |
| `backup` | skills/builtin/ | **MEDIUM** |
| `daily_backup` | skills/builtin/ | **LOW** |
| `container_start` | skills/builtin/ | **MEDIUM** |
| `container_stop` | skills/builtin/ | **MEDIUM** |
| `surface_repair` | skills/builtin/ | **MEDIUM** |
| `surface_restart` | skills/builtin/ | **MEDIUM** |
| `export` | skills/builtin/ | **LOW** |
| `import` | skills/builtin/ | **LOW** |
| `route_task` | skills/builtin/ | **HIGH** |
| `vault_sync` | skills/builtin/ | **MEDIUM** |
| `tasker_sync` | skills/builtin/ | **MEDIUM** |
| `ask_vault` | skills/builtin/ | **MEDIUM** |
| `brain_sync` | skills/builtin/ | partially tested |
| `attach_context` | skills/builtin/ | partially tested |

### Frontend
| Surface | File | Priority |
|---------|------|----------|
| DevStudio | `surfaces/devstudio/` | **LOW** |
| System | `surfaces/system/` | **LOW** |
| ProseUI | `surfaces/proseui/` | **LOW** |
| GridUI | `surfaces/gridui/` | **LOW** |
| AssistUI | `surfaces/assistui/` | **LOW** |
| MissionControl | `surfaces/missioncontrol/` | **LOW** |
| BrowserUI | `surfaces/browserui/` | **LOW** |
| GridCore | `surfaces/gridcore/` | **LOW** |
| UServer | `surfaces/userver/` | **LOW** |

---

## Phase 0 — Foundation ✅ COMPLETE

**Status:** 168 tests passing (79 → 168, +89 new tests)
**New files created:** 9 (skills, tools, mcp, secrets, metadata, exec, chat, docker, knowledge_remote)
**Existing files improved:** 4 (containers + surfaces + snacks + clipboard) — added 30+ edge case tests

## Phase 1 — Full Coverage (NOW)

#### 1. `backend/tests/test_api_skills.py`
- `GET /api/skills` → returns 200 + skill list + count
- `POST /api/skills/{id}/run` → returns 202 + job status (use hello-world skill)
- `POST /api/skills/run` → returns 200 + results (by path/name)
- `POST /api/skills/{invalid}/run` → returns 404
- `POST /api/skills/run` with invalid body → returns 400

#### 2. `backend/tests/test_api_tools.py`
- `GET /api/tools` → returns 200 + tool list
- `GET /api/tools/{id}/status` → returns 200 + tool status
- `GET /api/tools/{invalid}/status` → returns 404

#### 3. `backend/tests/test_api_mcp.py`
- `GET /api/mcp/tools` → returns 200 + 18 MCP tool descriptors
- `POST /api/mcp/call` → returns 200 + result
- `POST /api/mcp/call` with unknown tool → returns 404
- `POST /api/mcp/call` with invalid params → returns 400

#### 4. `backend/tests/test_api_secrets.py`
- `GET /api/secrets` → returns 200 + empty list
- `POST /api/secrets/key` → returns 200 + stored
- `GET /api/secrets/key` → returns 200 + value
- `DELETE /api/secrets/key` → returns 200 + deleted
- `GET /api/secrets/{unknown}` → returns 404
- `DELETE /api/secrets/{unknown}` → returns 404
- `GET /api/secrets/env` → returns 200
- `POST /api/secrets/import-env` → returns 200

#### 5. `backend/tests/test_api_metadata.py`
- `GET /api/system` → returns 200 + system info
- `GET /api/system/maintenance` → returns 200 + status
- `GET /api/system/workflow` → returns 200 + workflow info

#### 6. `backend/tests/test_api_exec.py`
- `POST /api/exec` with `echo hello` → returns 200 + output
- `POST /api/exec` without cmd → returns 400

#### 7. `backend/tests/test_api_chat.py`
- `GET /api/models` → returns 200 + model list (mock providers)
- `GET /api/chat/prompts` → returns 200
- `POST /api/chat` → returns 200 + response (mock provider)

#### 8. `backend/tests/test_api_docker.py`
- `GET /api/docker/ps` → returns 200

#### 9. `backend/tests/test_api_knowledge_remote.py` (NEW — tests AppFlowy remote bridge handlers)
- `GET /api/knowledge/workspaces` → returns 200
- `GET /api/knowledge/documents` → returns 200
- `GET /api/knowledge/search?q=test` → returns 200
- 404 for unknown document

### Priority B: Improve Existing Tests

#### `test_api_containers.py`
- Add test for `POST /api/containers` without runtime → 400
- Add test for `GET /api/containers/{invalid}` → 404
- Add test for `DELETE /api/containers/{invalid}` → 404
- Add test for stopping an already-stopped container (idempotent)

#### `test_api_surfaces.py`
- Add test for `GET /api/surfaces` empty → count 0
- Add test for stopping an already-stopped surface (idempotent)
- Add test for surface metadata filter

#### `test_api_snacks.py`
- Add test for invalid priority → 400
- Add test for delivering already-delivered snack (idempotent)
- Add test for `DELETE /api/snacks/queue` when queue is empty → 200 count 0

#### `test_api_clipboard.py`
- Add test for saving empty content → 400
- Add test for `DELETE /api/snacks/clipboard/{id}` → 200
- Add test for unpinning

---

## Phase 1 — Full Coverage ✅ COMPLETE

**Status:** 241 tests passing (241/241, +73 from Phase 0)

### Service Tests Created
- ✅ `test_provider_router.py` (12 tests) — routing, priority, config parsing, missing keys, streaming
- ✅ `test_secret_store.py` (12 tests) — set/get/delete, masking, dirty flag, sync_from_env, env override

### Skill Tests Created
- ✅ `test_skill_route_task.py` (10 tests) — simple/medium/complex routing, auto-detect, large context
- ✅ `test_skill_surface_repair.py` (3 tests) — nonexistent, healthy, repair issues
- ✅ `test_skill_surface_restart.py` (3 tests) — nonexistent, create, restart running
- ✅ `test_skill_container.py` (4 tests) — start/stop nonexistent, start/stop success
- ✅ `test_skill_backup.py` (3 tests) — backup creates file, daily backup full/database
- ✅ `test_skill_export_import.py` (4 tests) — export/import/roundtrip
- ✅ `test_skill_vault_sync.py` (2 tests) — missing config, missing script
- ✅ `test_skill_ask_vault.py` (4 tests) — list-workspaces, list-docs, search, get-doc not found

### Edge Case & Error Tests Created
- ✅ `test_api_error_handling.py` (7 tests) — malformed JSON, empty body, 404, 405, oversized
- ✅ `test_core_snackbar.py` (6 tests) — app creation, CORS middleware, settings, logging, DB migration, shutdown handler

### Bonus: Fixed 2 production bugs
- `container_start.py` — used nonexistent `transition_state()` → `start_container()`
- `container_stop.py` — used nonexistent `transition_state()` → `stop_container()`

---

## Implementation Pattern

### For API Integration Tests (aiohttp test utils):
```python
"""Test the /api/endpoint handlers."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from app.api.module import register_routes_or_handler


class EndpointTest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        # Import and register the specific routes/handlers
        register_routes_or_handler(app)
        return app

    async def test_happy_path(self):
        resp = await self.client.get("/api/endpoint")
        assert resp.status == 200
        data = await resp.json()
        assert "expected_key" in data

    async def test_404(self):
        resp = await self.client.get("/api/endpoint/nonexistent")
        assert resp.status == 404

    async def test_400_invalid(self):
        resp = await self.client.post("/api/endpoint", json={})
        assert resp.status == 400
```

### For Skill Unit Tests:
```python
"""Test skill_name skill."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_skill_runs_successfully():
    from app.skills.builtin.skill_name import SkillClass
    skill = SkillClass()
    result = await skill.run()
    assert result["success"] is True

@pytest.mark.asyncio
async def test_skill_with_params():
    from app.skills.builtin.skill_name import SkillClass
    skill = SkillClass()
    result = await skill.run(param1="value")
    assert result["success"] is True
    assert result.get("param1") == "value"

@pytest.mark.asyncio
async def test_skill_invalid_params():
    from app.skills.builtin.skill_name import SkillClass
    skill = SkillClass()
    result = await skill.run(invalid="param")
    # Should gracefully handle or default
    assert result["success"] is True  # or False depending on implementation
```

### For Service Unit Tests:
```python
"""Test service_name service."""
from __future__ import annotations

import pytest


class TestServiceName:
    def test_initialization(self):
        from app.services.service_name import ServiceClass
        svc = ServiceClass()
        assert svc is not None

    def test_happy_path(self):
        from app.services.service_name import ServiceClass
        svc = ServiceClass()
        result = svc.do_something()
        assert result is not None

    def test_edge_case(self):
        from app.services.service_name import ServiceClass
        svc = ServiceClass()
        result = svc.do_something(invalid_input=None)
        # Should not crash
        assert result is not None
```

---

## Run Tests After Each Phase

```bash
cd backend && source .venv/bin/activate && python -m pytest -q -x --tb=short 2>&1
```

**Success criteria for Phase 0:** All existing tests pass + all new API endpoint tests pass. Target: 60+ passing tests.

**Success criteria for Phase 1:** All Phase 0 tests + all skill + service tests pass. Target: 100+ passing tests.

---

## Files Not to Touch
- `backend/app/core/snackbar.py` — main server setup
- `backend/app/api/routes.py` — route registration
- Any `.pyc` files
- Any `node_modules`
- Any `.venv` files

## Configs
- Test dependencies already in `backend/pyproject.toml` under `[project.optional-dependencies] dev`
- `asyncio_mode = "auto"` in `[tool.pytest.ini_options]`
- `conftest.py` adds backend dir to `sys.path`
