/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest'
import {
  createCell,
  createBuffer,
  cloneBuffer,
  getDimensions,
  sameDimensions,
  TERMINAL_COLS,
  TERMINAL_ROWS,
} from '../grid-algebra/GridCell'
import {
  resize,
  overlay,
  scroll,
  crop,
  merge,
  fill,
  writeString,
} from '../grid-algebra/GridTransform'
import { getColor, UNIFIED_PALETTE } from '../grid-algebra/ColourPalette'
import { getFontFamily, getFontSizeScale } from '../grid-algebra/FontResolver'
import { resolveTeletextChar, TELETEXT_G0 } from '../grid-algebra/CharacterSet'

// ─── GridCell ────────────────────────────────────────────────────────

describe('GridCell', () => {
  it('createCell returns default cell', () => {
    const cell = createCell()
    expect(cell.char).toBe(' ')
    expect(cell.fg).toBe(7)
    expect(cell.bg).toBe(0)
    expect(cell.bold).toBe(false)
    expect(cell.flash).toBe(false)
    expect(cell.doubleHeight).toBe(false)
    expect(cell.doubleWidth).toBe(false)
  })

  it('createCell accepts custom values', () => {
    const cell = createCell('A', 1, 2, true, true, true, true)
    expect(cell.char).toBe('A')
    expect(cell.fg).toBe(1)
    expect(cell.bg).toBe(2)
    expect(cell.bold).toBe(true)
    expect(cell.flash).toBe(true)
    expect(cell.doubleHeight).toBe(true)
    expect(cell.doubleWidth).toBe(true)
  })

  it('createBuffer creates correct dimensions', () => {
    const buf = createBuffer(40, 12)
    expect(buf.length).toBe(12)
    expect(buf[0].length).toBe(40)
    expect(buf[0][0].char).toBe(' ')
  })

  it('createBuffer uses terminal defaults', () => {
    expect(TERMINAL_COLS).toBe(80)
    expect(TERMINAL_ROWS).toBe(24)
  })

  it('cloneBuffer creates deep copy', () => {
    const buf = createBuffer(10, 5)
    const cloned = cloneBuffer(buf)
    cloned[0][0].char = 'X'
    expect(buf[0][0].char).toBe(' ')
    expect(cloned[0][0].char).toBe('X')
  })

  it('getDimensions returns correct size', () => {
    const buf = createBuffer(80, 24)
    const { cols, rows } = getDimensions(buf)
    expect(cols).toBe(80)
    expect(rows).toBe(24)
  })

  it('sameDimensions compares buffers', () => {
    const a = createBuffer(40, 12)
    const b = createBuffer(40, 12)
    const c = createBuffer(80, 24)
    expect(sameDimensions(a, b)).toBe(true)
    expect(sameDimensions(a, c)).toBe(false)
  })
})

// ─── GridTransform ──────────────────────────────────────────────────

