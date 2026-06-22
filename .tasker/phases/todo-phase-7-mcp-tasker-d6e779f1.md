# Phase 7: MCP + Tasker Integration
- status: done
- source: ucore-dev
- source_id: phase-7
- synced_at: 2026-06-22T00:30:00Z

## Summary
Map S310 clipboard and S320 knowledge tools to MCP. Add MCP-facing workflow operations on top of .tasker/ Markdown files.

## Metadata
- area: mcp
- priority: low
- depends_on: phase-4, phase-6
- orchestrator: Cline + Roundtable (parallel MCP tool generation)

## Sub-tasks

### T7.1 Clipboard MCP tool
- status: done
- Add MCP tool for clipboard capture/get/delete
- Wire through /api/mcp/call

### T7.2 Knowledge MCP tools
- status: done
- Add MCP tools for workspace list, document list, search
- Wire through existing /api/knowledge/* endpoints

### T7.3 Tasker MCP operations
- status: done
- Add MCP operations for .tasker/ read, write, list boards
- Map to tasker_sync skill

### T7.4 Auto-sync .tasker/ from AppFlowy
- status: done
- Add overnight tasker_sync to maintenance chain
- Schedule after vault sync
