/**
 * GridCore UI — <gridui-canvas> Web Component
 *
 * Framework-agnostic custom element that renders a character grid
 * to a <canvas> element. Cells are rendered pixel-perfect with
 * NO gaps between tiles — each cell is exactly cellSize × cellSize
 * pixels with no padding, margin, or spacing.
 *
 * Features:
 * - Zero-gap cell rendering (fixes the "big gaps aside and below each tile" issue)
 * - 8-colour palette (foreground + background)
 * - Bold, blink, mosaic modes
 * - Intrinsic sizing: host width/height = cols × cellSize
 * - Emits cell-click and cell-hover events
 * - Supports setBuffer() for external buffer updates
 */

import type { GridBuffer, GridCell } from './types'
import { PALETTE_DARK, getColour } from './palette'

/* ─── Template ─────────────────────────────────────────────────── */

const template = document.createElement('template')
template.innerHTML = `
  <style>
    :host {
      display: inline-block;  /* shrink-wrap to grid content */
      line-height: 0;
      font-size: 0;
      overflow: hidden;
    }
    canvas {
      display: block;
      image-rendering: pixelated;
      image-rendering: crisp-edges;
    }
  </style>
  <canvas></canvas>
`

/* ─── Web Component ────────────────────────────────────────────── */

export class GridUICanvasElement extends HTMLElement {
  private _canvas: HTMLCanvasElement
  private _ctx: CanvasRenderingContext2D | null
  private _buffer: GridBuffer = []
  private _cols: number = 40
  private _rows: number = 25
  private _cellSize: number = 16
  private _font: string = 'monospace'
  private _palette = PALETTE_DARK
  private _blinkState: boolean = true
  private _blinkInterval: number | null = null
  private _hoveredCell: { col: number; row: number } | null = null
  private _resizeObserver: ResizeObserver | null = null
  /** Configured cellSize from attribute (before any container fitting) */
  private _configuredCellSize: number = 16
  /** Whether to auto-fit to container (default true, set fit-container="false" to disable) */
  private _fitToContainerEnabled: boolean = true

  /* ─── Observed Attributes ─────────────────────────────────────── */

  static get observedAttributes(): string[] {
    return ['cols', 'rows', 'cell-size', 'font', 'palette']
  }

  /* ─── Constructor ─────────────────────────────────────────────── */

  constructor() {
    super()
    const shadow = this.attachShadow({ mode: 'open' })
    shadow.appendChild(template.content.cloneNode(true))

    this._canvas = shadow.querySelector('canvas')!
    this._ctx = this._canvas.getContext('2d')

    // Bind event handlers
    this._canvas.addEventListener('click', this._onClick.bind(this))
    this._canvas.addEventListener('mousemove', this._onMouseMove.bind(this))
    this._canvas.addEventListener('mouseleave', this._onMouseLeave.bind(this))
  }

  /* ─── Lifecycle ───────────────────────────────────────────────── */

  connectedCallback(): void {
    this._parseAttributes()
    this._startBlink()
    // Observe container for responsive fitting
    this._resizeObserver = new ResizeObserver(() => this._fitToContainer())
    this._resizeObserver.observe(this.parentElement || this)
    // Size canvas and render
    this._fitToContainer()
    this._render()
  }


  disconnectedCallback(): void {
    this._stopBlink()
    this._resizeObserver?.disconnect()
    this._resizeObserver = null
  }

  attributeChangedCallback(): void {
    this._parseAttributes()
    this._render()
  }

  /* ─── Attribute Parsing ───────────────────────────────────────── */

  private _parseAttributes(): void {
    this._cols = parseInt(this.getAttribute('cols') || '40', 10)
    this._rows = parseInt(this.getAttribute('rows') || '25', 10)
    this._cellSize = parseInt(this.getAttribute('cell-size') || '16', 10)
    this._configuredCellSize = this._cellSize
    this._font = this.getAttribute('font') || 'monospace'
    this._fitToContainerEnabled = this.getAttribute('fit-container') !== 'false'

    // Ensure buffer matches dimensions
    if (this._buffer.length === 0) {
      this._buffer = this._createEmptyBuffer()
    }
  }

  /**
   * Fit the grid to the available container space.
   * Uses the configured cellSize when container is large enough,
   * shrinks cells proportionally when container is small.
   * Always keeps the grid centered.
   * Disable with fit-container="false" attribute.
   */
  private _fitToContainer(): void {
    if (!this._fitToContainerEnabled || !this.parentElement) {
      this._cellSize = this._configuredCellSize
    } else {
      const parent = this.parentElement
      const availW = parent.clientWidth
      const availH = parent.clientHeight
      const maxCellW = Math.floor(availW / this._cols)
      const maxCellH = Math.floor(availH / this._rows)
      // Use configured size if it fits, otherwise shrink to fit
      this._cellSize = Math.min(this._configuredCellSize, maxCellW, maxCellH)
      // Never go below 4px cells
      if (this._cellSize < 4) this._cellSize = 4
    }

    const dpr = window.devicePixelRatio || 1
    const cssWidth = this._cols * this._cellSize
    const cssHeight = this._rows * this._cellSize
    const pixelWidth = Math.round(cssWidth * dpr)
    const pixelHeight = Math.round(cssHeight * dpr)

    if (this._canvas.width !== pixelWidth || this._canvas.height !== pixelHeight) {
      this._canvas.width = pixelWidth
      this._canvas.height = pixelHeight
    }
    this._canvas.style.width = `${cssWidth}px`
    this._canvas.style.height = `${cssHeight}px`
    this.style.width = `${cssWidth}px`
    this.style.height = `${cssHeight}px`
  }

