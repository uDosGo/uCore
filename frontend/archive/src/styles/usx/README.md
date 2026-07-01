# USX Typography System v3.0

**Document ID:** USX-TYPOGRAPHY-003  
**Status:** Active, Mandatory  
**Date:** 2026-06-26  
**Purpose:** Dynamic typography system with Prose UI integration, Pico.css support, and multi-palette support

---

## Overview

The USX Typography System v3.0 is a **dynamic, consolidated typography system** that provides:

- **Dynamic font scaling** via `--font-base` variable
- **Prose UI integration** for markdown content
- **Pico.css integration** for UI components
- **Light/dark mode** support
- **Multiple palette support** (blue, green, purple, orange, red, pink, cyan, yellow)
- **Font family selection** (sans, serif, mono)
- **Viewport-based scaling** (mobile, tablet, desktop, TV)
- **Multi-column prose** extension

---

## Quick Start

### Import Order

```css
/* 1. Pico.css (component framework) */
@import '@picocss/pico/css/pico.min.css';

/* 2. USX Typography System */
@import './usx/usx-typography-standard.css';

/* 3. USX Spacing Scale */
@import './usx/usx-spacing-scale.css';

/* 4. USX Base (layout primitives) */
@import './usx/usx-base.css';
```

### Basic Usage

```tsx
// SurfaceComponent.tsx
import './styles.css';

export default function SurfaceComponent() {
  return (
    <div className="surface-container">
      <header className="surface-header">
        <h1>Surface Title</h1>
      </header>
      <main className="surface-main">
        <div className="prose">
          <h1>Lesson Title</h1>
          <p>This is paragraph one.</p>
          <p>This is paragraph two.</p>
        </div>
      </main>
    </div>
  );
}
```

```css
/* styles.css */
@import '@picocss/pico/css/pico.min.css';
@import './usx/usx-typography-standard.css';
@import './usx/usx-spacing-scale.css';
@import './usx/usx-base.css';
```

---

## Dynamic Variables

### Font Base (Controls ALL Text Scaling)

```css
:root {
  --font-base: 16px;  /* Default: Mobile */
}

/* Viewport overrides */
@media (max-width: 720px)  { :root { --font-base: 16px; } }
@media (min-width: 721px) and (max-width: 1280px) { :root { --font-base: 18px; } }
@media (min-width: 1281px) and (max-width: 1799px) { :root { --font-base: 20px; } }
@media (min-width: 1800px) { :root { --font-base: 32px; } }  /* TV */
```

**Result:** Changing `--font-base` automatically scales ALL text (Prose UI, Pico, headings, body, UI components).

### Font Families

```css
:root {
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-serif: 'Merriweather', Georgia, serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}
```

### Light/Dark Mode

```html
<!-- Light mode -->
<html data-theme="light">
  <!-- Content -->
</html>

<!-- Dark mode (default) -->
<html data-theme="dark">
  <!-- Content -->
</html>
```

### Palettes

```html
<!-- Blue palette (default) -->
<html data-palette="blue">
  <!-- Content -->
</html>

<!-- Green palette -->
<html data-palette="green">
  <!-- Content -->
</html>

<!-- Purple palette -->
<html data-palette="purple">
  <!-- Content -->
</html>

<!-- Orange palette -->
<html data-palette="orange">
  <!-- Content -->
</html>

<!-- Red palette -->
<html data-palette="red">
  <!-- Content -->
</html>

<!-- Pink palette -->
<html data-palette="pink">
  <!-- Content -->
</html>

<!-- Cyan palette -->
<html data-palette="cyan">
  <!-- Content -->
</html>

<!-- Yellow palette -->
<html data-palette="yellow">
  <!-- Content -->
</html>
```

### Font Styles

```html
<!-- Sans-serif (default) -->
<html data-font-style="sans">
  <!-- Content -->
</html>

<!-- Serif -->
<html data-font-style="serif">
  <!-- Content -->
</html>

<!-- Monospace -->
<html data-font-style="mono">
  <!-- Content -->
</html>
```

---

## Prose UI Integration

