# uCore MCP Servers

This directory contains MCP (Model Context Protocol) server configurations for uCore.

## Available MCP Servers

### 1. uCore Server
**Purpose**: Core uCore functionality including health checks, MCP API, and metadata management.

**Manifest**: `mcp-manifest.json`

**Features**:
- Health endpoint (`/health`)
- MCP API endpoints
- Metadata management
- Snackbar notifications
- Catalog services

**Start Command**:
```bash
cd backend && python -m app.main
```

### 2. Playwright MCP Server
**Purpose**: Browser automation and web scraping capabilities.

**Manifest**: `mcp-playwright-manifest.json`

**Features**:
- Browser control
- Page navigation
- Element interaction
- Screenshot capture
- Console logging

**Start Command**:
```bash
cd backend && bash start_playwright.sh
```

### 3. LightPanda MCP Server
**Purpose**: AI-powered code analysis and refactoring.

**Manifest**: `mcp-lightpanda-manifest.json`

**Features**:
- Code analysis
- Refactoring suggestions
- Type checking
- Documentation generation

**Start Command**:
```bash
cd backend && bash start_lightpanda.sh
```

## MCP Diagnostics

Check MCP server status and configuration:

```bash
cd backend && python -m mcp.mcp_diagnostics
```

## Integration

MCP servers are integrated via:
- `backend/app/api/mcp.py` - MCP API endpoints
- `backend/app/services/mcp/` - MCP service implementations
- `backend/mcp/*.json` - Server manifests

## Development

To add a new MCP server:

1. Create manifest in `backend/mcp/`
2. Implement server logic in `backend/app/services/mcp/`
3. Add API endpoints in `backend/app/api/mcp.py`
4. Update diagnostics in `backend/mcp/mcp_diagnostics.py`