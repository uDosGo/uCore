# CSS Centralization Plan - uCore UI System

## Current Problem
We have 9+ CSS files defining overlapping styles:
- `nestframe.css` - Base surface layout
- `global-toolbar.css` - Toolbar specific
- `usx-pico-integration.css` - Pico nav integration (also defines toolbar)
- `assistui.css` - AssistUI specific (also defines topbar)
- `vault-sidebar.css` - Sidebar
- Individual surface CSS (developer.css, workflow.css, etc)
- Typography-global-apply.css

**Result**: Conflicts, cascading issues, sidebar not showing, styles not applying

## Solution: Centralized Layout System

### New File Hierarchy (in main.tsx import order):

1. **usx-layout-system.css** (NEW - CORE)
   - All shared layout patterns
   - Global toolbar/topbar standardization (24px padding)
   - Main content padding
   - Sidebar spacing
   - No color/theme (defer to Pico)

2. **usx-pico-integration.css**
   - Pico variable integration only
   - Remove toolbar/nav duplication
   - Link Pico colors to components

3. **Surface-specific CSS**
   - Only component-specific styling
   - No layout rules
   - No toolbar/main/sidebar patterns

### Key Principles:

1. **Single Toolkit (usx-layout-system.css)**
   - `.global-toolbar` - 24px sides, flex row
   - `.usx-surface-main` - 24px padding
   - `.vault-sidebar-wrapper` - standard width
   - `.assistui-topbar` - inherits from .global-toolbar base
   - All surfaces use same layout classes

2. **No Duplication**
   - Remove toolbar styles from: global-toolbar.css, usx-pico-integration.css, assistui.css
   - Remove layout from surface-specific CSS
   - Source of truth: usx-layout-system.css

3. **Import Order (main.tsx)**
   ```
   1. nestframe.css (Pico base)
   2. usx-layout-system.css (LAYOUT ONLY)
   3. usx-pico-integration.css (COLORS/TOKENS)
   4. surface-specific CSS
   5. typography-global-apply.css
   ```

### Files to Create/Modify

**CREATE:**
- `usx-layout-system.css` - Centralized layout patterns

**REFACTOR:**
- `global-toolbar.css` → Remove all styling, import from usx-layout-system
- `usx-pico-integration.css` → Keep only Pico color/token integration
- `assistui.css` → Remove toolbar/layout, use base classes

**RESULT:**
- Single source of truth for layout
- Predictable CSS cascade
- Easy to modify spacing globally
- Surfaces inherit consistent patterns
