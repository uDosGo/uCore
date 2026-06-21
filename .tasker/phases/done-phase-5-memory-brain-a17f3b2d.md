# Phase 5: Memory / Brain Layer
- status: done
- source: ucore-dev
- source_id: phase-5
- synced_at: 2026-06-21T23:30:00Z

## Summary
Upgrade brain_sync to synthesize spool events + AppFlowy activity → wisdom.md. Add wisdom.md injection to attach_context.

## Metadata
- area: memory
- priority: medium
- depends_on: phase-4
- orchestrator: Cline

## Sub-tasks

### T5.1 Spool event synthesis
- status: done
- Created app/services/spool_reader.py — unified activity feed reader
- Parses ~/.ucore/logs/*.log into SpoolEntry dataclass with UDOS-ID tagging
- Auto-tags: error, success, skill, backup, sync, container
- summarize_spool() generates Markdown summary for brain_sync
- Spool API: GET /api/spool/feed and GET /api/spool/summary
- SPOOL_SPEC.md written
- 16 tests passing

### T5.2 Context injection
- status: done
- attach_context already supports include_wisdom=True
- wisdom.md injected as "Episodic Project Memory" section alongside CONTEXT.md

### T5.3 Wisdom durability
- status: done
- backup.py now includes wisdom.md, secrets.enc alongside database
- Maintenance scheduler uses include_spool=True, include_appflowy=True
- brain_sync _render_wisdom() includes Spool Activity section
