# Phase 4: Docs Consolidation → uDocs (Milestone A)
- status: done
- source: ucore-dev
- source_id: phase-4
- synced_at: 2026-06-21T23:30:00Z

## Summary
Consolidate distributed documentation into uDocs so architecture, API, and operational knowledge have one canonical home. Populate canonical uDocs sections from current uCore sources.

## Metadata
- area: docs
- priority: high
- provider: openrouter/o3-mini (medium, ~$0.01/task)
- orchestrator: Cline (primary) + Roundtable (parallel tasks)

## Sub-tasks

### T4.1 Scaffold uDocs architecture docs
- status: done
- overview.md (2.1KB), data-flow.md (new), security.md (new), ADR-001/002/003

### T4.2 Populate API reference
- status: done
- rest-api.md (4.2KB), mcp-bridge.md (new), websocket.md (new), secrets.md (in security.md)

### T4.3 Populate runbooks
- status: done
- development.md (1.8KB), deployment.md (new), backup-recovery.md (1.4KB), troubleshooting.md (new), appflowy-sync.md (1.4KB)

### T4.4 Populate surface docs
- status: done
- assistui.md, devstudio.md (1.5KB), ceefax.md (1.8KB), browserui.md, gridui.md, userver.md, system-surface.md, bbcsdl.md, dashboard.md

### T4.5 Create README.md for uCore
- status: done
- README.md with badges, architecture overview, endpoint reference, status

### T4.6 Archive/redirect duplicated docs
- status: done
- Deprecation notices added to GITHUB_AUTOMATION.md, GITHUB_SKILLS_SUMMARY.md, TASKER_MARKDOWN_WORKFLOW.md
