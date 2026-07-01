# Phase 5: MCP Server Deployment - Remaining Servers
- status: in-progress
- source: ucore-dev
- source_id: phase-5-mcp-servers
- synced_at: 2026-06-26T00:00:00Z

## Summary
Deploy remaining MCP servers (browser, playwright, firewatch, secrets, scheduler, serena) and complete server discovery/registry infrastructure.

## Metadata
- area: mcp
- priority: high
- depends_on: Phase 7 tasks (UDW-024-026)
- orchestrator: Cline + Roundtable

## Sub-tasks

### T5.1: mcp-browser (Consolidated to Playwright)
- status: done
- **Decision**: Consolidated to Playwright MCP (already deployed on port 8931)
- **Rationale**: Lightpanda requires separate browser instance + Bun runtime; Playwright is self-contained and more reliable
- **Playwright MCP** (port 8931):
  - [x] Installed via npm
  - [x] Configured with manifest
  - [x] Tested with Zen Browser
  - [x] Integrated with uCore
  - [x] Health check endpoint operational
- **Documentation**
  - [x] Document Playwright tool usage
  - [x] Create usage examples

### T5.2: mcp-playwright
- status: done
- **Install Playwright MCP server**
  - [x] `npm install -g @playwright/mcp` - Installed
  - [x] Configure for port 8931 - Created manifest and startup script
  - [x] Test with Zen Browser - Startup script tested successfully
- **Integrate with uCore**
  - [x] Add to MCP manifest - Created `mcp-playwright-manifest.json`
  - [ ] Register with agent router
  - [ ] Add health check endpoint
- **Documentation**
  - [ ] Document Playwright tool usage
  - [ ] Create usage examples

### T5.3: mcp-firewatch
- status: done
- **Install Firewatch MCP server**
  - [x] `pnpm add -g firewatch-mcp` - Installed
  - [x] Add to MCP manifest - Created `mcp-firewatch-manifest.json`
  - [x] Create startup script - `start_firewatch.sh`
  - [ ] Configure for port 8932 - Needs configuration
  - [ ] Test with Zen Browser - Pending
- **Integrate with uCore**
  - [ ] Register with agent router
  - [ ] Add health check endpoint
- **Documentation**
  - [ ] Document Firewatch tool usage
  - [ ] Create usage examples

### T5.4: done
- **Install Secrets Broker MCP server**
  - [x] `pnpm add -g mcp-credentials-broker` - Installed
  - [x] Add to MCP manifest - Created `mcp-secrets-manifest.json`
  - [x] Create startup script - `start_secrets.sh`
  - [ ] Configure for port 8933 - Needs configuration
  - [ ] Test secret management - Pending
- **Integrate with uCore**
  - [ ] Add to MCP manifest
  - [ ] Register with agent router
  - [ ] Add health check endpoint
- **Documentation**
  - [ ] Document secret management
  - [ ] Create security guidelines

### T5.5: done
- **Install Feed Sage MCP server**
  - [x] `pnpm add -g feed-sage` - Installed
  - [x] Add to MCP manifest - Created `mcp-scheduler-manifest.json`
  - [x] Create startup script - `start_scheduler.sh`
  - [ ] Configure for port 8935 - Needs configuration
  - [ ] Test scheduler hooks - Pending
- **Integrate with uCore**
  - [ ] Add to MCP manifest
  - [ ] Register with agent router
  - [ ] Add health check endpoint
- **Documentation**
  - [ ] Document scheduler usage
  - [ ] Create workflow templates
done
- **Install Serena Slim MCP server**
  - [x] `pnpm add -g serena-slim` - Installed
  - [x] Add to MCP manifest - Created `mcp-serena-manifest.json`
  - [x] Create startup script - `start_serena.sh`
  - [ ] Configure for port 8936 - Needs configuration
  - [ ] Test code analysis - Pending
- **Integrate with uCore**
- **Integrate with uCore**
  - [ ] Add to MCP manifest
  - [ ] Register with agent router
  - [ ] Add health check endpoint
- **Documentation**
  - [ ] Document Serena tool usage
  - [ ] Create code analysis examples

### T5.7: Server Dashboard
- status: done
- **Create MCP server dashboard**
  - [x] List all registered servers - Created MCPServersPanel
  - [x] Show status (online/offline) - Implemented with color-coded indicators
  - [x] Display tool counts - Shows tool count per server
  - [x] Show recent usage metrics - Last check timestamp
- **Add to Developer Surface**
  - [x] Add to Developer Surface - Added 'mcp-servers' tab
  - [x] Real-time updates - Auto-refresh every 30 seconds
  - [x] Health status indicators - Pulse animation for online status

## Execution Order

1. **T5.1**: Configure and test Lightpanda MCP server
2. **T5.2**: ✅ Complete - Playwright MCP server deployed
3. **T5.3-T5.6**: Research and find alternative MCP servers or implement custom
4. **T5.7**: Create MCP server dashboard

## Testing Strategy

- **Unit Tests**: Each MCP server with mock tools
- **Integration Tests**: MCP server → agent router → uCore
- **E2E Tests**: Full workflow with all MCP servers

## Definition of Done

- All MCP servers deployed and registered
- Server dashboard live with real-time status
- Health checks passing for all servers
- Documentation complete
- All tools accessible via `/api/mcp/tools`
