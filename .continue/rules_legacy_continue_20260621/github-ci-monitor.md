---
description: Monitor GitHub Actions CI/CD status and alert on failures
alwaysApply: false
---

# GitHub CI/CD Monitoring

Proactively monitor GitHub Actions workflow status across uDosGo organization repositories and alert user to failures.

## When to trigger:
- User asks "check ci" or "ci status" or "actions status"
- Scheduled check every hour (if Continue supports scheduling)
- After a git push
- When user mentions "deploy" or "release"

## Actions:
1. Use `github_actions_status` MCP tool to check all repos
2. Report summary of workflow runs
3. Highlight any failures with links
4. Suggest auto-retry for failed runs
5. Show recent successful deploys

## Example:
```
User: "check ci status"
Assistant: Checking GitHub Actions across all repos...

✅ uCore: 5/5 workflows passing
❌ uDosML: 1 failure (test-suite on main)
   - Failed 2 hours ago
   - Link: https://github.com/uDosGo/uDosML/actions/runs/123
   - Would you like me to retry this run?

✅ forge: All green
```

## Auto-retry logic:
- Retry if failure is <1 hour old
- Skip if failure has retry comment already
- Max 2 auto-retries per run
