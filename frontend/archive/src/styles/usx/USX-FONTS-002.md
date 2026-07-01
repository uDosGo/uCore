# USX Prose UI Font Standards — Consolidated

**Document ID:** USX-FONTS-002  
**Status:** Active, Mandatory  
**Date:** 2026-06-26  
**Source of Truth:** Prose UI + Pico.css documentation  
**Purpose:** Resolve font inconsistencies by fully adopting Prose UI's design token system with Pico.css integration and 10-foot TV ratios

---

## Executive Summary

**Problem:** Duplicate code and conflicting overrides between Prose UI (our S600-S699 learning surface), Prose UI (the `prose-ui.com` library), Pico.css, and NestFrame custom styles have caused inconsistent font sizes across viewports.

**Solution:** This standard **defers to Prose UI's official design tokens** as the primary source for all typography and markdown styling, with Pico.css providing the component layer and NestFrame only handling the 24px grid, page system, and controller focus.

---

## Part 1: Source Hierarchy (The "Rule of Three")

```yaml
Priority 1: Prose UI (prose-ui.com) — Typography & Markdown:
  - All `.prose` content styling
  - All design tokens (--p-* variables)
  - Headings, body, lists, code, tables, callouts, steps

Priority 2: Pico.css — UI Components & Base:
  - Buttons, forms, cards, modals, nav
  - Responsive base styles
  - Dark/light mode via data-theme

Priority 3: NestFrame — Gaps Only:
  - 24px grid (Pico doesn't have)
  - uSystem pages (S100-S899)
  - Controller focus (gamepad support)
  - TV (10-foot) overrides (scaling Prose UI + Pico)
```

### 1.1 What We Delete

| File/Code | Reason |
|-----------|--------|
| Custom heading styles | Prose UI handles |
| Custom body text styles | Prose UI handles |
| Custom markdown styles | Prose UI handles |
| Custom code block styles | Prose UI handles |
| Custom table styles | Prose UI handles |
| Overrides of Prose UI tokens | Use Prose UI's variables instead |
| Hardcoded px values | Use Prose UI or Pico variables |

---

## Part 2: Prose UI Design Tokens (The Source)

### 2.1 Core Typography Tokens

Prose UI provides these CSS variables. **We use them directly. No overrides unless necessary.**

```css
/* Prose UI's design tokens — the source of truth */
:root {
  /* Base font size — the ONE value that changes per viewport */
  --p-font-size: 1rem;        /* ← Change this for scaling */

  /* Heading tokens */
  --p-h1-font-size: 2.5rem;
  --p-h2-font-size: 2rem;
  --p-h3-font-size: 1.5rem;
  --p-h4-font-size: 1.25rem;

  /* Font families */
  --p-font-family-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --p-font-family-serif: 'Merriweather', Georgia, serif;
  --p-font-family-mono: 'JetBrains Mono', 'Fira Code', monospace;
}
```

### 2.2 Our Only Override (Prose UI's recommended method)

Per Prose UI's styling guide, we override tokens via CSS variables:

```css
/* USX Standard — Prose UI overrides (minimal) */
:root {
  /* Map our font families to Prose UI */
  --p-font-family-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --p-font-family-serif: 'Merriweather', Georgia, serif;
  --p-font-family-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Map our colors to Prose UI */
  --p-link-color: var(--pico-primary);
  --p-code-background: var(--bg-subtle);
  --p-table-border: var(--border-default);
}
```

---

## Part 3: Pico.css Integration (Typography & Components)

### 3.1 Pico's Typography Variables

Pico has its own typography variables. We keep them separate from Prose UI.

```css
/* Pico.css variables — used for UI, not markdown */
:root {
  --pico-font-size: 100%;    /* Scales Pico's base */
  --pico-font-family: 'Inter', system-ui, -apple-system, sans-serif;
  --pico-line-height: 1.5;
  --pico-typography-spacing-vertical: 1rem;
}
```

### 3.2 Pico + Prose UI Relationship

```css
/* Pico for UI — Prose UI for markdown */
body {
  font-family: var(--pico-font-family);
  font-size: var(--pico-font-size);
  line-height: var(--pico-line-height);
}

.prose {
  /* Prose UI controls markdown typography */
  font-family: var(--p-font-family-sans);
  font-size: var(--p-font-size);
  line-height: 1.5;
}
```

---

## Part 4: 10-Foot TV Ratios (The Scaling Solution)

### 4.1 The Problem We're Solving

| Viewport | Body (Prose UI) | Sidebar (Pico) | Issue |
|----------|-----------------|----------------|-------|
| Small (mobile) | 14px | 12px | Sidebar too small |
| Medium | 16px | 18px | Sidebar too large |
| Large | 18px | 20px | Sidebar too large |

