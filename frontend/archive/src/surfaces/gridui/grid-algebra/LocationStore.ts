/* ═══════════════════════════════════════════════════════════════════
   LocationStore — User location state management
   ═══════════════════════════════════════════════════════════════════
   Tracks current uCode location, zoom level, and layer.
   Provides navigation commands for the terminal and teletext.
   ═══════════════════════════════════════════════════════════════════ */

import {
  latLonToUCode,
  uCodeToLatLon,
  parseUCode,
  getNeighbour,
  getParentUCode,
  getChildUCodes,
  formatUCode,
  getZoomLevelDescription,
  getCellSizeDescription,
} from './SpatialCodec'
import { cityRegistry } from './CityRegistry'
import type { CityMarker } from './CityRegistry'

// ─── Types ────────────────────────────────────────────────────────────

export interface LocationState {
  /** Current uCode coordinate */
  uCode: string
  /** Current zoom level (300-360) */
  level: number
  /** Current layer (0-5) */
  layer: number
  /** Human-readable location name (city name or "Unknown") */
  locationName: string
  /** Latitude of current position */
  lat: number
  /** Longitude of current position */
  lon: number
  /** History of visited locations */
  history: string[]
  /** Bookmarked locations */
  bookmarks: string[]
}

// ─── Default location: Brisbane, Australia ────────────────────────────

const DEFAULT_LAT = -27.4698
const DEFAULT_LON = 153.0251
const DEFAULT_LEVEL = 340

// ─── Storage key for persistence ──────────────────────────────────────

const STORAGE_KEY = 'gridui-location'

// ─── LocationStore Class ──────────────────────────────────────────────

class LocationStore {
  private state: LocationState
  private listeners: Set<() => void> = new Set()

  constructor() {
    // Try to restore from localStorage
    const saved = this.load()
    if (saved) {
      this.state = saved
    } else {
      const uCode = latLonToUCode(DEFAULT_LAT, DEFAULT_LON, DEFAULT_LEVEL)
      this.state = {
        uCode,
        level: DEFAULT_LEVEL,
        layer: 0,
        locationName: 'Brisbane',
        lat: DEFAULT_LAT,
        lon: DEFAULT_LON,
        history: [uCode],
        bookmarks: [],
      }
    }
  }

  // ─── Persistence ──────────────────────────────────────────────────

