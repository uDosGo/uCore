/**
 * Grid Algebra — Viewport Resolution & Coordinate Math (v2.0)
 *
 * Core mathematical operations for the Grid Algebra system:
 * - Viewport resolution (viewport width → column spec)
 * - Viewport pixel calculations
 * - Grid buffer transforms (scale, crop, centre)
 * - Grid preset lookup
 *
 * Character Density Guarantee:
 *   Character count per column MUST increase with viewport size,
 *   never decrease. This ensures readable content at all sizes.
 *
 * Column Spec Resolution (v2.0):
 *   <480px:   1×40ch  (xs)
 *   480-768:  2×35ch  (sm)
 *   768-1024: 2×40ch  (md)
 *   1024-1440:3×35ch  (lg)
 *   1440-1920:3×40ch  (xl)
 *   1920px+:  4×40ch  (xxl)
 */

import type { ColumnSpec, Viewport, GridPreset } from './types'

/* ─── Grid Presets ─────────────────────────────────────────────── */

export const GRID_PRESETS: GridPreset[] = [
  // ─── Teletext (40×25 base, 24×24 cell = 960×600 at 1x) ──────
  { name: 'teletext',         cols: 40, rows: 25, aspect: '8:5',  description: 'Classic Ceefax/Teletext — 960×600 @1x, 1920×1200 @2x' },
  { name: 'teletext-wide',    cols: 80, rows: 25, aspect: '16:5', description: 'Wide teletext — 1920×600 @1x, 3840×1200 @2x' },
  { name: 'teletext-hd',      cols: 80, rows: 50, aspect: '8:5',  description: 'HD teletext — 1920×1200 @1x, 3840×2400 @2x' },

  // ─── Terminal (80×24 base, 24×24 cell = 1920×576 at 1x) ─────
  { name: 'terminal',         cols: 80, rows: 24, aspect: '10:3', description: 'Classic terminal — 1920×576 @1x, 3840×1152 @2x' },
  { name: 'terminal-wide',    cols: 120, rows: 24, aspect: '5:1', description: 'Wide terminal — 2880×576 @1x, 5760×1152 @2x' },
  { name: 'terminal-ultra',   cols: 160, rows: 24, aspect: '20:3',description: 'Ultra-wide terminal — 3840×576 @1x, 7680×1152 @2x' },

  // ─── Grid Worlds ──────────────────────────────────────────────
  { name: 'editor',           cols: 40, rows: 25, aspect: '8:5',  description: 'Grid editor — matches teletext standard' },
  { name: 'world-square',     cols: 80, rows: 80, aspect: '1:1',  description: 'Square world — 1920×1920 @1x, 3840×3840 @2x' },
  { name: 'world-classic',    cols: 80, rows: 60, aspect: '4:3',  description: 'Classic 4:3 world — 1920×1440 @1x, 3840×2880 @2x' },
  { name: 'world-widescreen', cols: 128, rows: 72, aspect: '16:9',description: 'Widescreen world — 3072×1728 @1x, 6144×3456 @2x' },
  { name: 'mini',             cols: 28, rows: 28, aspect: '1:1',  description: 'Square widget — 672×672 @1x' },
]

/**
 * Look up a grid preset by name.
 */
export function getGridPreset(name: string): GridPreset | undefined {
  return GRID_PRESETS.find(p => p.name === name)
}

/* ─── Column Spec Resolution ──────────────────────────────────── */

/**
 * Build a ColumnSpec object with pre-calculated maxWidth.
 */
function makeSpec(
  count: number,
  width: string,
  gap: string,
  breakpoint: number,
): ColumnSpec {
  const gaps = count > 1 ? ` + ${count - 1} * ${gap}` : ''
  const maxWidth = count <= 1
    ? width
    : `calc(${count} * ${width}${gaps})`
  return { count, width, gap, breakpoint, maxWidth }
}

/**
 * Resolve the optimal column spec for a given viewport width.
 *
 * Character count per column increases with viewport size:
 *   1×40ch → 2×35ch → 2×40ch → 3×35ch → 3×40ch → 4×40ch
 *
 * The maxWidth is pre-calculated for direct CSS use.
 */
export function resolveColumns(viewportWidth: number): ColumnSpec {
  if (viewportWidth >= 1920) {
    return makeSpec(4, '40ch', '24px', 1920)
  }
  if (viewportWidth >= 1440) {
    return makeSpec(3, '40ch', '24px', 1440)
  }
  if (viewportWidth >= 1024) {
    return makeSpec(3, '35ch', '24px', 1024)
  }
  if (viewportWidth >= 768) {
    return makeSpec(2, '40ch', '24px', 768)
  }
  if (viewportWidth >= 480) {
    return makeSpec(2, '35ch', '16px', 480)
  }
  return makeSpec(1, '40ch', '0', 0)
}

