# uCore CLI (uc)
- status: done
- source: ucore-dev
- source_id: backlog-ucore-cli
- synced_at: 2026-06-22T12:00:00Z
- completed: 2026-06-22

## Summary
Cline CLI serves as the unified orchestrator for uCore. It provides both interactive TUI and headless automation modes, eliminating the need for a separate `uc` CLI wrapper.

## Metadata
- area: cli
- priority: low
- replaces: separate uc CLI

## Why Cline CLI Instead of Separate Tool

### Design Comparison
| Aspect | Cline CLI | QQcode / Custom CLI |
|--------|-----------|--------------------|
| **Focus** | Collaborative TUI + headless automation | Lightweight, fast, deterministic |
| **Primary Use** | Pair programming + CI/CD scripts | Niche automation scenarios |
| **Adoption** | Industry standard (VS Code ext + CLI) | Experimental / custom |
| **Integration** | Tight MCP bridge with uCore | Requires custom wiring |
| **Maintenance** | Community-driven | Maintenance burden |

### Deployment Strategy: Cline CLI Modes

**Interactive Mode** (Development & Debugging)
```bash
cline
# Opens TUI with Plan/Act toggles, diffs, chat interface
```

**Headless Mode** (Overnight Automation)
```bash
cline --yolo "Run overnight maintenance suite"
# Auto-approves skill execution, logs to spool
```

**Structured Output** (Scripting & Monitoring)
```bash
cline --json "Check knowledge index coverage" | jq '.toolCalls'
# Programmatic NDJSON output for parsing
```

**Piped Input** (Unix Workflows)
```bash
cat config.yaml | cline "Validate this config"
# Read from stdin, process, return results
```

## Integration Points
- **Cline CLI** → uCore MCP bridge
- **VS Code Extension** → Cline CLI (fallback to TUI)
- **Roundtable MCP** → Parallel model execution
- **AppFlowy CLI** → Workspace management
- **uCore Skills** → Automation engine
- **n8n Workflows** → Webhook triggers

## Benefit: Single Orchestrator
By using Cline CLI instead of a separate tool, we avoid:
- Duplicate CLI argument parsing
- Maintenance of multiple entry points
- User confusion about which tool to use
- Redundant MCP bridge logic

Cline CLI is the industry standard and already supports all required automation modes.
