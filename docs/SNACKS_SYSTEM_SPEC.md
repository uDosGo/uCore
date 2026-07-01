> **Canonical version:** `/Users/fredbook/Code/uDocs/surfaces/snackbar.md`
> This repo copy is kept for local reference; edits should be made in uDocs.

# Snacks System Spec (macOS + AI + Markdown)

Date: 2026-06-21
Status: Implemented in uCore backend

## Objective

Restore and modernize the original macOS tray snacks workflow with:
- Core Apple snacks
- Apple Intelligence shortcut-based snack
- Markdown snack backed by markdown-it
- Unified spool logging to replies.jsonl

## Implemented Endpoints

- GET /api/snacks/system
- GET /api/snacks/system/badges
- POST /api/snacks/system/{snack_id}/run

Existing queue endpoints remain intact under /api/snacks for orchestration workflows.

## Snack Catalog

1. reminders (badge, 30s)
2. mail-vip (badge, 60s)
3. contacts-vip (badge, 300s)
4. notes (action)
5. calendar (action)
6. permissions-helper (action)
7. apple-intelligence (multi-action)
- summarise
- rewrite-professional
- compose
8. markdown-tools (multi-action)
- format
- to-html
- validate

## Execution Model

System snacks run from backend/app/menu/system_snacks.py.

- Apple app actions use osascript/open.
- Apple Intelligence uses the shortcuts CLI.
- Markdown actions use backend/tools/markdown_snack/markdown-snack.js.

## Spooling and Audit

Every run appends a JSON line to:
- ~/.local/share/snackmachine/replies.jsonl

Payload includes timestamp, snack_id, action, status, and result or error.

## Tray Menu Integration

backend/app/menu/unified_menu_simple.py now:
- loads snacks from /api/snacks/system
- loads live badge values from /api/snacks/system/badges
- executes system snack actions via /api/snacks/system/{id}/run
- renders multi-action submenu entries

**Note**: Full snack management is available in the SnackMachine surface (http://localhost:5173/snackmachine).

## Dependencies

Markdown snack Node dependency:
- backend/tools/markdown_snack/package.json
- dependency: markdown-it

Install once:

```bash
cd /Users/fredbook/Code/uCore/backend/tools/markdown_snack
npm install
```

## Notes

1. Apple Intelligence requires user-created Shortcuts with expected names.
2. Contacts VIP logic currently uses note text heuristic for VIP.
3. If shortcuts or node are missing, endpoint returns a structured error and spools it.
