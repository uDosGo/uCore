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
7. Native floating clipboard panel with search, selection, paste, pin, delete, refresh, and close actions.

Files:

- backend/app/menu/unified_menu.py (unified menu with clipboard panel)
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

## Implemented Panel (Phase 2)

The tray app now includes a first native floating clipboard panel opened from the
menu entry "Open Clipboard Popover".

Current panel behavior:

1. Search field backed by clipboard API search.
2. Native table list for recent/saved items.
3. Paste without closing the panel.
4. Pin/unpin selected item.
5. Delete selected item.
6. Refresh, capture, and close controls.
7. Keyboard behavior: Enter pastes, Esc closes, Cmd+Delete deletes, Down Arrow moves from search to results.

Current limitations:

1. It is a floating utility panel rather than a fully anchored NSPopover.
2. Global shortcut registration is still pending.
3. Keyboard behavior is implemented for core actions, but broader navigation polish is still possible.

## Next Implementation Steps

1. Refine panel anchoring so it tracks the tray icon more precisely.
2. Add global shortcut registration (MASShortcut path or Carbon fallback).
3. Persist popover UI preferences (size/position/behavior).
4. Upgrade utility panel to a stricter NSPopover-style presentation if needed.
5. Add richer keyboard polish for pin toggling and focus cycling.

## API Endpoints Used by Tray/Popover

- GET /api/snacks/clipboard
- GET /api/snacks/clipboard/search?q=...
- POST /api/snacks/clipboard/capture
- POST /api/snacks/clipboard/{item_id}/paste
- POST /api/snacks/clipboard/{item_id}/pin
- DELETE /api/snacks/clipboard/{item_id}
- POST /api/snacks/clipboard/cleanup
- POST /api/snacks/clipboard/clear
