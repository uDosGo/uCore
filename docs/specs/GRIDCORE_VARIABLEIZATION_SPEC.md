# GridCore Variableization Spec

Date: 2026-07-17
Status: Active - Phase 2 complete
Owner: Frontend GridCore

## 1. Purpose

Define a dedicated variable system for GridCore UI internals that is independent from USX design tokens.

This spec exists to:
- keep GridCore rendering/editor internals decoupled from USX stylistic constraints
- make GridCore dimensions and UI constants configurable without touching rendering logic
- support future theme/runtime overrides via a stable `--gridcore-*` variable contract

## 2. Scope and Boundaries

In scope:
- uCode GridCore editor internals (toolbars, popovers, control sizing, editor chrome)
- GridCore display/viewer component presentation chrome
- component-local CSS variables under `--gridcore-*`

Out of scope:
- Grid algebra and rendering behavior
- palette model and color index semantics
- GridBuffer data contracts
- USX surface shell contracts
- canvas renderer fill/stroke constants that are part of renderer behavior, not CSS chrome

Boundary rule:
- USX may style surface shell/container framing.
- GridCore internals must use `--gridcore-*` variables for internal constants.

## 3. Namespace

All GridCore variables MUST use this prefix:
- `--gridcore-*`

Initial implementation targets:
- `frontend-vue/src/surfaces/ucode/UCodeSurface.vue`
- `frontend-vue/src/grid-core/GridCoreUI.vue`
- `frontend-vue/src/grid-core/MultiColumnViewer.vue`
- `frontend-vue/src/grid-core/ProseViewer.vue`
- `frontend-vue/src/grid-core/SlideViewer.vue`
- `frontend-vue/src/styles/gridcore.css`
- `frontend-vue/src/main.ts` (contract import)
- `frontend-vue/src/stores/gridcoreSettings.ts`

## 4. Variable Contract

### 4.1 Typography and Base
- `--gridcore-font-family-mono`
- `--gridcore-font-size-xs`
- `--gridcore-font-size-sm`
- `--gridcore-font-size-md`
- `--gridcore-font-size-lg`

### 4.2 Toolbar and Controls
- `--gridcore-border-width`
- `--gridcore-border-color`
- `--gridcore-border`
- `--gridcore-focus-outline-width`
- `--gridcore-focus-outline-offset`
- `--gridcore-active-ring-width`
- `--gridcore-hover-bg`
- `--gridcore-selection-bg`
- `--gridcore-selection-bg-muted`
- `--gridcore-toolbar-gap`
- `--gridcore-toolbar-gap-lg`
- `--gridcore-toolbar-padding-y`
- `--gridcore-toolbar-padding-x`
- `--gridcore-toolbar-min-height`
- `--gridcore-control-height`
- `--gridcore-control-radius`
- `--gridcore-control-input-width`
- `--gridcore-control-input-pad-x`
- `--gridcore-tools-gap`
- `--gridcore-tools-pad-x`
- `--gridcore-actions-gap`
- `--gridcore-action-btn-height`
- `--gridcore-action-btn-pad-x`
- `--gridcore-tool-btn-size`
- `--gridcore-action-size`

### 4.3 Popovers and Overlays
- `--gridcore-popover-offset-y`
- `--gridcore-popover-cell-size`
- `--gridcore-popover-gap`
- `--gridcore-popover-padding`
- `--gridcore-popover-shadow`
- `--gridcore-popover-radius`
- `--gridcore-checker-size`
- `--gridcore-checker-color`
- `--gridcore-popover-transition`

### 4.4 Markers
- `--gridcore-marker-font-size`
- `--gridcore-marker-fg-color`
- `--gridcore-marker-bg-color`
- `--gridcore-marker-shadow`
- `--gridcore-marker-offset-sm`
- `--gridcore-marker-offset-md`
- `--gridcore-marker-pad-y`
- `--gridcore-marker-pad-x`
- `--gridcore-marker-fg-bg`
- `--gridcore-marker-bg-bg`

### 4.5 Palette
Palette variables model current editor swatch presentation only. They do not redefine palette index semantics.

