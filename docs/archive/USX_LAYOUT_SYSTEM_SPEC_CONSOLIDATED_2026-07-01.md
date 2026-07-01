# USX Layout System — Final Spec

> **Status:** FINAL — Consolidated into `usx-standard.css`
> **Legacy:** Archived at `docs/archive/usx-legacy/`
> **Source:** `frontend-vue/src/styles/usx-standard.css`

---

## 1. Architecture

The USX system is a **single-file CSS** design token + layout system. It provides:

- **Design tokens** (CSS custom properties) for spacing, typography, layout, and color
- **Layout primitives** for full-height surface containers
- **Surface Plate BEM classes** (`.surface__*`) for generated Vue surfaces
- **Component patterns** for cards, sections, grids, tabs, buttons, badges
- **Utility classes** for padding, margin, gap, flex
- **Flat design overrides** for Pico CSS integration
- **Responsive + accessibility** media queries

### File Layout

```
frontend-vue/src/styles/
  usx-standard.css          # THE ONLY FILE — single source of truth

docs/archive/usx-legacy/    # Archived legacy split files
  usx-base.css
  usx-layout-system.css
  usx-spacing-scale.css
  usx-pico-integration.css
  usx-pico-reset.css
  usx-typography-standard.css
  usx-typography-responsive.css
  tokens.css
  surface-host.css
  global-toolbar.css
  USX_LAYOUT_SYSTEM_SPEC.md  # Previous version of this spec
```

---

## 2. Design Tokens

All tokens are defined in `:root` under `--usx-*` namespace.

### Spacing Scale (8px system)

| Token | Value | Use |
|-------|-------|-----|
| `--usx-spacing-xs` | 4px | Tight gaps, badge padding |
| `--usx-spacing-sm` | 8px | Button padding, card gaps |
| `--usx-spacing-md` | 12px | Section gaps, compact padding |
| `--usx-spacing-lg` | 16px | Card padding, section padding |
| `--usx-spacing-xl` | 24px | Main content padding, topbar padding |
| `--usx-spacing-2xl` | 32px | Wide content padding |

### Component Tokens

| Token | Default | Purpose |
|-------|---------|---------|
| `--usx-card-padding-vertical` | 14px | Card Y padding |
| `--usx-card-padding-horizontal` | 16px | Card X padding |
| `--usx-card-gap` | 8px | Card child gap |
| `--usx-section-padding` | 16px | Section padding |
| `--usx-section-gap` | 12px | Section child gap |
| `--usx-compact-padding` | 12px | Compact container padding |
| `--usx-compact-gap` | 6px | Compact container gap |
| `--usx-button-padding-vertical` | 8px | Button Y padding |
| `--usx-button-padding-horizontal` | 16px | Button X padding |
| `--usx-button-gap` | 4px | Button icon/text gap |
| `--usx-badge-padding-vertical` | 2px | Badge Y padding |
| `--usx-badge-padding-horizontal` | 8px | Badge X padding |
| `--usx-grid-gap` | 12px | Default grid gap |
| `--usx-grid-gap-dense` | 8px | Dense grid gap |
| `--usx-grid-gap-loose` | 16px | Loose grid gap |
| `--usx-sidebar-gap` | 8px | Sidebar child gap |
| `--usx-sidebar-padding` | 12px | Sidebar padding |

### Surface Plate Tokens

| Token | Default | Purpose |
|-------|---------|---------|
| `--usx-surface-header-padding` | `var(--usx-spacing-lg) var(--usx-spacing-xl)` | Surface header |
| `--usx-surface-content-padding` | `var(--usx-spacing-xl)` | Surface content area |
| `--usx-surface-tab-bar-padding` | `var(--usx-spacing-xs) var(--usx-spacing-sm)` | Tab bar |
| `--usx-surface-tab-padding` | `var(--usx-spacing-sm) var(--usx-spacing-md)` | Individual tab |
| `--usx-surface-topbar-height` | 48px | Topbar height |
| `--usx-surface-topbar-padding` | `0 var(--usx-spacing-xl)` | Topbar padding |

