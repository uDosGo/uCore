/**
 * Grid Algebra — Grid Buffer Operations
 *
 * Functions for creating and manipulating grid buffers.
 * These are the canonical buffer operations used by both
 * GridCore UI (character-grid widgets) and the backend Ceefax store.
 */

import type { GridBuffer, GridCell } from './types'

/**
 * Create an empty grid buffer filled with space characters.
 */
export function createBuffer(cols: number, rows: number): GridBuffer {
  const buf: GridBuffer = []
  for (let r = 0; r < rows; r++) {
    const row: GridCell[] = []
    for (let c = 0; c < cols; c++) {
      row.push({ char: ' ', fg: 7, bg: 0 })
    }
    buf.push(row)
  }
  return buf
}

/**
 * Write a string into the buffer at the given position.
 *
 * Returns a new buffer with the string written (immutable pattern).
 */
export function writeString(
  buf: GridBuffer,
  col: number,
  row: number,
  text: string,
  fg: number = 7,
  bg: number = 0,
  bold: boolean = false,
): GridBuffer {
  // Clone the buffer
  const result = buf.map(r => r.map(c => ({ ...c })))
  const rows = result.length
  const cols = rows > 0 ? result[0].length : 0

  if (row < 0 || row >= rows) return result

  for (let i = 0; i < text.length; i++) {
    const c = col + i
    if (c >= 0 && c < cols) {
      result[row][c] = {
        char: text[i],
        fg,
        bg,
        bold,
      }
    }
  }
  return result
}

/**
 * Fill a rectangular region of the buffer with a character.
 *
 * Returns a new buffer with the region filled.
 */
export function fill(
  buf: GridBuffer,
  col: number,
  row: number,
  width: number,
  height: number,
  char: string = ' ',
  fg: number = 7,
  bg: number = 0,
): GridBuffer {
  const result = buf.map(r => r.map(c => ({ ...c })))
  const rows = result.length
  const cols = rows > 0 ? result[0].length : 0

  for (let r = row; r < row + height && r < rows; r++) {
    if (r < 0) continue
    for (let c = col; c < col + width && c < cols; c++) {
      if (c < 0) continue
      result[r][c] = { char, fg, bg }
    }
  }
  return result
}

/**
 * Scroll the buffer up by the given number of rows.
 * New rows are filled with empty cells at the bottom.
 *
 * Returns a new buffer with the scroll applied.
 */
export function scroll(buf: GridBuffer, rows: number = 1): GridBuffer {
  const totalRows = buf.length
  const cols = totalRows > 0 ? buf[0].length : 0
  if (rows <= 0 || totalRows === 0) return buf.map(r => r.map(c => ({ ...c })))

  const actualScroll = Math.min(rows, totalRows)
  const result = buf.slice(actualScroll).map(r => r.map(c => ({ ...c })))

  // Fill new rows at bottom
  for (let r = totalRows - actualScroll; r < totalRows; r++) {
    const row: GridCell[] = []
    for (let c = 0; c < cols; c++) {
      row.push({ char: ' ', fg: 7, bg: 0 })
    }
    result.push(row)
  }

  return result
}

/**
 * Clear the buffer (fill all cells with space).
 *
 * Returns a new empty buffer.
 */
export function clear(buf: GridBuffer): GridBuffer {
  const rows = buf.length
  const cols = rows > 0 ? buf[0].length : 0
  return createBuffer(cols, rows)
}

/**
 * Clone a grid buffer (deep copy).
 */
export function cloneBuffer(buf: GridBuffer): GridBuffer {
  return buf.map(r => r.map(c => ({ ...c })))
}

/**
 * Convert a grid buffer to a plain string (for debugging/export).
 * Each row is joined, rows are separated by newlines.
 */
export function bufferToString(buf: GridBuffer): string {
  return buf.map(row => row.map(c => c.char).join('')).join('\n')
}

/**
 * Convert a plain string back to a grid buffer.
 * Each line becomes a row, each character becomes a cell.
 */
export function stringToBuffer(text: string): GridBuffer {
  const lines = text.split('\n')
  const cols = Math.max(...lines.map(l => l.length), 0)
  return lines.map(line => {
    const row: GridCell[] = []
    for (let i = 0; i < cols; i++) {
      row.push({
        char: i < line.length ? line[i] : ' ',
        fg: 7,
        bg: 0,
      })
    }
    return row
  })
}
