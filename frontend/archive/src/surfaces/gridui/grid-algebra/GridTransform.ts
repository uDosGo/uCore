/* ═══════════════════════════════════════════════════════════════════
   GridTransform — Pure functions that transform GridBuffers
   ═══════════════════════════════════════════════════════════════════
   All functions are pure — they return new buffers without mutating
   the input. This makes them safe for React state updates.

   Operations:
     resize   — Crop or pad a buffer to new dimensions
     overlay  — Composite one buffer on top of another
     scroll   — Shift rows up/down (for terminal)
     crop     — Extract a sub-region
     merge    — Non-destructive union of two buffers
   ═══════════════════════════════════════════════════════════════════ */

import { GridBuffer, GridCell, createCell, cloneBuffer, getDimensions } from './GridCell'

// ─── Resize ──────────────────────────────────────────────────────────

/**
 * Resize a buffer to new dimensions.
 * - If new cols > old cols: pads with space cells on the right
 * - If new cols < old cols: crops from the right
 * - Same for rows (pads/crops from bottom)
 */
export function resize(buf: GridBuffer, newCols: number, newRows: number): GridBuffer {
  const { cols, rows } = getDimensions(buf)
  const result: GridBuffer = []

  for (let y = 0; y < newRows; y++) {
    const row: GridCell[] = []
    for (let x = 0; x < newCols; x++) {
      if (y < rows && x < cols) {
        row.push({ ...buf[y][x] })
      } else {
        row.push(createCell())
      }
    }
    result.push(row)
  }
  return result
}

// ─── Overlay ─────────────────────────────────────────────────────────

/**
 * Overlay one buffer on top of another at a given offset.
 * Non-space characters in `top` replace characters in `base`.
 * The base buffer is returned mutated (for performance).
 */
export function overlay(
  base: GridBuffer,
  top: GridBuffer,
  offsetX = 0,
  offsetY = 0,
): GridBuffer {
  const { cols: baseCols, rows: baseRows } = getDimensions(base)
  const { cols: topCols, rows: topRows } = getDimensions(top)
  const result = cloneBuffer(base)

  for (let ty = 0; ty < topRows; ty++) {
    for (let tx = 0; tx < topCols; tx++) {
      const bx = offsetX + tx
      const by = offsetY + ty
      if (bx >= 0 && bx < baseCols && by >= 0 && by < baseRows) {
        const topCell = top[ty][tx]
        // Only overlay non-space characters (or if explicitly flagged)
        if (topCell.char !== ' ' || topCell.bg !== 0) {
          result[by][bx] = { ...topCell }
        }
      }
    }
  }
  return result
}

// ─── Scroll ──────────────────────────────────────────────────────────

/**
 * Scroll a buffer up or down by `lines` rows.
 * Positive = scroll up (new lines appear at bottom)
 * Negative = scroll down (new lines appear at top)
 * Newly exposed rows are filled with empty cells.
 */
export function scroll(buf: GridBuffer, lines: number): GridBuffer {
  const { cols, rows } = getDimensions(buf)
  const result = cloneBuffer(buf)

  if (lines > 0) {
    // Scroll up: shift rows up, fill bottom
    for (let y = 0; y < rows; y++) {
      const srcY = y + lines
      if (srcY < rows) {
        result[y] = buf[srcY].map(c => ({ ...c }))
      } else {
        result[y] = Array.from({ length: cols }, () => createCell())
      }
    }
  } else if (lines < 0) {
    // Scroll down: shift rows down, fill top
    const absLines = -lines
    for (let y = rows - 1; y >= 0; y--) {
      const srcY = y - absLines
      if (srcY >= 0) {
        result[y] = buf[srcY].map(c => ({ ...c }))
      } else {
        result[y] = Array.from({ length: cols }, () => createCell())
      }
    }
  }

  return result
}

// ─── Crop ────────────────────────────────────────────────────────────

/**
 * Extract a sub-region from a buffer.
 * Returns a new buffer of size (w × h).
 * Clamps to buffer boundaries.
 */
export function crop(
  buf: GridBuffer,
  x: number,
  y: number,
  w: number,
  h: number,
): GridBuffer {
  const { cols, rows } = getDimensions(buf)
  const result: GridBuffer = []

  for (let dy = 0; dy < h; dy++) {
    const row: GridCell[] = []
    for (let dx = 0; dx < w; dx++) {
      const sx = x + dx
      const sy = y + dy
      if (sx >= 0 && sx < cols && sy >= 0 && sy < rows) {
        row.push({ ...buf[sy][sx] })
      } else {
        row.push(createCell())
      }
    }
    result.push(row)
  }
  return result
}

// ─── Merge ───────────────────────────────────────────────────────────

/**
 * Merge two buffers of the same dimensions.
 * For each cell, if either has a non-space char, use it.
 * If both have non-space chars, `b` wins.
 */
export function merge(a: GridBuffer, b: GridBuffer): GridBuffer {
  const { cols, rows } = getDimensions(a)
  const result = cloneBuffer(a)

  for (let y = 0; y < rows && y < b.length; y++) {
    for (let x = 0; x < cols && x < b[y].length; x++) {
      const bCell = b[y][x]
      if (bCell.char !== ' ' || bCell.bg !== 0) {
        result[y][x] = { ...bCell }
      }
    }
  }
  return result
}

// ─── Fill ────────────────────────────────────────────────────────────

/**
 * Fill a region of a buffer with a specific character and colours.
 */
export function fill(
  buf: GridBuffer,
  x: number,
  y: number,
  w: number,
  h: number,
  char: string,
  fg: number,
  bg: number,
): GridBuffer {
  const result = cloneBuffer(buf)
  const { cols, rows } = getDimensions(buf)

  for (let dy = 0; dy < h; dy++) {
    for (let dx = 0; dx < w; dx++) {
      const fx = x + dx
      const fy = y + dy
      if (fx >= 0 && fx < cols && fy >= 0 && fy < rows) {
        result[fy][fx] = { ...result[fy][fx], char, fg, bg }
      }
    }
  }
  return result
}

// ─── Write String ────────────────────────────────────────────────────

/**
 * Write a string into a buffer at a given position.
 * Returns a new buffer. Characters wrap at buffer edges.
 */
export function writeString(
  buf: GridBuffer,
  x: number,
  y: number,
  text: string,
  fg = 7,
  bg = 0,
  bold = false,
): GridBuffer {
  const result = cloneBuffer(buf)
  const { cols, rows } = getDimensions(buf)

  for (let i = 0; i < text.length; i++) {
    const dx = x + i
    if (y >= 0 && y < rows && dx >= 0 && dx < cols) {
      result[y][dx] = { char: text[i], fg, bg, bold, flash: false, doubleHeight: false, doubleWidth: false }
    }
  }
  return result
}
