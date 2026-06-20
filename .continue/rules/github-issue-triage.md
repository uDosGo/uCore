---
description: Automatically triage and label GitHub issues across org repos
alwaysApply: false
---

# GitHub Issue Triage

Automatically categorize, label, and manage GitHub issues across uDosGo repositories to maintain healthy issue tracking.

## When to trigger:
- User says "triage issues" or "check issues" or "clean up issues"
- Daily scheduled run (morning)
- When reviewing project status
- User mentions "inbox" or "todos"

## Actions:
1. Use `github_heal_issues` MCP tool for each repo
2. Auto-label issues by keywords:
   - "bug", "fix", "error" → bug
   - "feat", "feature", "enhance" → enhancement
   - "docs", "documentation" → documentation
   - "test", "testing" → testing
3. Identify stale issues (>30 days inactive)
4. Comment on issues missing information
5. Report triage summary to user

## Label rules:
```
bug: bug, fix, broken, error, crash, fail
enhancement: feature, feat, improve, add, new
documentation: doc, docs, readme, guide
question: how, why, what, help, support
good first issue: beginner, easy, starter
```

## Stale issue handling:
- Comment: "This issue has been inactive for 30 days. Is this still relevant?"
- Add "stale" label
- Close after 60 days if no response (with user approval)

## Example output:
```
✅ Triaged 23 issues across 5 repos
   - 15 auto-labeled
   - 3 marked stale
   - 1 closed (resolved)
   
Recent issues needing attention:
- uCore #42: "API timeout" (needs reproduction steps)
- forge #18: "Memory leak" (awaiting fix)
```