### Basic Prose

```css
.prose {
  font-family: var(--p-font-family-sans);
  font-size: var(--p-font-size);
  line-height: 1.6;
  max-width: 72ch;
  color: var(--pico-color);
}
```

### Multi-Column Prose

```tsx
import MultiColumnProse from './multi-column-prose';

export default function LessonSurface() {
  return (
    <MultiColumnProse>
      <h1>Lesson Title</h1>
      <p>This is paragraph one.</p>
      <p>This is paragraph two, which will flow into column 2 on wide screens.</p>
    </MultiColumnProse>
  );
}
```

```css
/* Automatically imported from usx-typography-standard.css */
.prose-multi {
  column-width: 280px;
  column-gap: var(--usx-spacing-lg, 1.5rem);
  column-rule: 1px solid var(--pico-border-color);
  column-fill: balance;
  max-width: 100%;
}

/* Responsive column counts */
@media (max-width: 720px) {
  .prose-multi {
    column-width: auto;
    column-count: 1;
  }
}

@media (min-width: 721px) and (max-width: 1280px) {
  .prose-multi {
    column-count: auto;
    column-width: 300px;
  }
}

@media (min-width: 1281px) and (max-width: 1799px) {
  .prose-multi {
    column-count: auto;
    column-width: 350px;
  }
}

@media (min-width: 1800px) {
  .prose-multi {
    column-count: auto;
    column-width: 400px;
  }
}
```

---

## Viewport Scaling Profiles

| Viewport | `--font-base` | Body Text | Use Case |
|----------|---------------|-----------|----------|
| Mobile (≤720px) | 16px | 16px | Small screens, phones |
| Tablet (721-1280px) | 18px | 18px | Tablets, laptops |
| Desktop (1281-1799px) | 20px | 20px | Standard desktops |
| TV/Ultrawide (≥1800px) | 32px | 32px | 10-foot viewing |

**Key Principle:** ONE value (`--font-base`) controls ALL text sizes across ALL viewports.

---

## File Structure

```
frontend/src/styles/
├── usx/
│   ├── README.md                          # This file
│   ├── usx-typography-standard.css        # Dynamic typography system
│   ├── usx-spacing-scale.css              # Spacing scale
│   ├── usx-base.css                       # Layout primitives
│   ├── usx-pico-integration.css           # Pico integration
│   ├── usx-pico-reset.css                 # Pico reset
│   ├── usx-layout-system.css              # Layout system
│   ├── usx-icon-refinement.css            # Icon refinement
│   ├── usx-icons.css                      # Icon styles
│   ├── multi-column-prose.css             # Multi-column prose extension
│   └── legacy/                            # Archived old files
│       ├── usx-typography-scale.css       # v2.0 (archived)
│       ├── usx-typography-prose.css       # v2.0 (archived)
│       ├── usx-typography.css             # v2.0 (archived)
│       └── typography-global-apply.css    # v2.0 (archived)
├── nestframe.css                          # Main entry point
└── ...
```

---

## Surface Template

```tsx
// SurfaceTemplate.tsx
import './styles.css';

export default function SurfaceTemplate() {
  return (
    <div className="surface-container">
      <header className="surface-header">
        <h1>Surface Title</h1>
      </header>
      <main className="surface-main">
        <div className="prose">
          <h1>Lesson Title</h1>
          <p>This is paragraph one.</p>
          <p>This is paragraph two.</p>
        </div>
      </main>
    </div>
  );
}
```

```css
/* styles.css */
@import '@picocss/pico/css/pico.min.css';
@import './usx/usx-typography-standard.css';
@import './usx/usx-spacing-scale.css';
@import './usx/usx-base.css';

/* Surface layout */
.surface-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.surface-header {
  padding: var(--usx-spacing-md);
  border-bottom: 1px solid var(--pico-border-color);
}

.surface-main {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-xl);
}

.surface-content {
  max-width: 72ch;
  margin: 0 auto;
}
```

---

## Migration Guide

### From v2.0 to v3.0

