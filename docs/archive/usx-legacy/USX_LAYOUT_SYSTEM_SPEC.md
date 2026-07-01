# USX Layout System Specification

**Date**: 2026-06-24  
**Version**: 1.0  
**Status**: Production  
**Author**: Cline  

---

## Overview

The **usx-layout-system.css** is the centralized source of truth for all UI layout patterns across uCore surfaces. It provides consistent spacing, sizing, and layout behavior without any color or theme logic.

### Core Principle
**Separation of Concerns**:
- **Layout** (usx-layout-system.css) → Positioning, sizing, spacing, flexbox
- **Theme** (usx-pico-integration.css) → Colors, borders, interactive states
- **Components** (surface-specific CSS) → Specialized styling per surface

---

## CSS Import Order (main.tsx)

```
1. nestframe.css                 ← Pico base + CSS variables
2. usx-spacing-scale.css         ← Spacing tokens (4px, 8px, 12px, 16px, 24px, 32px)
3. usx-pico-reset.css            ← Pico CSS resets
4. usx-layout-system.css         ← LAYOUT (no colors)
5. usx-pico-integration.css      ← Colors/tokens
6. usx-icon-refinement.css       ← Icon sizing
7. typography-global-apply.css   ← Font stack
8. hub/index.css                 ← Hub-specific
9. surface-specific CSS          ← Developer, Workflow, etc.
```

**Why This Order?**
- Layout defined first → safe to override in theme tier
- Theme applied second → uses layout classes without conflicts
- Surface CSS last → inherits both layout + theme

---

## Core Classes

### Global Toolbar / Topbar

**Universal**: Works for all surfaces (Workflow, Developer, AssistUI, etc.)

```css
.global-toolbar,
.assistui-topbar,
.usx-surface-header {
  display: flex;
  align-items: center;
  height: 48px;                               /* Fixed height */
  padding: 0 var(--usx-spacing-xl);          /* 24px sides */
  flex-shrink: 0;
  width: 100%;
  box-sizing: border-box;
  position: sticky;
  top: 0;
  z-index: 100;
}
```

**Structure**:
```
┌─────────────────────────────────────────────────────┐
│ [Left] │ [Middle: flex-1] │ [Right] │ [Far Right]   │
│ 32px   │ Auto             │ 32px    │ No shrink     │
└─────────────────────────────────────────────────────┘
```

- **Left**: Home, Sidebar toggle, Web Reader, AssistUI buttons
- **Middle**: Surface-specific nav tabs (flex: 1, centered)
- **Right**: Additional controls (margin-left: auto, flex-shrink: 0)
- **Far Right**: Dev Mode badge (margin-left: auto, flex-shrink: 0)

### Main Content

```css
.usx-surface-main,
main.usx-surface-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  width: 100%;
  padding: var(--usx-spacing-xl);  /* 24px on all sides */
  box-sizing: border-box;
}
```

**Variants**:
- `.usx-surface-main--compact` → `padding: var(--usx-spacing-md)` (12px)
- `.usx-surface-main--wide` → `padding: var(--usx-spacing-2xl)` (32px)

### Sidebar

```css
.vault-sidebar-wrapper {
  display: flex;
  gap: 0.3rem;
  height: 100%;
  flex-shrink: 0;
}

.vault-sidebar {
  overflow: hidden;
  transition: width 0.2s ease;
}

.vault-sidebar--open {
  width: 280px;
}

.vault-sidebar--closed {
  width: 0;
}
```

### Navigation Buttons

```css
.global-toolbar-nav-btn,
.assistui-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-xs);          /* 4px */
  border: none;
  border-radius: 0;
  cursor: pointer;
  transition: all 100ms ease;
  white-space: nowrap;
  text-decoration: none;
}

.global-toolbar-nav-btn {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);  /* 4px vert, 8px horiz */
  border-bottom: 2px solid transparent;
}
```

---

## Spacing Scale

All spacing uses CSS variables defined in `usx-spacing-scale.css`:

```css
--usx-spacing-xs: 4px      /* Compact inline */
--usx-spacing-sm: 8px      /* Small gaps */
--usx-spacing-md: 12px     /* Standard */
--usx-spacing-lg: 16px     /* Primary padding */
--usx-spacing-xl: 24px     /* Container padding (MAIN) */
--usx-spacing-2xl: 32px    /* Extra large */
```

**Example Usage**:
- Main content: `padding: var(--usx-spacing-xl)` = 24px
- Topbar: `padding: 0 var(--usx-spacing-xl)` = 24px sides
- Nav gaps: `gap: var(--usx-spacing-sm)` = 8px
- Icon spacing: `gap: var(--usx-spacing-xs)` = 4px

