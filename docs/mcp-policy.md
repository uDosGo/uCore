# MCP for Everything Policy

Version: 1.0.0
Effective: 2026-06-26

Owner: Developer Productivity Team

## Purpose
- Establish MCP as the universal integration layer for all tools, services, and workflows in the uCore ecosystem.
- Ensure discoverability, security, and consistent agent interaction across the stack.

## Scope
- All backend services, developer tools, infrastructure, internal workflows, and third-party integrations.

## Architecture Standards
- MCP Server Requirements: protocol v0.1.0+, stdio transport for local, SSE/streamable-http for remote; health endpoint; semantic versioning.
- Discovery: list_tools() with JSON schema validation.
- Security: short-lived tokens, least privilege, audit logging.
- Health: /health endpoint (HTTP transport).
- Versioning: semantic versioning for server.

### Tool Naming Convention
- {domain}_{action}_{target}
- Examples: browser_navigate_url, secret_get_key, docker_start_container, github_create_pr

### Tool Permissions
- always, ask, never, auto (declared in config.toml or manifest).
- Spool logs must record tool calls with source = mcp.

## Implementation Guidelines
- New services must expose an MCP server alongside the primary API and be co-located with the service.
- Existing services should wrap via an MCP proxy and Dockerize the wrapper for deployment consistency.
- Document tools in the service README with examples.

## Agent Integration
- Agents discover MCP servers via an endpoint (e.g., /api/agents) and call list_tools() to learn capabilities.
- If an MCP server is unavailable, retry with backoff, log errors, and surface user-friendly errors.

## Monitoring & Compliance
- Track tool call counts, success rate, latency, cost, and uptime.
- Weekly audits of MCP servers; block tools with never permission from calls.

## Appendix A: Quick Start
- Add mcp-manifest.json for new servers with tools and health checks.
- Register with the router on startup.
- Use the manifest to derive a stable onboarding checklist for engineers.

This document is a living policy and will be updated as the MCP ecosystem evolves.
