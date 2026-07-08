# @udos/usx-tokens

**USX Design Token System v3.1.0** — shared CSS custom properties for uDos surfaces.

Used by:
- **uCore** (`@udos/ui-hub-vue`) — developer dashboard, workflow, assist UI
- **HomeNest** (`homenest-console`) — 10-foot living-room media + automation console

## Architecture

```
@udos/usx-tokens/
├── tokens/              ← Canonical CSS custom property definitions
│   ├── tokens-color.css      ← --usx-color-primary, --surface, --border, etc.
│   ├── tokens-components.css ← --usx-radius, --card-padding, --tab-border
│   ├── tokens-spacing.css    ← --usx-spacing-xs → 2xl
│   ├── tokens-touch.css      ← --usx-touch-min touch targets
│   └── tokens-typography.css ← --usx-font-size, --family, --weight
│
├── themes/              ← Theme overrides (swap variable values only)
│   ├── dark.css
│   ├── light.css
│   └── high-contrast.css
│
├── home-nest/           ← 10-foot console additions
│   ├── console-grid.css      ← 12-column TV grid, poster wall, launcher tiles
│   ├── controller-focus.css  ← dpad/gamepad focus rings, button hints
│   └── media-player.css       ← Now-playing bar, transport, seek, volume
│
├── usx-standard.css     ← Layout primitives (surfaces, cards, tabs, buttons)
└── README.md
```

## Usage

### In any uDos Vue surface

```css
/* Import in order: PicoCSS base → tokens → theme → standard → optional */
@import '@picocss/pico';
@import '@udos/usx-tokens/tokens/tokens-color.css';
@import '@udos/usx-tokens/tokens/tokens-components.css';
@import '@udos/usx-tokens/tokens/tokens-spacing.css';
@import '@udos/usx-tokens/tokens/tokens-touch.css';
@import '@udos/usx-tokens/tokens/tokens-typography.css';
@import '@udos/usx-tokens/themes/dark.css';
@import '@udos/usx-tokens';
```

### In template

```html
<div class="usx-surface">
  <header class="surface__header">
    <h1 class="surface__title">My Surface</h1>
  </header>
  <main class="usx-main">
    <div class="usx-card">
      <p>Content using var(--usx-color-on-surface)</p>
    </div>
  </main>
</div>
```

## Design Philosophy

1. **PicoCSS is the base framework.** USX tokens layer on top as the canonical variable system.
2. **Zero hardcoded values.** Every color, spacing, radius uses `var(--usx-*)`.
3. **Themes only override variable values** — they don't change CSS rules.
4. **HomeNest extends, never forks.** Console additions live in `home-nest/` and import AFTER the core tokens.

## Publishing

```bash
cd packages/usx-tokens
npm version patch  # or minor / major
npm publish --access public
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2026-07-08 | Extracted from uCore `frontend-vue/src/styles/`. Added HomeNest 10-foot console additions. Added PicoCSS peer dependency. |