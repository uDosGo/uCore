# Episodic Log Runbook

Status: Active
Path: `.episodic/corrections.jsonl`
Owner: uCore memory layer

## Purpose

The episodic log is the durable correction and lesson history for uCore.
It records events that should outlast a single brain_sync session, including
mistakes that were fixed, important decisions, and recurring patterns worth
flagging for future AI context sessions.

Entries are preserved even as `wisdom.md` is refreshed with each brain_sync
run. The episodic log feeds into the `## Episodic Log` section of wisdom.md.

## Entry Types

| Type | When to use |
|---|---|
| `correction` | A mistake was found and fixed |
| `lesson` | A pattern or principle was learned |
| `decision` | An architectural or workflow decision was made |
| `observation` | A recurring pattern or anomaly worth noting |

## Severity Levels

| Level | Meaning |
|---|---|
| `low` | Minor fix or informational note |
| `medium` | Moderate impact; affects a subsystem or workflow |
| `high` | Major impact; affects architecture, security, or stability |

## How to Write an Entry

### Via skill API

```http
POST /api/skills/episodic_log/run
Content-Type: application/json

{
  "type": "correction",
  "description": "Fixed missing settings import in attach_context",
  "context": "Surfaced by test_skills_memory.py",
  "severity": "medium",
  "tags": ["python", "import"]
}
```

### Via MCP call

```json
{
  "name": "episodic_log",
  "arguments": {
    "type": "lesson",
    "description": "Use apply_patch for multi-file edits to reduce context usage",
    "severity": "low"
  }
}
```

### Direct Python

```python
from app.services.episodic_store import append_entry

append_entry(
    entry_type="decision",
    description="DocLang export format is JSONL with doclang+ai_context keys",
    context="Established in docs/DOCLANG_BRIDGE_EXPORT_SPEC.md",
    severity="medium",
    tags=["doclang", "architecture"],
    source="handover",
)
```

## Storage Format

Entries are stored as newline-delimited JSON (JSONL) at:

```
.episodic/corrections.jsonl
```

Each line is a JSON object:

```json
{
  "timestamp": "2026-06-22T04:15:00+00:00",
  "type": "correction",
  "description": "Fixed missing settings import in attach_context",
  "context": "Surfaced by test_skills_memory.py",
  "severity": "medium",
  "tags": ["python", "import"],
  "source": "skill"
}
```

## Integration with brain_sync

When `include_episodic: true` (default), `brain_sync` reads recent entries
via `episodic_store.summarize_entries(hours=<window>)` and includes a
`## Episodic Log (last Nh)` section in the refreshed `wisdom.md`.

## Reading Entries

```python
from app.services.episodic_store import read_entries, summarize_entries

# All corrections in last 48h
entries = read_entries(hours=48, entry_type="correction")

# Markdown summary for wisdom synthesis
summary = summarize_entries(hours=24)
```

## Maintenance

The episodic log is append-only. Entries are not pruned automatically.
Old entries can be archived manually by moving `corrections.jsonl` to
a dated file in this folder:

```
.episodic/corrections-2026-06.jsonl
```

A future maintenance task may add automated archival after 90 days.

## Files in This Folder

| File | Purpose |
|---|---|
| `RUNBOOK.md` | This runbook |
| `corrections.jsonl` | Active episodic log (created on first write) |
