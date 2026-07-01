#!/bin/bash
# Startup script for Feed Sage MCP server

MCP_SERVER="${MCP_SCHEDULER_BIN:-$HOME/Library/pnpm/global/5/bin/feed-sage}"
MANIFEST="${UCORE_ROOT:-$HOME/Code/uCore}/backend/mcp/mcp-scheduler-manifest.json"

if [ ! -f "$MCP_SERVER" ]; then
    echo "Error: Feed Sage MCP server not found at $MCP_SERVER"
    exit 1
fi

if [ ! -f "$MANIFEST" ]; then
    echo "Error: Manifest not found at $MANIFEST"
    exit 1
fi

echo "Starting Feed Sage MCP server..."
exec "$MCP_SERVER" --config "$MANIFEST"
