> **Canonical version:** `/Users/fredbook/Code/uDocs/runbooks/mcp-setup.md`
> This repo copy is kept for local reference; edits should be made in uDocs.

# uCore MCP Setup Guide

## Overview

uCore uses MCP (Model Context Protocol) servers for extended functionality including browser automation, code analysis, and AI-powered features.

## Prerequisites

- Node.js >= 22.0.0
- pnpm >= 9.0.0
- Python >= 3.12,<3.13 (3.12 recommended)
- uCore backend running

## Installation

### 1. Install Dependencies

```bash
# Install pnpm workspace dependencies
pnpm install

# Install Python dependencies
cd backend
pip install -e .[dev]
```

### 2. Configure Environment

Create `.env` file in root directory:

```bash
# uCore Configuration
UCORE_DEBUG=1
PYTHONUNBUFFERED=1

# MCP Configuration
MCP_SERVERS_ENABLED=true

# Server Configuration
UCORE_SERVER_PORT=8484
UCORE_SERVER_HOST=0.0.0.0
```

## Starting MCP Servers

### Start All Servers

```bash
# Start backend server (includes MCP)
pnpm run mcp:start

# Or start separately
pnpm run dev:backend
```

### Start Individual Servers

```bash
# Core uCore server
cd backend && python -m app.main

# Playwright MCP
cd backend && bash start_playwright.sh

# LightPanda MCP
cd backend && bash start_lightpanda.sh
```

### Start with Launchd (macOS)

```bash
# Install menu (auto-start on login)
cd backend && .venv/bin/python -m app.menu.install_macos_menu

# Or use the consolidated launchd manager directly
cd backend && .venv/bin/python -c "from app.menu.launchd_manager import install; install()"
```

**Note**: `com.udos.ucore-popcorn.plist` is deprecated. Use `com.udos.ucore-menu.plist` which points to `unified_menu_simple.py`.

## MCP API Endpoints

### Health Check

```bash
curl http://localhost:8484/health
```

Response:
```json
{
  "status": "ok",
  "service": "uCore",
  "version": "4.0.0",
  "menu": {
    "running": true,
    "installed": true,
    "pid": 74540
  }
}
```

### MCP API

```bash
# List available MCP tools
curl http://localhost:8484/api/mcp/tools

# Execute MCP tool
curl -X POST http://localhost:8484/api/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "playwright_navigate", "params": {"url": "https://example.com"}}'
```

## MCP Server Configuration

### Manifest Files

Each MCP server has a manifest file in `backend/mcp/`:

- `mcp-manifest.json` - Core uCore server
- `mcp-playwright-manifest.json` - Playwright server
- `mcp-lightpanda-manifest.json` - LightPanda server

### Server Registration

Servers are registered in `backend/app/api/mcp.py`:

```python
from mcp import Server

# Register servers
ucore_server = Server("ucore")
playwright_server = Server("playwright")
lightpanda_server = Server("lightpanda")
```

## Development

### Adding a New MCP Server

1. Create manifest:
```json
{
  "name": "my-server",
  "version": "1.0.0",
  "description": "My MCP server",
  "tools": [
    {
      "name": "my_tool",
      "description": "Tool description",
      "inputSchema": {
        "type": "object",
        "properties": {
          "param1": {"type": "string"}
        }
      }
    }
  ]
}
```

2. Implement server:
```python
# backend/app/services/mcp/my_server.py
from mcp import Server

server = Server("my-server")

@server.tool()
async def my_tool(param1: str) -> str:
    """Tool implementation"""
    return f"Result: {param1}"
```

3. Register in API:
```python
# backend/app/api/mcp.py
from app.services.mcp.my_server import server as my_server

app.include_router(my_server.router)
```

4. Update diagnostics:
```python
# backend/mcp/mcp_diagnostics.py
def check_my_server():
    """Check my server status"""
    # Implementation
```

## Troubleshooting

### Server Not Starting

```bash
# Check logs
tail -f ~/.ucore/logs/stderr.log

# Run diagnostics
cd backend && python -m mcp.mcp_diagnostics

# Check port availability
lsof -i :8484
```

### Connection Issues

```bash
# Test health endpoint
curl http://localhost:8484/health

# Check MCP API
curl http://localhost:8484/api/mcp/status
```

### Dependencies Not Found

```bash
# Reinstall dependencies
pnpm install
cd backend && pip install -e .[dev]
```

## Best Practices

1. **Use pnpm**: All Node.js dependencies should be managed via pnpm workspace
2. **Environment Variables**: Store sensitive config in `.env` file
3. **Logging**: Check logs in `~/.ucore/logs/` for debugging
4. **Health Checks**: Always verify server health before operations
5. **Manifests**: Keep manifests updated with latest tool definitions

## Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [uCore Documentation](./README.md)