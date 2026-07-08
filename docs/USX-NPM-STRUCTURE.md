---
title: "USX Design Token System — npm Structure & Migration"
status: active
last_updated: 2026-07-08
category: architecture
tags: [usx, design-tokens, npm, uDos]
---

# USX Design Token System — npm Structure & Migration Guide

## Overview

**USX v3.0.0** is now the canonical **uDos design token system** published to npm as **`@udos/usx-tokens`**.

- **Source home:** `uCore/packages/usx-tokens/` (canonical)
- **Published:** npm registry (public, `@udos` scope)
- **Shared by:** uCore, HomeNest, Groovebox, and future uDos surfaces
- **Replaces:** Each project's local `/src/styles/` copies

---

## New npm Structure

### Package Layout

```
@udos/usx-tokens@3.0.0/
├── tokens/                 ← Canonical CSS variables
│   ├── tokens-color.css          (--usx-color-*, --surface-*, --border-*)
│   ├── tokens-components.css     (--usx-radius, --card-padding, --tab-border)
│   ├── tokens-spacing.css        (--usx-spacing-xs through 2xl)
│   ├── tokens-touch.css          (--usx-touch-min for touch targets)
│   └── tokens-typography.css     (--usx-font-size, --family, --weight)
│
├── themes/                 ← Theme overrides (variable swaps only)
│   ├── dark.css            (default uDos dark theme)
│   ├── light.css
│   ├── c64.css            (retro Commodore 64)
│   ├── teletext.css       (BBC Teletext)
│   └── high-contrast.css
│
├── home-nest/              ← HomeNest 10-foot console specifics
│   ├── console-grid.css        (12-column TV grid, poster walls)
│   ├── controller-focus.css    (dpad/gamepad focus rings)
│   └── media-player.css         (now-playing bar, transport)
│
├── usx-standard.css         ← Base layout primitives
│   (surfaces, cards, buttons, tabs, modals—no hardcoded values)
│
└── package.json
```

### Entry Points (package.json exports)

```json
{
  "exports": {
    ".": "./usx-standard.css",
    "./tokens/color": "./tokens/tokens-color.css",
    "./tokens/components": "./tokens/tokens-components.css",
    "./tokens/spacing": "./tokens/tokens-spacing.css",
    "./tokens/touch": "./tokens/tokens-touch.css",
    "./tokens/typography": "./tokens/tokens-typography.css",
    "./themes/dark": "./themes/dark.css",
    "./themes/light": "./themes/light.css",
    "./themes/c64": "./themes/c64.css",
    "./themes/high-contrast": "./themes/high-contrast.css",
    "./home-nest/console-grid": "./home-nest/console-grid.css",
    "./home-nest/controller-focus": "./home-nest/controller-focus.css",
    "./home-nest/media-player": "./home-nest/media-player.css"
  }
}
```

**Why exports?** Allows flexible imports without bundling the entire CSS.

---

## Migration Path for UI Projects

### Old Structure (Per-Project)
```
my-ui-project/
└── src/styles/
    ├── colors.css
    ├── spacing.css
    ├── components.css
    └── theme.css
```

### New Structure (Shared npm)
```
my-ui-project/
├── package.json
│   {
│     "dependencies": {
│       "@udos/usx-tokens": "^3.0.0"
│     }
│   }
└── src/
    ├── styles/
    │   ├── theme-overrides.css   ← Optional, project-specific
    │   └── app.css               ← Import usx + customize
    └── components/
        └── MyComponent.tsx       ← Uses var(--usx-color-primary), etc.
```

---

## Integration Examples

### For Vue Projects (HomeNest, uCore)

```typescript
// src/main.ts
import '@picocss/pico/css/pico.css';

// Import tokens first (in order)
import '@udos/usx-tokens/tokens/tokens-color.css';
import '@udos/usx-tokens/tokens/tokens-components.css';
import '@udos/usx-tokens/tokens/tokens-spacing.css';
import '@udos/usx-tokens/tokens/tokens-touch.css';
import '@udos/usx-tokens/tokens/tokens-typography.css';

// Then theme
import '@udos/usx-tokens/themes/dark.css';

// Then standard layout
import '@udos/usx-tokens/usx-standard.css';

// Project-specific (optional)
import './styles/app.css';

// Then surfaces
import App from './App.vue';
```

### For React Projects (Groovebox)

```tsx
// src/main.tsx
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

// Import USX tokens
import '@udos/usx-tokens/tokens/tokens-color.css';
import '@udos/usx-tokens/tokens/tokens-components.css';
import '@udos/usx-tokens/tokens/tokens-spacing.css';
import '@udos/usx-tokens/tokens/tokens-touch.css';
import '@udos/usx-tokens/tokens/tokens-typography.css';

// Theme
import '@udos/usx-tokens/themes/dark.css';

// Standard layout
import '@udos/usx-tokens/usx-standard.css';

// App styles
import './App.css';

import App from './App';
```

### Using Individual Tokens

