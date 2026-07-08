# USX Token Alignment — uCore ↔ HomeNest (July 2026)

**Status:** Active
**Last updated:** 2026-07-08

## Summary

The USX token system has been extracted from `uCore/frontend-vue/src/styles/` into a **shared npm package**: `@udos/usx-tokens` v3.0.0.

This package is published from the **HomeNest monorepo** (`fredporter/HomeNest`, path `packages/usx-tokens/`) and will be consumed by both uCore and HomeNest.

## What Changed

| Before | After |
|--------|-------|
| Tokens live in `frontend-vue/src/styles/tokens/` | Tokens live in `packages/usx-tokens/tokens/` in HomeNest |
| `usx-standard.css` in uCore only | `usx-standard.css` shared via npm package |
| No 10-foot console support | `home-nest/` additions for console grid, controller focus, media player |
| Ad-hoc PicoCSS mapping | Formal PicoCSS → USX mapping layer in `tokens-color.css` |

## Path Mapping

| uCore current path | `@udos/usx-tokens` import path |
|---|---|
| `src/styles/tokens/tokens-color.css` | `@udos/usx-tokens/tokens/color` |
| `src/styles/tokens/tokens-components.css` | `@udos/usx-tokens/tokens/components` |
| `src/styles/tokens/tokens-spacing.css` | `@udos/usx-tokens/tokens/spacing` |
| `src/styles/tokens/tokens-touch.css` | `@udos/usx-tokens/tokens/touch` |
| `src/styles/tokens/tokens-typography.css` | `@udos/usx-tokens/tokens/typography` |
| `src/styles/usx-standard.css` | `@udos/usx-tokens` (default export) |
| `src/styles/themes/dark.css` | `@udos/usx-tokens/themes/dark` |
| `src/styles/themes/*.css` | `@udos/usx-tokens/themes/*` |

## Next Steps for uCore (next dev round)

1. Install `@udos/usx-tokens` as a dependency:
   ```bash
   cd ~/Code/uCore && pnpm add @udos/usx-tokens
   ```

2. Replace direct imports with npm package imports in `frontend-vue/src/main.ts` or wherever tokens are loaded.

3. Remove the local copies from `frontend-vue/src/styles/tokens/` and `frontend-vue/src/styles/usx-standard.css` (they now live in the npm package).

4. Use the HomeNest 10-foot console imports if building a media/TV surface:
   ```css
   @import '@udos/usx-tokens/home-nest/console-grid.css';
   @import '@udos/usx-tokens/home-nest/controller-focus.css';
   @import '@udos/usx-tokens/home-nest/media-player.css';
   ```

## Design Decisions

- **PicoCSS is the base framework.** We keep it. USX tokens layer on top via `var(--usx-*)` custom properties.
- **Themes only swap variable values** — the CSS rules (in `usx-standard.css`) don't change per theme.
- **HomeNest extends, never forks.** uCore token behavior is unchanged. HomeNest scales typography and touch targets up for 10-foot viewing but keeps the same variable names.
- **uCore's `--pico-*` compatibility mappings** are preserved in `tokens-color.css` so PicoCSS-based components resolve to USX colors transparently.

## Repository

- **Package source:** `github.com/fredporter/HomeNest` → `packages/usx-tokens/`
- **Published as:** `@udos/usx-tokens` on npm/GitHub Packages