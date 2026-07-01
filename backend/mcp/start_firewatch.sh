#!/bin/bash
# Startup script for Firewatch MCP server

MCP_SERVER="${MCP_FIREWATCH_BIN:-$HOME/Library/pnpm/global/5/bin/firewatch-mcp}"
MANIFEST="${UCORE_ROOT:-$HOME/Code/uCore}/backend/mcp/mcp-firewatch-manifest.json"

if [ ! -f "$MCP_SERVER" ]; then
    echo "Error: Firewatch MCP server not found at $MCP_SERVER"
    exit 1
fi

if [ ! -f "$MANIFEST" ]; then
    echo "Error: Manifest not found at $MANIFEST"
    exit 1
fi

echo "Starting Firewatch MCP server..."
exec "$MCP_SERVER" --manifest "$MANIFEST"
