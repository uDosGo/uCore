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
- Tray integration: backend/app/menu/snackbar_menu.py

## Recommended Next Cleanup

1. Decide whether backend/app/ui/popcorn.py remains a separate tray app or merges into snackbar_menu.py.
2. Align launchd naming and startup commands for menu app and core daemon.
3. Add tests for /api/snacks/system endpoints and tray-facing behavior.
