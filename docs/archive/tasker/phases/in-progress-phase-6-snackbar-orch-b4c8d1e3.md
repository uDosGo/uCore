# Phase 6: Snackbar / System Orchestration
- status: done
- source: ucore-dev
- source_id: phase-6
- synced_at: 2026-06-21T23:59:59Z

## Summary
Wire clipboard capture into overnight maintenance chain. Keep clipboard, tray menu, and spool logging under one orchestration model.

## Metadata
- area: system
- priority: medium
- depends_on: phase-4
- orchestrator: Cline

## Sub-tasks

### T6.1 Clipboard maintenance integration
- status: done
- Add clipboard cleanup to daily maintenance chain
- Wire S310 capture/cleanup to overnight schedule

### T6.2 Spool logging to maintenance
- status: done
- Add spool rotation to maintenance scheduler
- Track popover/global-shortcut work under system orchestration

### T6.3 Tray menu
- status: done
- Add tray menu surface state to maintenance model
