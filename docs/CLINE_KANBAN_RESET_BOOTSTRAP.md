# Cline Reset + Kanban Bootstrap (uCore)

Date: 2026-06-21

## What this gives you

- Clean Cline state reset with backups
- MCP integration to uCore bridge (`~/.continue/mcp-udos.py`)
- Preflight checks for Cline + MCP + local Kanban flow
- Baseline rules aligned with Markdown-first `.tasker/` workflow

## 1) Reset Cline settings

From repository root:

```bash
bash scripts/reset_cline_setup.sh
```

Optional full reset (also clears Cline secrets, with backup):

```bash
bash scripts/reset_cline_setup.sh --full
```

Backups are written to `~/.cline/backups/<timestamp>/`.

## 2) Verify MCP + workflow prerequisites

```bash
bash scripts/cline_kanban_preflight.sh
```

Expected checks:

- `~/.cline/mcp_settings.json` exists
- `~/.continue/mcp-udos.py` exists
- uCore endpoints respond:
  - `/api/health`
  - `/api/mcp/tools`
- `npx` is available for `npx kanban`

## 3) Start local workflow services

Run backend (if not already running), then launch Kanban:

```bash
npx kanban --host 127.0.0.1 --port 3484
```

Or launch the Cline CLI Kanban mode directly:

```bash
cline --kanban
```

Guardrail: keep Kanban and MCP localhost-only by default.

## 4) Scheduling automation

Use `launchd` or `cron` to schedule recurring workflows. Current Cline CLI builds do not expose a dedicated `schedule` subcommand, so scheduling should call shell scripts or API endpoints.

Example recurring command:

```bash
bash scripts/cline_kanban_preflight.sh && curl -fsS http://127.0.0.1:8484/api/system/workflow >/dev/null
```

## 5) Roundtable/Codex capability

uCore routing already treats medium-complexity tasks as Codex/Roundtable tier via `skill_route_task`.
Use MCP tool `skill_route_task` to decide provider/model per task complexity.

## 6) Pre-implementation wiring for dev flow

Current baseline is:

- Kanban as orchestration UI
- `.tasker/` as durable task source of truth
- uCore `/api/system/workflow` for status visibility

Recommended next integration points:

1. Add a Make/NPM command to run preflight + backend + Kanban together.
2. Add a small script to sync Kanban card metadata to `.tasker/` links.
3. Add CI check to validate `.tasker/` card references in PRs.
