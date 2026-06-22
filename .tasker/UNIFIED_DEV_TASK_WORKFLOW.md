# uCore Unified Dev Task Workflow
- status: in-progress
- source: ucore-dev
- source_id: unified-dev-workflow-20260621
- synced_at: 2026-06-21T23:59:59Z

## Purpose

This file is the single source of truth for active development planning, handover actions, and backlog intake.

All plan-oriented documents should point here instead of carrying parallel task lists.

## Compliance Rules

1. One canonical workflow: this file.
2. Task execution units remain in .tasker/phases and .tasker/backlog.
3. Any new plan or handover must register tasks here first.
4. Status vocabulary: todo, in-progress, blocked, done.
5. Every task must include owner lane, priority, and source.

## Workflow Stages

1. Intake: collect tasks from handovers, checklists, incidents.
2. Normalize: map each item to a task id and owner lane.
3. Prioritize: classify as P0, P1, P2.
4. Execute: update status in task files and this index.
5. Verify: attach test or endpoint verification evidence.
6. Close: mark done and move summary into wisdom.md.

## Active Work Queue (Consolidated)

| ID | Status | Priority | Lane | Source | Summary |
|---|---|---|---|---|---|
| UDW-001 | done | P1 | System | Phase 6 | Wire S310 capture and cleanup into overnight maintenance chain |
| UDW-002 | done | P1 | System | Phase 6 | Add spool rotation and cleanup to maintenance scheduler |
| UDW-003 | done | P2 | System UI | Phase 6 | Expose tray and system state in maintenance model/view |
| UDW-004 | done | P1 | MCP | Phase 7 | Add clipboard MCP operations through api/mcp/call |
| UDW-005 | done | P1 | MCP | Phase 7 | Add knowledge MCP operations for workspace, docs, search |
| UDW-006 | done | P1 | Tasker | Phase 7 | Add tasker MCP operations for board/task read and write |
| UDW-007 | done | P1 | Automation | Phase 7 | Schedule tasker sync after vault sync in maintenance chain |
| UDW-008 | done | P1 | AI Runtime | Handover perf | Keep local default on qwen2.5-coder:7b-instruct-q4_K_M |
| UDW-009 | done | P1 | AI Runtime | Handover perf | Route medium and complex workloads to OpenRouter |
| UDW-010 | done | P1 | AI Runtime | Handover perf | Implement local SQLite chat cache in extension/tooling path |
| UDW-011 | done | P1 | AI Runtime | Handover perf | Ensure OpenRouter to local fallback behavior is reliable |
| UDW-012 | done | P2 | Observability | Handover perf | Track latency and cache hit ratio in recurring checks |
| UDW-013 | done | P1 | Docs | Next rounds | Define DocLang bridge export format for AppFlowy and vault |
| UDW-014 | done | P1 | Docs | Next rounds | Add transform step for AI-efficient structured context |
| UDW-015 | done | P2 | Memory | Next rounds | Extend brain sync inputs with spool, AppFlowy, test-failures |
| UDW-016 | done | P2 | Memory | Next rounds | Add episodic log runbook for durable correction history |
| UDW-017 | done | P1 | UI | Next rounds | Add global shortcut open for clipboard panel |
| UDW-018 | done | P2 | UI | Next rounds | Extend maintenance orchestration with richer cleanup tasks |
| UDW-019 | done | P1 | UI | Next rounds | Add clipboard orchestration system page |
| UDW-020 | in-progress | P1 | UI | Next rounds | Add knowledge-local and AppFlowy tools system page |
| UDW-021 | todo | P2 | UI | Next rounds | Add migration and consolidation dashboard view |
| UDW-022 | todo | P2 | Workflow | Next rounds | Add direct Kanban launch and health actions in S300 |
| UDW-023 | todo | P1 | Workflow | Next rounds | Add task detail and board actions in S300 and Developer |
| UDW-024 | todo | P2 | Orchestration | Backlog | Complete Cline plus Roundtable orchestration hardening |
| UDW-025 | todo | P2 | AI UX | Backlog | Build AI provider manager system page |
| UDW-026 | todo | P2 | CLI | Backlog | Build uc CLI for server control and skill execution |
| UDW-027 | done | P1 | Knowledge | Consolidation | Add AppFlowy index coverage endpoint for per-source expected versus indexed tracking |
| UDW-028 | done | P1 | Automation | Consolidation | Add launchd installer script for scheduled AppFlowy import runs |
| UDW-029 | done | P1 | Knowledge | Consolidation | Add workspace mapping script to bind source entries to discovered AppFlowy workspace IDs |
| UDW-030 | done | P1 | UI | Consolidation | Remove legacy GridCore/Labs surface links and reduce active UI surface footprint |
| UDW-031 | in-progress | P1 | UI | Consolidation | Add mission drop panel ingest flow for binder and mission processing |

## Execution Order

1. UDW-001 through UDW-007
2. UDW-008 through UDW-012
3. UDW-019 through UDW-023
4. UDW-013 through UDW-018
5. UDW-024 through UDW-026

## Source Mapping

- Phase files:
  - .tasker/phases/in-progress-phase-6-snackbar-orch-b4c8d1e3.md
  - .tasker/phases/todo-phase-7-mcp-tasker-d6e779f1.md
- Backlog files:
  - .tasker/backlog/todo-cline-orchestration-c901d2e3.md
  - .tasker/backlog/todo-ai-provider-manager-a12b34c5.md
  - .tasker/backlog/todo-ucore-cli-b567d890.md
- Handover sources:
  - HANDOVER.md
  - docs/HANDOVER_UDOS_LOCAL_MODEL_PERFORMANCE.md
- Checklist source:
  - docs/NEXT_ROUNDS_CHECKLIST.md
- Archive snapshot:
  - docs/archive/plans/2026-06-21-plan-migration-snapshot.md

## Update Protocol

1. Edit task detail in phase or backlog file.
2. Update corresponding UDW row status here.
3. Run validation:
   - bash scripts/ai_stack_health_check.sh
4. Record significant outcomes in wisdom.md.