---

## Utility Classes

### Flexbox Utilities

```css
.usx-flex-row { display: flex; align-items: center; gap: var(--usx-spacing-md); }
.usx-flex-col { display: flex; flex-direction: column; gap: var(--usx-spacing-md); }
.usx-flex-center { display: flex; align-items: center; justify-content: center; }
```

### Spacing Utilities

```css
.usx-gap-xs/.usx-gap-sm/.usx-gap-md/.usx-gap-lg/.usx-gap-xl

.usx-p-xs/.usx-p-sm/.usx-p-md/.usx-p-lg/.usx-p-xl  /* Padding all sides */

.usx-px-lg/.usx-px-xl  /* Horizontal padding */
.usx-py-md/.usx-py-lg  /* Vertical padding */
```

### Overflow Utilities

```css
.usx-overflow-hidden
.usx-overflow-auto
.usx-overflow-y-auto
.usx-overflow-x-auto
```

### Sizing Utilities

```css
.usx-flex-1 { flex: 1; }
.usx-flex-shrink-0 { flex-shrink: 0; }
.usx-full-height { height: 100%; }
.usx-full-width { width: 100%; }
```

---

## Surface-Specific Patterns

### Workflow Surface
```html
<div class="usx-surface-layout">
  <GlobalToolbar tabs={[...]} />
  <div class="usx-surface-body">
    <VaultSidebar />
    <main class="usx-surface-main">
      {/* Content */}
    </main>
  </div>
</div>
```

### Developer Surface
```html
<div class="usx-surface-layout">
  <GlobalToolbar tabs={[...]} />
  <main class="usx-surface-main">
    {/* Full-width content */}
  </main>
</div>
```

### AssistUI Surface
```html
<div class="assistui-surface">
  <header class="assistui-topbar">
    {/* Topbar content */}
  </header>
  <div class="assistui-main">
    <VaultSidebar />
    <div class="assistui-body">
      <div class="assistui-messages">
        {/* Messages */}
      </div>
      <footer class="assistui-footer">
        {/* Input */}
      </footer>
    </div>
  </div>
</div>
```

---

## Responsive Design

Mobile adjustments (max-width: 768px):

```css
.usx-surface-main {
  padding: var(--usx-spacing-md);  /* 12px instead of 24px */
}

.global-toolbar {
  padding: 0 var(--usx-spacing-md);  /* 12px sides */
}
```

---

## File Structure

```
frontend/src/styles/usx/
├── usx-layout-system.css      ← LAYOUT (centralized) — 500 lines
├── usx-pico-integration.css   ← THEME (colors/tokens)
├── usx-spacing-scale.css      ← Variables (tokens)
├── usx-pico-reset.css         ← Pico resets
├── usx-icons.css              ← Icon sizing
├── usx-typography.css         ← Typography base
└── usx-icon-refinement.css    ← Icon tweaks

frontend/src/styles/
├── global-toolbar.css         ← Component styling only (20 lines)
├── assistui.css               ← Component styling only
├── nestframe.css              ← Pico base
└── [surface-specific CSS]
```

---

## Migration Guide (from old approach)

### Before (Broken)
- Toolbar layout defined in: `global-toolbar.css`, `usx-pico-integration.css`, `assistui.css`
- Main content padding: scattered across multiple files
- Result: Cascading conflicts, sidebar visibility issues

### After (Centralized)
- Toolbar layout defined in: `usx-layout-system.css` (once)
- Main content padding: `usx-layout-system.css` (once)
- Colors/interactions: `usx-pico-integration.css`
- Component styling: Surface-specific CSS

---

## Design Principles

1. **Single Source of Truth**: Each pattern defined once
2. **Cascade Safety**: Layout first, theme second, components last
3. **No Conflicts**: Impossible to accidentally override layout with theme
4. **Easy Maintenance**: Change 24px padding in ONE place
5. **Consistent UX**: All surfaces inherit same layout
6. **Scalable**: Add new surfaces with confidence

---

## Future Roadmap

- [ ] Extract Material Design 3 icons as CDN option
- [ ] Add dark/light theme toggle
- [ ] Create Figma components mirroring layout system
- [ ] Build Storybook with all layout patterns
- [ ] Add animation system (transitions, keyframes)
- [ ] Document mobile-first breakpoints

---

## Contact

For questions or improvements, refer to `.tasker/CSS_CENTRALIZATION_PLAN.md` or create a task in the Kanban board.
