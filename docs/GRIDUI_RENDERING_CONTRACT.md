# GridUI Rendering Contract — uCode Runtime Target

**Date**: 2026-07-03
**Status**: v3.1 — Teletext: G0 block bitmaps + MODE7GX3 fillText text, mixed font rendering, Grid Editor
**Purpose**: Defines the pixel-exact rendering contract. The uCode backend runtime produces `GridBuffer` objects; the frontend renders them.

---

## Architecture

```
GridAlgebra (fixed grid presets)     ← grid-core/types.ts, buffer.ts, algebra.ts
  └── GridBuffer: GridCell[][]       ← cols × rows, cells auto-fit to container
       └── GridCell {
             char: string            ← G0 char code (teletext) or Unicode
             fg, bg: number          ← palette indices 0-7
             bold?, blink?, mosaic?  ← formatting flags
             width?: number          ← render width in CSS px (optional)
           }
            ↓
GridUICanvasElement.setBuffer(buf)   ← Web Component (canvas 2D)
  ├── Background: fillRect gapless   ← 1px overlap to kill seams
  ├── Teletext blocks (G0 bitmap)    ← █▄▀║═╔╗ etc. — pixel-crisp offscreen canvas
  ├── Teletext text (fillText)       ← MODE7GX3 font, 1.3× scale, clipped per-cell
  ├── Terminal mode (fillText)       ← pressstart2p, square, natural
  ├── Block Renderer (fillRect)      ← graphic chars fillRect
  ├── Gridlines                      ← optional, faint 1px lines at cell boundaries
  └── Auto-fit via ResizeObserver    ← cells size to container, ceiling at configured cellSize

G0Renderer (g0-renderer.ts)         ← Ceefax teletext bitmap pipeline
  ├── Pre-renders MODE7GX3 glyphs    ← 4x offscreen canvas, thresholded to binary
  ├── Renders at cellSize × cellSize  ← NN-scaled from 12×10 native
  └── Zero anti-aliasing             ← pixel-crisp output

```

## Core Principle: Fixed Grid, Variable Char Width

```
┌─────────────────────────────────────────────────┐
│  Grid is always: cols × cellSize CSS pixels      │
│  e.g. 40 × 20px = 800 × 500                      │
│                                                   │
│  Each cell background: 20 × 20 px (gapless)       │
│  Each char renders at: cell.width || defaultCharW │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ background│  │ background│  │ background│       │
│  │   [==]    │  │ [MODE7GX3]│  │ [Press2P] │       │
│  │  charW=26 │  │ charW=26  │  │ charW=20  │       │
│  └──────────┘  └──────────┘  └──────────┘        │
│  Same grid cell size (20×20), different char width │
└─────────────────────────────────────────────────┘
```

## Surface Layout

### UCodeSurface (route: `/ucode`) — 4-tab hub

| Tab | Cols | Rows | Cell | Font | Char W | Auto-fit | Notes |
|-----|------|------|------|------|--------|----------|-------|
| **Terminal** | 40 | 25 | auto (ceiling 100) | `pressstart2p` | cell | Yes | Square, natural |
| **Teletext** | 40 | 25 | auto (ceiling 100) | `mode7gx3` | G0 bitmap | Yes | Pixel-crisp, G0 pipeline |
| **Grid Editor** | 24×24 edit + 40×25 layer | auto | selectable via sidebar | — | Yes | Tools, palette, actions left; font/char sidebar right |
| **Layer Composer** | — | — | — | — | — | Prose stub — under development |

### Grid Editor Layout

