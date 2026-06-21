# uCore Spool/Activity Feed — Spec

**Version:** 2.0
**Status:** Active
**Component:** uCore backend + brain_sync
**Purpose:** A unified, searchable log of all uCore ecosystem activity — skill executions,
system events, AppFlowy operations, clipboard events — exposed as a spool feed for
the clipboard popover Logs tab, brain_sync synthesis, and MCP tools.

---

## 1. Core Concept — The Activity Feed as a Spool

The **Activity Feed** reads from `~/.ucore/logs/*.log` files, parsing structured log
entries into a queryable event stream.

| Concept | Implementation |
|---------|----------------|
| **Feed source** | `~/.ucore/logs/*.log` (append-only log files) |
| **Parser** | `backend/app/services/spool_reader.py` |
| **Feed viewer** | MCP tools + clipboard popover Logs tab (future) |
| **Real-time updates** | File watcher (future, via IPC) |
| **Search & filter** | By level, module, date, full-text |
| **Actionable** | Log entries link to skill re-execution (future) |

## 2. Log Entry Format

```python
@dataclass
class SpoolEntry:
    timestamp: str    # ISO 8601
    level: str        # INFO, WARNING, ERROR, DEBUG, CRITICAL
    source: str       # log file name
    module: str       # module identifier
    message: str      # log message
    raw: str          # original line
    tags: list[str]   # auto-tagged
    metadata: dict    # structured metadata (future)
```

## 3. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/spool/feed | Recent spool entries with filters |
| GET | /api/spool/summary | Markdown summary for brain_sync |

## 4. Integration

- **brain_sync**: Calls `summarize_spool()` → includes "Spool Activity" section in wisdom.md
- **backup**: Includes wisdom.md alongside database + secrets
- **attach_context**: Injects wisdom.md alongside CONTEXT.md (include_wisdom=True)
- **MCP (future)**: `skill_read_spool`, `skill_search_spool`