```css
/* MyComponent.css */
.my-card {
  background: var(--surface-container);
  color: var(--usx-color-on-surface);
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  border: 1px solid var(--border-subtle);
}

.my-button {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  padding: var(--usx-touch-min);
  min-height: var(--usx-touch-min);
  font-size: var(--usx-font-size-body);
}
```

---

## Installation & Setup

### 1. Update package.json

```json
{
  "dependencies": {
    "@udos/usx-tokens": "^3.0.0"
  }
}
```

### 2. Install

```bash
npm install @udos/usx-tokens
# or
yarn add @udos/usx-tokens
# or
pnpm add @udos/usx-tokens
```

### 3. Import in Your Entry Point

See examples above by framework.

### 4. Remove Old Local Tokens

```bash
rm -rf src/styles/tokens/ src/styles/theme.css
# Or just replace references in imports
```

---

## Development & Publishing

### For uCore Maintainers

**Making changes to tokens:**

```bash
cd uCore/packages/usx-tokens
# Edit tokens/tokens-color.css, etc.
npm version patch  # or minor / major
npm publish --access public
```

**Version bump:**
- `patch` (3.0.0 → 3.0.1) — bug fixes, minor tweaks
- `minor` (3.0.0 → 3.1.0) — new tokens, new themes, new features
- `major` (3.0.0 → 4.0.0) — breaking changes (rename tokens, restructure)

### For Project Maintainers (HomeNest, Groovebox, etc.)

**After npm publish:**

```bash
npm update @udos/usx-tokens
# Test the update
npm run dev
# Commit
git add package.json package-lock.json
git commit -m "feat: bump @udos/usx-tokens to 3.0.1"
```

---

## Token Reference

### Color Tokens (`tokens-color.css`)

```css
--usx-color-primary        /* Primary brand color */
--usx-color-on-primary     /* Text/icon on primary */
--usx-color-secondary      /* Secondary accent */
--surface                  /* Default surface background */
--surface-container        /* Elevated surface (cards, panels) */
--surface-container-high   /* Very elevated (modals, popups) */
--usx-color-on-surface     /* Text on surface */
--border-subtle            /* Subtle borders */
--border-strong            /* Emphasis borders */
```

### Spacing Tokens (`tokens-spacing.css`)

```css
--usx-spacing-xs      /* 2px (tight) */
--usx-spacing-sm      /* 4px */
--usx-spacing-md      /* 8px (default gutters) */
--usx-spacing-lg      /* 16px (section margins) */
--usx-spacing-xl      /* 24px */
--usx-spacing-2xl     /* 32px (major sections) */
```

### Touch Targets (`tokens-touch.css`)

```css
--usx-touch-min       /* 48px (minimum touch target per accessibility) */
--usx-touch-comfortable /* 56px (comfortable for remote/gamepad) */
```

### Typography (`tokens-typography.css`)

```css
--usx-font-size-caption    /* 12px */
--usx-font-size-body       /* 16px (default) */
--usx-font-size-headline   /* 24px */
--usx-font-family-sans     /* System sans-serif */
--usx-font-weight-regular  /* 400 */
--usx-font-weight-bold     /* 700 */
```

---

## Design Principles

1. **Single source of truth** — All projects import from `@udos/usx-tokens`, never fork.
2. **Variables, not CSS rules** — Tokens define values; projects define layout & behavior.
3. **Themes are value swaps** — A theme only overrides `--usx-*` values, not CSS rules.
4. **Extensions, not overrides** — New UI surface needs? Add to `home-nest/` or create `groovebox/`.
5. **PicoCSS is the base** — USX layers on top; never reimplements basic styles.

---

## Common Questions

### Q: Can I use USX without PicoCSS?

**A:** Yes. USX tokens are just CSS custom properties. You can use them with any CSS framework or hand-written CSS. PicoCSS is recommended for uDos projects but not required.

### Q: How do I override a token in my project?

**A:** In your own CSS, redefine the variable after importing USX:

```css
@import '@udos/usx-tokens/usx-standard.css';

:root {
  --usx-color-primary: #ff6b6b;  /* Override to red */
}
```

### Q: Can I extend USX with my own tokens?

**A:** Yes. Define your project tokens after importing USX:

```css
@import '@udos/usx-tokens/usx-standard.css';

:root {
  --my-project-primary: var(--usx-color-primary);  /* Reference USX */
  --my-brand-accent: #ffa500;  /* New token */
}
```

### Q: What if I'm still on an older version (pre-npm)?

**A:** Check your project's `package.json`:
- If it doesn't list `@udos/usx-tokens`, migrate using the steps above.
- If you've imported from a local `/src/styles/`, replace with `import '@udos/usx-tokens/...'`.

### Q: How do I report a bug or suggest a new token?

**A:** File an issue in the [uCore repository](https://github.com/fredporter/uCore/issues) with the label `usx-tokens`.

---

## Related Docs

- [uCore Architecture](../../uCore/docs/architecture.md)
- [HomeNest Console Design](../../HomeNest/docs/architecture.md)
- [PicoCSS Reference](https://picocss.com/)