```
┌──────────────────────────────────────────────────────────────┐
│  SurfaceTabNav (Terminal | Teletext | Grid Editor | Layer)   │
│  [refresh] [save] [load] [📊 preset popover]                 │
├────────────┬──────────────────────────┬──────────────────────┤
│  Tools     │  Editor Viewport         │  Sidebar             │
│  ┌──┐ ┌──┐ │  24×24 cell grid         │  Font: [Term][Tele]  │
│  │✏️│ │🪣│ │  with gridlines           │  ┌──┬──┬──┬──┬──┐   │
│  └──┘ └──┘ │  Auto-fits container     │  │  │  │  │  │  │   │
│  ┌──┐ ┌──┐ │  Click → edits layer     │  └──┴──┴──┴──┴──┘   │
│  │🧹│ │💉│ │                          │  Characters grid    │
│  └──┘ └──┘ │                          │  (renders in font)  │
│  Palette   │                          │  Active Char: [#]   │
│  ┌─┬─┬─┬─┐ │                          │                     │
│  │F│ │ │ │ │                          │                     │
│  ├─┼─┼─┼─┤ │                          │                     │
│  │ │ │ │B│ │                          │                     │
│  └─┴─┴─┴─┘ │                          │                     │
│  Actions   │                          │                     │
│  [Fill]    ├──────────────────────────┤                     │
│  [Clr]     │  Layer (collapsible)      │                     │
│  [Exp]     │  40×25 grid               │                     │
│  [Imp]     │  Auto-fits container      │                     │
│            │  Click → copies to editor │                     │
├────────────┴──────────────────────────┴──────────────────────┤
│  Layer bar: [▼] Layer · 40×25  Focus: (0, 0)               │
└──────────────────────────────────────────────────────────────┘
```

### Standalone Routes (legacy — use UCodeSurface for all tabs)

| Route | Cols | Rows | Cell | Font | Notes |
|-------|------|------|------|------|-------|
| `/terminal` | 40 | 25 | auto | `pressstart2p` | Uses grid-core canvas renderer |
| `/teletext` | 40 | 25 | auto | `mode7gx3` | G0 blocks + fillText text |

## Teletext Rendering (mode7gx3)

The `mode7gx3` font renders in two modes:

| Character type | Method | Font | Notes |
|---------------|--------|------|-------|
| Block graphics (`█▄▀▐▌░▒▓│─║═╔╗╚╝╠╣╦╩╬`) | G0 bitmap pipeline | MODE7GX3 (pre-rendered) | Pixel-crisp, zero anti-aliasing |
| Text (A-Z, 0-9, punctuation) | fillText with clipping | MODE7GX3 (TTF) | 1.3× scale, readable |

The G0 renderer pre-renders MODE7GX3 glyphs at 4× on an offscreen canvas, thresholds pixels to binary, then renders with 2× NN scaling for crisp output.

The TELETEXT_BLOCKS set (defined in `gridui-canvas.ts`) determines which characters use G0 vs fillText.

## Font Selector (Grid Editor Sidebar)

The right sidebar provides font/character selection. Font choice applies to both editor and layer canvases.

| Button | Font Family | Render Path | Char Set |
|--------|-------------|-------------|----------|
| **Terminal** | `"Press Start 2P"` | `fillText` with clipping | Printable ASCII (0x21-0x7E) |
| **Teletext** | `"MODE7GX3"` | G0 bitmap renderer | ASCII + teletext block graphics |

Font switching is wired via `watch(editorFont)` → `setAttribute('font', ...)` → `attributeChangedCallback` → `_render()`.

The sidebar character grid renders chips in the selected font via `chipFont` computed. Clicking a character sets it as the active char and places one instance at the center of the editor viewport.

## Canvas Hardening (Tab Switching)

The gridui-canvas Web Component uses `display: none/''` to preserve state across tab switches. Key fixes:

1. **Re-attach on v-if destroy**: When Vue's `v-if` destroys/recreates container DOM, cached canvases are re-appended via `gridContainer.value.contains(el)` check.
2. **Reflow guard**: `void el.offsetHeight` forces layout before `_fitToContainer` reads parent dimensions.
3. **initGrid on preset change**: Uses `initGrid(tab)` instead of `loadTabContent(tab)` to create fresh canvases with updated dimensions.
4. **ResizeObserver**: Each canvas observes its parent element and re-fits cells when container resizes.

## Pixel-Perfect Rendering Guarantees

### Container Auto-Fit (v3)
Cells auto-size to fit the available container space. The `fit-container` attribute (default `true`) enables ResizeObserver-based fitting:

```javascript
// _fitToContainer() logic
const maxCellW = Math.floor(availW / cols)
const maxCellH = Math.floor(availH / rows)
cellSize = Math.min(configuredCellSize, maxCellW, maxCellH)
if (cellSize < 4) cellSize = 4  // minimum
```

Set `fit-container="false"` for fixed-size rendering (used by legacy standalone routes).

### Cell Dimensions (when fit-container="false")
```
canvas CSS width  = cols × cellSize          (exact, e.g. 800px)
canvas CSS height = rows × cellSize          (exact, e.g. 500px)
canvas pixel w/h  = CSS dims × devicePixelRatio
```

### Zero-Gap Background
Each cell background fills the full cell with 1px overlap to eliminate anti-aliased seam lines:
```javascript
ctx.fillRect(x, y, cellW + 1, cellH + 1)
```

### G0 Bitmap Renderer (Teletext)
For `mode7gx3` font, characters are rendered via a pixel-crisp bitmap pipeline:
```
12×10 native G0 glyph  →  4× offscreen canvas  →  threshold to binary
→  2× NN scaling  →  24×20 render within 24×24 cell  →  no anti-aliasing
```

### Regular Font Rendering (Terminal)
For `pressstart2p` and other fonts:
```javascript
ctx.save()
ctx.beginPath()
ctx.rect(x, y, cellW, cellH)  // clip to cell
ctx.clip()
ctx.fillText(cell.char, cx, y + cellH / 2)
ctx.restore()
```

### Variable Char Width
```javascript
// Per-cell width overrides default
const chW = cell.width ? Math.round(cell.width * dpr) : defaultCharW

// Character centered within its width inside the fixed cell
const cx = x + (cellW - chW) / 2 + chW / 2
ctx.fillText(cell.char, cx, y + cellH / 2)
```

| Scenario | Cell | Char Width | Overflow | Clipped |
|----------|------|-----------|----------|---------|
| Square font (pressstart2p) | 20px | 20px (= cell) | None | No |
| Teletext (MODE7GX3) | 20px | **26px** | +3px each side | Yes |
| Per-cell override | 20px | cell.width | Varies | Yes |

### Font Sizing (derived from char-width)
```
fontScale = defaultCharW / cellW    (in physical pixels)
fontSize  = cellSize × fontScale × dpr
```

| Font | Config | Scale | Font Size | Glyph Fill |
|------|--------|-------|-----------|------------|
| `pressstart2p` | char-width=20 | 1.0× | 40px @2x | ~50% (natural) |
| `mode7gx3` | char-width=26 | **1.3×** | 52px @2x | **101%** ✅ |
| `mode7gx3` (fallback) | char-width=24 | 1.0× | 40px @2x | ~78% |

### Colour Palette
The 8-colour unified palette (`PALETTE_DARK`) from `grid-core/palette.ts`:<｜end▁of▁thinking｜>

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="read_file">
<｜｜DSML｜｜parameter name="filePath" string="true">/Users/fredbook/Code/uCore/docs/GRIDUI_RENDERING_CONTRACT.md
| Index | Dark Theme | Purpose |
|-------|-----------|---------|
| 0 | `#000000` | Background/black |
| 1 | `#dc3545` | Red/error |
| 2 | `#198754` | Green/success |
| 3 | `#ffc107` | Yellow/warning |
| 4 | `#0d6efd` | Blue/info |
| 5 | `#6f42c1` | Purple/accent |
| 6 | `#0dcaf0` | Cyan/info-alt |
| 7 | `#f8f9fa` | Foreground/white |

## Container Behavior

### Grid Sizing
- The `<gridui-canvas>` custom element sizes itself intrinsically to `cols × cellSize` CSS pixels.
- The host element sets `style.width` and `style.height` to match.
- The viewport (`.ucode-viewport`) is a flex container with `overflow: auto`.
- If the grid is **smaller** than the viewport → centered via flexbox.
- If the grid is **larger** than the viewport → scrollbars appear.

