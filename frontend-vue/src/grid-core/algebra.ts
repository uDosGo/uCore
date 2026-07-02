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
  // ─── Current Active Surfaces (40×25, 20px cell) ──────────────
  { name: 'terminal',  cols: 40, rows: 25, aspect: '8:5',  description: 'Terminal — 800×500 @20px, pressstart2p' },
  { name: 'teletext',  cols: 40, rows: 25, aspect: '8:5',  description: 'Teletext — 800×500 @20px, MODE7GX3 1.3:1 cells' },
  { name: 'editor',    cols: 40, rows: 25, aspect: '8:5',  description: 'Grid editor — 40×25 teletext standard' },

  // ─── Retro Terminal (80×24, 24px base cell) ──────────────────
  { name: 'terminal-retro',    cols: 80, rows: 24, aspect: '10:3', description: '1920×576 @1x · 3840×1152 @2x · retro sweet spot' },
  { name: 'terminal-wide',     cols: 120, rows: 24, aspect: '5:1', description: '2880×576 @1x · 5760×1152 @2x' },

  // ─── Teletext (40×25, 24px base cell) ────────────────────────
  { name: 'teletext-retro',    cols: 40, rows: 25, aspect: '8:5',  description: '960×600 @1x · 1920×1200 @2x · 2880×1800 @3x ideal' },
  { name: 'teletext-hd',       cols: 80, rows: 50, aspect: '8:5',  description: '1920×1200 @1x · 3840×2400 @2x' },

  // ─── Aspect Ratio Presets (24×24 base cell) ──────────────────
  { name: 'square-80',         cols: 80, rows: 80, aspect: '1:1',  description: '1920×1920 @1x · 3840×3840 @2x' },
  { name: 'square-60',         cols: 60, rows: 60, aspect: '1:1',  description: '1440×1440 @1x · 2880×2880 @2x' },
  { name: 'mini',              cols: 28, rows: 28, aspect: '1:1',  description: '672×672 @1x · widget / dashboard tile' },

  { name: 'classic-80x60',     cols: 80, rows: 60, aspect: '4:3',  description: '1920×1440 @1x · 3840×2880 @2x' },
  { name: 'classic-40x30',     cols: 40, rows: 30, aspect: '4:3',  description: '960×720 @1x · 1920×1440 @2x' },

  { name: 'widescreen-128x72', cols: 128, rows: 72, aspect: '16:9', description: '3072×1728 @1x · 6144×3456 @2x' },
  { name: 'widescreen-80x45',  cols: 80, rows: 45, aspect: '16:9', description: '1920×1080 @1x · 3840×2160 @2x (4K exact)' },

  { name: 'ultrawide-160x91',  cols: 160, rows: 91, aspect: '16:9.1', description: '3840×2184 @1x · 7680×4368 @2x' },
  { name: 'ultrawide-80x45',   cols: 80, rows: 45, aspect: '16:9', description: '1920×1080 @1x · ultrawide compatible' },
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
