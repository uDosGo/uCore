# USX Typography System — Usage Guide

## Overview

The USX typography system provides a global, responsive font-size hierarchy with runtime switching capability. It's designed for 10-foot displays with responsive scaling down for desktop/tablet/mobile.

### Quick Start

1. **Base Import**: Already loaded globally via `nestframe.css` → `usx-typography-scale.css`
2. **No setup needed** — just use the CSS variables or utility classes

---

## Typography Hierarchy

### Sizes (Base 10-foot profile)

| Level | Use Case | Base Size | Line Height |
|-------|----------|-----------|-------------|
| **Display** | Hero text, landing page | 44px | 1.2 |
| **H1** | Page titles | 32px | 1.25 |
| **H2** | Section headers | 24px | 1.33 |
| **H3** | Subsection headers | 20px | 1.4 |
| **Body** | Main content, default | 14px | 1.6 |
| **Meta** | Supporting text (0.8em) | 11.2px | 1.5 |

### Responsive Scaling

- **10-foot** (TV/Large display): 100% — ideal readability at distance
- **Desktop/Laptop** (1025px+): 80% of 10-foot = smaller proportional sizes
- **Tablet** (768px–1024px): 80% = same as desktop
- **Mobile** (≤767px): 65% = more compact for small screens

---

## Usage Methods

### Method 1: CSS Variables (Recommended for Components)

Use CSS variables directly in your styles:

```css
.my-heading {
  font-size: var(--usx-font-size-h2);
  font-weight: var(--usx-font-weight-heading);
  line-height: var(--usx-line-height-h2);
  letter-spacing: var(--usx-letter-spacing-heading);
}

.my-meta {
  font-size: var(--usx-font-size-meta);
  color: var(--pico-muted-color);
}
```

### Method 2: Utility Classes (Quick Styling)

Add utility classes to HTML elements:

```html
<h2 class="usx-h2">Section Title</h2>
<p class="usx-body">Regular paragraph text.</p>
<small class="usx-meta">Supporting information</small>
```

### Method 3: HTML Element Defaults

Elements automatically use the appropriate scale:

```html
<h1>Page Title</h1>           <!-- Uses usx-font-size-h1 -->
<h2>Section</h2>              <!-- Uses usx-font-size-h2 -->
<h3>Subsection</h3>           <!-- Uses usx-font-size-h3 -->
<p>Body text</p>              <!-- Uses usx-font-size-body -->
<small>Meta text</small>       <!-- Uses usx-font-size-meta -->
```

---

## CSS Variables Reference

### Font Size Variables

```css
--usx-font-size-display: 44px (base)
--usx-font-size-h1: 32px (base)
--usx-font-size-h2: 24px (base)
--usx-font-size-h3: 20px (base)
--usx-font-size-body: 14px (base)
--usx-font-size-meta: calc(14px * 0.8) = 11.2px (base)
```

### Font Weight Variables

```css
--usx-font-weight-display: 700
--usx-font-weight-heading: 600
--usx-font-weight-body: 400
--usx-font-weight-meta: 500
```

### Font Family Variables

```css
--usx-font-family-display: (inherits Pico)
--usx-font-family-heading: (inherits Pico)
--usx-font-family-body: (inherits Pico)
--usx-font-family-mono: 'SF Mono', 'Fira Code', 'JetBrains Mono'
```

### Line Height Variables

```css
--usx-line-height-display: 1.2
--usx-line-height-h1: 1.25
--usx-line-height-h2: 1.33
--usx-line-height-h3: 1.4
--usx-line-height-body: 1.6
--usx-line-height-meta: 1.5
```

### Letter Spacing Variables

```css
--usx-letter-spacing-display: -0.02em
--usx-letter-spacing-heading: -0.01em
--usx-letter-spacing-body: 0
--usx-letter-spacing-meta: 0.01em
```

---

## Runtime Scaling — Switching Profiles

To force a specific scale regardless of viewport size, set the `data-typography-scale` attribute on the `<html>` element:

### JavaScript Example

```javascript
// Force 10-foot scale for large displays
document.documentElement.setAttribute('data-typography-scale', '10-foot');

// Force desktop scale (0.8x)
document.documentElement.setAttribute('data-typography-scale', 'desktop-compact');

// Force mobile scale (0.65x)
document.documentElement.setAttribute('data-typography-scale', 'mobile-compact');

// Reset to automatic (removes attribute)
document.documentElement.removeAttribute('data-typography-scale');
```

### Available Profiles

| Profile | Scale | Use Case |
|---------|-------|----------|
| `10-foot` | 100% | TVs, large displays, presentations |
| `desktop-compact` | 80% | Desktop/laptop computers |
| `mobile-compact` | 65% | Mobile phones, compact layouts |
| *(none / auto)* | Auto | Responsive based on viewport |