/**
 * Resolve the optimal prose column width for a given viewport width.
 * Useful for single-column prose layouts that need responsive max-width.
 */
export function resolveProseWidth(viewportWidth: number): string {
  if (viewportWidth >= 1024) return '40ch'
  if (viewportWidth >= 768) return '40ch'
  if (viewportWidth >= 480) return '35ch'
  return '40ch'
}

/**
 * Convert a ColumnSpec to a CSS max-width value for a single column.
 */
export function columnSpecToMaxWidth(spec: ColumnSpec): string {
  return spec.width
}

/**
 * Calculate the total content width for a column spec (columns + gaps).
 * Returns the pre-calculated maxWidth from the spec.
 */
export function columnSpecTotalWidth(spec: ColumnSpec): string {
  return spec.maxWidth
}

/* ─── Viewport Math ────────────────────────────────────────────── */

/**
 * Calculate pixel dimensions for a character grid viewport.
 *
 * @param cols - Number of character columns
 * @param rows - Number of character rows
 * @param cellSize - Pixel width of each cell (height = cellSize * 1.2)
 * @param font - Font family name
 */
export function calcViewport(
  cols: number,
  rows: number,
  cellSize: number,
  font: string,
): Viewport {
  return {
    cols,
    rows,
    cellWidth: cellSize,
    cellHeight: Math.round(cellSize * 1.2),
    font,
  }
}

/**
 * Calculate the total pixel dimensions of a viewport.
 */
export function viewportPixelSize(vp: Viewport): { width: number; height: number } {
  return {
    width: vp.cols * vp.cellWidth,
    height: vp.rows * vp.cellHeight,
  }
}

/* ─── Grid Buffer Transforms ───────────────────────────────────── */

/**
 * Scale a grid buffer to new dimensions using nearest-neighbour.
 *
 * Useful for adapting a grid buffer to a different viewport size
 * while preserving character content.
 */
export function scaleBuffer(
  buf: import('./types').GridBuffer,
  newCols: number,
  newRows: number,
): import('./types').GridBuffer {
  const oldRows = buf.length
  const oldCols = oldRows > 0 ? buf[0].length : 0
  const result: import('./types').GridBuffer = []

  for (let r = 0; r < newRows; r++) {
    const srcRow = Math.min(Math.floor((r / newRows) * oldRows), oldRows - 1)
    const row: import('./types').GridCell[] = []
    for (let c = 0; c < newCols; c++) {
      const srcCol = Math.min(Math.floor((c / newCols) * oldCols), oldCols - 1)
      row.push({ ...buf[srcRow][srcCol] })
    }
    result.push(row)
  }
  return result
}

/**
 * Crop a grid buffer to a sub-region.
 */
export function crop(
  buf: import('./types').GridBuffer,
  col: number,
  row: number,
  width: number,
  height: number,
): import('./types').GridBuffer {
  const result: import('./types').GridBuffer = []
  for (let r = row; r < row + height && r < buf.length; r++) {
    const srcRow = buf[r]
    if (!srcRow) break
    const newRow: import('./types').GridCell[] = []
    for (let c = col; c < col + width && c < srcRow.length; c++) {
      newRow.push({ ...srcRow[c] })
    }
    result.push(newRow)
  }
  return result
}

/**
 * Centre a grid buffer within a larger viewport, padding with empty cells.
 */
export function centre(
  buf: import('./types').GridBuffer,
  canvasCols: number,
  canvasRows: number,
): import('./types').GridBuffer {
  const rows = buf.length
  const cols = rows > 0 ? buf[0].length : 0
  const emptyCell = (): import('./types').GridCell => ({
    char: ' ', fg: 7, bg: 0,
  })

  const result: import('./types').GridBuffer = []
  const rowOffset = Math.floor((canvasRows - rows) / 2)
  const colOffset = Math.floor((canvasCols - cols) / 2)

  for (let r = 0; r < canvasRows; r++) {
    const row: import('./types').GridCell[] = []
    for (let c = 0; c < canvasCols; c++) {
      const srcR = r - rowOffset
      const srcC = c - colOffset
      if (srcR >= 0 && srcR < rows && srcC >= 0 && srcC < cols) {
        row.push({ ...buf[srcR][srcC] })
      } else {
        row.push(emptyCell())
      }
    }
    result.push(row)
  }
  return result
}