describe('GridTransform', () => {
  it('resize pads buffer', () => {
    const buf = createBuffer(10, 5)
    const resized = resize(buf, 20, 10)
    expect(getDimensions(resized)).toEqual({ cols: 20, rows: 10 })
  })

  it('resize crops buffer', () => {
    const buf = createBuffer(80, 24)
    const resized = resize(buf, 40, 12)
    expect(getDimensions(resized)).toEqual({ cols: 40, rows: 12 })
  })

  it('writeString writes text at position', () => {
    const buf = createBuffer(40, 5)
    const result = writeString(buf, 2, 1, 'Hello')
    expect(result[1][2].char).toBe('H')
    expect(result[1][6].char).toBe('o')
    // Original buffer unchanged (pure function)
    expect(buf[1][2].char).toBe(' ')
  })

  it('writeString respects buffer bounds', () => {
    const buf = createBuffer(5, 2)
    const result = writeString(buf, 3, 0, 'ABCDE')
    expect(result[0][3].char).toBe('A')
    expect(result[0][4].char).toBe('B')
    // C, D, E are out of bounds — silently dropped
  })

  it('scroll shifts rows up', () => {
    let buf = createBuffer(10, 3)
    buf = writeString(buf, 0, 0, 'Line0')
    buf = writeString(buf, 0, 1, 'Line1')
    buf = writeString(buf, 0, 2, 'Line2')
    const scrolled = scroll(buf, 1)
    expect(scrolled[0][0].char).toBe('L') // was Line1
    expect(scrolled[1][0].char).toBe('L') // was Line2
    expect(scrolled[2][0].char).toBe(' ') // new blank line
  })

  it('overlay composites buffers', () => {
    const base = createBuffer(10, 3)
    const top = createBuffer(5, 2)
    const topModified = writeString(top, 0, 0, 'HELLO')
    const result = overlay(base, topModified, 2, 1)
    // top[0][0]='H' → base[1][2], top[0][4]='O' → base[1][6]
    expect(result[1][2].char).toBe('H')
    expect(result[1][6].char).toBe('O')
    // Verify original base is unchanged (pure function)
    expect(base[1][2].char).toBe(' ')
  })

  it('crop extracts sub-region', () => {
    let buf = createBuffer(20, 10)
    buf = writeString(buf, 5, 5, 'CENTER')
    const cropped = crop(buf, 4, 4, 8, 3)
    expect(getDimensions(cropped)).toEqual({ cols: 8, rows: 3 })
    expect(cropped[1][1].char).toBe('C')
  })

  it('merge combines buffers', () => {
    const a = createBuffer(10, 3)
    const b = createBuffer(10, 3)
    const bModified = writeString(b, 0, 0, 'MERGED')
    const result = merge(a, bModified)
    expect(result[0][0].char).toBe('M')
  })

  it('fill paints a region', () => {
    const buf = createBuffer(20, 5)
    const result = fill(buf, 2, 1, 5, 2, '#', 1, 0)
    expect(result[1][2].char).toBe('#')
    expect(result[1][2].fg).toBe(1)
    expect(result[1][7].char).toBe(' ')
  })
})

// ─── ColourPalette ──────────────────────────────────────────────────

describe('ColourPalette', () => {
  it('getColor returns correct hex values', () => {
    expect(getColor('unified', 0)).toBe('#0d1117') // Black
    expect(getColor('unified', 7)).toBe('#e6edf3') // White
  })

  it('getColor clamps out-of-range indices', () => {
    expect(getColor('unified', -1)).toBe('#0d1117')
    expect(getColor('unified', 99)).toBe('#e6edf3')
  })

  it('UNIFIED_PALETTE has 8 colors', () => {
    expect(UNIFIED_PALETTE.colors).toHaveLength(8)
  })
})

// ─── FontResolver ───────────────────────────────────────────────────

describe('FontResolver', () => {
  it('getFontFamily returns CSS font string for pressstart2p', () => {
    const family = getFontFamily('pressstart2p')
    expect(family).toContain('Press Start 2P')
    expect(family).toContain('monospace')
  })

  it('getFontFamily returns CSS font string for vt323', () => {
    const family = getFontFamily('vt323')
    expect(family).toContain('VT323')
    expect(family).toContain('monospace')
  })

  it('getFontSizeScale returns valid scale', () => {
    expect(getFontSizeScale('pressstart2p')).toBe(0.65)
    expect(getFontSizeScale('vt323')).toBe(1.0)
  })
})

// ─── CharacterSet ───────────────────────────────────────────────────

describe('CharacterSet', () => {
  it('resolveTeletextChar maps basic Latin', () => {
    expect(resolveTeletextChar(0x41)).toBe('A')
    expect(resolveTeletextChar(0x61)).toBe('a')
    expect(resolveTeletextChar(0x30)).toBe('0')
  })

  it('resolveTeletextChar maps control chars to space', () => {
    expect(resolveTeletextChar(0x00)).toBe(' ')
    expect(resolveTeletextChar(0x1F)).toBe(' ')
  })

  it('resolveTeletextChar maps block graphics', () => {
    expect(resolveTeletextChar(0xCA)).toBe('█')
    expect(resolveTeletextChar(0xF5)).toBe('─')
  })

  it('TELETEXT_G0 has 256 entries', () => {
    expect(Object.keys(TELETEXT_G0)).toHaveLength(256)
  })
})