- `--gridcore-palette-0`
- `--gridcore-palette-1`
- `--gridcore-palette-2`
- `--gridcore-palette-3`
- `--gridcore-palette-4`
- `--gridcore-palette-5`
- `--gridcore-palette-6`
- `--gridcore-palette-7`

### 4.6 Sidebar
- `--gridcore-sidebar-width`
- `--gridcore-sidebar-title-size`
- `--gridcore-sidebar-font-btn-size`
- `--gridcore-sidebar-font-btn-gap`
- `--gridcore-sidebar-font-btn-padding-y`
- `--gridcore-sidebar-char-columns`
- `--gridcore-sidebar-char-gap`
- `--gridcore-sidebar-char-radius`
- `--gridcore-sidebar-char-font-size`
- `--gridcore-sidebar-preview-min-height`
- `--gridcore-sidebar-char-input-width`
- `--gridcore-sidebar-char-input-size`

### 4.7 Preset Popover and Misc Chrome
- `--gridcore-preset-popover-max-height`
- `--gridcore-preset-popover-gap`
- `--gridcore-preset-popover-shadow`
- `--gridcore-preset-popover-min-width`
- `--gridcore-prose-heading-size`

## 5. Implementation Rules

1. New GridCore internals must not add fresh hardcoded px/hex constants when an existing `--gridcore-*` variable applies.
2. Do not rename existing palette index classes or GridCore renderer hooks in this phase.
3. Preserve behavior; this phase is variableization only.
4. Keep spec and implementation in lockstep: when adding a new `--gridcore-*` variable, add it to this document.

## 6. Migration Plan

Phase 1:
- introduce local `--gridcore-*` variables in `UCodeSurface.vue`
- replace repeated hardcoded constants in internal editor CSS

Phase 2:
- extract GridCore variables to a dedicated GridCore stylesheet/module
- add runtime preset switching for GridCore variables
- route remaining uCode editor chrome constants through the dedicated `--gridcore-*` contract
- route GridCore viewer presentation chrome through the dedicated `--gridcore-*` contract

Phase 2 progress:
- extracted variable contract to `frontend-vue/src/styles/gridcore.css`
- wired contract globally in `frontend-vue/src/main.ts`
- scoped to uCode GridCore surface via `.gridcore-surface` class
- added Phase 2 contract groups for GridCore borders, focus rings, palette swatches, marker geometry, sidebar character grids, and preset popover sizing
- replaced matching hardcoded uCode internals with `--gridcore-*` variables in `frontend-vue/src/surfaces/ucode/UCodeSurface.vue`
- extended the contract root to standalone GridCore viewer components
- replaced Pico/raw presentation styles in `GridCoreUI.vue`, `MultiColumnViewer.vue`, `ProseViewer.vue`, and `SlideViewer.vue`
- left `palette.ts`, `g0-renderer.ts`, and `gridui-canvas.ts` renderer/data constants out of CSS variableization by design

Phase 3:
- map approved variable subsets into formal GridCore settings UI and persistence

Phase 3 progress:
- added persisted Pinia store at `frontend-vue/src/stores/gridcoreSettings.ts`
- added preset override classes in `frontend-vue/src/styles/gridcore.css`
- wired uCode surface root to `gridcore-surface--{preset}`
- connected Developer Settings GridCore preset controls to the persisted store

## 6.1 Preset Classes

Preset classes are variable-only overrides. They must not change renderer data, grid algebra, palette indices, or canvas behavior.

- `gridcore-surface--compact`
- `gridcore-surface--normal` (base `.gridcore-surface` contract)
- `gridcore-surface--spacious`
- `gridcore-surface--hd`
- `gridcore-surface--retro`

## 7. Acceptance Criteria

- GridCore internals in `UCodeSurface.vue` use `--gridcore-*` variables for repeated control/popover constants.
- Phase 2 editor chrome constants are defined in `frontend-vue/src/styles/gridcore.css`, not inline in the surface.
- GridCore viewer component presentation styles use `--gridcore-*` variables rather than Pico or direct USX styling.
- No rendering behavior changes.
- USX shell framing remains independent and unchanged in responsibility.
