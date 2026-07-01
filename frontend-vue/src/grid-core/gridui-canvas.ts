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
 * - Auto-scales to fit container
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
      display: inline-block;
      line-height: 0;        /* CRITICAL: removes line-height gaps */
      font-size: 0;          /* CRITICAL: removes font-size gaps */
      overflow: hidden;
      position: relative;
    }
    canvas {
      display: block;        /* CRITICAL: removes inline-block gap below canvas */
      width: 100%;
      height: 100%;
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
  private _resizeObserver: ResizeObserver | null = null
  private _hoveredCell: { col: number; row: number } | null = null

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
    this._setupResizeObserver()
    this._startBlink()
    // Fit canvas to container before first render
    this._fitCanvas()
    this._render()
  }


  disconnectedCallback(): void {
    this._stopBlink()
    this._resizeObserver?.disconnect()
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
    this._font = this.getAttribute('font') || 'monospace'

    // Ensure buffer matches dimensions
    if (this._buffer.length === 0) {
      this._buffer = this._createEmptyBuffer()
    }
  }

  /* ─── Resize Observer ─────────────────────────────────────────── */

  private _setupResizeObserver(): void {
    this._resizeObserver = new ResizeObserver(() => {
      this._fitCanvas()
      this._render()
    })
    this._resizeObserver.observe(this)
  }

  /**
   * Fit the canvas to the element's display size.
   * Uses devicePixelRatio for crisp rendering on Retina displays.
   */
  private _fitCanvas(): void {
    const rect = this.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1
    const pixelWidth = Math.round(rect.width * dpr)
    const pixelHeight = Math.round(rect.height * dpr)

    if (this._canvas.width !== pixelWidth || this._canvas.height !== pixelHeight) {
      this._canvas.width = pixelWidth
      this._canvas.height = pixelHeight
      this._canvas.style.width = `${rect.width}px`
      this._canvas.style.height = `${rect.height}px`
    }
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
    const rect = this.getBoundingClientRect()

    // Calculate scale to fit the grid into the available space
    const scaleX = (rect.width * dpr) / (this._cols * this._cellSize)
    const scaleY = (rect.height * dpr) / (this._rows * this._cellSize)
    const scale = Math.min(scaleX, scaleY, 1) // Don't upscale beyond 1x

    const cellW = Math.round(this._cellSize * scale)
    const cellH = Math.round(this._cellSize * scale)

    // Clear canvas
    ctx.fillStyle = '#000000'
    ctx.fillRect(0, 0, this._canvas.width, this._canvas.height)

    // Set font for character rendering
    // Monospace fonts are ~0.6× font-size in width, so we need
    // fontSize ≈ cellW / 0.6 to make each char fill the cell width.
    // We intentionally make font slightly larger than cell height;
    // adjacent row backgrounds clip vertical overflow.
    const fontSize = Math.round(cellW / 0.6)
    ctx.font = `${fontSize}px "${this._font}", monospace`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'

    // Draw each cell — NO gaps between cells
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
          ctx.fillRect(x, y, cellW, cellH)
          continue
        }

        // Draw background — fills the entire cell area with NO gap
        ctx.fillStyle = getColour(cell.bg, this._palette)
        ctx.fillRect(x, y, cellW, cellH)

        // Draw character
        if (cell.char && cell.char !== ' ') {
          ctx.fillStyle = getColour(cell.fg, this._palette)

          // Bold: draw twice for thicker appearance
          if (cell.bold) {
            ctx.fillText(cell.char, x + cellW / 2 - 1, y + cellH / 2)
            ctx.fillText(cell.char, x + cellW / 2 + 1, y + cellH / 2)
          } else {
            ctx.fillText(cell.char, x + cellW / 2, y + cellH / 2)
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
    const scaleX = rect.width / (this._cols * this._cellSize)
    const scaleY = rect.height / (this._rows * this._cellSize)
    const scale = Math.min(scaleX, scaleY, 1)

    const cellW = this._cellSize * scale
    const cellH = this._cellSize * scale

    const col = Math.floor(x / cellW)
    const row = Math.floor(y / cellH)

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
