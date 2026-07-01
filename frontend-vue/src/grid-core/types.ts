/**
 * Grid Algebra — Core Types
 *
 * Defines the canonical data structures for the Grid Algebra system.
 * These types are shared between GridCore UI (character-grid widgets)
 * and Prose UI (text/content browsers).
 *
 * @see ColumnSpec.maxWidth — Pre-calculated CSS max-width with gaps,
 *      e.g. "calc(3 * 40ch + 2 * 24px)" for a 3-column layout.
 */

/** A single cell in a grid buffer */
export interface GridCell {
  char: string        // The character to display
  fg: number          // Foreground colour index (0-7)
  bg: number          // Background colour index (0-7)
  bold?: boolean      // Bold flag
  blink?: boolean     // Blink flag (teletext)
  mosaic?: boolean    // Mosaic block graphic flag
}

/** A 2D grid buffer (rows x cols) */
export type GridBuffer = GridCell[][]

/** Viewport dimensions for character-grid rendering */
export interface Viewport {
  cols: number        // Number of character columns
  rows: number        // Number of character rows
  cellWidth: number   // Pixel width of each cell
  cellHeight: number  // Pixel height of each cell
  font: string        // Font family name
}

/** Column specification for prose layouts (Grid Algebra v2.0) */
export interface ColumnSpec {
  count: number       // Number of columns (1, 2, 3, or 4)
  width: string       // Per-column CSS width value (e.g. "35ch", "40ch")
  gap: string         // CSS gap value (e.g. "24px", "16px", "0")
  breakpoint: number  // Minimum viewport width in px for this spec
  maxWidth: string    // Pre-calculated total width: "calc(N * W + (N-1) * G)"
}

/** Grid character presets */
export interface GridPreset {
  name: string
  cols: number
  rows: number
  aspect: string
  description: string
}

/** Colour palette entry */
export interface ColourEntry {
  index: number
  name: string
  hex: string
}

/** Markdown rendering mode */
export type RenderMode = 'prose' | 'columns' | 'slides' | 'web-pub' | 'grid'

/** GridCore UI interaction mode */
export type GridMode = 'view' | 'edit' | 'map'
