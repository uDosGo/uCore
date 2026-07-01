/* ═══════════════════════════════════════════════════════════════════
   GridUICanvasElement — Framework-agnostic embeddable grid widget
   ═══════════════════════════════════════════════════════════════════
   A Web Component (Custom Element) that renders a GridBuffer as a
   CSS grid of <span> elements. Works in Vue, React, or plain HTML.

   Usage (HTML):
     <gridui-canvas cols="80" rows="24"></gridui-canvas>

   Usage (JS):
     const el = document.createElement('gridui-canvas')
     el.cols = 40
     el.rows = 12
     el.setBuffer(myBuffer)
     container.appendChild(el)

   Usage (Vue):
     <template>
       <div ref="gridRef"></div>
     </template>
     <script setup>
     import '@vendor/gridui-canvas/GridUICanvasElement'
     const gridRef = ref()
     onMounted(() => {
       const el = document.createElement('gridui-canvas')
       el.cols = 80; el.rows = 24
       el.setBuffer(buffer)
       gridRef.value.appendChild(el)
     })
     </script>

   Architecture:
     GridBuffer (data) → GridUICanvasElement (Web Component) → DOM <span> grid
     No React, no Vue, no framework deps.
   ═══════════════════════════════════════════════════════════════════ */

import {
  type GridBuffer,
  createBuffer,
  getDimensions,
} from './grid-algebra/GridCell'
import { writeString, scroll } from './grid-algebra/GridTransform'
import { getColor, type PaletteId } from './grid-algebra/ColourPalette'
import { type GridFont, getFontFamily, getFontSizeScale } from './grid-algebra/FontResolver'

// ─── Types ──────────────────────────────────────────────────────────

export interface GridUICanvasConfig {
  cols?: number
  rows?: number
  paletteId?: PaletteId
  font?: GridFont
  cellSize?: number
}

// ─── Web Component ──────────────────────────────────────────────────

export class GridUICanvasElement extends HTMLElement {
  // Observed attributes
  static get observedAttributes(): string[] {
    return ['cols', 'rows', 'palette', 'font', 'cell-size']
  }

  // Internal state
  private _buffer: GridBuffer = createBuffer(80, 24)
  private _paletteId: PaletteId = 'unified'
  private _font: GridFont = 'pressstart2p'
  private _cellSize = 24
  private _shadow: ShadowRoot
  private _container: HTMLDivElement
  private _resizeObserver: ResizeObserver | null = null

  constructor() {
    super()
    this._shadow = this.attachShadow({ mode: 'open' })
    this._container = document.createElement('div')
    this._shadow.appendChild(this._container)
  }

  // ─── Lifecycle ────────────────────────────────────────────────

  connectedCallback(): void {
    // Accessibility: set ARIA role and label
    if (!this.hasAttribute('role')) {
      this.setAttribute('role', 'img')
    }
    if (!this.hasAttribute('aria-label')) {
      this.setAttribute('aria-label', `Grid display ${this.cols} by ${this.rows}`)
    }
    if (!this.hasAttribute('tabindex')) {
      this.setAttribute('tabindex', '0')
    }
    this._render()
    this._resizeObserver = new ResizeObserver(() => this._render())
    this._resizeObserver.observe(this)
  }

  disconnectedCallback(): void {
    this._resizeObserver?.disconnect()
    this._resizeObserver = null
  }

  attributeChangedCallback(name: string, _old: string, value: string): void {
    switch (name) {
      case 'cols':
        this._resizeBuffer(parseInt(value) || 80, this.rows)
        break
      case 'rows':
        this._resizeBuffer(this.cols, parseInt(value) || 24)
        break
      case 'palette':
        this._paletteId = (value as PaletteId) || 'unified'
        this._render()
        break
      case 'font':
        this._font = (value as GridFont) || 'pressstart2p'
        this._render()
        break
      case 'cell-size':
        this._cellSize = parseInt(value) || 24
        this._render()
        break
    }
  }

  // ─── Public API ───────────────────────────────────────────────

  get cols(): number {
    return getDimensions(this._buffer).cols
  }

  set cols(value: number) {
    this._resizeBuffer(value, this.rows)
  }

  get rows(): number {
    return getDimensions(this._buffer).rows
  }

  set rows(value: number) {
    this._resizeBuffer(this.cols, value)
  }

  get buffer(): GridBuffer {
    return this._buffer
  }

