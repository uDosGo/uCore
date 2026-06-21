# Cline GitHub Workflows (uCore)

Date: 2026-06-21
Status: Canonical Cline playbook

## Purpose

Replace legacy Continue rule files with Cline-native, prompt-driven MCP workflows.

This runbook maps three high-value automation flows:

- Auto PR creation
- CI/CD monitoring
- Issue triage

## Prerequisites

- Cline configured with uCore MCP server in `~/.cline/mcp_settings.json`
- uCore backend running and reachable
- GitHub token available for MCP GitHub tools

Quick checks:

```bash
cline mcp --help
curl -fsS http://127.0.0.1:8484/api/mcp/tools | head
```

## Workflow 1: Auto PR Creation

Trigger phrases:

- "ready to PR"
- "create a PR for this branch"
- "submit these changes"

Prompt pattern for Cline:

```text
Create a PR for the current branch.
1) inspect git status and branch
2) summarize changed files and commit messages
3) use MCP GitHub tool to open PR against main
4) return PR URL and next reviewer actions
```

Expected behavior:

1. Detect non-main branch.
2. Verify branch is pushed (or push).
3. Generate title/body from commit diff.
4. Invoke GitHub MCP PR creation tool.
5. Return PR URL.

## Workflow 2: CI/CD Monitoring

Trigger phrases:

- "check ci status"
- "actions status"
- "show failing workflows"

Prompt pattern for Cline:

```text
Check GitHub Actions status across uDosGo repositories.
1) call MCP CI status tool
2) summarize passing/failing runs
3) provide links for failures
4) suggest retry candidates for recent transient failures
```

Expected behavior:

1. Query workflow runs.
2. Highlight failures by repo and branch.
3. Suggest retry path where appropriate.

## Workflow 3: Issue Triage

Trigger phrases:

- "triage issues"
- "clean up issue inbox"
- "review stale issues"

Prompt pattern for Cline:

```text
Triage open issues across target repositories.
1) call MCP issue triage/heal tool
2) auto-label by keyword categories
3) flag stale issues older than 30 days
4) produce a concise triage report
```

Expected behavior:

1. Apply label heuristics.
2. Mark stale items.
3. Return summary and priority list.

## Scheduled Automation (launchd/cron)

Current Cline CLI in this environment does not expose a `schedule` subcommand, so scheduling should use `launchd` or `cron` wrappers that execute Cline prompts or uCore API calls.

### Option A: Cron (simple)

```bash
# every hour: CI check via Cline
0 * * * * cd /Users/fredbook/Code/uCore && cline task --cwd /Users/fredbook/Code/uCore "Check CI status across uDosGo repos and summarize failures only" --json >> /tmp/ucore-ci.log 2>&1

# weekdays 9:15: issue triage via Cline
15 9 * * 1-5 cd /Users/fredbook/Code/uCore && cline task --cwd /Users/fredbook/Code/uCore "Triage open issues for uCore using MCP and summarize actions taken" --json >> /tmp/ucore-triage.log 2>&1
```

### Option B: launchd (macOS)

Create a LaunchAgent that runs a shell wrapper calling one of:

- `cline task ...`
- `curl http://127.0.0.1:8484/api/github/trigger/...`

Use launchd when you need reliable startup behavior and per-user service management.

## Legacy Archive

Legacy Continue rule files were archived to:

- `.continue/rules_legacy_continue_20260621/`

They are retained only for historical reference and are not part of the active Cline workflow.
