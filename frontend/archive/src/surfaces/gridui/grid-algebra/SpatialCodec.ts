/* ═══════════════════════════════════════════════════════════════════
   SpatialCodec — Lat/Lon ↔ uCode Coordinate Conversion
   ═══════════════════════════════════════════════════════════════════
   Converts real-world GPS coordinates to uCode grid coordinates
   and back. Uses Web Mercator projection (EPSG:3857) for consistent
   global mapping.

   Layer Bands:
     L300 — Global (~668 km/cell)
     L310 — Continental (~66.8 km/cell)
     L320 — Regional (~6.68 km/cell)
     L330 — City (~668 m/cell)
     L340 — Neighbourhood (~66.8 m/cell)
     L350 — Block (~6.68 m/cell)
     L360 — Building (~0.668 m/cell)

   Zoom accuracy target: 3m (between L350 and L360)
   ═══════════════════════════════════════════════════════════════════ */

const EARTH_CIRCUMFERENCE_M = 40075000

/**
 * Calculate cell size in metres for a given zoom level.
 * L300 = ~668km, each +10 levels divides by 10.
 */
export function cellSizeAtLevel(level: number): number {
  return EARTH_CIRCUMFERENCE_M / Math.pow(2, (level - 300) / 10)
}

/**
 * Convert latitude/longitude to a uCode coordinate string.
 * @param lat Latitude in decimal degrees (-90 to 90)
 * @param lon Longitude in decimal degrees (-180 to 180)
 * @param targetLevel Target zoom level (300-360, default 340)
 * @returns uCode string e.g. "L340-H42J-08F2-0"
 */
export function latLonToUCode(
  lat: number,
  lon: number,
  targetLevel: number = 340
): string {
  // Normalize to Web Mercator (EPSG:3857) range [0, 1]
  const x = (lon + 180) / 360
  const y =
    (1 -
      Math.log(
        Math.tan((lat * Math.PI) / 180) +
          1 / Math.cos((lat * Math.PI) / 180)
      ) /
        Math.PI) /
    2

  const level = targetLevel
  const cellSizeM = cellSizeAtLevel(level)
  const gridSizeM = cellSizeM * 24 // 24 cells per grid

  const totalGrids = EARTH_CIRCUMFERENCE_M / gridSizeM

  const gridX = Math.floor(x * totalGrids)
  const gridY = Math.floor(y * totalGrids)
  const cellX = Math.floor((x * totalGrids * 24) % 24)
  const cellY = Math.floor((y * totalGrids * 24) % 24)

  // Encode to base-36 (0-9, A-Z), 2 chars each
  const encodeBase36 = (num: number): string => {
    return num.toString(36).padStart(2, '0').toUpperCase()
  }

  return `L${level}-${encodeBase36(gridX)}${encodeBase36(gridY)}-${encodeBase36(cellX)}${encodeBase36(cellY)}-0`
}

/**
 * Parse a uCode string into its components.
 */
export function parseUCode(
  uCode: string
): {
  level: number
  gridX: number
  gridY: number
  cellX: number
  cellY: number
  layer: number
} | null {
  const match = uCode.match(
    /L(\d+)-([A-Z0-9]{2})([A-Z0-9]{2})-([A-Z0-9]{2})([A-Z0-9]{2})-(\d)/
  )
  if (!match) return null

  const [, levelStr, gx, gy, cx, cy, layerStr] = match
  return {
    level: parseInt(levelStr),
    gridX: parseInt(gx, 36),
    gridY: parseInt(gy, 36),
    cellX: parseInt(cx, 36),
    cellY: parseInt(cy, 36),
    layer: parseInt(layerStr),
  }
}

/**
 * Convert a uCode coordinate back to latitude/longitude.
 * Returns the centre of the cell.
 */
export function uCodeToLatLon(
  uCode: string
): { lat: number; lon: number } | null {
  const parsed = parseUCode(uCode)
  if (!parsed) return null

  const { level, gridX, gridY, cellX, cellY } = parsed
  const cellSizeM = cellSizeAtLevel(level)
  const gridSizeM = cellSizeM * 24
  const totalGrids = EARTH_CIRCUMFERENCE_M / gridSizeM

  // Centre of the cell (add 0.5 to get midpoint)
  const x = (gridX * 24 + cellX + 0.5) / (totalGrids * 24)
  const y = (gridY * 24 + cellY + 0.5) / (totalGrids * 24)

  // Inverse Web Mercator
  const lon = x * 360 - 180
  const lat =
    Math.atan(Math.sinh(Math.PI * (1 - 2 * y))) * (180 / Math.PI)

  return { lat, lon }
}

/**
 * Get the uCode of a neighbouring cell.
 * @param uCode Source uCode
 * @param dx Change in X (-1, 0, 1)
 * @param dy Change in Y (-1, 0, 1)
 * @returns Neighbour uCode or null if invalid
 */
