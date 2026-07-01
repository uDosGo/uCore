/**
 * Grid Algebra — Public API
 *
 * Barrel file that exports all grid-core functionality.
 */

export type {
  GridCell,
  GridBuffer,
  Viewport,
  ColumnSpec,
  GridPreset,
  ColourEntry,
  RenderMode,
  GridMode,
} from './types'

export {
  GRID_PRESETS,
  getGridPreset,
  resolveColumns,
  resolveProseWidth,
  columnSpecToMaxWidth,
  columnSpecTotalWidth,
  calcViewport,
  viewportPixelSize,
  scaleBuffer,
  crop,
  centre,
} from './algebra'

export {
  createBuffer,
  writeString,
  fill,
  scroll,
  clear,
  cloneBuffer,
  bufferToString,
  stringToBuffer,
} from './buffer'

export {
  PALETTE_DARK,
  PALETTE_LIGHT,
  getColour,
  colourCSS,
} from './palette'