  /* ─── Blink Support ───────────────────────────────────────────── */

  private _startBlink(): void {
    this._blinkState = true
    this._blinkInterval = window.setInterval(() => {
      this._blinkState = !this._blinkState
      this._render()
    }, 500)
  }

  private _stopBlink(): void {
    if (this._blinkInterval !== null) {
      clearInterval(this._blinkInterval)
      this._blinkInterval = null
    }
  }

  /* ─── Buffer Management ───────────────────────────────────────── */

  private _createEmptyBuffer(): GridBuffer {
    const buf: GridBuffer = []
    for (let r = 0; r < this._rows; r++) {
      const row: GridCell[] = []
      for (let c = 0; c < this._cols; c++) {
        row.push({ char: ' ', fg: 7, bg: 0 })
      }
      buf.push(row)
    }
    return buf
  }

  /**
   * Get the current grid buffer.
   */
  get buffer(): GridBuffer {
    return this._buffer
  }

  /**
   * Set the grid buffer and re-render.
   * This is the primary API for external code to update the display.
   */
  setBuffer(buf: GridBuffer): void {
    this._buffer = buf
    this._cols = buf.length > 0 ? buf[0].length : this._cols
    this._rows = buf.length
    this._render()
  }

  /**
   * Clear the buffer (fill with spaces).
   */
  clear(): void {
    this._buffer = this._createEmptyBuffer()
    this._render()
  }

  /* ─── Rendering ───────────────────────────────────────────────── */

  /**
   * Render the grid buffer to the canvas.
   *
   * CRITICAL: Each cell is drawn as a filled rectangle of exactly
   * cellSize × cellSize pixels, with NO gaps between adjacent cells.
   * The background colour fills the entire cell, then the character
   * is drawn on top in the foreground colour.
   *
   * FIX: letterSpacing is NOT a standard CanvasRenderingContext2D property.
   * It was being used incorrectly, causing no actual effect (silently ignored).
   * The proper approach is to set font size correctly for monospace chars
   * and rely on fillRect for exact pixel positioning.
   */
  private _render(): void {
    if (!this._ctx) return

    const ctx = this._ctx
    const dpr = window.devicePixelRatio || 1

    // Ensure canvas is sized to fit container
    this._fitToContainer()

    // Disable canvas smoothing for pixel-perfect rendering — prevents
    // anti-aliased seams between adjacent filled rectangles.
    ctx.imageSmoothingEnabled = false

    const cellW = Math.round(this._cellSize * dpr)
    const cellH = Math.round(this._cellSize * dpr)

    // Clear canvas
    ctx.fillStyle = '#000000'
    ctx.fillRect(0, 0, this._canvas.width, this._canvas.height)

    // Font size = full cell height so characters fill the cell vertically.
    // Clipping per cell prevents overflow into adjacent cells.
    // Press Start 2P: pixel font at cellSize maps its pixel grid to cells
    // VT323: teletext font slightly oversized to fill cell height
    // Block chars: graphic/line characters that should fill the cell as solid rects
    // This gives true grid-aligned rendering instead of relying on font glyph widths.
    const BLOCK_CHARS = new Set([
      '=', '-', '|', '#', '*', '.', '~', 'X', 'x', '+', '·',
      '─', '│', '═', '║', '╔', '╗', '╚', '╝', '╠', '╣', '╦', '╩', '╬',
      '█', '▄', '▀', '▐', '▌', '░', '▒', '▓',
    ])

    // Font for text characters — oversized and clipped so glyphs fill the cell
    const fontScale = (this._font === 'pressstart2p' || this._font === '"pressstart2p"')
      ? 1.5   // Press Start 2P has narrow glyphs (±50% width) — boost to fill
      : (this._font === 'vt323' || this._font === '"vt323"')
        ? 1.2  // VT323 is wider
        : 1.0
    const fontSize = Math.round(this._cellSize * fontScale * dpr)
    ctx.font = `${fontSize}px "${this._font}", monospace`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'

    // Draw each cell — ZERO gaps between cells.
    // Background fills overlap by 1px to eliminate anti-aliased seam lines
    // that can appear between adjacent rectangles on some GPUs/browsers.
    for (let r = 0; r < this._rows && r < this._buffer.length; r++) {
      const row = this._buffer[r]
      if (!row) continue

      for (let c = 0; c < this._cols && c < row.length; c++) {
        const cell = row[c]
        if (!cell) continue

        const x = c * cellW
        const y = r * cellH

        // Skip blink cells when blink state is off
        if (cell.blink && !this._blinkState) {
          ctx.fillStyle = getColour(cell.bg, this._palette)
          ctx.fillRect(x, y, cellW + 1, cellH + 1)
          continue
        }

        // Draw background — fills entire cell + 1px overlap to kill seams
        ctx.fillStyle = getColour(cell.bg, this._palette)
        ctx.fillRect(x, y, cellW + 1, cellH + 1)

        // Draw character
        if (cell.char && cell.char !== ' ') {
          ctx.fillStyle = getColour(cell.fg, this._palette)

          if (BLOCK_CHARS.has(cell.char)) {
            // Block chars: fill the entire cell as a solid rectangle.
            // This gives true grid-aligned rendering for graphic elements.
            ctx.fillRect(x, y, cellW, cellH)
          } else {
            // Text chars: render as font glyph, clipped to cell boundaries
            ctx.save()
            ctx.beginPath()
            ctx.rect(x, y, cellW, cellH)
            ctx.clip()

            // Bold: draw twice for thicker appearance
            if (cell.bold) {
              ctx.fillText(cell.char, x + cellW / 2 - 1, y + cellH / 2)
              ctx.fillText(cell.char, x + cellW / 2 + 1, y + cellH / 2)
            } else {
              ctx.fillText(cell.char, x + cellW / 2, y + cellH / 2)
            }

            ctx.restore()
          }
        }

        // Mosaic mode: draw block graphic
        if (cell.mosaic) {
          this._drawMosaic(ctx, x, y, cellW, cellH, cell.char)
        }
      }
    }
  }

