# Feed System Specification

> **Version:** 1.0
> **Status:** Active
> **Scope:** Activity Pod, Feed MCP Server, FeedConsumer, Feed Panel, Nugget runtime

## 1. Philosophy

The Feed System is the unified incoming data layer that captures all user
activity (browser history, email, messages, alerts, search queries) and
transforms it into actionable development context. It bridges the gap between
external user activity and internal developer workflow.

## 2. Core Definitions

| Term | Definition | Storage |
|------|------------|---------|
| **Feed** | Incoming user activity stream | SQLite (Activity Pod) |
| **Pod** | SQLite database package | `.db` file + schema |
| **Nugget** | Runtime + files | Directory with scripts, configs, assets |
| **Seed** | Initial data/structure | JSON schema, SQL DDL, or template |
| **Slate** | Template system | Directory with manifests |
| **Spool** | Feed in motion | In-memory + JSONL log |

## 3. Architecture

```
User Activity Sources:
  Browser (Chrome/Arc/Safari) → Email (Mail.app) → Messages (iMessage)
  Alerts (Push) → Search Queries → Calendar Events → Clipboard History
        ↓
Feed Ingest Layer (FeedServer MCP)
  - feed_ingest_activity: insert into Activity Pod
  - feed_query: query by source, timeframe, importance
  - feed_suggest_binders: AI-driven binder suggestions
  - feed_link_task: link .tasker task to activity
        ↓
Feed Storage Layer (SQLite Pods)
  - Activity Pod: user_activity, contacts, contexts
  - Feedback: binder_suggestions, task_activity_links
        ↓
Feed Processing Layer (FeedConsumer)
  - Bridges feed → Spool (audit trail)
  - Keyword-based task trigger detection
        ↓
Developer Surface (FeedPanel)
  - View incoming feed
  - Link activities to tasks
  - Review binder suggestions
```

## 4. Pod Schema

**Location:** `backend/schemas/activity.schema.sql`
**Database:** `~/.ucore/pods/activity.db`

Tables:
- `user_activity` — core activity events (source, type, title, content, url, importance)
- `contacts` — synced from macOS Contacts.app
- `contexts` — grouped activities
- `binder_suggestions` — AI-generated binder suggestions
- `task_activity_links` — task-to-activity relationships

Indexes: timestamp, contact_id, source, (source, source_id)

## 5. Feed MCP Server

**Location:** `backend/app/mcp/feed/feed_server.py`
**Class:** `FeedServer`

Tools:
| Tool | Method | Description |
|------|--------|-------------|
| `feed_ingest_activity` | `ingest_activity()` | Insert activity into Pod |
| `feed_query` | `query_feed()` | Query by source, since, limit, importance_min |
| `feed_suggest_binders` | `suggest_binders()` | Cluster unprocessed activities, return suggestions |
| `feed_link_task` | `link_task_to_activity()` | Link task to activity, mark processed |

## 6. Feed API

**Location:** `backend/app/api/feed_api.py`

Routes:
| Method | Path | Handler |
|--------|------|---------|
| POST | `/api/feed/ingest` | `handle_feed_ingest` |
| GET | `/api/feed/query` | `handle_feed_query` |
| GET | `/api/feed/suggest` | `handle_feed_suggest` |
| POST | `/api/feed/link` | `handle_feed_link` |

## 7. FeedConsumer

**Location:** `backend/app/services/feed_consumer.py`
**Class:** `FeedConsumer`

Bridges each ingested activity into the Spool for audit trail. Includes
keyword-based task trigger detection (bug/crash → bug-report, tool/script →
tool-suggestion, doc/guide → doc-suggestion).

## 8. Frontend Feed Store

**Location:** `frontend-vue/src/stores/feed.ts`
**Store:** `useFeedStore`

Provides:
- `fetchActivities(opts)` — query feed with source/since/limit/importanceMin
- `ingestActivity(payload)` — post a new activity
- `fetchSuggestions(minConfidence)` — get binder suggestions
- `linkToTask(taskId, activityId, linkType)` — link task to activity
- `filteredActivities` — reactive filter by source
- `pendingSuggestions` — filtered by min confidence

## 9. Seed Data

**Location:** `backend/seeds/feed-pod-seed.json`

Source configuration for:
- Browser: Chrome, Arc, Safari history paths
- Email: Mail.app MailData path
- Messages: iMessage chat.db path
- Contacts: AddressBook Sources path
- Search, Alerts, Calendar, Clipboard sources

## 10. Integration Points

| System | Connection |
|--------|-----------|
| **Spool** | FeedConsumer writes to spool on each ingest |
| **Tasker** | `feed_link_task` creates `.tasker` link records |
| **Binder** | `feed_suggest_binders` generates binder suggestions |
| **Slate** | Templates include feed config in slate.yaml |
| **Dev Layer** | Feed panel available in Developer Surface |

## 11. Implementation Status

- [x] Activity Pod schema (5 tables, 4 indexes)
- [x] FeedServer with 4 MCP tools
- [x] Feed API routes wired into routes.py
- [x] FeedConsumer bridging feed → Spool
- [x] Frontend Pinia feed store
- [x] Seed data for macOS sources
- [x] .clinerules updated with Feed System rules
- [ ] FeedPanel.vue on Developer Surface (future)
- [ ] Nugget runtime scripts (ingest_browser.py, ingest_email.py, etc.)
- [ ] AI-powered binder suggestion engine (keyword-based placeholder in place)