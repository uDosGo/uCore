#!/usr/bin/env bash
set -euo pipefail

# Preflight checks for Cline + MCP + Kanban local workflow.

UC_BASE_URL="${UC_BASE_URL:-http://127.0.0.1:8484}"
KANBAN_HOST="${KANBAN_HOST:-127.0.0.1}"
KANBAN_PORT="${KANBAN_PORT:-3484}"

ok() { printf "[OK] %s\n" "$1"; }
warn() { printf "[WARN] %s\n" "$1"; }
fail() { printf "[FAIL] %s\n" "$1"; }

if [[ -f "$HOME/.cline/mcp_settings.json" ]]; then
  ok "Cline MCP settings found"
else
  fail "Missing $HOME/.cline/mcp_settings.json"
fi

if [[ -f "$HOME/.continue/mcp-udos.py" ]]; then
  ok "uCore MCP bridge script found"
else
  fail "Missing $HOME/.continue/mcp-udos.py"
fi

if command -v curl >/dev/null 2>&1; then
  if curl -fsS "$UC_BASE_URL/api/health" >/dev/null 2>&1; then
    ok "uCore health endpoint reachable: $UC_BASE_URL/api/health"
  else
    warn "uCore health endpoint not reachable: $UC_BASE_URL/api/health"
  fi

  if curl -fsS "$UC_BASE_URL/api/mcp/tools" >/dev/null 2>&1; then
    ok "uCore MCP tools endpoint reachable: $UC_BASE_URL/api/mcp/tools"
  else
    warn "uCore MCP tools endpoint not reachable: $UC_BASE_URL/api/mcp/tools"
  fi
else
  warn "curl not found; skipped HTTP checks"
fi

if command -v npx >/dev/null 2>&1; then
  ok "npx available for Kanban launch"
else
  fail "npx missing; install Node.js"
fi

if command -v lsof >/dev/null 2>&1; then
  if lsof -iTCP:"$KANBAN_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    ok "Kanban service appears to be listening on $KANBAN_HOST:$KANBAN_PORT"
  else
    warn "No process listening on $KANBAN_HOST:$KANBAN_PORT"
  fi
fi

echo "Preflight done"
