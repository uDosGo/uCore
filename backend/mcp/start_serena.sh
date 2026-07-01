#!/bin/bash
# Startup script for Serena Slim MCP server

MCP_SERVER="${MCP_SERENA_BIN:-$HOME/Library/pnpm/global/5/bin/serena-slim}"
MANIFEST="${UCORE_ROOT:-$HOME/Code/uCore}/backend/mcp/mcp-serena-manifest.json"

if [ ! -f "$MCP_SERVER" ]; then
    echo "Error: Serena Slim MCP server not found at $MCP_SERVER"
    exit 1
fi

if [ ! -f "$MANIFEST" ]; then
    echo "Error: Manifest not found at $MANIFEST"
    exit 1
fi

echo "Starting Serena Slim MCP server..."
exec "$MCP_SERVER" --config "$MANIFEST"
