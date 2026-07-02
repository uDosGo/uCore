# GridUI Rendering Contract — uCode Runtime Target

**Date**: 2026-07-02
**Status**: Baseline established — frontend alignment complete
**Purpose**: This document defines the pixel-exact rendering contract between the uCore frontend (GridUI surface) and the uCode backend runtime. The uCode runtime must produce grid buffers that render correctly in this surface.

---

## Rendering Pipeline

```
uCode Runtime (backend)
  → GridBuffer (2D GridCell[][], rows × cols)
    → GridUICanvasElement.setBuffer(buf)
      → Canvas 2D Context
        → Pixel buffer → Display
```

## Surface Layout

### UCodeSurface (route: `/ucode`)

| Tab | Cols | Rows | Cell Size | Font | Expected Pixel Size | Aspect |
|-----|------|------|-----------|------|-------------------|--------|
| **Terminal** | 80 | 24 | 16px | `pressstart2p` | 1280×384 | ~10:3 |
| **Teletext** | 40 | 25 | 20px | `vt323` | 800×500 | 8:5 |
| **Grid** (editor view) | 24 | 24 | 24px | `vt323` | 576×576 | 1:1 |
| **Grid** (layer) | 40 | 25 | 12px | `vt323` | 480×300 | 8:5 |
| **Layer** | 40 | 25 | 20px | `vt323` | 800×500 | 8:5 |

### Standalone Routes

| Route | Cols | Rows | Cell Size | Font | Expected Pixel Size |
|-------|------|------|-----------|------|-------------------|
| `/terminal` | 80 | 24 | 16px | `pressstart2p` | 1280×384 |
| `/teletext` | 40 | 25 | 20px | `vt323` | 800×500 |

## Pixel-Perfect Rendering Guarantees

### Cell Dimensions
```
canvas CSS width  = cols × cellSize        (exact CSS pixels)
canvas CSS height = rows × cellSize        (exact CSS pixels)
canvas pixel width  = canvas CSS width  × devicePixelRatio
canvas pixel height = canvas CSS height × devicePixelRatio
```

### Zero-Gap Rendering
```css
/* No gaps between adjacent cells */
cellSpacing: 0
gap: 0
padding: 0
margin: 0
```
Each cell is rendered as a `fillRect(x, y, cellW, cellH)` with no spacing between adjacent rectangles. Background fills extend edge-to-edge.

### Font Sizing
| Font Family | Scale Factor | Font Size Formula |
|------------|-------------|-------------------|
| `pressstart2p` | 0.65 | `cellSize × 0.65 × dpr` |
| `vt323` | 0.9 | `cellSize × 0.9 × dpr` |
| fallback monospace | ~0.6 | `cellW / 0.6` |

Text is centered in each cell with `textAlign: center` and `textBaseline: middle`.

### Colour Palette
The 8-colour unified palette (`PALETTE_DARK`) is defined in `grid-core/palette.ts`:
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
}

type GridBuffer = GridCell[][]  // [row][col], y × x
```

**Source**: `frontend-vue/src/grid-core/types.ts`

> **Note**: The vendor grid-algebra (`vendor/gridui-canvas/grid-algebra/GridCell.ts`) has additional fields (`flash`, `doubleHeight`, `doubleWidth`). The canvas renderer only uses `char`, `fg`, `bg`, `bold`, `blink`, and `mosaic`. The runtime should use the `grid-core` type as the canonical buffer format.

## uCode Runtime Requirements

The uCode backend runtime must produce `GridBuffer` objects that the frontend can render. The runtime should:

1. **Produce buffers matching one of the preset grid sizes** (or define custom sizes)
2. **Use colour indices 0-7** from the unified palette
3. **Support `bold` flag** for double-stroke rendering
4. **Support `blink` flag** for teletext-style blinking characters
5. **Support `mosaic` flag** for block graphic characters
6. **Each cell contains exactly one character** (single Unicode code point)

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

## Playwright Audit Results (2026-07-02 Baseline)

| Tab | Expected | Actual (Host) | Canvas Pixels | Cell Check |
|-----|----------|--------------|---------------|------------|
| Terminal | 1280×384 | 1280×384 ✅ | 2560×768 | 16×16 ✅ |
| Teletext | 800×500 | 800×500 ✅ | 1600×1000 | 20×20 ✅ |
| Grid (editor) | 576×576 | 576×576 ✅ | 1152×1152 | 24×24 ✅ |
| Grid (layer) | 480×300 | 480×300 ✅ | 960×600 | 12×12 ✅ |
| Layer | 800×500 | 800×500 ✅ | 1600×1000 | 20×20 ✅ |

**All tabs render at exact pixel dimensions with zero gaps.**
