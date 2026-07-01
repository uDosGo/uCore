/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  GridUICanvasElement,
  createGridUICanvas,
  textToGridBuffer,
  createBuffer,
  writeString,
  getDimensions,
} from '../GridUICanvasElement'

// ─── Web Component Registration ─────────────────────────────────────

describe('GridUICanvasElement', () => {
  it('is registered as <gridui-canvas>', () => {
    expect(customElements.get('gridui-canvas')).toBe(GridUICanvasElement)
  })

  it('can be created via document.createElement', () => {
    const el = document.createElement('gridui-canvas') as GridUICanvasElement
    expect(el).toBeInstanceOf(GridUICanvasElement)
    expect(el.cols).toBe(80)
    expect(el.rows).toBe(24)
  })

  it('can be created via createGridUICanvas factory', () => {
    const el = createGridUICanvas({ cols: 40, rows: 12 })
    expect(el).toBeInstanceOf(GridUICanvasElement)
    expect(el.cols).toBe(40)
    expect(el.rows).toBe(12)
  })

  it('setBuffer updates the buffer', () => {
    const el = createGridUICanvas({ cols: 20, rows: 5 })
    const buf = createBuffer(20, 5)
    const modified = writeString(buf, 0, 0, 'TEST')
    el.setBuffer(modified)
    expect(el.buffer[0][0].char).toBe('T')
  })

  it('write writes a string at position', () => {
    const el = createGridUICanvas({ cols: 20, rows: 5 })
    el.write(5, 2, 'HELLO', 2, 0, true)
    expect(el.buffer[2][5].char).toBe('H')
    expect(el.buffer[2][5].fg).toBe(2)
    expect(el.buffer[2][5].bold).toBe(true)
  })

  it('clear resets to blank buffer', () => {
    const el = createGridUICanvas({ cols: 20, rows: 5 })
    el.write(0, 0, 'DATA')
    el.clear()
    expect(el.buffer[0][0].char).toBe(' ')
  })

  it('getMetrics returns correct dimensions', () => {
    const el = createGridUICanvas({ cols: 40, rows: 12, cellSize: 16 })
    const metrics = el.getMetrics()
    expect(metrics.cols).toBe(40)
    expect(metrics.rows).toBe(12)
    expect(metrics.cellSize).toBe(16)
    expect(metrics.width).toBe(640)
    expect(metrics.height).toBe(192)
  })

  it('renders shadow DOM', () => {
    // Polyfill ResizeObserver for jsdom
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    const el = createGridUICanvas({ cols: 10, rows: 3 })
    document.body.appendChild(el)
    const shadow = el.shadowRoot
    expect(shadow).toBeTruthy()
    el.remove()
  })

  it('attribute changes update state', () => {
    const el = createGridUICanvas({ cols: 80, rows: 24 })
    el.setAttribute('cols', '40')
    el.setAttribute('rows', '12')
    expect(el.cols).toBe(40)
    expect(el.rows).toBe(12)
  })
})

// ─── textToGridBuffer ────────────────────────────────────────────────

describe('textToGridBuffer', () => {
  it('converts single line text', () => {
    const buf = textToGridBuffer('Hello', 80)
    expect(buf[0][0].char).toBe('H')
    expect(buf[0][4].char).toBe('o')
  })

  it('converts multi-line text', () => {
    const buf = textToGridBuffer('Line1\nLine2', 80)
    expect(buf[0][0].char).toBe('L')
    expect(buf[1][0].char).toBe('L')
  })

  it('respects column width', () => {
    const buf = textToGridBuffer('ABCDEFGHIJ', 5)
    // Only first 5 chars fit on the line
    expect(buf[0][0].char).toBe('A')
    expect(buf[0][4].char).toBe('E')
  })
})