### Retina/DPR Handling
- Canvas pixel dimensions = CSS dimensions × `devicePixelRatio`
- The `<canvas>` element's `width`/`height` attributes are set in physical pixels.
- CSS `width`/`height` on the canvas use CSS pixel values (matching grid dimensions).
- This ensures crisp rendering on Retina displays.

## Rendering Component Architecture

```
UCodeSurface.vue                    ← Tab UI, demo data loading
  ├── canvasCache (Map<tabId, Element>)  ← State preservation across tab switches
  └── gridui-canvas (Web Component)      ← Renders each tab's grid

grid-core/gridui-canvas.ts          ← Canvas 2D renderer (PRIMARY)
  └── GridUICanvasElement            ← Custom Element
       ├── _fitCanvas()              ← Sets canvas to cols×cellSize
       ├── _render()                 ← Draws each cell as fillRect + fillText
       ├── setBuffer(buf)            ← Public API for buffer updates
       └── Supports blink, bold, mosaic modes

vendor/gridui-canvas/GridUICanvasElement.ts  ← CSS Grid span renderer (ALTERNATE)
  └── Used by standalone /terminal route (TerminalSurface.vue)
```

## Grid Buffer Type (Canonical)

```typescript
interface GridCell {
  char: string        // The character to display (single glyph)
  fg: number          // Foreground colour index (0-7)
  bg: number          // Background colour index (0-7)
  bold?: boolean      // Bold flag
  blink?: boolean     // Blink flag (teletext)
  mosaic?: boolean    // Mosaic block graphic flag
  /** Render width in CSS pixels within the fixed cell.
   *  Defaults to char-width attribute (26 for teletext, 20 for terminal).
   *  Enables mixing square fonts, teletext, and sprites on same grid line. */
  width?: number
}

type GridBuffer = GridCell[][]  // [row][col], y × x
```

**Source**: `frontend-vue/src/grid-core/types.ts`

## Runtime Adapter Status

Current terminal/uCode surfaces are renderer demos, not runtime bridges:

| Surface | Current role | Runtime-backed status |
|---------|--------------|-----------------------|
| `TerminalSurface` | Demo/local terminal shell rendered through the GridCore canvas path | Not wired to a PTY, shell, BBC BASIC runtime, uCode VM, or GridSmith world runner |
| uCode Terminal tab | Local GridCore buffer demo inside the uCode hub | Not wired to an execution runtime |
| GridCore | Rendering/data primitives: `GridBuffer`, `GridCell`, canvas sizing, palette, font rendering | Runtime-agnostic by design |

The next runtime milestone is to replace the terminal demo shell with a runtime-backed adapter. That adapter must preserve GridCore as the rendering primitive layer and introduce a narrow bridge contract above it.

Minimum adapter contract:

1. **Input stream**: frontend key/command events are normalized before crossing the runtime boundary.
2. **Output stream**: backend/runtime output is delivered as ordered text, control events, or complete/partial `GridBuffer` updates.
3. **Transport**: choose REST for request/response commands or WebSocket for interactive streaming; terminal/PTY mode should use WebSocket.
4. **Buffer mapping**: adapter owns conversion from runtime output into `GridBuffer`; GridCore only renders buffers.
5. **Runtime target**: adapter configuration must explicitly select one runtime kind: shell/PTY, BBC BASIC, uCode VM, or GridSmith world runner.
6. **Lifecycle**: adapter exposes start, stop, resize, reset, and error states so surfaces can recover without canvas-specific logic.

### Render Modes (per cell, on the same grid line)

| Mode | How | Cell example |
|------|-----|-------------|
| **Square font** | `fillText` at cell size | `pressstart2p` — 20px char in 20px cell |
| **Teletext text** | `fillText` clipped, MODE7GX3 font | MODE7GX3 at 1.3× scale, readable characters |
| **Teletext blocks** | G0 bitmap renderer | `█▄▀║═╔╗` — pixel-crisp, zero aliasing |
| **Block graphic** | `fillRect` full cell | `=`, `-`, `|`, `#`, `X` |
| **Sprite/emoji** | `cell.width` + `cell.char` | Any width, any glyph |
| **Mosaic** | 2×3 sub-cell blocks | Teletext G0 block graphics |

