/**
 * @module grid-algebra
 * @description Pure TypeScript grid algebra engine — framework-agnostic.
 *
 * Provides GridBuffer data structure, transformations, colour palette,
 * font resolution, and teletext character mapping.
 *
 * No framework dependencies. Safe for Web Components, Vue, React, or plain JS.
 */
export {
  type GridCell,
  type GridBuffer,
  TERMINAL_COLS,
  TERMINAL_ROWS,
  createCell,
  createBuffer,
  cloneBuffer,
  getDimensions,
  sameDimensions,
} from './GridCell'

export {
  resize,
  overlay,
  scroll,
  crop,
  merge,
  fill,
  writeString,
} from './GridTransform'

export {
  type PaletteId,
  type Palette,
  UNIFIED_PALETTE,
  PALETTES,
  PALETTE_LIST,
  getColor,
  hexToRgb,
} from './ColourPalette'

export {
  type GridFont,
  type FontConfig,
  DEFAULT_FONTS,
  getFont,
  getFontFamily,
  getFontSizeScale,
} from './FontResolver'

export {
  TELETEXT_G0,
  resolveTeletextChar,
} from './CharacterSet'
