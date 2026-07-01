/* ═══════════════════════════════════════════════════════════════════
   GridCell — Universal cell type for grid-algebra
   ═══════════════════════════════════════════════════════════════════
   A GridCell represents a single character cell in any grid buffer.
   It carries foreground/background colour indices, and formatting flags.

   Colour indices are palette-relative (0-7 for teletext, 0-15 for ANSI).
   The ColourPalette module maps these to actual hex colours.

   GridBuffer is a 2D array: rows × cols (y × x).
   ═══════════════════════════════════════════════════════════════════ */

// ─── Cell Types ──────────────────────────────────────────────────────

export interface GridCell {
  char: string           // The character (single glyph, typically 1 char)
  fg: number             // Foreground colour index (0-7 teletext, 0-15 ANSI)
  bg: number             // Background colour index
  bold: boolean          // Bold/high-intensity flag
  flash: boolean         // Teletext flash/blink flag
  doubleHeight: boolean  // Teletext double-height row flag
  doubleWidth: boolean   // Teletext double-width char flag
}

export type GridBuffer = GridCell[][]  // rows × cols (y × x)

// ─── Constants ───────────────────────────────────────────────────────

export const TERMINAL_COLS = 80
export const TERMINAL_ROWS = 24

// ─── Factory ─────────────────────────────────────────────────────────

export function createCell(
  char = ' ',
  fg = 7,
  bg = 0,
  bold = false,
  flash = false,
  doubleHeight = false,
  doubleWidth = false,
): GridCell {
  return { char, fg, bg, bold, flash, doubleHeight, doubleWidth }
}

/** Create an empty GridBuffer filled with space cells */
export function createBuffer(cols: number, rows: number): GridBuffer {
  const buf: GridBuffer = []
  for (let y = 0; y < rows; y++) {
    const row: GridCell[] = []
    for (let x = 0; x < cols; x++) {
      row.push(createCell())
    }
    buf.push(row)
  }
  return buf
}

/** Clone a GridBuffer (deep copy) */
export function cloneBuffer(buf: GridBuffer): GridBuffer {
  return buf.map(row => row.map(cell => ({ ...cell })))
}

/** Get dimensions of a GridBuffer */
export function getDimensions(buf: GridBuffer): { cols: number; rows: number } {
  const rows = buf.length
  const cols = rows > 0 ? buf[0].length : 0
  return { cols, rows }
}

/** Check if two buffers have the same dimensions */
export function sameDimensions(a: GridBuffer, b: GridBuffer): boolean {
  const da = getDimensions(a)
  const db = getDimensions(b)
  return da.cols === db.cols && da.rows === db.rows
}