## uCode Runtime Requirements

The uCode backend runtime must produce `GridBuffer` objects. The runtime should:

1. **Use any grid size** — 40×25 is the current standard; aspect presets in algebra.ts
2. **Colour indices 0-7** from the unified palette (GitHub Dark / Bootstrap)
3. **Per-cell char widths** via `cell.width` — enables mixed rendering
4. **Support `bold`** for double-stroke, **`blink`** for teletext flash
5. **Support `mosaic`** for 2×3 block graphics
6. **Single Unicode code point per cell** — one character per GridCell

### Canvas vs CSS Rendering Decision — uCode Runtime Analysis

#### Comparison

| Factor | Canvas 2D (current) | CSS DOM (`<span>` per cell) | Hybrid |
|--------|---------------------|---------------------------|--------|
| **Text crispness** | `fillText` always anti-aliased | `-webkit-font-smoothing:none` = **pixel-crisp** ✅ | Canvas for graphics, CSS for text |
| **G0 bitmap quality** | Via offscreen canvas + NN scaling = crisp | Via @font-face (Galax approach) = **native crisp** | CSS text + canvas overlay |
| **Performance (static)** | Single element, GPU composited ✅ | 1000 spans = fine ✅ | Slightly more complex |
| **Performance (animated)** | `setBuffer()` → `_render()` = direct pixel push ✅ | 1000 DOM updates = layout thrash ❌ | Canvas handles animation |
| **Per-pixel control** | Full — blend modes, transforms, drawImage ✅ | None ❌ | Canvas overlay handles this |
| **Sprite overlay** | `drawImage` = trivial ✅ | Absolute positioning = painful ❌ | Canvas overlay ✅ |
| **Text selection** | None ❌ | Native browser selection ✅ | CSS layer handles this |
| **Accessibility** | None ❌ | Screen readers see text ✅ | CSS layer handles this |
| **Hit-testing** | Manual cell-from-coord math | Browser native (click on span) | Both available |
| **Scrolling** | `ctx.scroll` or re-render | Native DOM scroll | Canvas in scroll container |
| **Implementation** | 300-line Web Component ✅ | Template per cell, event delegation | Two layers, synced |

#### Recommendation: Canvas for Runtime, CSS for Viewing

The uCode runtime will produce two types of output:

| Output type | Volume | Update rate | Best renderer |
|-------------|--------|-------------|---------------|
| **Running BASIC/AMOS program** | Streaming | Per-frame (e.g. 30fps) | **Canvas** — direct pixel buffer updates, no DOM churn |
| **Teletext page** | Static/loaded | Once | **CSS** — pixel-crisp text, selectable, accessible |
| **Sprites / game graphics** | Continuous | Per-frame | **Canvas** — drawImage, transforms |
| **Grid editor** | Interactive | On click | **Canvas** — single buffer, instant redraw |

**Decision**: The uCore frontend keeps **Canvas 2D** as the primary renderer. The `<gridui-canvas>` Web Component is designed to be embedded in any framework (Vue, React, plain HTML). For the uCode runtime specifically:

1. **Canvas for active runtime output** — BASIC programs, game loops, sprites, scrolling terminal. Single buffer, direct pixel push, no DOM overhead.
2. **G0 bitmap cache** — Pre-render MODE7GX3 characters to binary bitmaps (see planned enhancement below). This gives pixel-crisp teletext text on canvas, matching CSS quality.
3. **CSS DOM for static viewing** — Optional render mode where the grid is rendered as CSS `<span>` elements with `-webkit-font-smoothing: none` for maximum readability. Used for teletext page browsing, documentation, etc.
4. **Hybrid as future path** — CSS for text layer, canvas overlay for graphics. Requires position synchronization but gives the best of both worlds.

### G0 Bitmap Renderer

The teletext view uses a **G0 bitmap renderer** instead of `fillText()`. This eliminates canvas anti-aliasing, matching galax.xyz CSS quality.