### Typography

| Token | Value |
|-------|-------|
| `--usx-font-family` | `'Inter', system-ui, -apple-system, ...` |
| `--usx-font-family-mono` | `'Menlo', 'Monaco', 'Courier New', monospace` |
| `--usx-font-size-xs` | 0.75rem |
| `--usx-font-size-sm` | 0.875rem |
| `--usx-font-size-base` | 1rem |
| `--usx-font-size-lg` | 1.125rem |
| `--usx-font-size-xl` | 1.25rem |
| `--usx-line-height-tight` | 1.4 |
| `--usx-line-height-base` | 1.6 |
| `--usx-line-height-relaxed` | 1.8 |

### Layout Constraints

| Token | Value |
|-------|-------|
| `--usx-max-width` | 1280px |
| `--usx-prose-width` | 72ch |
| `--usx-sidebar-width` | 280px |
| `--usx-topbar-height` | 48px |

### Border Radius

| Token | Value |
|-------|-------|
| `--usx-border-radius-sm` | 4px |
| `--usx-border-radius-md` | 6px |
| `--usx-border-radius-lg` | 8px |
| `--usx-border-radius-full` | 999px |

### Component Heights

| Token | Value |
|-------|-------|
| `--usx-input-height` | 40px |
| `--usx-input-height-sm` | 32px |
| `--usx-input-height-lg` | 44px |

---

## 3. Surface Plate BEM Classes

These are the canonical classes for all generated surfaces. **No scoped CSS needed** — just use these classes in the template.

### Root Container

```html
<div class="surface">
```

Full-height flex column. Use on the outermost element of every surface.

### Header

```html
<header class="surface__header">
  <h1 class="surface__title">Title</h1>
  <p class="surface__description">Description</p>
</header>
```

### Content Area

```html
<div class="surface__content">
  <!-- scrollable main content -->
</div>
```

### Topbar

```html
<header class="surface__topbar">
  <h1 class="surface__topbar-title">Title</h1>
  <div class="surface__topbar-actions">
    <slot name="actions" />
  </div>
</header>
```

### Tab Bar

```html
<div class="surface__tabs">
  <button class="surface__tab surface__tab--active">Tab 1</button>
  <button class="surface__tab">Tab 2</button>
</div>
```

### Footer / Input Area

```html
<footer class="surface__footer">
  <div class="surface__input-row">
    <input />
    <button>Send</button>
  </div>
</footer>
```

### Messages

```html
<div class="surface__messages">
  <div class="surface__message surface__message--user">User message</div>
  <div class="surface__message surface__message--assistant">AI response</div>
</div>
```

### Canvas

```html
<div class="surface__canvas">
  <!-- grid/canvas content -->
</div>
```

### Toolbar

```html
<header class="surface__toolbar">
  <h1 class="surface__topbar-title">Title</h1>
  <div class="surface__toolbar-actions">
    <slot name="toolbar-actions" />
  </div>
</header>
```

### Panel

```html
<div class="surface__panel">
  <h3 class="surface__panel-title">Panel Title</h3>
  <p class="surface__panel-description">Panel description</p>
</div>
```

---

## 4. Plate Templates

Four Cookiecutter templates generate surfaces using the BEM classes above:

| Template | Directory | Key Classes Used |
|----------|-----------|-----------------|
| `surface-basic` | `plates/surface/surface-basic/` | `.surface`, `.surface__header`, `.surface__title`, `.surface__description`, `.surface__content` |
| `surface-tabbed` | `plates/surface/surface-tabbed/` | `.surface`, `.surface__tabs`, `.surface__tab`, `.surface__tab--active`, `.surface__content` |
| `surface-chat` | `plates/surface/surface-chat/` | `.surface`, `.surface__topbar`, `.surface__topbar-title`, `.surface__messages`, `.surface__message`, `.surface__footer`, `.surface__input-row` |
| `surface-grid` | `plates/surface/surface-grid/` | `.surface`, `.surface__toolbar`, `.surface__topbar-title`, `.surface__canvas` |