  /** Set the entire buffer and re-render */
  setBuffer(buf: GridBuffer): void {
    this._buffer = buf
    this._render()
  }

  /** Write a string at position (x, y) and re-render */
  write(x: number, y: number, text: string, fg = 7, bg = 0, bold = false): void {
    this._buffer = writeString(this._buffer, x, y, text, fg, bg, bold)
    this._render()
  }

  /** Scroll the buffer by N lines (positive = up) and re-render */
  scrollLines(lines: number): void {
    this._buffer = scroll(this._buffer, lines)
    this._render()
  }

  /** Clear the buffer to blank and re-render */
  clear(): void {
    this._buffer = createBuffer(this.cols, this.rows)
    this._render()
  }

  /** Get current viewport metrics */
  getMetrics(): { cols: number; rows: number; cellSize: number; width: number; height: number } {
    const { cols, rows } = getDimensions(this._buffer)
    return {
      cols,
      rows,
      cellSize: this._cellSize,
      width: cols * this._cellSize,
      height: rows * this._cellSize,
    }
  }

  // ─── Private ──────────────────────────────────────────────────

  private _resizeBuffer(newCols: number, newRows: number): void {
    const { cols, rows } = getDimensions(this._buffer)
    if (newCols === cols && newRows === rows) return

    // Rebuild buffer at new size (preserving existing content)
    const newBuf = createBuffer(newCols, newRows)
    for (let y = 0; y < Math.min(rows, newRows); y++) {
      for (let x = 0; x < Math.min(cols, newCols); x++) {
        newBuf[y][x] = { ...this._buffer[y][x] }
      }
    }
    this._buffer = newBuf
    this._render()
  }

  private _render(): void {
    const { cols, rows } = getDimensions(this._buffer)
    const fontFamily = getFontFamily(this._font)
    const fontScale = getFontSizeScale(this._font)
    const cellSize = this._cellSize
    const fontSize = cellSize * fontScale

    // Build cell HTML
    let html = ''
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cell = this._buffer[y][x]
        const fg = getColor(this._paletteId, cell.fg)
        const bg = getColor(this._paletteId, cell.bg)
        const char = cell.char === '<' ? '&lt;' : cell.char === '>' ? '&gt;' : cell.char === '&' ? '&amp;' : cell.char === '"' ? '&quot;' : cell.char
        html += `<span style="width:${cellSize}px;height:${cellSize}px;line-height:${cellSize}px;text-align:center;color:${fg};background:${bg};font-weight:${cell.bold ? 'bold' : 'normal'};font-size:${fontSize}px;overflow:hidden;white-space:pre">${char}</span>`
      }
    }

    this._container.innerHTML = html
    this._container.style.cssText = `
      display: grid;
      grid-template-columns: repeat(${cols}, ${cellSize}px);
      grid-template-rows: repeat(${rows}, ${cellSize}px);
      width: ${cols * cellSize}px;
      height: ${rows * cellSize}px;
      gap: 0;
      overflow: hidden;
      font-family: ${fontFamily};
    `
  }
}

// ─── Register Custom Element ────────────────────────────────────────

const ELEMENT_NAME = 'gridui-canvas'

if (!customElements.get(ELEMENT_NAME)) {
  customElements.define(ELEMENT_NAME, GridUICanvasElement)
}

// ─── Convenience Factory ────────────────────────────────────────────

/**
 * Create a GridUICanvas element with the given config.
 * Returns the DOM element ready to be appended.
 */
export function createGridUICanvas(config: GridUICanvasConfig = {}): GridUICanvasElement {
  const el = document.createElement(ELEMENT_NAME) as GridUICanvasElement
  if (config.cols) el.cols = config.cols
  if (config.rows) el.rows = config.rows
  if (config.paletteId) el.setAttribute('palette', config.paletteId)
  if (config.font) el.setAttribute('font', config.font)
  if (config.cellSize) el.setAttribute('cell-size', String(config.cellSize))
  return el
}

/**
 * Helper: Convert plain text to a GridBuffer.
 */
export function textToGridBuffer(text: string, cols = 80): GridBuffer {
  const lines = text.split('\n')
  const rows = Math.max(lines.length, 1)
  let buf = createBuffer(cols, rows)
  for (let y = 0; y < lines.length; y++) {
    buf = writeString(buf, 0, y, lines[y])
  }
  return buf
}

// Re-export grid-algebra for convenience
export * from './grid-algebra/index'
