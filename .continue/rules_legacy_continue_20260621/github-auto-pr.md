---
description: Automatically create GitHub PRs when significant code changes are made
alwaysApply: false
---

# GitHub Auto-PR Creation

When user has made significant code changes (>50 lines or >3 files modified) and is on a feature branch, automatically suggest creating a PR.

## When to trigger:
- User says "ready to PR" or "create pr" or "push changes"
- Code changes detected on non-main branch
- User asks about submitting changes

## Actions:
1. Check current git status and branch
2. Verify changes are committed
3. Generate PR title from commit messages
4. Generate PR description from changes
5. Use `github_create_pr` MCP tool to create the PR
6. Report PR URL to user

## Example:
```
User: "I'm done with the feature, ready to submit"
Assistant: I'll create a PR for you.
- Current branch: feature/new-api
- 5 files changed, 127 insertions
- Creating PR: "Add new API endpoints"
- PR created: https://github.com/uDosGo/uCore/pull/42
```

## Configuration:
- Min lines changed: 20
- Exclude files: *.lock, *.log, dist/
- Auto-push before PR: true
