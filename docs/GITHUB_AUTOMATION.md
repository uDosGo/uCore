> **DEPRECATED** — This document has been superseded by canonical docs in [uDocs](https://github.com/uDosGo/uDocs). This file will be removed after migration verification. See [CONSOLIDATION_PLAN.md](./CONSOLIDATION_PLAN.md) for details.
# GitHub Automation Setup Guide

Complete setup guide for uCore's GitHub automation system with Cline integration.

## Overview

The GitHub automation system provides:
- **6 MCP Tools** for autonomous GitHub operations
- **Cline MCP integration** for intelligent workflow triggers
- **Web API** for external integrations and webhooks
- **Cross-repo management** for uDosGo organization

## Quick Start

### 1. Set Up GitHub Token

```bash
# Copy environment template
cp .env.example .env

# Add your GitHub Personal Access Token
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN_HERE"
```

**Token Permissions Required:**
- `repo` (full control)
- `workflow` (manage Actions)
- `read:org` (read organization data)
- `write:discussion` (manage issues)

### 2. Install Dependencies

```bash
cd backend
pip install PyGithub GitPython

# Verify gh CLI is installed
gh --version
gh auth status
```

### 3. Start uCore Snackbar

```bash
# From backend directory
python -m app.snackbar.server --port 8765

# Verify it's running
curl http://localhost:8765/health
```

### 4. Reload VSCode

Restart VSCode to load updated MCP configuration.

## MCP Tools

### 1. `github_publish_release`

Create and publish GitHub releases with auto-generated changelogs.

**Usage in Cline:**
```
User: "Release version 0.2.0 to GitHub"
Cline: Uses github_publish_release tool
```

**API Usage:**
```bash
curl -X POST http://localhost:8765/api/github/trigger/publish_release \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "uCore",
    "version": "0.2.0",
    "draft": false
  }'
```

### 2. `github_sync_repos`

Clone or pull all organization repositories.

**Usage:**
```python
from backend.app.services.mcp.github_tools import get_github_tools

tools = get_github_tools()
result = tools.sync_repos(local_dir="~/Code/uDosGo")
```

### 3. `github_create_pr`

Auto-create PRs with smart title and description generation.

**Cline Prompt Example:**
```
User: "Create a PR for this branch"
```

**What it does:**
- Detects current branch
- Generates PR title from commits
- Creates PR description
- Opens PR and returns URL

### 4. `github_heal_issues`

Auto-triage and label issues across repos.

**Cline Prompt Example:**
```
User: "Triage open issues for this repo"
```

**Features:**
- Auto-labels by keywords (bug, feature, docs)
- Identifies stale issues (>30 days)
- Adds helpful comments
- Can auto-close resolved issues

### 5. `github_actions_status`

Check CI/CD workflow status across all repos.

**Cline Prompt Example:**
```
User: "Check CI status across uDosGo repos"
```

**Auto-retry:**
```python
result = tools.actions_status(auto_retry_failed=True)
```

### 6. `github_approve_pr`

Auto-review and approve PRs with checks.

**Usage:**
```python
result = tools.approve_pr(
    repo_name="uCore",
    pr_number=42,
    auto_merge=True,  # Merge if checks pass
    run_tests=True    # Run local tests first
)
```

## Cline Integration

### Prompt-Driven MCP Usage

Available in Cline chat:

- "Create a PR from current branch"
- "Publish a new release"
- "Check CI/CD status"
- "Triage open issues"
- "Sync organization repos"

### Workflow Playbooks

Canonical Cline-native workflows are documented in:

- `docs/CLINE_GITHUB_WORKFLOWS.md`

The playbook covers:

- Auto-PR flow (prompt + MCP tool sequence)
- CI monitoring flow (interactive and scheduled)
- Issue triage flow (interactive and scheduled)

## Web API Endpoints

### GET `/api/github/status`

Organization-wide status dashboard.

**Response:**
```json
{
  "success": true,
  "org": "uDosGo",
  "repos": {"total": 12, "list": [...]},
  "ci": {"total_runs": 45, "failures": 2},
  "issues": {"total_open": 18}
}
```

### POST `/api/github/webhook`

GitHub webhook receiver for event automation.

**Setup:**
1. Go to GitHub org settings → Webhooks
2. Add webhook: `https://your-server.com/api/github/webhook`
3. Set secret in `.env`: `GITHUB_WEBHOOK_SECRET`
4. Events: push, pull_request, issues, workflow_run

**Automated Actions:**
- `push` to main → Check CI
- `pull_request` opened → Auto-label
- `issues` opened → Auto-triage
- `workflow_run` failed → Alert

### POST `/api/github/trigger/{tool}`

Manually trigger any GitHub tool.

**Example:**
```bash
curl -X POST http://localhost:8765/api/github/trigger/heal_issues \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "uCore",
    "auto_label": true,
    "auto_close_stale": false
  }'
```

### GET `/api/github/repos`

List all organization repositories.

## Usage Examples

### Example 1: Daily Issue Triage

```bash
# Run via Cline
User: "triage all issues"

# Or via API
curl -X POST http://localhost:8765/api/github/trigger/heal_issues \
  -d '{"repo_name": "uCore", "auto_label": true}'
```

### Example 2: Release Workflow

```bash
# 1. Check CI is green
User: "check ci status"

# 2. Create release
User: "release version 1.0.0"

# 3. Cline auto-publishes with changelog
```

### Example 3: PR Automation

```bash
# Make changes on feature branch
git checkout -b feature/new-api
# ... make changes ...
git add .
git commit -m "Add new API endpoints"

# Let Cline create the PR
User: "ready to submit PR"
Cline: "Creating PR... https://github.com/uDosGo/uCore/pull/42"
```

## Troubleshooting

### Token Issues

```bash
# Verify token
echo $GITHUB_TOKEN

# Test with gh CLI
gh api user

# Check permissions
gh auth status
```

### MCP Connection

```bash
# Check if Snackbar is running
curl http://localhost:8765/health

# Restart if needed
pkill -f snackbar
python -m app.snackbar.server --port 8765
```

### Cline Not Seeing Tools

1. Reload VSCode window (Cmd+R)
2. Check Cline output logs for MCP errors
3. Verify `~/.cline/mcp_settings.json` has the uCore MCP server
4. Confirm backend is reachable at the configured URL

## Advanced Configuration

### Custom Webhook Handlers

Edit `backend/app/api/github.py` to add custom webhook logic:

```python
elif event_type == "release":
    # Custom release event handling
    pass
```

### Custom Issue Labels

Modify `github_tools.py` → `_detect_issue_labels()`:

```python
def _detect_issue_labels(self, title: str) -> list[str]:
    if "urgent" in title.lower():
        labels.append("priority:high")
    # Add more rules...
```

### Scheduled Automation

Use cron or GitHub Actions to trigger tools:

```yaml
# .github/workflows/daily-triage.yml
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM daily
jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - name: Triage issues
        run: |
          curl -X POST ${{ secrets.UCORE_API }}/api/github/trigger/heal_issues \
            -d '{"repo_name": "uCore", "auto_label": true}'
```

## Security Notes

- **Never commit `.env` file** - contains secrets
- **Rotate GitHub tokens** regularly
- **Use webhook secrets** for production webhooks
- **Limit token scopes** to minimum required
- **Monitor API access logs**

## Next Steps

1. ✅ Set up GitHub token
2. ✅ Test MCP tools via Cline
3. ✅ Configure webhooks (optional)
4. 🔄 Customize rules for your workflow
5. 🔄 Add more automation as needed

## Support

- GitHub Issues: https://github.com/uDosGo/uCore/issues
- Documentation: https://udos.dev/ucore
- Cline Docs: https://docs.cline.bot