**Pipeline:**
```
MODE7GX3 font
  → Render char at 48×40 (4× G0 size) on offscreen canvas
    → Read pixels, threshold at 50% alpha → binary (fg/bg)
      → Downscale 4× to 12×10 → G0 glyph bitmap
        → Cache (Uint8Array, 120 bytes per char, 96 chars = 11.5KB)
          → Render: 2× nearest-neighbour → 24×20, center in 24×24 cell
            → putImageData or per-pixel fillRect
```

**Mosaic blocks** (2×3) are generated algorithmically from the 6-bit pattern in the character code — no font needed.

**Result**: Zero anti-aliasing. Pixel-crisp Ceefax text matching galax.xyz CSS quality, rendered at canvas framerates with no DOM overhead.

### Viewport Size Reference (24×24 base cell)

```yaml
viewports:
  terminal_80x24:
    1x: "1920×576"   # 80×24 × 24px
    2x: "3840×1152"  # 80×24 × 48px  ← sweet spot
  
  teletext_40x25:
    1x: "960×600"    # 40×25 × 24px
    2x: "1920×1200"  # 40×25 × 48px
    3x: "2880×1800"  # 40×25 × 72px  ← teletext ideal
  
  world_square_80x80:
    1x: "1920×1920"
    2x: "3840×3840"
  
  world_classic_80x60:
    1x: "1920×1440"
    2x: "3840×2880"
  
  widescreen_128x72:
    1x: "3072×1728"
    2x: "6144×3456"
```

## Verification Checklist

- [ ] Canvas `width`/`height` = `cols × cellSize × dpr`
- [ ] Canvas CSS dimensions = `cols × cellSize`
- [ ] Host element dimensions match canvas
- [ ] No gaps between adjacent cells (verify via `getImageData` pixel sampling)
- [ ] Font renders centered in cell (check `textBaseline: 'middle'`)
- [ ] Retina displays render at 2x without blur
- [ ] Tab switching preserves buffer state
- [ ] Grid larger than viewport → scrollable
- [ ] Grid smaller than viewport → centered

## Key Design Decisions

1. **Fixed 24×24 cells, variable char widths** — The grid algebra is constant. Character width is a per-cell property (`GridCell.width`), enabling mixed rendering modes (square font, teletext, sprites) on the same grid line.

2. **Per-cell font sizing**: `fontScale = defaultCharW / cellW` — the font size derives from the char width. This means `char-width=26` at 20px cells gives 1.3× scale, filling 101% of the cell width.

3. **MODE7GX3 for teletext** — Downloaded from galax.xyz, based on ModeSeven (BBC Micro MODE 7). Loaded via @font-face from `public/fonts/`. Replaces VT323 which had narrow glyphs.

4. **All canvas, not CSS** — The `<gridui-canvas>` Web Component renders to a single `<canvas>` element. CSS DOM rendering with `-webkit-font-smoothing: none` could give crisper text but loses the per-pixel control needed for sprite/mosaic overlay.

5. **Per-cell mosaic blocks** — The G0 2×3 mosaic system (6 sub-cells, each on/off via 6-bit code) is supported via the `mosaic` flag on `GridCell`.

6. **G0 bitmap renderer (planned)** — Pre-render MODE7GX3 chars to 12×10 bitmaps via offscreen canvas, threshold to binary, render with nearest-neighbour scaling for pixel-crisp output matching galax.xyz quality.

## Playwright Audit Results (2026-07-02)

| Tab | Expected | Actual | Canvas Pixels | Char Fill | Gaps |
|-----|----------|--------|---------------|-----------|------|
| Terminal (40×25, 20px, press2p) | 800×500 | 800×500 ✅ | 1600×1000 | ~50% (natural) | 0 bg gaps |
| Teletext (40×25, 20px, mode7gx3) | 800×500 | 800×500 ✅ | 1600×1000 | **101%** ✅ | 0 bg, 10 narrow-char |
| Grid editor (24×24, 24px) | 576×576 | 576×576 ✅ | 1152×1152 | 100% (block) | 0 |
| Grid layer (40×25, 12px) | 480×300 | 480×300 ✅ | 960×600 | — | — |

**All tabs: zero background gaps. Teletext: 0/40 separator gaps (edge-to-edge).**