export function getNeighbour(
  uCode: string,
  dx: number,
  dy: number
): string | null {
  const parsed = parseUCode(uCode)
  if (!parsed) return null

  let { level, gridX, gridY, cellX, cellY, layer } = parsed

  cellX += dx
  cellY += dy

  // Wrap around grid boundaries
  while (cellX < 0) {
    cellX += 24
    gridX--
  }
  while (cellX >= 24) {
    cellX -= 24
    gridX++
  }
  while (cellY < 0) {
    cellY += 24
    gridY--
  }
  while (cellY >= 24) {
    cellY -= 24
    gridY++
  }

  const encodeBase36 = (num: number): string => {
    return num.toString(36).padStart(2, '0').toUpperCase()
  }

  return `L${level}-${encodeBase36(gridX)}${encodeBase36(gridY)}-${encodeBase36(cellX)}${encodeBase36(cellY)}-${layer}`
}

/**
 * Get the parent uCode at a higher (less detailed) zoom level.
 * e.g. L340 → L330 (parent covers 24×24 cells)
 */
export function getParentUCode(
  uCode: string,
  targetLevel: number
): string | null {
  const parsed = parseUCode(uCode)
  if (!parsed) return null
  if (targetLevel >= parsed.level) return uCode // can't zoom in via parent

  const levelDiff = parsed.level - targetLevel
  const factor = Math.pow(24, levelDiff)

  const parentGridX = Math.floor(parsed.gridX / factor)
  const parentGridY = Math.floor(parsed.gridY / factor)
  const parentCellX = Math.floor(
    (parsed.gridX % factor) * 24 + parsed.cellX / factor
  )
  const parentCellY = Math.floor(
    (parsed.gridY % factor) * 24 + parsed.cellY / factor
  )

  const encodeBase36 = (num: number): string => {
    return num.toString(36).padStart(2, '0').toUpperCase()
  }

  return `L${targetLevel}-${encodeBase36(parentGridX)}${encodeBase36(parentGridY)}-${encodeBase36(parentCellX)}${encodeBase36(parentCellY)}-${parsed.layer}`
}

/**
 * Get the child uCodes at a more detailed zoom level.
 * Each parent cell contains 24×24 child cells.
 */
export function getChildUCodes(
  uCode: string,
  targetLevel: number
): string[] {
  const parsed = parseUCode(uCode)
  if (!parsed) return []
  if (targetLevel <= parsed.level) return [uCode] // can't zoom out via child

  const levelDiff = targetLevel - parsed.level
  const factor = Math.pow(24, levelDiff)
  const children: string[] = []

  const encodeBase36 = (num: number): string => {
    return num.toString(36).padStart(2, '0').toUpperCase()
  }

  for (let dy = 0; dy < factor; dy++) {
    for (let dx = 0; dx < factor; dx++) {
      const childGridX = parsed.gridX * factor + dx
      const childGridY = parsed.gridY * factor + dy
      children.push(
        `L${targetLevel}-${encodeBase36(childGridX)}${encodeBase36(childGridY)}-${encodeBase36(0)}${encodeBase36(0)}-${parsed.layer}`
      )
    }
  }

  return children
}

/**
 * Calculate the distance in metres between two uCode coordinates.
 */
export function distanceBetween(
  uCode1: string,
  uCode2: string
): number | null {
  const pos1 = uCodeToLatLon(uCode1)
  const pos2 = uCodeToLatLon(uCode2)
  if (!pos1 || !pos2) return null

  // Haversine formula
  const R = 6371000 // Earth radius in metres
  const dLat = ((pos2.lat - pos1.lat) * Math.PI) / 180
  const dLon = ((pos2.lon - pos1.lon) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((pos1.lat * Math.PI) / 180) *
      Math.cos((pos2.lat * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

/**
 * Format a uCode for display.
 */
export function formatUCode(uCode: string): string {
  const parsed = parseUCode(uCode)
  if (!parsed) return uCode
  return `L${parsed.level} ${parsed.gridX.toString(36).toUpperCase().padStart(2, '0')}:${parsed.gridY.toString(36).toUpperCase().padStart(2, '0')} ${parsed.cellX.toString(36).toUpperCase().padStart(2, '0')}:${parsed.cellY.toString(36).toUpperCase().padStart(2, '0')} L${parsed.layer}`
}

/**
 * Get a human-readable description of a zoom level.
 */
export function getZoomLevelDescription(level: number): string {
  const descriptions: Record<number, string> = {
    300: 'Global',
    310: 'Continental',
    320: 'Regional',
    330: 'City',
    340: 'Neighbourhood',
    350: 'Block',
    360: 'Building',
  }
  return descriptions[level] || `Level ${level}`
}

/**
 * Get the cell size in human-readable format for a zoom level.
 */
export function getCellSizeDescription(level: number): string {
  const size = cellSizeAtLevel(level)
  if (size >= 1000) {
    return `${(size / 1000).toFixed(1)} km`
  }
  return `${size.toFixed(1)} m`
}
