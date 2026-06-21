# Clipboard Buffer Surface on macOS: Tray + Popover Plan

Date: 2026-06-21  
Status: Active implementation

## What Is Live Now

The macOS tray menu is restored and enhanced with clipboard-buffer workflows.

Implemented in menu:

1. Clipboard section with live count.
2. Search action for clipboard history.
3. Saved (pinned) items and recent items listed directly in tray menu.
4. One-click item restore to clipboard.
5. Capture current clipboard action.
6. Clear history (non-pinned) and clear all actions.

Files:

- backend/app/menu/snackbar_menu.py
- backend/app/api/snacks.py
- backend/app/menu/clipboard_buffer.py

## Why This Is the Right Intermediate Surface

- Native macOS tray access is discoverable and always visible.
- Existing menu flow has low complexity and immediate utility.
- It reuses local-first Snackbar clipboard APIs and spool model.

## Popover Target (Ideal Surface)

Target is a floating popover anchored to the tray icon with:

1. Search bar.
2. Keyboard navigation (up/down, enter).
3. Delete shortcut (cmd+delete).
4. Keep-open multi-paste behavior.
5. Optional global open shortcut (cmd+shift+V).

## Next Implementation Steps

1. Add an NSPanel/NSPopover controller in backend/app/menu/snackbar_menu.py.
2. Render a searchable list view backed by /api/snacks/clipboard endpoints.
3. Add keyboard handlers for enter, esc, cmd+delete.
4. Add global shortcut registration (MASShortcut path or Carbon fallback).
5. Persist popover UI preferences (size/position/behavior).

## API Endpoints Used by Tray/Popover

- GET /api/snacks/clipboard
- GET /api/snacks/clipboard/search?q=...
- POST /api/snacks/clipboard/capture
- POST /api/snacks/clipboard/{item_id}/paste
- POST /api/snacks/clipboard/{item_id}/pin
- DELETE /api/snacks/clipboard/{item_id}
- POST /api/snacks/clipboard/cleanup
- POST /api/snacks/clipboard/clear
