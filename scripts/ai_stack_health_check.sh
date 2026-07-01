#!/usr/bin/env bash
set -euo pipefail

# Health check for Cline/Continue config + uCore MCP/API + skill routing.

BASE_URL="${UCORE_URL:-http://127.0.0.1:8484}"

PASS=0
WARN=0
FAIL=0

ok() { echo "[OK] $*"; PASS=$((PASS+1)); }
warn() { echo "[WARN] $*"; WARN=$((WARN+1)); }
bad() { echo "[FAIL] $*"; FAIL=$((FAIL+1)); }

[[ -f "$HOME/.cline/mcp_settings.json" ]] && ok "Cline MCP config present" || bad "Missing ~/.cline/mcp_settings.json"
[[ -f "$HOME/.continue/config.yaml" ]] && ok "Continue config present" || bad "Missing ~/.continue/config.yaml"
[[ -f "$HOME/.continue/mcp-udos.py" ]] && ok "MCP bridge script present" || bad "Missing ~/.continue/mcp-udos.py"

command -v cline >/dev/null 2>&1 && ok "Cline CLI installed" || bad "Cline CLI not found"
command -v python3 >/dev/null 2>&1 && ok "python3 installed" || bad "python3 missing"

if curl -fsS "$BASE_URL/api/health" >/dev/null 2>&1; then
  ok "uCore health endpoint reachable"
else
  bad "uCore health endpoint unreachable: $BASE_URL/api/health"
fi

SYSTEM_JSON="$(curl -fsS "$BASE_URL/api/system" 2>/dev/null || true)"
if [[ -n "$SYSTEM_JSON" ]]; then
  AI_REQS="$(echo "$SYSTEM_JSON" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("services",{}).get("ai_runtime",{}).get("requests",""))' 2>/dev/null || true)"
  AI_LATENCY="$(echo "$SYSTEM_JSON" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("services",{}).get("ai_runtime",{}).get("average_latency_ms",""))' 2>/dev/null || true)"
  CACHE_HIT_RATIO="$(echo "$SYSTEM_JSON" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("services",{}).get("ai_runtime",{}).get("cache",{}).get("hit_ratio",""))' 2>/dev/null || true)"

  if [[ -n "$AI_REQS" && -n "$AI_LATENCY" && -n "$CACHE_HIT_RATIO" ]]; then
    ok "AI runtime stats available (requests=$AI_REQS avg_latency_ms=$AI_LATENCY cache_hit_ratio=$CACHE_HIT_RATIO)"
  else
    warn "AI runtime stats unavailable in /api/system payload"
  fi
else
  warn "System metadata endpoint unavailable for AI runtime stats"
fi

TOOLS_JSON="$(curl -fsS "$BASE_URL/api/mcp/tools" 2>/dev/null || true)"
if [[ -n "$TOOLS_JSON" ]]; then
  if echo "$TOOLS_JSON" | grep -q '"tools"'; then
    ok "MCP tools endpoint reachable"
  else
    bad "MCP tools endpoint returned unexpected payload"
  fi
else
  bad "MCP tools endpoint unreachable: $BASE_URL/api/mcp/tools"
fi

# Validate MCP stdio bridge path by performing tools/list over JSON-RPC.
BRIDGE_OUT="$(printf '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n' | python3 "$HOME/.continue/mcp-udos.py" 2>/dev/null || true)"
if echo "$BRIDGE_OUT" | grep -q '"result"'; then
  ok "MCP stdio bridge responds to tools/list"
else
  bad "MCP stdio bridge failed tools/list"
fi

# Maintenance visibility check.
if curl -fsS "$BASE_URL/api/system/maintenance" >/dev/null 2>&1; then
  ok "Maintenance endpoint reachable"
else
  warn "Maintenance endpoint unavailable"
fi

# Skill execution sanity check (low-impact routing skill).
ROUTE_CODE="$(curl -s -o /tmp/ucore_route_task_check.json -w '%{http_code}' \
  -X POST "$BASE_URL/api/skills/route_task/run" \
  -H 'Content-Type: application/json' \
  -d '{"task":"repair MCP connectivity and summarize actions","complexity":"auto"}')"
if [[ "$ROUTE_CODE" == "200" ]]; then
  ok "skill_route_task run succeeded"
else
  warn "skill_route_task returned HTTP $ROUTE_CODE"
fi

if command -v ollama >/dev/null 2>&1; then
  if ollama list 2>/dev/null \
    | tr -d '\r' \
    | awk 'NR>1 {print $1}' \
    | grep -Fxq 'qwen2.5-coder:7b-instruct-q4_K_M'; then
    ok "Recommended local model present: qwen2.5-coder:7b-instruct-q4_K_M"
  else
    warn "Recommended local model not found in ollama list"
  fi
else
  warn "Ollama not installed"
fi

if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
  ok "OPENROUTER_API_KEY is set in environment"
else
  warn "OPENROUTER_API_KEY is not set in current shell"
fi

echo "---"
echo "Pass: $PASS  Warn: $WARN  Fail: $FAIL"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
