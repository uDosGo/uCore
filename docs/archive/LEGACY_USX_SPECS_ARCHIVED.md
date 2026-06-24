# Legacy USX Specifications (Archived)

**Date Archived**: 2026-06-24  
**Reason**: CSS centralization and layout system refactor  
**Status**: SUPERSEDED by `USX_LAYOUT_SYSTEM_SPEC.md`

## Overview

This document archives the legacy USX specifications that were previously scattered across multiple files. These have been consolidated into a single, centralized layout system.

## Archived Specifications

### 1. Old Approach (Deprecated)
- **global-toolbar.css** - Defined toolbar layout + nav styling → NOW: Only component styling
- **usx-pico-integration.css** - Defined toolbar layout + colors → NOW: Only theme colors
- **assistui.css** - Defined topbar layout → NOW: Only component styling
- **nestframe.css** - Defined main content padding → NOW: usx-layout-system.css
- Scattered surface-specific CSS files → NOW: Centralized usx-layout-system.css

### 2. Problems with Old Approach
- **Cascading Conflicts**: Same patterns defined in multiple files
- **Sidebar Issues**: Visibility problems due to conflicting z-index/width rules
- **Inconsistent Spacing**: 24px padding defined differently in multiple places
- **Maintenance Nightmare**: Change one thing, break three others
- **No Single Source of Truth**: Each file had its own interpretation of "correct"

### 3. What Changed

**Before**:
```
global-toolbar.css
├─ .global-toolbar { display: flex; padding: 0 16px; ... }
├─ .global-toolbar-nav { flex: 1; justify-content: center; ... }
└─ .global-toolbar-nav-btn { padding: 4px 8px; ... }

usx-pico-integration.css
├─ .global-toolbar { background: var(--pico-card-background-color); ... }
├─ .global-toolbar-nav { margin: 0; padding: 0; ... }  ← CONFLICT
└─ .global-toolbar-nav-btn { color: var(--pico-muted-color); ... }

assistui.css
├─ .assistui-topbar { padding: 0 24px; ... }  ← Different from global-toolbar!
└─ (more topbar styling)
```

**After**:
```
usx-layout-system.css (SINGLE SOURCE OF TRUTH)
├─ .global-toolbar { display: flex; height: 48px; padding: 0 24px; ... }
├─ .assistui-topbar { inherit from .global-toolbar }
├─ .global-toolbar-nav { flex: 1; justify-content: center; ... }
└─ .global-toolbar-nav-btn { padding: 4px 8px; ... }

usx-pico-integration.css (COLORS ONLY)
├─ .global-toolbar { background: var(--pico-card-background-color); }
├─ .global-toolbar-nav-btn { color: var(--pico-muted-color); }
└─ (no layout conflicts)
```

## New Standard

**See**: `docs/USX_LAYOUT_SYSTEM_SPEC.md` for the production specification.

### Key Files (Current)
- `frontend/src/styles/usx/usx-layout-system.css` - Single source of truth for layout
- `frontend/src/styles/usx/usx-pico-integration.css` - Colors/theme only
- `frontend/src/styles/global-toolbar.css` - Component styling only (20 lines)
- `frontend/src/styles/assistui.css` - Component styling only

### CSS Import Order (main.tsx)
1. nestframe.css (Pico base)
2. usx-spacing-scale.css (variables)
3. usx-pico-reset.css (resets)
4. **usx-layout-system.css** ← NEW (layout)
5. usx-pico-integration.css (colors)
6. [rest of CSS]

## Migration Notes for Future Developers

### If You Need to Modify Toolbar
1. **Layout changes** → `frontend/src/styles/usx/usx-layout-system.css`
   - Padding, height, flex behavior, spacing

2. **Color/theme changes** → `frontend/src/styles/usx/usx-pico-integration.css`
   - Background, borders, text color, hover states

3. **Component-specific styling** → `frontend/src/styles/global-toolbar.css`
   - Font sizes, specific button behavior, transitions

### If You Need to Modify Main Content
1. **Layout** → `usx-layout-system.css` (`.usx-surface-main`)
2. **Colors** → `usx-pico-integration.css`
3. **Surface-specific** → Surface CSS files (developer.css, workflow.css, etc.)

### Common Gotchas to Avoid
- ❌ Don't add layout rules to `usx-pico-integration.css`
- ❌ Don't add color rules to `usx-layout-system.css`
- ❌ Don't define `.global-toolbar` in multiple files
- ❌ Don't use hardcoded pixel values (use `var(--usx-spacing-*)`)

✅ Do:
- Keep layout and theme separated
- Use centralized `usx-layout-system.css`
- Use spacing variables consistently
- Test all surfaces when making layout changes

## History

**2026-06-24**: Centralization complete
- Created `usx-layout-system.css`
- Removed duplicate toolbar/layout rules
- Fixed import order in main.tsx
- Verified no cascading conflicts
- Updated topbar and sidebar visibility
- Fixed Dev Mode badge overlapping issue

## For Reference

Old planning documents are in: `/docs/archive/usx-planning/`

---

**DO NOT REVERT THESE CHANGES** — The centralized approach is production-ready and solves all cascading issues. If you find a bug, trace it to the specific CSS file (layout, theme, or component) and fix it at the source.
