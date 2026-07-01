---
title: "Wave 4: GridUI Canvas Engine — Framework-Agnostic Embeddable Widget"
status: done
source: vue-refactor
source_id: wave-4-canvas
tags: [canvas, gridalgebra, bbcruntime, web-component, wave-4]
created: 2026-06-28
completed: 2026-06-29
---

# Wave 4: GridUI Canvas Engine — Framework-Agnostic Embeddable Widget

## Goal
Extract the GridUI canvas engine from the archived React frontend into a **self-contained, framework-agnostic embeddable widget** aligned with `gridalgebra` and `bbcruntime`. It should work in Vue, React, or plain HTML — no framework coupling.

## Architecture Decision
- **NOT a Vue component** — a Web Component / Custom Element
- Uses `gridalgebra` (pure TS) for grid math
- Uses `bbcruntime` for BBC Basic execution
- Renders to `<canvas>` element
- Exposes a simple JS API: `new GridUICanvas({ target, cols, rows })`

## Sub-tasks

### 4.1 — Scaffold `frontend-vue/src/vendor/gridui-canvas/` package
- [ ] Create `gridui-canvas.ts` — main entry point
- [ ] Create `GridUICanvasElement` — Web Component (extends HTMLElement)
- [ ] Create `canvas-renderer.ts` — low-level canvas drawing
- [ ] Create `grid-session.ts` — wraps gridalgebra + bbcruntime
- [ ] Create `types.ts` — shared interfaces (Cell, GridState, RenderConfig)
- [ ] Register as `<gridui-canvas>` custom element

### 4.2 — Port gridalgebra integration
- [ ] Import `@udos/gridcore` grid algebra engine (pure TS, already in workspace)
- [ ] Wire `GridSession` to create/manage grids via gridalgebra API
- [ ] Port cell transform pipeline from React `GridUIBuffer`
- [ ] Port palette/rendering modules from React `GridUIRenderer`

### 4.3 — Port bbcruntime integration
- [ ] Import bbcruntime for BBC Basic program execution
- [ ] Wire `GridSession.runBasic(program)` → grid state updates
- [ ] Port BASIC import flow from React `gridsmith_import_basic_program`

### 4.4 — Port Teletext surface
- [ ] Replace `TeletextSurface.vue` placeholder with real implementation
- [ ] Embed `<gridui-canvas>` element via Vue `ref`
- [ ] Add teletext-specific controls (character set, display mode, colors)
- [ ] Wire to MCP `gridsmith_*` tools

### 4.5 — Port Terminal surface
- [ ] Replace `TerminalSurface.vue` placeholder with real implementation
- [ ] Embed `<gridui-canvas>` element via Vue `ref`
- [ ] Add terminal-specific controls (font, scrollback, cursor)
- [ ] Wire to backend terminal WebSocket

### 4.6 — Port UCode/GridCore surface
- [ ] Replace `UCodeSurface.vue` placeholder with real implementation
- [ ] Embed `<gridui-canvas>` element via Vue `ref`
- [ ] Add ucode-specific controls (map view, grid editor, assets)
- [ ] Wire to MCP `gridsmith_latlon_to_ucode` / `gridsmith_ucode_to_latlon`

### 4.7 — Vitest unit tests
- [ ] Test `GridUICanvasElement` custom element registration
- [ ] Test `canvas-renderer.ts` drawing primitives
- [ ] Test `grid-session.ts` gridalgebra integration
- [ ] Test bbcruntime integration
- [ ] Test Vue surface wrappers mount correctly

### 4.8 — Accessibility audit
- [ ] ARIA labels on canvas container
- [ ] Keyboard navigation for grid cells
- [ ] Screen reader announcements for cell content
- [ ] Focus management for embedded widget

## Dependencies
- `@udos/gridcore` (already in workspace as pure TS)
- `bbcruntime` (needs to be added or vendored)
- No React, no Vue, no framework deps in the canvas package itself

## Reference
- React source: `frontend/archive/src/surfaces/gridui/`
- Grid algebra: `frontend/archive/src/surfaces/gridui/GridUIBuffer.ts`
- Renderer: `frontend/archive/src/surfaces/gridui/GridUIRenderer.ts`
- GridSmith bridge: `backend/app/services/gridsmith_bridge.py`
