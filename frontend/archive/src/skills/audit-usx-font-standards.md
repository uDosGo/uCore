# USX Font Standards Audit Skill

**Document ID:** USX-FONTS-AUDIT-001  
**Status:** Active  
**Date:** 2026-06-26  
**Purpose:** Audit surfaces against USX Prose UI font standards and identify violations

---

## Overview

This skill audits surfaces for compliance with the USX Prose UI font standards (USX-FONTS-002). It checks for:

1. **Hardcoded font sizes** (px values instead of CSS variables)
2. **Duplicate/conflicting CSS** (multiple sources for same styles)
3. **Inconsistent font sizes** (body vs sidebar, different viewports)
4. **Prose UI violations** (markdown content not using Prose UI tokens)
5. **Pico.css violations** (UI components not using Pico variables)
6. **NestFrame violations** (missing --font-base system)

---

## Audit Checklist

### Prose UI Check (Markdown Content)
- [ ] Prose UI library installed and imported
- [ ] Markdown content uses `.prose` class
- [ ] No custom CSS for markdown elements (headings, body, lists, code, tables)
- [ ] Prose UI tokens (`--p-*`) are used, not hardcoded values

### Pico Check (UI Components)
- [ ] Pico.css imported
- [ ] Semantic HTML used (no custom classes for buttons, forms, cards)
- [ ] Pico variables (`--pico-*`) are used, not hardcoded values

### NestFrame Check (Gaps)
- [ ] `--font-base` defined and used for both Pico and Prose UI
- [ ] TV (10-foot) override uses `--font-base: 32px`
- [ ] No hardcoded font sizes anywhere (px values)

### Violations Found
- [ ] Hardcoded px values — [list]
- [ ] Sidebar font size different from body — [list]
- [ ] Inconsistent meta sizes — [list]
- [ ] Duplicate/conflicting CSS — [list]

### Fixes Applied
- [ ] Replaced hardcoded px with variables
- [ ] Unified body/sidebar font sizes via `--font-base`
- [ ] Standardized meta text via Prose UI
- [ ] Removed duplicate/conflicting code

---

## Audit Script

Run the audit script to automatically detect violations:

```bash
#!/bin/bash
# audit-fonts.sh

echo "🔍 Auditing for font size violations..."

# Check for hardcoded font sizes
echo "--- Hardcoded font sizes (violation): ---"
grep -rn "font-size:[^;]*px" --include="*.css" --include="*.jsx" . | \
  grep -v "var(--" | \
  grep -v "calc(" | \
  grep -v "prose-ui" | \
  grep -v "pico" || echo "None found ✅"

# Check for duplicate heading styles
echo "--- Duplicate heading styles (violation): ---"
grep -rn "h1\b\|h2\b\|h3\b" --include="*.css" . | \
  grep -v "prose-ui" | \
  grep -v "pico" | \
  grep -v "nestframe" | \
  grep -v "\.prose" || echo "None found ✅"

# Check for conflicting sidebar styles
echo "--- Sidebar font sizes (should use --font-base): ---"
grep -rn ".sidebar" --include="*.css" . | \
  grep "font-size:" | \
  grep -v "var(--font-base)" || echo "None found ✅"

echo "✅ Font audit complete."
```

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

### Violation 2: Sidebar Font Size Different from Body

**Problem:**
```css
/* ❌ VIOLATION */
body { font-size: 16px; }
.sidebar { font-size: 14px; }
```

**Fix:**
```css
/* ✅ CORRECT */
:root {
  --font-base: 16px;
}

body, .sidebar {
  font-size: calc(var(--font-base) / 16px * 100%);
}
```

### Violation 3: Duplicate Heading Styles

**Problem:**
```css
/* ❌ VIOLATION - Multiple sources */
h1 { font-size: 2.5rem; }
.prose h1 { font-size: 2.5rem; }
.usx-prose h1 { font-size: 2rem; }
```

**Fix:**
```css
/* ✅ CORRECT - Use ONE source */
.prose h1 {
  font-size: var(--p-h1-font-size);
}
```

### Violation 4: Missing --font-base System

**Problem:**
```css
/* ❌ VIOLATION - No unified scaling */
@media (max-width: 720px) { .sidebar { font-size: 14px; } }
@media (min-width: 721px) { .sidebar { font-size: 18px; } }
```

**Fix:**
```css
/* ✅ CORRECT - Unified scaling */
:root {
  --font-base: 16px;
}

@media (max-width: 720px)  { :root { --font-base: 16px; } }
@media (min-width: 721px) and (max-width: 1280px) { :root { --font-base: 18px; } }
@media (min-width: 1281px) and (max-width: 1799px) { :root { --font-base: 20px; } }
@media (min-width: 1800px) { :root { --font-base: 32px; } }  /* 10-foot */
```

---

## Surface Template

Use this template for new surfaces:

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
        <div className="surface-content">
          {/* Prose UI for markdown content */}
          <div className="prose">
            <h1>Lesson Title</h1>
            <p>This is paragraph one.</p>
            <p>This is paragraph two.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
```

```css
/* styles.css */
@import '@picocss/pico/css/pico.min.css';
@import './prose-ui-standard.css';

/* Unified font system */
:root {
  --font-base: 16px;
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-serif: 'Merriweather', Georgia, serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

/* Map to Prose UI */
:root {
  --p-font-size: calc(var(--font-base) / 16px * 1rem);
  --p-font-family-sans: var(--font-sans);
  --p-font-family-serif: var(--font-serif);
  --p-font-family-mono: var(--font-mono);
}

/* Map to Pico */
:root {
  --pico-font-size: calc(var(--font-base) / 16px * 100%);
  --pico-font-family: var(--font-sans);
}

/* Viewport overrides */
@media (max-width: 720px)  { :root { --font-base: 16px; } }
@media (min-width: 721px) and (max-width: 1280px) { :root { --font-base: 18px; } }
@media (min-width: 1281px) and (max-width: 1799px) { :root { --font-base: 20px; } }
@media (min-width: 1800px) { :root { --font-base: 32px; } }

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

## Audit Report Template

```markdown
## Surface: [name] (S[number])
**Auditor:** [name]
**Date:** [date]

### Prose UI Check
- [x] Prose UI library installed and imported
- [x] Markdown content uses `.prose` class
- [x] No custom CSS for markdown elements
- [x] Prose UI tokens are used

### Pico Check
- [x] Pico.css imported
- [x] Semantic HTML used
- [x] Pico variables are used

### NestFrame Check
- [x] `--font-base` defined
- [x] TV override uses `--font-base: 32px`
- [x] No hardcoded font sizes

### Violations Found
None ✅

### Fixes Applied
None

### Notes
Surface is fully compliant with USX font standards.
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
| Duplicate/conflicting code | DELETE all but one source |

**The rule:** One value (`--font-base`) controls ALL text sizes across ALL viewports. No exceptions. No duplicates. No hardcoding.