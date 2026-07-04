# pyrchard-uCode Development Handover Notes

**Date:** 2026-07-04T21:39:00+08:00
**Session:** PyCharm (Girdui) setup complete → handoff to next agent
**Branch:** main @ 9f4c802

---

## 1. Current State

### Git HEAD
```
9f4c802 fix: match Grid colour popover swatch style to Pixel — 1px border, inset shadow active states
4f39f05 fix: unify colour popovers — true 3x3 square grid, 36px cells, matching Pixel & Grid
c946237 refactor(Grid): remove sidebar palette, make colour popover a true 3x3 grid with transparent cell
389f5f6 fix(Grid): remove remaining F marker from sidebar palette
7699c7c refactor(Grid): remove close-up editor pane, make Layer the primary editing surface with Pixel-style toolbar
```

### Version
`pyproject.toml`: **4.0.3**

### Sprint Status
- **Sprint:** sprint.2026-07-02 "Control Panel + Agentic Execution Sprint" — **complete** (10/10 tasks done)
- **Completed count:** 58 tasks total in `.tasker.dev-flow.yaml`
- **Task count:** 44 defined tasks

---

## 2. What Was Just Done (Recent Session)

### PyCharm / Girdui Setup
- PyCharm IDE environment configured for the uCore workspace
- All project directories and virtual environments mapped

### Recent Grid UI Refinements (last 5 commits)
- Colour popover now matches Pixel's swatch style: 1px border, inset shadow active states
- Unified colour popovers: true 3x3 square grid, 36px cells, consistent between Pixel & Grid surfaces
- Removed sidebar palette from Grid; colour popover is now a standalone 3x3 grid
- Removed close-up editor pane; Layer is now the primary editing surface
- Pixel-style toolbar integrated into Layer editing surface

---

## 3. Architecture Overview (for the next agent)

### Project Structure
- **Backend:** Python 3.12 (`backend/app/`) — ASGI server on port 8484, managed by launchd (`com.udos.ucore-server`)
- **Frontend (Vue):** `frontend-vue/` — Vite dev server on localhost:5175
- **Frontend (React/legacy):** `frontend/` — older surfaces
- **MCP Servers:** Multiple — Hivemind (8490), Firewatch, Serena, Scheduler, Secrets, Knowledge
- **Config:** `config/` — agents.yaml, llm_router.yaml, openrouter.yaml, kanban.yaml

### Key Subsystems
| Subsystem | Location | Status |
|-----------|----------|--------|
| Control Panel | `frontend-vue/src/` (8 Vue files) + `backend/app/api/control.py` | Live |
| Hivemind Consensus | `backend/app/mcp/consensus.py` + `hivemind_server.py:8490` | Live |
| LLM Router | `backend/app/services/provider_router.py` | Live |
| Skills Registry | `backend/app/skills/builtin/` (BaseSkill subclasses) | Live |
| Feed System | Pod (SQLite) + MCP server + FeedConsumer | Live |
| Plates (Templates) | `backend/plate_refresh/` + `plates/` dirs | Live |
| USX Style System | `frontend-vue/src/styles/tokens/` + themes | Live |
| Catalog Service | `backend/app/services/catalog/` | Live |
| Distribution/Packages | `backend/app/services/distribution_system/` | Live |
| GridCore (Vue) | `frontend-vue/src/grid-core/` | Renderer only |
| GridSmith API | `backend/app/api/gridsmith_api.py` | REST endpoints |

### Key Ports
| Port | Service |
|------|---------|
| 8484 | uCore backend (ASGI) |
| 5175 | Vue frontend dev server |
| 8490 | Hivemind MCP server |
| 3484 | Cline Kanban |
| 4891 | Roundtable AI |
| 11434 | Ollama |

---

## 4. Known Issues & Watch Items

