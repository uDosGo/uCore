# MCP Diagnostics Endpoint (Prototype)

- Expose an endpoint at /api/mcp/diagnostics that returns:
  - current tool registry snapshot (names, ids, and schemas)
  - last N tool calls attempted (payload, response, status)
  - health status and a quick router health check
  - a short recommended remediation path

- This is a dev-mode endpoint to accelerate triage during MCP integration work.
