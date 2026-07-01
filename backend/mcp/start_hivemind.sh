#!/bin/bash
# Startup script for Hivemind MCP server (multi-agent orchestration)
# Port: 8490

UCORE_ROOT="${UCORE_ROOT:-$HOME/Code/uCore}"
AGENTS_CONFIG="${UCORE_ROOT}/backend/config/agents.yaml"
HOST="127.0.0.1"
PORT=8490

echo "Starting Hivemind MCP server on ${HOST}:${PORT}..."
echo "Agents config: ${AGENTS_CONFIG}"

cd "$UCORE_ROOT/backend" || exit 1

exec python3 -m app.mcp.hivemind_server \
    --host "$HOST" \
    --port "$PORT" \
    --agents-config "$AGENTS_CONFIG"
