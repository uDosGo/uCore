# USX Font Sizing Standards — June 26, 2026

## Overview
uCore frontend uses a **responsive typography system** with viewport-aware scaling and a strict hierarchy to ensure proportional consistency across Small (mobile), Medium (tablet), and Large (desktop) screens.

**Core Principle**: All font sizes are **relative (em-based)** except the CSS variable root `--usx-base-font-size` set by `useGlobalSettings` hook. Icons and sidebar text scale automatically with body text.

---

## Typography Scale Profiles

### Base Scale Hierarchy (10-foot profile — default)
All elements start from this baseline, then scale down for smaller viewports:

| Level | Base Size | Line Height | Usage |
|-------|-----------|-------------|-------|
| **Display** | 44px | 1.2 | Landing, hero headings |
| **H1** | 32px | 1.25 | Page titles |
| **H2** | 24px | 1.33 | Section titles |
| **H3** | 20px | 1.4 | Subsection titles |
| **Body** | 14px | 1.6 | Primary content |
| **Meta** | 11.2px (14 × 0.8) | 1.5 | Secondary, muted text |

### Viewport-Specific Scaling
Mobile/tablet viewports scale ALL typography automatically:

| Viewport | Breakpoint | Scale | Applied To |
|----------|-----------|-------|-----------|
| **Desktop** | 1025px+ | **1.0x** (base) | Display/H1/H2/H3/Body/Meta |
| **Tablet** | 768–1024px | **0.8x** | All sizes shrink proportionally |
| **Mobile** | <768px | **0.65x** | All sizes shrink proportionally |

**Media Queries** (in `usx-typography-scale.css`):
```css
/* Mobile: 65% of base */
@media (max-width: 767px) {
  :root:not([data-typography-scale]) {
    --usx-font-size-body: calc(14px * 0.65);
    /* h1, h2, h3, display scale proportionally */
  }
}

/* Tablet: 80% of base */
@media (min-width: 768px) and (max-width: 1024px) {
  :root:not([data-typography-scale]) {
    --usx-font-size-body: calc(14px * 0.8);
  }
}
```

---

## Sidebar & Navigation Font Sizing

### ✅ Correct Patterns (Match Body Size)
- **Sidebar nav items** (file names): `1em` (inherit body font size)
- **Sidebar metadata** (counts, dates): `0.8em` (meta text scale)
- **Navigation labels**: `1em` (match body)
- **Search inputs**: `1em` (match body)

### ❌ Hardcoded Overrides (Anti-Pattern — Remove)
❌ Sidebar nav: ~~`0.8em`~~ → Changed to `1em`  
❌ Search input: ~~`0.92em`~~ → Changed to `1em`  

**Rationale**: Sidebar text should match body font size in all viewports. Meta text (counts, timestamps) stay at 0.8em multiplier.

---

## Icon Sizing

### ✅ Canonical Rule
**Icons match adjacent text font-size.** SVG icons use `font-size` to scale.

### Icon Size Classes

| Class | Default | Tablet | Mobile | Usage |
|-------|---------|--------|--------|-------|
| Inline/Button icons | `1em` | `1em` | `1em` | Adjacent to text (no media override needed) |
| Card/header icons | `1em` | `1em` | `1em` | In section titles |
| **Large empty-state icons** | `2.5em` | `2.0em` (0.8×) | `1.625em` (0.65×) | Binder/browser empty states, **NOW RESPONSIVE** |

### Large Icon Classes (Now Responsive)
The following classes now scale per viewport:

```css
.hub-card-icon.large svg,
.sys-page-icon svg,
.binder-empty-icon svg,
.browserui-empty-icon svg,
.mc-drop-panel-icon svg,
.assistui-conv-empty svg
```

Applied media queries:
```css
@media (max-width: 767px) { font-size: calc(2.5em * 0.65); }
@media (min-width: 768px) and (max-width: 1024px) { font-size: calc(2.5em * 0.8); }
```

---

## Font Weight Hierarchy

| Level | Weight | Usage |
|-------|--------|-------|
| Display | 700 | Hero text |
| Headings (H1/H2/H3) | 600 | Titles |
| Body | 400 | Paragraph text |
| Meta | 500 | Supporting labels |
| Sidebar buttons | 500 | Navigation labels |

---

## Color Palette Integration

Font sizes are **independent of color** — use CSS variables for colors:
- `var(--pico-color)` — Primary text
- `var(--pico-muted-color)` — Meta/secondary text
- `var(--pico-primary)` — Accent/interactive

---

## Best Practices & Guidelines

### ✅ DO:
- ✅ Use `em` units for all text sizing (relative to parent font-size)
- ✅ Define font-size in root CSS variables (`--usx-font-size-*`)
- ✅ Use media queries to scale proportionally by viewport
- ✅ Let icons inherit `font-size: 1em` from parent elements
- ✅ Use `0.8em` multiplier ONLY for meta/secondary text (counts, timestamps, hints)
- ✅ Test on Small/Medium/Large screens for proportion consistency

### ❌ DON'T:
- ❌ Hardcode `px` sizes directly in component CSS (use `em` or CSS variables)
- ❌ Break sidebar/body proportions with arbitrary sizing (e.g., `0.78em`, `0.92em`)
- ❌ Set large icons to fixed `2.5em` without media queries
- ❌ Use different font-size scales per surface (maintain global standards)
- ❌ Nest `font-size` multipliers deeply (keep hierarchy flat)

---

## Files Modified (Jun 26, 2026)

1. **`frontend/src/styles/vault-sidebar.css`**
   - ✅ Changed `.vault-sidebar-search-input` from `0.92em` → `1em`
   - ✅ Kept metadata sizes at `0.8em` (correct)

2. **`frontend/src/styles/usx/usx-icons.css`**
   - ✅ Added media queries to large icon classes (`.hub-card-icon.large svg`, `.sys-page-icon svg`, etc.)
   - ✅ Tablet: `calc(2.5em * 0.8)` = `2.0em`
   - ✅ Mobile: `calc(2.5em * 0.65)` = `1.625em`
   - ✅ Same responsive treatment for `.bi` (Bootstrap Icons) classes

3. **`frontend/src/styles/usx/usx-typography-scale.css`**
   - ✅ No changes needed (already correct with 0.65x, 0.8x scaling)

---

## Testing Checklist

After changes, verify on:

- [ ] **Small Screen (≤767px)**: Body text matches sidebar, icons not oversized
- [ ] **Medium Screen (768–1024px)**: Body/sidebar proportions consistent, icons scaled 0.8x
- [ ] **Large Screen (1025px+)**: Full 10-foot scale, icons at 2.5em
- [ ] **Sidebar**: File names match body size, metadata stays 0.8em
- [ ] **Empty States**: Large icons scale proportionally (not fixed)
- [ ] **Navigation**: Button/nav items inherit text font-size via `1em`

---

## Related Documentation

- `usx-typography-scale.css` — Root typography variables & media queries
- `usx-icons.css` — Icon sizing standards (canonical source)
- `useGlobalSettings.ts` — Hook for switching typography profiles at runtime

---

## Future Considerations

1. **Runtime Typography Switching**: `useGlobalSettings` supports `data-typography-scale` attribute for forcing 10-foot/desktop-compact/mobile-compact scales.
2. **Custom Font Sizes**: When adding new components, always use CSS variables (`var(--usx-font-size-body)`) rather than hardcoding.
3. **A/B Testing**: Measure readability impact of font size changes before rolling out to all users.