---

## Component Typography Reference

### Navigation

```css
.global-toolbar-nav-btn {
  font-size: var(--usx-font-size-body);
  font-weight: var(--usx-font-weight-body);
}
```

### Buttons

```css
button, .btn, .hub-btn {
  font-size: var(--usx-font-size-body);
  font-weight: var(--usx-font-weight-heading);
}

button.small, .btn.small {
  font-size: var(--usx-font-size-meta);
  font-weight: var(--usx-font-weight-body);
}
```

### Badges & Pills

```css
.badge, .pill, .tag {
  font-size: var(--usx-font-size-meta);
  font-weight: var(--usx-font-weight-heading);
  line-height: var(--usx-line-height-meta);
}
```

### Card Titles & Subtitles

```css
.card-title, .hub-card-title {
  font-size: var(--usx-font-size-h3);
  font-weight: var(--usx-font-weight-heading);
}

.card-subtitle, .hub-card-subtitle {
  font-size: var(--usx-font-size-meta);
  color: var(--pico-muted-color, #8b949e);
}
```

### Dialog/Modal

```css
.dialog-title, .modal-title {
  font-size: var(--usx-font-size-h2);
  font-weight: var(--usx-font-weight-heading);
}

.dialog-body {
  font-size: var(--usx-font-size-body);
  line-height: var(--usx-line-height-body);
}
```

### Prose/Markdown

```css
.prose, .markdown, article {
  font-size: var(--usx-font-size-body);
  line-height: var(--usx-line-height-body);
}
```

---

## Customization

### Override Global Font

To change the font for all typography levels, update the variables:

```css
:root {
  --usx-font-family-display: 'Georgia', serif;
  --usx-font-family-heading: 'Comic Sans', cursive;
  --usx-font-family-body: 'Custom Font', system-ui;
}
```

### Adjust Scale Factors

To change responsive breakpoints, modify media queries in `usx-typography-scale.css`:

```css
@media (min-width: 1025px) {
  :root {
    /* Adjust multiplier from 0.8 to custom value */
    --usx-font-size-body: calc(14px * 0.75);
  }
}
```

---

## Migration Guide

### From Old System (hardcoded sizes)

**Before:**
```css
.my-title {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.33;
}
```

**After:**
```css
.my-title {
  font-size: var(--usx-font-size-h2);
  font-weight: var(--usx-font-weight-heading);
  line-height: var(--usx-line-height-h2);
}
/* Or use utility class: class="usx-h2" */
```

---

## Accessibility

### Respects User Preferences

- **Reduced motion**: Animations disabled for users with motion sensitivity
- **High contrast**: Meta text uses bolder weight for better visibility
- **Readable minimum**: All scales maintain WCAG AA readability standards

### Testing Typography

```javascript
// Check computed values
const heading = document.querySelector('h2');
const computedStyle = window.getComputedStyle(heading);
console.log('Font size:', computedStyle.fontSize);
console.log('Line height:', computedStyle.lineHeight);
```

---

## Browser Support

- **Modern browsers**: Chrome, Firefox, Safari, Edge (all recent versions)
- **CSS Variables**: Universal support in modern browsers
- **Fallback**: All variables have hardcoded fallbacks
- **Mobile**: iOS Safari 12.2+, Android 5.0+

---

## Troubleshooting

### Sizes Not Changing?

1. Ensure `usx-typography-scale.css` is imported **before** other styles
2. Check selector specificity — inline styles or `!important` override variables
3. Verify `nestframe.css` is loaded (which auto-imports the typography module)

### Text Too Small on Mobile?

- Check `data-typography-scale` attribute — may be forcing a specific profile
- Verify media query breakpoints match your device
- Test with browser DevTools device emulation

### Font Not Changing?

- Update `--usx-font-family-body` (and other family variables) in `:root {}`
- Ensure font is available/loaded (via `@font-face` if custom)
- Check `font-family` inheritance chain

---

## File Structure

```
frontend/src/styles/
├── nestframe.css                    (imports usx-typography-scale.css)
├── usx/
│   ├── usx-typography-scale.css    (main module — DO NOT EDIT MANUALLY)
│   ├── usx-pico-integration.css    (uses typography scales)
│   └── usx-icons.css               (icon sizing)
└── TYPOGRAPHY_USAGE.md             (this file)
```

---

## Contact & Questions

For issues with the typography system, check:
1. **Font sizes not responding?** → Verify `data-typography-scale` attribute
2. **Responsive scaling broken?** → Check media query breakpoints in `usx-typography-scale.css`
3. **Custom font not working?** → Override `--usx-font-family-*` variables
