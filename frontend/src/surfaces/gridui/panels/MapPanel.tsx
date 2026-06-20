/* ═══════════════════════════════════════════════════════════════════
   MapPanel — Spatial navigation, cities, bookmarks, layer stack
   ═══════════════════════════════════════════════════════════════════
   Unified map tab for the GridUI surface. Provides:
     - Current location display (uCode, GPS, city name)
     - Region/city browser with search
     - Bookmarks management
     - Location history
     - Zoom level controls
     - Layer stack selector
     - Quick navigation commands (GOTO, GPS, UCODE)
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo, useCallback } from 'react'
import { Icon } from '../../../components/Icon'
import { useStore } from '../GridUIStore'
import { locationStore } from '../grid-algebra/LocationStore'
import { cityRegistry } from '../grid-algebra/CityRegistry'
import type { CityMarker } from '../grid-algebra/CityRegistry'

// ─── Region display names ────────────────────────────────────────────
const REGION_LABELS: Record<string, string> = {
  oceania: 'Oceania',
  southeast_asia: 'Southeast Asia',
  east_asia: 'East Asia',
  south_asia: 'South Asia',
  europe: 'Europe',
  north_america: 'North America',
  south_america: 'South America',
  africa: 'Africa',
  middle_east: 'Middle East',
}

// ─── MapPanel Component ──────────────────────────────────────────────
export function MapPanel() {
  const store = useStore()
  const [activeSection, setActiveSection] = useState<'location' | 'browse' | 'bookmarks' | 'history'>('location')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null)
  const [gotoInput, setGotoInput] = useState('')
  const [gotoMode, setGotoMode] = useState<'city' | 'gps' | 'ucode'>('city')
  const [gotoResult, setGotoResult] = useState<string | null>(null)

  // ─── Force re-render on location changes ─────────────────────────
  const [tick, setTick] = useState(0)
  const refreshLocation = useCallback(() => setTick(t => t + 1), [])

  // ─── Current location state ──────────────────────────────────────
  const loc = locationStore.getState()

  // ─── Filtered cities ─────────────────────────────────────────────
  const filteredCities = useMemo(() => {
    let cities = selectedRegion
      ? cityRegistry.getByRegion(selectedRegion)
      : cityRegistry.getAll()

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      cities = cities.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.region.toLowerCase().includes(q) ||
        c.uCode.toLowerCase().includes(q)
      )
    }
    return cities
  }, [selectedRegion, searchQuery])

  // ─── Regions with counts ─────────────────────────────────────────
  const regions = useMemo(() => {
    return cityRegistry.getRegions().map(r => ({
      id: r,
      label: REGION_LABELS[r] || r,
      count: cityRegistry.getByRegion(r).length,
    }))
  }, [])

  // ─── Bookmarks ───────────────────────────────────────────────────
  const bookmarks = locationStore.getBookmarks()
  const bookmarkCities = useMemo(() => {
    return bookmarks.map(b => {
      const city = cityRegistry.findByUCode(b)
      return { uCode: b, city }
    })
  }, [bookmarks, tick])

  // ─── History ─────────────────────────────────────────────────────
  const history = locationStore.getHistory()

  // ─── Handle GOTO ─────────────────────────────────────────────────
  const handleGoto = useCallback(() => {
    const input = gotoInput.trim()
    if (!input) return

    let result: string
    if (gotoMode === 'city') {
      result = locationStore.goToCity(input)
    } else if (gotoMode === 'gps') {
      const parts = input.split(/\s+/)
      if (parts.length < 2) {
        result = '?USAGE: <latitude> <longitude>'
      } else {
        const lat = parseFloat(parts[0])
        const lon = parseFloat(parts[1])
        result = isNaN(lat) || isNaN(lon)
          ? '?INVALID COORDINATES'
          : locationStore.goToGPS(lat, lon)
      }
    } else {
      result = locationStore.goToUCode(input)
    }

    setGotoResult(result)
    refreshLocation()
    setTimeout(() => setGotoResult(null), 4000)
  }, [gotoInput, gotoMode, refreshLocation])

  // ─── Handle city click ───────────────────────────────────────────
  const handleCityClick = useCallback((city: CityMarker) => {
    const result = locationStore.goToCity(city.name)
    setGotoResult(result)
    refreshLocation()
    setTimeout(() => setGotoResult(null), 4000)
  }, [refreshLocation])

  // ─── Handle bookmark click ───────────────────────────────────────
  const handleBookmarkClick = useCallback((uCode: string) => {
    const result = locationStore.goToUCode(uCode)
    setGotoResult(result)
    refreshLocation()
    setTimeout(() => setGotoResult(null), 4000)
  }, [refreshLocation])

  // ─── Handle history click ────────────────────────────────────────
  const handleHistoryClick = useCallback((uCode: string) => {
    const result = locationStore.goToUCode(uCode)
    setGotoResult(result)
    refreshLocation()
    setTimeout(() => setGotoResult(null), 4000)
  }, [refreshLocation])

  // ─── Zoom controls ───────────────────────────────────────────────
  const handleZoomIn = useCallback(() => {
    const result = locationStore.zoomIn()
    setGotoResult(result)
    refreshLocation()
    setTimeout(() => setGotoResult(null), 2000)
  }, [refreshLocation])

  const handleZoomOut = useCallback(() => {
    const result = locationStore.zoomOut()
    setGotoResult(result)
    refreshLocation()
    setTimeout(() => setGotoResult(null), 2000)
  }, [refreshLocation])

  // ─── Bookmark current ────────────────────────────────────────────
  const handleBookmarkCurrent = useCallback(() => {
    const result = locationStore.bookmarkCurrent()
    setGotoResult(result)
    refreshLocation()
    setTimeout(() => setGotoResult(null), 2000)
  }, [refreshLocation])

  // ─── Layer stack ─────────────────────────────────────────────────
  const handleLayerChange = useCallback((layer: number) => {
    const result = locationStore.setLayer(layer)
    setGotoResult(result)
    refreshLocation()
    setTimeout(() => setGotoResult(null), 2000)
  }, [refreshLocation])

  return (
    <div className="gridui-panel">
      <div className="gridui-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 16 }}>

        {/* ─── Section Tabs ──────────────────────────────────────── */}
        <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid var(--grid-border, #30363d)', paddingBottom: 8 }}>
          {([
            { id: 'location' as const, label: 'Location', icon: 'my_location' },
            { id: 'browse' as const, label: 'Browse', icon: 'map' },
            { id: 'bookmarks' as const, label: 'Bookmarks', icon: 'bookmark' },
            { id: 'history' as const, label: 'History', icon: 'history' },
          ]).map(s => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className={`gridui-editor-tab ${activeSection === s.id ? 'gridui-editor-tab--active' : ''}`}
              style={{ fontSize: '0.8rem', padding: '4px 12px' }}
            >
              <Icon name={s.icon} size={14} style={{ marginRight: 4 }} />
              {s.label}
            </button>
          ))}
        </div>

        {/* ─── Goto Result Toast ─────────────────────────────────── */}
        {gotoResult && (
          <div style={{
            padding: '8px 12px',
            borderRadius: 6,
            background: gotoResult.startsWith('?') ? '#E76F5120' : '#23863620',
            border: `1px solid ${gotoResult.startsWith('?') ? '#E76F5140' : '#3fb95040'}`,
            color: gotoResult.startsWith('?') ? '#E76F51' : '#3fb950',
            fontSize: '0.8rem',
          }}>
            {gotoResult}
          </div>
        )}

        {/* ─── Quick Navigation ──────────────────────────────────── */}
        <div className="gridui-card" style={{ marginBottom: 0 }}>
          <div className="gridui-card-header">
            <Icon name="explore" size={16} />
            <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
              Quick Navigation
            </h3>
          </div>
          <div className="gridui-card-body">
            <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
              {([
                { id: 'city' as const, label: 'City' },
                { id: 'gps' as const, label: 'GPS' },
                { id: 'ucode' as const, label: 'uCode' },
              ]).map(m => (
                <button
                  key={m.id}
                  onClick={() => setGotoMode(m.id)}
                  className={`gridui-display-mode-btn ${gotoMode === m.id ? 'gridui-display-mode-btn--active' : 'gridui-display-mode-btn--inactive'}`}
                  style={{ fontSize: '0.7rem', padding: '2px 10px' }}
                >
                  {m.label}
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="text"
                value={gotoInput}
                onChange={e => setGotoInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleGoto() }}
                placeholder={
                  gotoMode === 'city' ? 'City name (e.g. Tokyo)' :
                  gotoMode === 'gps' ? 'Latitude Longitude' :
                  'uCode (e.g. L340-H42J-0K0K-0)'
                }
                className="gridui-settings-number-input"
                style={{ flex: 1 }}
              />
              <button
                onClick={handleGoto}
                className="gridui-display-mode-btn gridui-display-mode-btn--active"
                style={{ fontSize: '0.8rem', padding: '4px 16px' }}
              >
                Go
              </button>
            </div>
          </div>
        </div>

        {/* ─── Section Content ───────────────────────────────────── */}
        {activeSection === 'location' && (
          <div className="gridui-card">
            <div className="gridui-card-header">
              <Icon name="my_location" size={16} />
              <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                Current Location
              </h3>
              <button
                onClick={refreshLocation}
                className="gridui-display-mode-btn gridui-display-mode-btn--inactive"
                style={{ fontSize: '0.7rem', padding: '2px 8px' }}
              >
                <Icon name="refresh" size={12} style={{ marginRight: 2 }} />
                Refresh
              </button>
            </div>
            <div className="gridui-card-body">
              {/* Location info grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
                <div style={{ padding: '8px 10px', background: 'var(--grid-bg-secondary, #161b22)', borderRadius: 6, border: '1px solid var(--grid-border, #30363d)' }}>
                  <div style={{ fontSize: '0.65rem', color: 'var(--grid-text-secondary, #8b949e)', marginBottom: 2 }}>Location</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-primary, #e6edf3)' }}>{loc.locationName}</div>
                </div>
                <div style={{ padding: '8px 10px', background: 'var(--grid-bg-secondary, #161b22)', borderRadius: 6, border: '1px solid var(--grid-border, #30363d)' }}>
                  <div style={{ fontSize: '0.65rem', color: 'var(--grid-text-secondary, #8b949e)', marginBottom: 2 }}>uCode</div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 500, color: '#58a6ff', fontFamily: "'SF Mono','Fira Code',monospace" }}>{loc.uCode}</div>
                </div>
                <div style={{ padding: '8px 10px', background: 'var(--grid-bg-secondary, #161b22)', borderRadius: 6, border: '1px solid var(--grid-border, #30363d)' }}>
                  <div style={{ fontSize: '0.65rem', color: 'var(--grid-text-secondary, #8b949e)', marginBottom: 2 }}>GPS</div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--grid-text-primary, #e6edf3)' }}>{loc.lat.toFixed(4)}, {loc.lon.toFixed(4)}</div>
                </div>
                <div style={{ padding: '8px 10px', background: 'var(--grid-bg-secondary, #161b22)', borderRadius: 6, border: '1px solid var(--grid-border, #30363d)' }}>
                  <div style={{ fontSize: '0.65rem', color: 'var(--grid-text-secondary, #8b949e)', marginBottom: 2 }}>Zoom Level</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-primary, #e6edf3)' }}>L{loc.level}</div>
                </div>
              </div>

              {/* Zoom controls */}
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--grid-text-secondary, #8b949e)' }}>Zoom:</span>
                <button onClick={handleZoomOut} className="gridui-display-mode-btn gridui-display-mode-btn--inactive" style={{ fontSize: '0.8rem', padding: '2px 10px' }}>−</button>
                <span style={{ fontSize: '0.9rem', fontWeight: 600, minWidth: 40, textAlign: 'center' }}>L{loc.level}</span>
                <button onClick={handleZoomIn} className="gridui-display-mode-btn gridui-display-mode-btn--inactive" style={{ fontSize: '0.8rem', padding: '2px 10px' }}>+</button>
                <div style={{ flex: 1 }} />
                <button onClick={handleBookmarkCurrent} className="gridui-display-mode-btn gridui-display-mode-btn--inactive" style={{ fontSize: '0.7rem', padding: '2px 10px' }}>
                  <Icon name="bookmark" size={12} style={{ marginRight: 2 }} />
                  Bookmark
                </button>
              </div>

              {/* Layer stack */}
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--grid-text-secondary, #8b949e)', marginBottom: 6 }}>Layer Stack</div>
                <div style={{ display: 'flex', gap: 4 }}>
                  {[0, 1, 2, 3, 4, 5].map(l => (
                    <button
                      key={l}
                      onClick={() => handleLayerChange(l)}
                      className={`gridui-display-mode-btn ${loc.layer === l ? 'gridui-display-mode-btn--active' : 'gridui-display-mode-btn--inactive'}`}
                      style={{ fontSize: '0.7rem', padding: '2px 10px' }}
                    >
                      L{l}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'browse' && (
          <div className="gridui-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="gridui-card-header">
              <Icon name="map" size={16} />
              <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                Browse Cities
              </h3>
              <span style={{ fontSize: '0.7rem', color: 'var(--grid-text-secondary, #8b949e)' }}>
                {cityRegistry.count} cities
              </span>
            </div>
            <div className="gridui-card-body" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              {/* Search */}
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search cities..."
                className="gridui-settings-number-input"
                style={{ width: '100%', marginBottom: 8 }}
              />

              {/* Region filter chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
                <button
                  onClick={() => setSelectedRegion(null)}
                  className={`gridui-display-mode-btn ${selectedRegion === null ? 'gridui-display-mode-btn--active' : 'gridui-display-mode-btn--inactive'}`}
                  style={{ fontSize: '0.7rem', padding: '2px 8px' }}
                >
                  All
                </button>
                {regions.map(r => (
                  <button
                    key={r.id}
                    onClick={() => setSelectedRegion(r.id === selectedRegion ? null : r.id)}
                    className={`gridui-display-mode-btn ${selectedRegion === r.id ? 'gridui-display-mode-btn--active' : 'gridui-display-mode-btn--inactive'}`}
                    style={{ fontSize: '0.7rem', padding: '2px 8px' }}
                  >
                    {r.label} ({r.count})
                  </button>
                ))}
              </div>

              {/* City list */}
              <div style={{ flex: 1, overflowY: 'auto', maxHeight: 400 }}>
                {filteredCities.length === 0 ? (
                  <div style={{ color: 'var(--grid-text-secondary, #8b949e)', fontSize: '0.8rem', padding: '16px 0', textAlign: 'center' }}>
                    No cities found
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {filteredCities.map(city => (
                      <div
                        key={city.uCode}
                        onClick={() => handleCityClick(city)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          padding: '6px 8px',
                          background: 'var(--grid-bg-secondary, #161b22)',
                          borderRadius: 4,
                          border: '1px solid var(--grid-border, #30363d)',
                          cursor: 'pointer',
                          transition: 'background 100ms',
                        }}
                        onMouseEnter={e => (e.currentTarget.style.background = '#1c2333')}
                        onMouseLeave={e => (e.currentTarget.style.background = 'var(--grid-bg-secondary, #161b22)')}
                      >
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>{city.name}</div>
                          <div style={{ fontSize: '0.65rem', color: 'var(--grid-text-secondary, #8b949e)' }}>
                            {city.region} · P{city.teletextPage} · {city.landmark}
                          </div>
                        </div>
                        <span style={{ fontSize: '0.65rem', color: '#58a6ff', fontFamily: "'SF Mono','Fira Code',monospace" }}>
                          {city.uCode}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeSection === 'bookmarks' && (
          <div className="gridui-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="gridui-card-header">
              <Icon name="bookmark" size={16} />
              <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                Bookmarks
              </h3>
              <span style={{ fontSize: '0.7rem', color: 'var(--grid-text-secondary, #8b949e)' }}>
                {bookmarks.length} saved
              </span>
            </div>
            <div className="gridui-card-body" style={{ flex: 1 }}>
              {bookmarkCities.length === 0 ? (
                <div style={{ color: 'var(--grid-text-secondary, #8b949e)', fontSize: '0.8rem', padding: '16px 0', textAlign: 'center' }}>
                  No bookmarks yet. Use the Location tab to bookmark your current position.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {bookmarkCities.map((b, i) => (
                    <div
                      key={b.uCode}
                      onClick={() => handleBookmarkClick(b.uCode)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '6px 8px',
                        background: 'var(--grid-bg-secondary, #161b22)',
                        borderRadius: 4,
                        border: '1px solid var(--grid-border, #30363d)',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={e => (e.currentTarget.style.background = '#1c2333')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'var(--grid-bg-secondary, #161b22)')}
                    >
                      <Icon name="bookmark" size={16} style={{ color: '#d29922' }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                          {b.city?.name || 'Unknown Location'}
                        </div>
                        <div style={{ fontSize: '0.65rem', color: 'var(--grid-text-secondary, #8b949e)' }}>
                          {b.city?.region || ''} · {b.city ? `P${b.city.teletextPage}` : ''}
                        </div>
                      </div>
                      <span style={{ fontSize: '0.65rem', color: '#58a6ff', fontFamily: "'SF Mono','Fira Code',monospace" }}>
                        {b.uCode}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeSection === 'history' && (
          <div className="gridui-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="gridui-card-header">
              <Icon name="history" size={16} />
              <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                Location History
              </h3>
              <span style={{ fontSize: '0.7rem', color: 'var(--grid-text-secondary, #8b949e)' }}>
                {history.length} entries
              </span>
            </div>
            <div className="gridui-card-body" style={{ flex: 1 }}>
              {history.length === 0 ? (
                <div style={{ color: 'var(--grid-text-secondary, #8b949e)', fontSize: '0.8rem', padding: '16px 0', textAlign: 'center' }}>
                  No history yet. Navigate to a location to start tracking.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3, maxHeight: 400, overflowY: 'auto' }}>
                  {history.slice().reverse().map((h, i) => {
                    const city = cityRegistry.findByUCode(h)
                    return (
                      <div
                        key={`${h}-${i}`}
                        onClick={() => handleHistoryClick(h)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          padding: '5px 8px',
                          background: 'var(--grid-bg-secondary, #161b22)',
                          borderRadius: 4,
                          border: '1px solid var(--grid-border, #30363d)',
                          cursor: 'pointer',
                          opacity: i === 0 ? 1 : 0.8,
                        }}
                        onMouseEnter={e => (e.currentTarget.style.background = '#1c2333')}
                        onMouseLeave={e => (e.currentTarget.style.background = 'var(--grid-bg-secondary, #161b22)')}
                      >
                        <span style={{ fontSize: '0.65rem', color: 'var(--grid-text-secondary, #8b949e)', minWidth: 20 }}>
                          #{history.length - i}
                        </span>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '0.8rem', fontWeight: 500 }}>
                            {city?.name || 'Unknown'}
                          </div>
                        </div>
                        <span style={{ fontSize: '0.65rem', color: '#58a6ff', fontFamily: "'SF Mono','Fira Code',monospace" }}>
                          {h}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
