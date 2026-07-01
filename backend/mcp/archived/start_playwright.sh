#!/bin/bash
# Startup script for Playwright MCP server

MCP_SERVER="${MCP_PLAYWRIGHT_BIN:-$HOME/.nvm/versions/node/v20.20.2/bin/playwright-mcp}"
MANIFEST="${UCORE_ROOT:-$HOME/Code/uCore}/backend/mcp/mcp-playwright-manifest.json"

if [ ! -f "$MCP_SERVER" ]; then
    echo "Error: Playwright MCP server not found at $MCP_SERVER"
    exit 1
fi

if [ ! -f "$MANIFEST" ]; then
    echo "Error: Manifest not found at $MANIFEST"
    exit 1
fi

echo "Starting Playwright MCP server..."
exec "$MCP_SERVER" --config "$MANIFEST"
