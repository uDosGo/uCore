# USX Typography v3.0 Migration Guide

**Document ID:** USX-MIGRATION-001  
**Status:** Active  
**Date:** 2026-06-26  
**Purpose:** Guide for migrating from USX v2.0 to v3.0

---

## Overview

This guide helps you migrate existing surfaces from USX Typography v2.0 to v3.0, which consolidates all typography into a single dynamic system.

---

## Migration Steps

### Step 1: Update Import Order

**Before (v2.0):**
```css
@import '@picocss/pico/css/pico.min.css';
@import './prose-ui-standard.css';
@import './usx/usx-typography-scale.css';
@import './usx/usx-typography-prose.css';
```

**After (v3.0):**
```css
@import '@picocss/pico/css/pico.min.css';
@import './usx/usx-typography-standard.css';
@import './usx/usx-spacing-scale.css';
@import './usx/usx-base.css';
```

### Step 2: Remove Hardcoded Font Sizes

**Before (v2.0):**
```css
/* ❌ Remove these */
h1 { font-size: 2.5rem; }
.sidebar { font-size: 14px; }
.prose h1 { font-size: 2rem; }
```

**After (v3.0):**
```css
/* ✅ Use dynamic variables */
.prose h1 {
  font-size: var(--p-h1-font-size);
}

.sidebar {
  font-size: calc(var(--font-base) / 16px * 100%);
}
```

### Step 3: Add Dynamic Variables

**Before (v2.0):**
```html
<!-- ❌ No theme/palette/font-style -->
<html>
  <!-- Content -->
</html>
```

**After (v3.0):**
```html
<!-- ✅ Add dynamic variables -->
<html data-theme="dark" data-palette="blue" data-font-style="sans">
  <!-- Content -->
</html>
```

### Step 4: Update Surface Components

**Before (v2.0):**
```tsx
import './styles.css';

export default function MySurface() {
  return (
    <div className="surface-container">
      <header className="surface-header">
        <h1>Surface Title</h1>
      </header>
      <main className="surface-main">
        <div className="prose">
          <h1>Lesson Title</h1>
          <p>This is paragraph one.</p>
        </div>
      </main>
    </div>
  );
}
```

**After (v3.0):**
```tsx
import './styles.css';

export default function MySurface() {
  return (
    <div className="surface-container">
      <header className="surface-header">
        <h1>Surface Title</h1>
      </header>
      <main className="surface-main">
        <div className="prose">
          <h1>Lesson Title</h1>
          <p>This is paragraph one.</p>
        </div>
      </main>
    </div>
  );
}
```

**Note:** No changes needed to surface components! The CSS handles everything.

### Step 5: Test Viewport Scaling

**Test at different viewports:**
- Mobile (≤720px): `--font-base: 16px`
- Tablet (721-1280px): `--font-base: 18px`
- Desktop (1281-1799px): `--font-base: 20px`
- TV (≥1800px): `--font-base: 32px`

**Test light/dark mode:**
```html
<html data-theme="light">
  <!-- Content -->
</html>

<html data-theme="dark">
  <!-- Content -->
</html>
```

**Test palettes:**
```html
<html data-palette="blue">
  <!-- Content -->
</html>

<html data-palette="green">
  <!-- Content -->
</html>

<html data-palette="purple">
  <!-- Content -->
</html>

<html data-palette="orange">
  <!-- Content -->
</html>

<html data-palette="red">
  <!-- Content -->
</html>

<html data-palette="pink">
  <!-- Content -->
</html>

<html data-palette="cyan">
  <!-- Content -->
</html>

<html data-palette="yellow">
  <!-- Content -->
</html>
```

**Test font styles:**
```html
<html data-font-style="sans">
  <!-- Content -->
</html>

<html data-font-style="serif">
  <!-- Content -->
</html>

<html data-font-style="mono">
  <!-- Content -->
</html>
```

---

## Common Migration Issues

### Issue 1: Font Sizes Look Different

**Cause:** Old hardcoded sizes vs new dynamic sizes

**Fix:** Remove all hardcoded font sizes and use CSS variables

### Issue 2: Light/Dark Mode Not Working

**Cause:** Missing `data-theme` attribute on `<html>` element

**Fix:** Add `data-theme="dark"` (or "light") to `<html>` element

### Issue 3: Palette Not Applied

**Cause:** Missing `data-palette` attribute on `<html>` element

**Fix:** Add `data-palette="blue"` (or other palette) to `<html>` element

### Issue 4: Font Style Not Applied

**Cause:** Missing `data-font-style` attribute on `<html>` element

**Fix:** Add `data-font-style="sans"` (or "serif", "mono") to `<html>` element

### Issue 5: Multi-Column Prose Not Working

**Cause:** Using old `.prose-multi` class instead of `<MultiColumnProse>` component

**Fix:** Import and use the `<MultiColumnProse>` component

```tsx
import MultiColumnProse from './multi-column-prose';

export default function LessonSurface() {
  return (
    <MultiColumnProse>
      <h1>Lesson Title</h1>
      <p>This is paragraph one.</p>
      <p>This is paragraph two.</p>
    </MultiColumnProse>
  );
}
```

---

## Surface-by-Surface Migration Checklist

### Surface: [name] (S[number])

- [ ] Update import order in CSS file
- [ ] Remove hardcoded font sizes
- [ ] Add dynamic variables to `<html>` element
- [ ] Test light/dark mode
- [ ] Test palette
- [ ] Test font style
- [ ] Test viewport scaling
- [ ] Run audit script
- [ ] Verify no violations

---

## Audit After Migration

Run the audit script to verify compliance:

```bash
./scripts/audit-fonts.sh
```

Expected results:
- ✅ No hardcoded font sizes
- ✅ No duplicate heading styles
- ✅ No sidebar font size issues
- ✅ `--font-base` system properly defined
- ✅ Prose UI properly used
- ✅ Pico.css imported
- ✅ TV (10-foot) override found

---

## Rollback Plan

If migration fails, rollback to v2.0:

1. Restore archived files from `frontend/src/styles/usx/legacy/`
2. Update imports back to v2.0
3. Remove dynamic variables from `<html>` element
4. Restore hardcoded font sizes

---

## Support

For issues or questions:
- [USX Typography v3.0 README](../usx/README.md)
- [USX Font Standards](../usx/USX-FONTS-002.md)
- [Audit Skill](./audit-usx-font-standards.md)
- [Audit Script](../../scripts/audit-fonts.sh)