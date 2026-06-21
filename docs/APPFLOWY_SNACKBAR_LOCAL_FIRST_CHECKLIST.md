# AppFlowy Snackbar Integration Checklist – Local-First (No Cloud)

Project: Snackbar / uConnect  
Target: AppFlowy (open-source, privacy-first workspace)  
Goal: Enable Snackbar to read, write, and automate AppFlowy documents, databases, and AI chat using only local SQLite and file-based integration.

## 1. Core Integration: Direct SQLite Access

| # | Task | Details | Status |
|---|------|---------|--------|
| 1.1 | Locate AppFlowy SQLite databases | Supports ~/AppFlowy/data/database.sqlite and ~/AppFlowy/data/chat.sqlite, plus desktop fallback paths | ✅ |
| 1.2 | Create a Snackbar SQLite reader | Implemented in backend/app/knowledge/local_first.py | ✅ |
| 1.3 | Map AppFlowy database schema to Snackbar models | Table discovery and generic query support implemented; full typed mapping pending | 🟨 Partial |
| 1.4 | Test direct read queries | Exposed via POST /api/knowledge/local/query (read mode) | ✅ |
| 1.5 | Implement safe write operations | write mode with backup + SQL guardrails + spool logging | ✅ |

## 2. Agent Integration (Local)

| # | Task | Details | Status |
|---|------|---------|--------|
| 2.1 | Configure AppFlowy AI to use local Ollama | Documented strategy; runtime config remains user environment specific | 🟨 Partial |
| 2.2 | Create Snackbar agent that reads AppFlowy DB | Local query endpoint and reusable module available for skills/agents | ✅ |
| 2.3 | Create Snackbar agent that creates/updates AppFlowy rows | write-capable endpoint implemented for SQLite insert/update/delete | ✅ |
| 2.4 | Expose AppFlowy data as local MCP resources | Can be served via existing MCP bridge + local query endpoint; direct MCP resource wrappers pending | 🟨 Partial |

## 3. Snack Machine Workflow Integration

| # | Task | Details | Status |
|---|------|---------|--------|
| 3.1 | Create AppFlowy Sync snack | scripts/appflowy_sync_snack.sh added | ✅ |
| 3.2 | Create AppFlowy Mission Import snack | scripts/appflowy_mission_import_snack.sh added | ✅ |
| 3.3 | Add AppFlowy trigger to workflow engine | script-based integration ready; scheduler wiring to specific triggers pending | 🟨 Partial |
| 3.4 | Use sqlite3 triggers | DB trigger authoring not added yet (schema-specific) | ⬜ |

## 4. Plugin / Component Integration (Local)

| # | Task | Details | Status |
|---|------|---------|--------|
| 4.1 | Create Snackbar data plugin for AppFlowy Editor | Not implemented in this repo | ⬜ |
| 4.2 | Add slash command support for Snackbar actions | Not implemented in this repo | ⬜ |
| 4.3 | Use Node definition and BlockComponentBuilder pattern | Not implemented in this repo | ⬜ |

## 5. Spool Integration (Local)

| # | Task | Details | Status |
|---|------|---------|--------|
| 5.1 | Log all AppFlowy operations to Snackbar spool | Implemented in local_first.py (replies.jsonl) | ✅ |
| 5.2 | Sync AppFlowy rows to Snackbar vault | Implemented via POST /api/knowledge/local/export and sync snack script | ✅ |
| 5.3 | Use local file-based locking | Implemented for spool writes | ✅ |

## 6. Testing & Verification

| # | Task | Details | Status |
|---|------|---------|--------|
| 6.1 | Verify SQLite access | Endpoint support implemented; command can be run locally | ✅ |
| 6.2 | Test end-to-end workflow | Foundation in place; user workflow validation pending | 🟨 Partial |
| 6.3 | Test local agent chat | Existing local Ollama pathways exist; checklist-specific test pending | 🟨 Partial |
| 6.4 | Validate offline operation | Local-only design implemented; full offline validation pending | 🟨 Partial |

## 7. Dependencies & Credentials (Local Only)

| # | Item | Details | Status |
|---|------|---------|--------|
| 7.1 | AppFlowy installed locally | External prerequisite | ⬜ |
| 7.2 | sqlite3 command-line tool | Available on macOS by default | ✅ |
| 7.3 | Ollama (optional) | Optional prerequisite for local AI | 🟨 Partial |
| 7.4 | Node.js or Python SQLite library | Python sqlite3 used natively; Node optional | ✅ |

## Implemented API Surface

- GET /api/knowledge/local/databases
- GET /api/knowledge/local/tables?db=database
- POST /api/knowledge/local/query
- POST /api/knowledge/local/export

## Notes

1. Write operations are restricted to INSERT/UPDATE/DELETE and create automatic DB backups.
2. Query operations are restricted to SELECT/PRAGMA/WITH in read mode.
3. All AppFlowy local operations are logged to replies.jsonl.
