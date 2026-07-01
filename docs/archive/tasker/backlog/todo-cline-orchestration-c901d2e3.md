# Cline + Roundtable Orchestration Setup
- status: done
- source: ucore-dev
- source_id: backlog-cline-roundtable
- synced_at: 2026-06-22T12:00:00Z
- completed: 2026-06-22

## Summary
Established Cline as primary orchestrator with dual-mode CLI support. Cline operates as both an interactive TUI (Text User Interface) for collaborative pair programming and a headless command-line tool for automation.

## Metadata
- area: orchestration
- priority: medium
- orchestrator: Cline + Roundtable MCP

## Implementation: Cline CLI Modes

### 🤖 Interactive TUI Mode
Default mode when running `cline` without arguments or with `-i` flag.
- **Plan/Act toggle** and **auto-approve** via `Tab` and `Shift+Tab`
- **Markdown rendering** and **syntax-highlighted diffs**
- Support for **slash commands** (`/settings`) and file mentions (`@mention`)
- **Scrollable chat** with mouse support for collaborative, in-terminal work
- Use case: hands-on development, code review, paired debugging

### ⚙️ Command-Line Tool Mode
Activated when providing a prompt directly or using flags.
- **Headless Execution (`--yolo`)**: Auto-approve all tool calls for CI/CD and scripts
- **Structured Output (`--json`)**: NDJSON streaming for programmatic consumption
- **Piped Input**: Unix pipeline support (e.g., `cat file | cline "Summarize this"`)
- Use case: overnight automation, skill execution, maintenance chains, scheduled tasks

## Deployed Stack
- Cline as primary VS Code extension and CLI orchestrator
- Roundtable MCP for parallel model execution (Claude + Gemini + OpenRouter)
- uCore MCP bridge for knowledge, skills, and secrets access
- Overnight maintenance via Cline CLI `--yolo` mode
- Integration with AppFlowy workspaces and n8n automation workflows