  /**
   * Draw a mosaic block graphic in the given cell area.
   * Mosaic characters use the foreground colour to fill portions of the cell.
   */
  private _drawMosaic(
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    w: number,
    h: number,
    char: string,
  ): void {
    ctx.fillStyle = getColour(7, this._palette) // White foreground for mosaic
    const hw = Math.round(w / 2)
    const hh = Math.round(h / 2)

    switch (char) {
      case '\u2580': // Upper half block
        ctx.fillRect(x, y, w, hh)
        break
      case '\u2584': // Lower half block
        ctx.fillRect(x, y + hh, w, hh)
        break
      case '\u2588': // Full block
        ctx.fillRect(x, y, w, h)
        break
      case '\u258C': // Left half block
        ctx.fillRect(x, y, hw, h)
        break
      case '\u2590': // Right half block
        ctx.fillRect(x + hw, y, hw, h)
        break
    }
  }

  /* ─── Event Handling ──────────────────────────────────────────── */

  private _getCellFromEvent(event: MouseEvent): { col: number; row: number } | null {
    const rect = this._canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Cell size in CSS pixels (canvas is sized to exactly cols*cellSize × rows*cellSize)
    const col = Math.floor(x / this._cellSize)
    const row = Math.floor(y / this._cellSize)

    if (col >= 0 && col < this._cols && row >= 0 && row < this._rows) {
      return { col, row }
    }
    return null
  }

  private _onClick(event: MouseEvent): void {
    const cell = this._getCellFromEvent(event)
    if (cell) {
      this.dispatchEvent(new CustomEvent('cell-click', {
        detail: cell,
        bubbles: true,
        composed: true,
      }))
    }
  }

  private _onMouseMove(event: MouseEvent): void {
    const cell = this._getCellFromEvent(event)
    if (cell) {
      const prev = this._hoveredCell
      if (!prev || prev.col !== cell.col || prev.row !== cell.row) {
        this._hoveredCell = cell
        this.dispatchEvent(new CustomEvent('cell-hover', {
          detail: cell,
          bubbles: true,
          composed: true,
        }))
      }
    }
  }

  private _onMouseLeave(): void {
    this._hoveredCell = null
    this.dispatchEvent(new CustomEvent('cell-hover', {
      detail: null,
      bubbles: true,
      composed: true,
    }))
  }
}

/* ─── Registration ─────────────────────────────────────────────── */

if (!customElements.get('gridui-canvas')) {
  customElements.define('gridui-canvas', GridUICanvasElement)
}

/* ─── Factory Function ─────────────────────────────────────────── */

/**
 * Create a <gridui-canvas> element with the given options.
 *
 * This is the primary API for Vue/React integration.
 */
export function createGridUICanvas(options: {
  cols?: number
  rows?: number
  cellSize?: number
  font?: string
} = {}): GridUICanvasElement {
  const el = document.createElement('gridui-canvas') as GridUICanvasElement
  if (options.cols !== undefined) el.setAttribute('cols', String(options.cols))
  if (options.rows !== undefined) el.setAttribute('rows', String(options.rows))
  if (options.cellSize !== undefined) el.setAttribute('cell-size', String(options.cellSize))
  if (options.font !== undefined) el.setAttribute('font', options.font)
  return el
}
