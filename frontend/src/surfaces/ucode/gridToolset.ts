export interface GridToolView {
  id: string
  name: string
  subtitle: string
  summary: string
  apis: string[]
  upgrade: string[]
}

export const GRID_TOOL_VIEWS: GridToolView[] = [
  {
    id: 'grid-editor',
    name: 'Grid Editor',
    subtitle: 'Cell-level editing and history',
    summary: 'Unified editor primitives for drawing, fill, clear, and command-pattern undo/redo.',
    apis: [
      'placeCharacter(cell, char, x, y)',
      'setPixel(cell, x, y, color)',
      'drawLine(cell, x1, y1, x2, y2, color)',
      'fillArea(cell, x, y, color)',
      'clearCell(cell)',
      'undo()',
      'redo()',
    ],
    upgrade: [
      'Extract editor core from UI wrappers',
      'Add import/export for JSON and PNG',
      'Share one drawing API across surfaces',
    ],
  },
  {
    id: 'layer-composer',
    name: 'Layer Composer',
    subtitle: 'Stack, blend, and group layers',
    summary: 'Unlimited layer model with visibility, opacity, blend modes, groups, and lock states.',
    apis: [
      'createLayer(grid, zIndex, name)',
      'deleteLayer(grid, layerId)',
      'setLayerVisibility(grid, layerId, visible)',
      'setLayerOpacity(grid, layerId, opacity)',
      'reorderLayer(grid, layerId, newIndex)',
      'mergeLayers(grid, layerId1, layerId2)',
    ],
    upgrade: [
      'Lift composer behavior from panel-local state',
      'Add blending modes and layer groups',
      'Enable cross-grid copy/paste',
    ],
  },
  {
    id: 'svg-font-mapper',
    name: 'SVG Font Mapping',
    subtitle: 'Glyph import and bitmap mapping',
    summary: 'GridCore-managed SVG/OTF/TTF font ingestion, glyph indexing, and sprite export.',
    apis: [
      'parseSVG(svgString)',
      'svgToBitmap(svg, width, height)',
      'bitmapToGrid(bitmap)',
      'extractGlyphs(svgFont)',
      'mapGlyphToCell(glyph, cell)',
    ],
    upgrade: [
      'Add full font family library support',
      'Support variable cell sizes 16x16 through 128x128',
      'Export sprite sheets, BDF, and SVG',
    ],
  },
  {
    id: 'map-rendering',
    name: 'Grid Map Rendering',
    subtitle: 'Unified Canvas and DOM rendering',
    summary: 'Single renderer API for tile rendering, LOD control, and server-side export pipelines.',
    apis: [
      'renderMap(grid, viewport, rendererType)',
      'renderTile(grid, x, y, zoom)',
      'renderLayer(grid, layerId, rendererType)',
      'setLOD(lodLevel)',
      'exportToPNG(filename)',
    ],
    upgrade: [
      'Consolidate duplicate renderer loops',
      'Render visible tiles only',
      'Add map batch export pipeline',
    ],
  },
  {
    id: 'spatial-algebra',
    name: 'Grid Map Location Algebra',
    subtitle: 'uCode coordinate math and pathing',
    summary: 'Shared spatial algebra for uCode, lat/lon transforms, bounding boxes, and navigation.',
    apis: [
      'latLonToUCode(lat, lon, level)',
      'uCodeToLatLon(coord)',
      'getNeighbour(coord, direction)',
      'getBoundingBox(coord1, coord2)',
      'pathFind(from, to, grid)',
      'clusterRegion(coord, radius)',
    ],
    upgrade: [
      'Extend support to virtual bands L000-L899',
      'Add A* pathfinding',
      'Add region and bounds query helpers',
    ],
  },
]