### Generator Script

```bash
plates/surface/generate_surface.sh
```

Prompts for surface_id, surface_title, surface_description, route_path, and plate_type.

---

## 5. Component Patterns

### Cards

```html
<div class="usx-card">content</div>
```

### Sections

```html
<div class="usx-section">content</div>
```

### Grid

```html
<div class="usx-grid">
  <div>item</div>
  <div>item</div>
</div>
```

Variants: `.usx-grid--dense`, `.usx-grid--loose`

### Tabs

```html
<div class="usx-tabs">
  <button class="usx-tab usx-tab--active">Tab</button>
  <button class="usx-tab">Tab</button>
</div>
```

### Buttons

```html
<button class="usx-button">Default</button>
<button class="usx-button usx-btn--primary">Primary</button>
<button class="usx-icon-button"><span class="material-symbols-outlined">icon</span></button>
```

### Badges

```html
<span class="usx-badge">Default</span>
<span class="usx-badge usx-badge--accent">Accent</span>
<span class="usx-badge usx-badge--success">Success</span>
<span class="usx-badge usx-badge--error">Error</span>
```

---

## 6. Utility Classes

### Padding

`.usx-p-{xs|sm|md|lg|xl|2xl}` — all sides
`.usx-px-{xs|sm|md|lg|xl}` — left + right
`.usx-py-{xs|sm|md|lg|xl}` — top + bottom

### Margin

`.usx-m-{xs|sm|md|lg|xl}` — all sides
`.usx-mb-{xs|sm|md|lg|xl}` — bottom
`.usx-mt-{xs|sm|md|lg|xl}` — top

### Gap

`.usx-gap-{xs|sm|md|lg|xl}`

### Flex

`.usx-flex` — `display: flex`
`.usx-flex-row` — row with center alignment + gap
`.usx-flex-col` — column with gap
`.usx-flex-between` — space-between row
`.usx-flex-center` — centered row
`.usx-items-center` — align-items: center
`.usx-justify-between` — justify-content: space-between

### Reset

`.usx-no-padding` — `padding: 0 !important`
`.usx-no-margin` — `margin: 0 !important`
`.usx-no-gap` — `gap: 0 !important`
`.usx-no-space` — `margin: 0 !important; padding: 0 !important`

---

## 7. Flat Design Overrides

The "Flat Design Overrides" section in `usx-standard.css` strips Pico CSS borders and applies solid backgrounds. These use `!important` intentionally to override Pico's specificity.

**Key overrides:**
- `button, [role="button"], input, textarea, select` — `border: none !important`
- `.usx-topbar, .global-toolbar, [role="banner"]` — `border-bottom: none !important`
- Buttons get solid `background` instead of bordered
- Inputs get solid `background` with no border
- Toolbar tabs use underlined active state

---

## 8. Responsive Breakpoints

| Breakpoint | Changes |
|------------|---------|
| `max-width: 768px` | Font size → 13px, topbar height → 44px, tab labels hidden |

---

## 9. Accessibility

- `prefers-reduced-motion` — disables all animations/transitions
- `*:focus-visible` — blue outline on keyboard focus

---

## 10. Usage Rules

1. **NO hardcoded values in templates.** Always use `--usx-*` tokens or `.surface__*` classes.
2. **NO scoped CSS for layout.** Surface plates should have empty `<style scoped>` blocks.
3. **NO `@import` for Google Fonts.** Fonts load via `<link>` in `index.html`.
4. **NO duplicate utility classes.** All utilities are defined once in `usx-standard.css`.
5. **Surface-specific selectors** (`.assistui-*`, `.filepicker-sidebar__*`, `.browserui-*`) belong in their component's scoped CSS, not in the global stylesheet.
