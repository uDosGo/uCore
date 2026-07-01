#!/bin/bash
# Startup script for Secrets Broker MCP server

MCP_SERVER="${MCP_SECRETS_BIN:-$HOME/Library/pnpm/global/5/bin/mcp-credentials-broker}"
MANIFEST="${UCORE_ROOT:-$HOME/Code/uCore}/backend/mcp/mcp-secrets-manifest.json"

if [ ! -f "$MCP_SERVER" ]; then
    echo "Error: Secrets Broker MCP server not found at $MCP_SERVER"
    exit 1
fi

if [ ! -f "$MANIFEST" ]; then
    echo "Error: Manifest not found at $MANIFEST"
    exit 1
fi

echo "Starting Secrets Broker MCP server..."
exec "$MCP_SERVER" --config "$MANIFEST"