### Active Test Failures (10 signals, last 24h)
- `test_chat_cache.py::test_provider_router_chat_uses_cache`
- `test_core_snackbar.py::test_shutdown_handler`
- `test_episodic_log.py` — 4 tests failing (skill entry, invalid type, description requirement, comma tags)
- `test_episodic_log.py::test_brain_sync_includes_episodic_summary`
- `test_flow_router.py` — 3 tests failing (basic, analytics, clear)

### Backend Stability
- **Snackbar 500 crash loop** (fieldnotes 2026-07-01): Backend exits immediately after maintenance scheduler starts. Suspect event loop exit in `app/core/snackbar.py`. Workaround: frontend gracefully degrades with try/catch.
- **Skill load warnings:** `skill_dev_destroy_rebuild.py` and `skill_hardcoded_path_detector` fail to load from registry
- **Maintenance jobs:** `vault_sync` and `tasker_sync` report `success=False`

### Durability Lessons (from wisdom.md)
1. **Skill loop guards required:** Any multi-step pipeline skill MUST have `max_iterations` guard (default 3) + cooldown tracker (5 min TTL) — `skill_surface_rebuild` has it; add to new pipeline skills
2. **launchd KeepAlive trap:** Use `launchctl bootout` to stop, not `kill`. Deprecated configs with `KeepAlive <true/>` respawn killed processes immediately
3. **Syntax error detection:** Always run `flake8` or `py_compile` on changed files — a bare `except` nesting bug in `snackbar_menu.py` only surfaced in stderr.log

---

## 5. Next Steps / Suggested Work

### Immediate Priority
1. **Fix the 10 failing tests** — episodic_log and flow_router modules need attention
2. **Investigate snackbar crash loop** — backend on 8484 may be down; check `launchctl` status
3. **Fix skill load warnings** — `skill_dev_destroy_rebuild` and `skill_hardcoded_path_detector` import errors

### Continuing Work
- **Grid UI polish:** Colour popover and Layer editing surface are actively being refined
- **GridSmith Node agent:** Still needs implementation as per gap analysis in fieldnotes (backend CLI + MCP tools for world building)
- **DocLang bridge export:** Spec exists at `docs/DOCLANG_BRIDGE_EXPORT_SPEC.md`
- **Settings architecture:** Spec at `docs/SETTINGS_ARCHITECTURE_2026.md`

### Documentation Round (before next push)
Per `.clinerules` Docs Round Completion checklist:
- [ ] Update FEATURE_SPEC.md for any feature delivered
- [ ] Archive completed sprint plans to `docs/archive/`
- [ ] Archive completed tasker items
- [ ] Update `devlog.mcp.yaml` with new/modified files
- [ ] Update `fieldnotes.md` with key decisions
- [ ] Update `wisdom.md` lessons if any
- [ ] Bump version patch in `pyproject.toml` and `package.json`
- [ ] Update `.tasker.dev-flow.yaml`

---

## 6. Useful Commands

```bash
# Check backend health
curl http://localhost:8484/api/health

# Check launchd status
launchctl list | grep ucore

# Run tests
cd backend && python -m pytest -x --tb=short

# Start frontend dev server
cd frontend-vue && pnpm dev

# Check spool activity
cat ~/.ucore/spool/*.log | tail -50

# Git workflow
git log --oneline -10
git status
```

---

## 7. Key Files Reference

| File | Purpose |
|------|---------|
| `.tasker.dev-flow.yaml` | Canonical task list (58 done, 44 total) |
| `devlog.mcp.yaml` | Recent change log |
| `fieldnotes.md` | Developer observations and debugging notes |
| `wisdom.md` | Durable lessons + spool activity + test failures |
| `pyproject.toml` | Python project metadata (v4.0.3) |
| `package.json` | Node project metadata |
| `.clinerules` | Agent operating principles and workflow rules |
| `CONTEXT.md` | Project context overview |

---

**Handoff complete.** Next agent should start by checking backend health, running the test suite to confirm current state, and picking up from the known issues list above.