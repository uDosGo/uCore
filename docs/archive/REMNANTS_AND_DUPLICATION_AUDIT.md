# Remnants and Duplication Audit

Date: 2026-06-21

## Scope

Audit requested areas:
- previous migration remnants
- snackmachine/snackbar/snackshack duplication
- tray icon/menu restoration
- original system snacks restoration

## Findings

1. MCP bridge duplication remnants
- Found six unreferenced split files under backend/app/services/mcp/:
  - mcp_bridge_bridge.py
  - mcp_bridge_health.py
  - mcp_bridge_other.py
  - mcp_bridge_peers.py
  - mcp_bridge_skills.py
  - mcp_bridge_snacks.py
- Canonical implementation already exists in backend/app/services/mcp/__init__.py.

Action:
- Removed all six duplicate remnants.

2. Snackbar vs system snacks mismatch
- Existing tray menu read /api/snacks queue items, not fixed system snacks.
- This broke parity with original macOS snack behavior.

Action:
- Added dedicated system snacks API and switched menu integration to system snacks.

3. Snackshack model gap
- No explicit packaged spec for the 8 core snacks.

Action:
- Added docs/SNACKS_SYSTEM_SPEC.md with catalog, endpoints, and operational notes.

## Current Canonical Components

- Queue orchestration: backend/app/services/snackbar_orchestrator.py
- System snacks execution: backend/app/menu/system_snacks.py
- MCP bridge canonical: backend/app/services/mcp/__init__.py
- **Tray integration: backend/app/menu/unified_menu_simple.py** (streamlined menu)

## Recommended Next Cleanup

1. ~~Decide whether backend/app/ui/popcorn.py remains a separate tray app or merges into snackbar_menu.py.~~ ✅ **DONE** - Merged into unified_menu.py
2. ~~Align launchd naming and startup commands for menu app and core daemon.~~ ✅ **DONE**
3. ~~Add tests for /api/snacks/system endpoints and tray-facing behavior.~~ ✅ **DONE**
4. ~~Deprecate `popcorn.py` and `snackbar_menu.py` with redirect stubs.~~ ✅ **DONE** - Files archived, stubs removed
5. ✅ **DONE** - Simplified menu to essential items only, full snack management in SnackMachine surface
6. ✅ **DONE** - Consolidated launchd installation logic into `launchd_manager.py` (single source of truth)

## Launchd Consolidation (2026-06-28)

**Problem**: 5 different files contained duplicate launchd plist generation logic:
- `install_macos_menu.py` - CLI installer
- `unified_menu.py` - legacy menu (has ObjC class conflicts)
- `unified_menu_simple.py` - streamlined menu
- `popcorn_manager.py` - backward compatibility wrapper
- `system_snack.py` - snack plugin

**Solution**: Created `backend/app/menu/launchd_manager.py` as single source of truth:
- `install()` - install launchd plist
- `uninstall()` - uninstall launchd plist
- `is_installed()` - check if installed
- `is_running()` - check via lockfile
- `get_status()` - full status dict
- `get_plist_content()` - generate plist (used by all callers)

All 5 files now delegate to `launchd_manager.py`, ensuring consistent behavior and eliminating drift.
