# Legacy Menu Bar Apps (Archived)

**Date Archived**: 2026-06-27  
**Reason**: Unified into single `unified_menu_simple.py`  
**Status**: SUPERSEDED by `backend/app/menu/unified_menu_simple.py`

## Overview

Three generations of macOS menu bar apps have been consolidated:

### Archived Files
1. **`backend/app/ui/popcorn.py`** - Ollama/UI Hub manager (🍿 icon)
2. **`backend/app/menu/snackbar_menu.py`** - Clipboard/Snacks/Surfaces (🍔 icon)
3. **`backend/app/menu/archived/unified_menu.py`** - Full-featured unified menu (superseded, archived 2026-06-28)

## What Changed

### Before: Two Separate Apps
```
popcorn.py (🍿)
├─ Ollama status/checking
├─ Ollama controls (start/stop/restart)
├─ UI Hub health/heal
├─ Backend daemon management
└─ S190 fallback page

snackbar_menu.py (🍔)
├─ Clipboard buffer
├─ Clipboard panel (NSPanel)
├─ Global shortcut (Ctrl+Cmd+V)
├─ Snacks from /api/snacks/system
├─ Surfaces menu (8 predefined)
├─ Start at login toggle
└─ Backend/frontend restart
```

### After: Streamlined Unified App
```
unified_menu_simple.py (🍿)
├─ UI Hub status and access
├─ Quick access to SnackMachine surface
├─ Clipboard buffer (essential)
├─ Backend status
├─ Start at login toggle
└─ Single lockfile: ~/.ucore/ucore-menu.pid
```

**Note**: Full snack management moved to SnackMachine surface (http://localhost:5173/snackmachine)

## Migration Notes

- **Icon**: Kept 🍿 Popcorn emoji (more distinctive)
- **Lockfile**: Consolidated to `~/.ucore/ucore-menu.pid`
- **Launchd**: Updated to point to `unified_menu_simple.py`
- **API**: All endpoints preserved, same backend integration
- **Launchd Manager**: Single source of truth in `launchd_manager.py`

## Rollback

If needed, the original implementations can be restored from git history:
```bash
git checkout HEAD~1 -- backend/app/ui/popcorn.py
git checkout HEAD~1 -- backend/app/menu/snackbar_menu.py
```