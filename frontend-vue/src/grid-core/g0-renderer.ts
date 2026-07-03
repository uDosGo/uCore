/**
 * G0 Bitmap Renderer — Ceefax Teletext Character Generator
 *
 * Pre-renders MODE7GX3 characters to 12×10 binary bitmaps via offscreen
 * canvas, then renders them with nearest-neighbour 2× scaling for
 * pixel-crisp teletext output (zero anti-aliasing).
 *
 * Pipeline:
 *   MODE7GX3 font → offscreen canvas (48×40) → threshold → 12×10 bitmap → cache
 *   → render: 2× NN scale → 24×20 → center in 24×24 cell → main canvas
 *
 * Mosaic blocks (2×3) are generated algorithmically from 6-bit pattern.
 *
 * @see docs/GRIDUI_RENDERING_CONTRACT.md
 */

/* ─── Constants ────────────────────────────────────────────── */

/** G0 character native width (pixels) */
const GLYPH_W = 12
/** G0 character native height (pixels) */
const GLYPH_H = 10
/** Render scale factor (4× for offscreen rendering to preserve detail) */
const CACHE_SCALE = 4
/** Offscreen canvas size for cache rendering */
const CACHE_W = GLYPH_W * CACHE_SCALE  // 48
const CACHE_H = GLYPH_H * CACHE_SCALE  // 40
/** Output scale (2× for 24×24 cell rendering) */
const RENDER_SCALE = 2
/** Output glyph size within cell */
const RENDER_W = GLYPH_W * RENDER_SCALE  // 24
const RENDER_H = GLYPH_H * RENDER_SCALE  // 20
/** Characters to render as filled blocks (teletext block graphics) */
const BLOCK_CODES = new Set<number>()
// Generate all 64 mosaic block codes (0x60-0x7F range)
for (let i = 0; i < 64; i++) BLOCK_CODES.add(i)

/** Mapping from teletext char code to mosaic pattern (6 bits → 6 sub-cells) */
function mosaicPattern(charCode: number): number {
  // G0 mosaic: lower 6 bits = sub-cell pattern
  // Bit 0: top-left, 1: top-right, 2: middle-left,
  // 3: middle-right, 4: bottom-left, 5: bottom-right
  return charCode & 0x3F
}

/* ─── Types ────────────────────────────────────────────────── */

/** A 12×10 binary bitmap — each byte is 0 (bg) or 1 (fg) */
export type G0Bitmap = Uint8Array

/* ─── G0 Renderer ──────────────────────────────────────────── */

export class G0Renderer {
  private _glyphCache = new Map<number, G0Bitmap>()
  private _canvas: HTMLCanvasElement
  private _ctx: CanvasRenderingContext2D

  constructor() {
    this._canvas = document.createElement('canvas')
    this._canvas.width = CACHE_W
    this._canvas.height = CACHE_H
    const ctx = this._canvas.getContext('2d')
    if (!ctx) throw new Error('Failed to create offscreen canvas for G0 renderer')
    this._ctx = ctx
  }

  /**
   * Get (or generate and cache) a G0 bitmap for the given character code.
   */
  getBitmap(charCode: number): G0Bitmap {
    if (this._glyphCache.has(charCode)) {
      return this._glyphCache.get(charCode)!
    }

    const bitmap = this._generateBitmap(charCode)
    this._glyphCache.set(charCode, bitmap)
    return bitmap
  }

  /**
   * Render a G0 character into a cell on the main canvas.
   *
   * @param ctx - Main canvas 2D context
   * @param x - Cell x position in CSS pixels (top-left of cell from caller)
   * @param y - Cell y position in CSS pixels
   * @param cellSize - Cell CSS pixel size (e.g. 20 for teletext)
   * @param charCode - G0 character code
   * @param fg - Foreground hex colour
   * @param bg - Background hex colour
   * @param dpr - Device pixel ratio
   */
  render(
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    cellSize: number,
    charCode: number,
    fg: string,
    bg: string,
    dpr: number,
  ): void {
    const bitmap = this.getBitmap(charCode)

    const cellW = Math.round(cellSize * dpr)
    const cellH = Math.round(cellSize * dpr)

    // Calculate per-pixel scale to fill the full cell
    // Native glyph is 12×10; we scale to fill cellSize×cellSize
    const bw = Math.round(cellW / GLYPH_W)
    const totalW = bw * GLYPH_W
    const offsetX = Math.round(Math.max(0, (cellW - totalW) / 2))

    // Distribute remaining height evenly across rows for pixel-perfect fill
    const baseH = Math.floor(cellH / GLYPH_H)
    const extraPx = cellH - baseH * GLYPH_H
    const rowHeights: number[] = []
    for (let r = 0; r < GLYPH_H; r++) {
      rowHeights.push(baseH + (r < extraPx ? 1 : 0))
    }

    const px = Math.round(x * dpr) + offsetX

    // Draw each pixel row by row, with distributed row heights to fill cell
    let drawY = Math.round(y * dpr)
    for (let row = 0; row < GLYPH_H; row++) {
      const bh = rowHeights[row]
      for (let col = 0; col < GLYPH_W; col++) {
        const isFg = bitmap[row * GLYPH_W + col] === 1
        ctx.fillStyle = isFg ? fg : bg
        const bx = px + col * bw
        ctx.fillRect(bx, drawY, bw, bh)
      }
      drawY += bh
    }
  }