**Root cause:** Prose UI and Pico scaled independently. We need them to scale together.

### 4.2 The Solution — Unified Scaling

**Principle:** One `--font-base` value controls BOTH Prose UI and Pico typography.

```css
/* 1. Define ONE base value per viewport */
:root {
  --font-base: 16px;  /* Small default */
}

/* 2. Map Prose UI's --p-font-size to --font-base */
:root {
  --p-font-size: calc(var(--font-base) / 16px * 1rem);
}

/* 3. Map Pico's --pico-font-size to --font-base */
:root {
  --pico-font-size: calc(var(--font-base) / 16px * 100%);
}

/* 4. Viewport overrides (ONE value each) */
@media (max-width: 720px)  { :root { --font-base: 16px; } }
@media (min-width: 721px) and (max-width: 1280px) { :root { --font-base: 18px; } }
@media (min-width: 1281px) and (max-width: 1799px) { :root { --font-base: 20px; } }

/* 5. TV (10-foot) — the "almost there" fix */
@media (min-width: 1800px) and (min-height: 800px) {
  :root {
    --font-base: 32px;  /* 2x larger for 10-foot viewing */
  }
}
```

**Result:** Body and sidebar text are ALWAYS the same size across all viewports.

### 4.3 Prose UI's Built-in Scaling

Prose UI already handles responsive typography via `--p-font-size`. We're simply aligning it with our system.

```css
/* Prose UI's default responsive behavior */
@media (min-width: 640px) { :root { --p-font-size: 1.125rem; } }
@media (min-width: 1024px) { :root { --p-font-size: 1.25rem; } }
```

**Our change:** We override these with our unified `--font-base` system.

---

## Part 5: Complete Implementation (No Hardcoding)

### 5.1 The One CSS File (Merge and Delete Duplicates)

```css
/* nestframe.css — THE ONLY TYPOGRAPHY FILE */

/* 1. Import Pico and Prose UI */
@import 'https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css';
@import 'prose-ui/dist/styles.css';

/* 2. Define ONE base variable */
:root {
  --font-base: 16px;

  /* Font families (used by both Pico and Prose UI) */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-serif: 'Merriweather', Georgia, serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

/* 3. Map Pico and Prose UI to --font-base */
:root {
  /* Prose UI */
  --p-font-size: calc(var(--font-base) / 16px * 1rem);
  --p-font-family-sans: var(--font-sans);
  --p-font-family-serif: var(--font-serif);
  --p-font-family-mono: var(--font-mono);

  /* Pico */
  --pico-font-size: calc(var(--font-base) / 16px * 100%);
  --pico-font-family: var(--font-sans);
}

/* 4. Viewport overrides (ONE value each) */
@media (max-width: 720px)  { :root { --font-base: 16px; } }
@media (min-width: 721px) and (max-width: 1280px) { :root { --font-base: 18px; } }
@media (min-width: 1281px) and (max-width: 1799px) { :root { --font-base: 20px; } }

/* 5. TV (10-foot) */
@media (min-width: 1800px) and (min-height: 800px) {
  :root {
    --font-base: 32px;
    --touch-min: 72px;
  }
  button, [role="button"], input, select, textarea {
    min-height: var(--touch-min);
  }
}

/* 6. NestFrame Gaps (only what Pico + Prose UI don't have) */
.nestframe-grid { /* grid */ }
.uSystem-page { /* page system */ }
.controller-focus:focus { /* gamepad focus */ }
```

### 5.2 Duplicate/Conflicting Code to DELETE

```diff
- /* DELETE: Custom heading styles */
- h1 { font-size: 2.5rem; }
- .prose h1 { font-size: 2.5rem; }

- /* DELETE: Custom body styles */
- body { font-size: 16px; }
- .sidebar { font-size: 14px; }

- /* DELETE: Custom meta styles */
- .meta { font-size: 12px; }

- /* DELETE: Hardcoded overrides */
- @media (max-width: 720px) { .sidebar { font-size: 14px; } }
```

---

## Part 6: Audit Checklist (Font-Specific)

### 6.1 Font Size Audit

```markdown
## Surface: [name] (S[number])
**Auditor:** [name]
**Date:** [date]

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
```

### 6.2 Automated Audit Script

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

## Part 7: Quick Reference Card

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
| Duplicate/conflicting code | DELETE all but one source (Prose UI for markdown, Pico for UI, NestFrame for gaps) |

**The rule:** One value (`--font-base`) controls ALL text sizes across ALL viewports. No exceptions. No duplicates. No hardcoding.

**Next step:** Run the audit script, delete ALL duplicate CSS, apply the unified `--font-base` system, and verify body/sidebar are the same size at every viewport.