**Old v2.0 imports:**
```css
@import '@picocss/pico/css/pico.min.css';
@import './prose-ui-standard.css';
@import './usx/usx-typography-scale.css';
@import './usx/usx-typography-prose.css';
```

**New v3.0 imports:**
```css
@import '@picocss/pico/css/pico.min.css';
@import './usx/usx-typography-standard.css';
@import './usx/usx-spacing-scale.css';
@import './usx/usx-base.css';
```

**Key Changes:**
1. Consolidated all typography into `usx-typography-standard.css`
2. Removed hardcoded font sizes
3. Added dynamic `--font-base` system
4. Added light/dark mode support
5. Added palette support
6. Added font style support
7. Multi-column prose is now built-in

---

## Audit Checklist

### Prose UI Check
- [ ] Prose UI library installed and imported
- [ ] Markdown content uses `.prose` class
- [ ] No custom CSS for markdown elements
- [ ] Prose UI tokens (`--p-*`) are used

### Pico Check
- [ ] Pico.css imported
- [ ] Semantic HTML used
- [ ] Pico variables (`--pico-*`) are used

### NestFrame Check
- [ ] `--font-base` defined
- [ ] TV override uses `--font-base: 32px`
- [ ] No hardcoded font sizes

### Dynamic Variables Check
- [ ] Light/dark mode configured
- [ ] Palette selected
- [ ] Font style selected
- [ ] Viewport scaling works

---

## Common Violations & Fixes

### Violation 1: Hardcoded px Values

**Problem:**
```css
/* ❌ VIOLATION */
h1 { font-size: 2.5rem; }
.sidebar { font-size: 14px; }
```

**Fix:**
```css
/* ✅ CORRECT */
:root {
  --font-base: 16px;
}

.prose h1 {
  font-size: var(--p-h1-font-size);
}

.sidebar {
  font-size: calc(var(--font-base) / 16px * 100%);
}
```

### Violation 2: Missing Dynamic Variables

**Problem:**
```html
<!-- ❌ VIOLATION - No theme/palette/font-style -->
<html>
  <!-- Content -->
</html>
```

**Fix:**
```html
<!-- ✅ CORRECT -->
<html data-theme="dark" data-palette="blue" data-font-style="sans">
  <!-- Content -->
</html>
```

---

## Quick Reference

```css
/* === THE ONE SOURCE OF TRUTH === */
:root {
  --font-base: 16px;  /* ← Change this for ALL text scaling */
}

/* === MAP TO PROSE UI === */
.prose {
  font-size: calc(var(--font-base) / 16px * 1rem);
  font-family: var(--font-sans);
}

/* === MAP TO PICO === */
body, .sidebar, .main-content {
  font-size: calc(var(--font-base) / 16px * 100%);
  font-family: var(--font-sans);
}

/* === VIEWPORT OVERRIDES (ONE VALUE EACH) === */
@media (max-width: 720px)  { :root { --font-base: 16px; } }
@media (max-width: 1280px) { :root { --font-base: 18px; } }
@media (max-width: 1799px) { :root { --font-base: 20px; } }
@media (min-width: 1800px) { :root { --font-base: 32px; } }  /* 10-foot */
```

---

## Summary

| Problem | Solution |
|---------|----------|
| Body and sidebar different sizes | Both use `--font-base` |
| Hardcoded sizes | All sizes use `--font-base` calculations |
| Prose UI vs Pico mismatch | Both map to `--font-base` |
| TV (10-foot) scaling | ONE variable (`--font-base: 32px`) |
| Duplicate/conflicting code | Consolidated into `usx-typography-standard.css` |
| No light/dark mode | Use `data-theme` attribute |
| No palette support | Use `data-palette` attribute |
| No font style selection | Use `data-font-style` attribute |

**The rule:** One value (`--font-base`) controls ALL text sizes across ALL viewports. No exceptions. No duplicates. No hardcoding.

---

## Support

For issues or questions, refer to:
- [USX Font Standards](./USX-FONTS-002.md)
- [Audit Skill](./audit-usx-font-standards.md)
- [Audit Script](../../scripts/audit-fonts.sh)