  /**
   * Generate a G0 bitmap for a teletext character or mosaic block.
   */
  private _generateBitmap(charCode: number): G0Bitmap {
    const bitmap = new Uint8Array(GLYPH_W * GLYPH_H)

    // Mosaic blocks (0x60-0x7F): generate from bit pattern
    if (charCode >= 0x60 && charCode <= 0x7F) {
      const pattern = mosaicPattern(charCode)
      this._renderMosaicBlock(bitmap, pattern)
      return bitmap
    }

    // Alphanumeric chars: render MODE7GX3 font on offscreen canvas
    this._renderFontGlyph(bitmap, charCode)
    return bitmap
  }

  /**
   * Render a 2×3 mosaic block pattern into the bitmap.
   * Each sub-cell is 6×3.3 pixels in the 12×10 grid (rounded).
   * Simplified: each sub-cell is a 6×3 block (18 pixels).
   */
  private _renderMosaicBlock(bitmap: Uint8Array, pattern: number): void {
    const subW = 6  // 12 / 2
    const subH = 3  // 10 / 3 (floor)

    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 2; c++) {
        const bitIndex = r * 2 + c
        const isActive = (pattern >> bitIndex) & 1
        if (!isActive) continue

        // Fill this sub-cell in the bitmap
        const startCol = c * subW
        const startRow = r * subH
        const endRow = r < 2 ? startRow + subH : GLYPH_H  // last row fills remainder

        for (let row = startRow; row < endRow; row++) {
          for (let col = startCol; col < startCol + subW; col++) {
            if (col < GLYPH_W && row < GLYPH_H) {
              bitmap[row * GLYPH_W + col] = 1
            }
          }
        }
      }
    }
  }

  /**
   * Render a MODE7GX3 font glyph to the offscreen canvas, read pixels,
   * threshold to binary, and downscale to 12×10.
   */
  private _renderFontGlyph(bitmap: Uint8Array, charCode: number): void {
    const ctx = this._ctx
    const canvas = this._canvas

    // Clear
    ctx.fillStyle = '#000000'
    ctx.fillRect(0, 0, CACHE_W, CACHE_H)

    // Draw character at 4× size for crisp thresholding
    ctx.font = `${CACHE_H}px "MODE7GX3", monospace`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillStyle = '#ffffff'
    ctx.fillText(String.fromCharCode(charCode), CACHE_W / 2, CACHE_H / 2)

    // Read pixels
    const imageData = ctx.getImageData(0, 0, CACHE_W, CACHE_H)
    const pixels = imageData.data

    // Downscale 4× to 12×10 using block averaging + threshold
    for (let row = 0; row < GLYPH_H; row++) {
      for (let col = 0; col < GLYPH_W; col++) {
        // Sample the 4×4 block in the cache
        let sumAlpha = 0
        for (let dy = 0; dy < CACHE_SCALE; dy++) {
          for (let dx = 0; dx < CACHE_SCALE; dx++) {
            const sx = col * CACHE_SCALE + dx
            const sy = row * CACHE_SCALE + dy
            const idx = (sy * CACHE_W + sx) * 4 + 3  // alpha channel
            sumAlpha += pixels[idx]
          }
        }
        const avgAlpha = sumAlpha / (CACHE_SCALE * CACHE_SCALE)
        // Threshold: pixels with >50% alpha are foreground
        bitmap[row * GLYPH_W + col] = avgAlpha > 127 ? 1 : 0
      }
    }
  }

  /** Clear the glyph cache (e.g., on font change) */
  clearCache(): void {
    this._glyphCache.clear()
  }
}