  private load(): LocationState | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) return JSON.parse(raw)
    } catch {}
    return null
  }

  private save(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state))
    } catch {}
  }

  // ─── Subscriptions ────────────────────────────────────────────────

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notify(): void {
    this.save()
    for (const listener of this.listeners) {
      listener()
    }
  }

  // ─── Getters ──────────────────────────────────────────────────────

  getState(): LocationState {
    return { ...this.state }
  }

  getUCode(): string {
    return this.state.uCode
  }

  getLevel(): number {
    return this.state.level
  }

  getLayer(): number {
    return this.state.layer
  }

  getLocationName(): string {
    return this.state.locationName
  }

  getLatLon(): { lat: number; lon: number } {
    return { lat: this.state.lat, lon: this.state.lon }
  }

  getHistory(): string[] {
    return [...this.state.history]
  }

  getBookmarks(): string[] {
    return [...this.state.bookmarks]
  }

  // ─── Navigation ───────────────────────────────────────────────────

  /**
   * Move to a specific uCode coordinate.
   */
  goToUCode(uCode: string): string {
    const parsed = parseUCode(uCode)
    if (!parsed) return `?INVALID UCODE: ${uCode}`

    const latLon = uCodeToLatLon(uCode)
    const nearest = cityRegistry.findNearest(uCode)

    this.state = {
      ...this.state,
      uCode,
      level: parsed.level,
      layer: parsed.layer,
      locationName: nearest?.name || 'Unknown Location',
      lat: latLon?.lat ?? 0,
      lon: latLon?.lon ?? 0,
      history: [...this.state.history.slice(-99), uCode],
    }
    this.notify()
    return `OK: ${nearest?.name || 'Unknown'} — ${formatUCode(uCode)}`
  }

  /**
   * Move to a city by name.
   */
  goToCity(name: string): string {
    const city = cityRegistry.findByName(name)
    if (!city) {
      // Try partial match
      const all = cityRegistry.getAll()
      const matches = all.filter(c =>
        c.name.toLowerCase().includes(name.toLowerCase())
      )
      if (matches.length === 0) {
        return `?CITY NOT FOUND: ${name}`
      }
      if (matches.length === 1) {
        return this.goToUCode(matches[0].uCode)
      }
      return `?MULTIPLE MATCHES: ${matches.map(m => m.name).join(', ')}`
    }
    return this.goToUCode(city.uCode)
  }

  /**
   * Move to GPS coordinates.
   */
  goToGPS(lat: number, lon: number): string {
    const uCode = latLonToUCode(lat, lon, this.state.level)
    return this.goToUCode(uCode)
  }

  /**
   * Zoom in (increase level, more detail).
   */
  zoomIn(): string {
    const nextLevel = Math.min(360, this.state.level + 10)
    if (nextLevel === this.state.level) {
      return '?ALREADY AT MAXIMUM ZOOM (L360)'
    }
    const children = getChildUCodes(this.state.uCode, nextLevel)
    if (children.length === 0) return '?CANNOT ZOOM IN FURTHER'
    // Move to the first child cell (top-left)
    return this.goToUCode(children[0])
  }

  /**
   * Zoom out (decrease level, less detail).
   */
  zoomOut(): string {
    const nextLevel = Math.max(300, this.state.level - 10)
    if (nextLevel === this.state.level) {
      return '?ALREADY AT MINIMUM ZOOM (L300)'
    }
    const parent = getParentUCode(this.state.uCode, nextLevel)
    if (!parent) return '?CANNOT ZOOM OUT FURTHER'
    return this.goToUCode(parent)
  }

  /**
   * Move to a specific zoom level.
   */
  setLevel(level: number): string {
    const clamped = Math.max(300, Math.min(360, level))
    // Round to nearest 10
    const rounded = Math.round(clamped / 10) * 10
    if (rounded > this.state.level) {
      return this.zoomIn()
    } else if (rounded < this.state.level) {
      return this.zoomOut()
    }
    return `OK: Already at L${rounded}`
  }

  /**
   * Move in a direction (N, S, E, W, NE, NW, SE, SW).
   */
  move(direction: string): string {
    const dir = direction.toUpperCase()
    const dirMap: Record<string, [number, number]> = {
      N: [0, -1],
      S: [0, 1],
      E: [1, 0],
      W: [-1, 0],
      NE: [1, -1],
      NW: [-1, -1],
      SE: [1, 1],
      SW: [-1, 1],
    }
    const delta = dirMap[dir]
    if (!delta) return `?INVALID DIRECTION: ${dir} (use N, S, E, W, NE, NW, SE, SW)`
    const neighbour = getNeighbour(this.state.uCode, delta[0], delta[1])
    if (!neighbour) return '?CANNOT MOVE IN THAT DIRECTION'
    return this.goToUCode(neighbour)
  }

  /**
   * Switch to a different layer (0-5).
   */
  setLayer(layer: number): string {
    if (layer < 0 || layer > 5) return '?LAYER MUST BE 0-5'
    const parsed = parseUCode(this.state.uCode)
    if (!parsed) return '?INVALID CURRENT LOCATION'
    const newUCode = `L${parsed.level}-${parsed.gridX.toString(36).padStart(2, '0').toUpperCase()}${parsed.gridY.toString(36).padStart(2, '0').toUpperCase()}-${parsed.cellX.toString(36).padStart(2, '0').toUpperCase()}${parsed.cellY.toString(36).padStart(2, '0').toUpperCase()}-${layer}`
    this.state = { ...this.state, uCode: newUCode, layer }
    this.notify()
    return `OK: Switched to layer ${layer}`
  }

  /**
   * Add current location to bookmarks.
   */
  bookmarkCurrent(): string {
    if (this.state.bookmarks.includes(this.state.uCode)) {
      return '?ALREADY BOOKMARKED'
    }
    this.state = {
      ...this.state,
      bookmarks: [...this.state.bookmarks, this.state.uCode],
    }
    this.notify()
    return `OK: Bookmarked ${this.state.locationName}`
  }

  /**
   * Remove a bookmark.
   */
  removeBookmark(uCode: string): string {
    if (!this.state.bookmarks.includes(uCode)) {
      return '?NOT IN BOOKMARKS'
    }
    this.state = {
      ...this.state,
      bookmarks: this.state.bookmarks.filter(b => b !== uCode),
    }
    this.notify()
    return 'OK: Bookmark removed'
  }

  /**
   * Get a formatted status string for display.
   */
  getStatusString(): string {
    const { uCode, level, layer, locationName, lat, lon } = this.state
    const levelDesc = getZoomLevelDescription(level)
    const cellSize = getCellSizeDescription(level)
    return [
      `Location: ${locationName}`,
      `uCode: ${uCode}`,
      `GPS: ${lat.toFixed(4)}, ${lon.toFixed(4)}`,
      `Zoom: L${level} (${levelDesc}, ${cellSize}/cell)`,
      `Layer: ${layer}`,
    ].join('\n')
  }

  /**
   * Get a short status line for the teletext info bar.
   */
  getShortStatus(): string {
    const { locationName, level } = this.state
    return `${locationName} | L${level}`
  }
}

// ─── Singleton export ─────────────────────────────────────────────────
export const locationStore = new LocationStore()
export default locationStore
