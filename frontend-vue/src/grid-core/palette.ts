/**
 * Grid Algebra — Colour Palette
 *
 * 8-colour palette for teletext/grid rendering.
 * Supports both dark and light theme variants.
 */

import type { ColourEntry } from './types'

/** Dark theme palette (default) */
export const PALETTE_DARK: ColourEntry[] = [
  { index: 0, name: 'Black',   hex: '#000000' },
  { index: 1, name: 'Red',     hex: '#e6193c' },
  { index: 2, name: 'Green',   hex: '#3fb950' },
  { index: 3, name: 'Yellow',  hex: '#f2cc60' },
  { index: 4, name: 'Blue',    hex: '#58a6ff' },
  { index: 5, name: 'Magenta', hex: '#bc8cff' },
  { index: 6, name: 'Cyan',    hex: '#39c5cf' },
  { index: 7, name: 'White',   hex: '#c9d1d9' },
]

/** Light theme palette */
export const PALETTE_LIGHT: ColourEntry[] = [
  { index: 0, name: 'Black',   hex: '#000000' },
  { index: 1, name: 'Red',     hex: '#cc0000' },
  { index: 2, name: 'Green',   hex: '#00aa00' },
  { index: 3, name: 'Yellow',  hex: '#cccc00' },
  { index: 4, name: 'Blue',    hex: '#0000cc' },
  { index: 5, name: 'Magenta', hex: '#cc00cc' },
  { index: 6, name: 'Cyan',    hex: '#00cccc' },
  { index: 7, name: 'White',   hex: '#ffffff' },
]

/**
 * Get the hex colour for a given index from the active palette.
 * Falls back to white (index 7) if out of range.
 */
export function getColour(index: number, palette: ColourEntry[] = PALETTE_DARK): string {
  const entry = palette.find(c => c.index === index)
  return entry?.hex ?? palette[7].hex
}

/**
 * Convert a colour index to a CSS colour string.
 */
export function colourCSS(index: number, palette: ColourEntry[] = PALETTE_DARK): string {
  return getColour(index, palette)
}
