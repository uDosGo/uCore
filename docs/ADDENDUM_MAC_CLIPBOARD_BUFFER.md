# Addendum: Mac-Friendly Copy-Paste Buffer (Snackbar Spool Integration)

Version: 1.0  
Status: Proposed + v0 backend implementation  
Component: Snackbar / uConnect

## Purpose

Provide a persistent, searchable, automatable clipboard history for macOS that
stays local-first and integrates with Snackbar spool events.

## Implemented in v0 (This Repo)

1. Clipboard buffer service with JSONL + SQLite index.
2. Snack API endpoints for save, capture, list, search, pin, paste, delete, cleanup.
3. AI snack integration logs prompt/reply and places reply into system clipboard.
4. Markdown snack integration logs input/output to clipboard buffer.
5. Polling clipboard watcher utility for local launchd/manual use.

## Storage

- JSONL spool: ~/Library/Application Support/Snackbar/clipboard.jsonl
- SQLite index: ~/Library/Application Support/Snackbar/clipboard.db
- Image cache dir: ~/Library/Application Support/Snackbar/images/

## API Surface

- GET /api/snacks/clipboard
- GET /api/snacks/clipboard/search?q=...
- POST /api/snacks/clipboard/capture
- POST /api/snacks/clipboard/save
- POST /api/snacks/clipboard/{item_id}/pin
- POST /api/snacks/clipboard/{item_id}/paste
- DELETE /api/snacks/clipboard/{item_id}
- POST /api/snacks/clipboard/cleanup

## Data Shape

Each logical item includes:

```json
{
  "id": "clip_20260621_143022_ab12cd34",
  "timestamp": "2026-06-21T14:30:22Z",
  "source": "user_copy",
  "type": "text",
  "content": "Meeting notes: ...",
  "metadata": {
    "app": "Safari",
    "url": "https://...",
    "file_path": "/path/to/file"
  },
  "pinned": false
}
```

## Watcher

Watcher utility:

- backend/app/menu/clipboard_watcher.py

Example:

```bash
cd /Users/fredbook/Code/uCore/backend
python -m app.menu.clipboard_watcher --interval 0.8 --max-items 500 --max-days 30
```

## Remaining Roadmap Items

1. Native menu popup and global shortcuts (cmd+shift+V, cmd+shift+F, cmd+shift+P).
2. Rich formats (RTF/images/files) ingestion from NSPasteboard APIs.
3. UI settings panel for app include/exclude and retention policy.
4. Optional FTS indexing for larger history sets.
