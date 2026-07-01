/* ═══════════════════════════════════════════════════════════════════
   GridEditorPanel — USX grid layers & cell editor with Character Maps
   ═══════════════════════════════════════════════════════════════════
   Now viewport-aware: uses store.viewport for grid dimensions and
   store.gridFont for character map previews.
   
   Refactored: Layers/Chars sidebar moved into main content area as
   a top tab bar + collapsible panel, freeing up the left sidebar
   slot for the VaultSidebar (filepicker).

   Layer Compositing: visible layers are composited using grid-algebra
   overlay/merge functions, rendering actual cell content per layer.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo, useCallback } from 'react'
import { Icon } from '../../../components/Icon'
import { useStore, CHAR_W, CHAR_H } from '../GridUIStore'
import { createBuffer, createBufferCell, cloneBuffer, getDimensions, overlay, merge, writeString, fill } from '@udos/gridcore'
import { GridBufferRenderer } from './GridBufferRenderer'
import type { PaletteId } from '../grid-algebra/ColourPalette'
import { useSvgBridge } from '../hooks/useSvgBridge'

type EditorTab = 'layers' | 'chars'

// ─── Layer buffer content helpers ────────────────────────────────────
// Each layer can hold its own GridBuffer. We store them in a simple
// map keyed by layer ID, seeded with demo content for visual feedback.

interface LayerBufferEntry {
  buffer: import('@udos/gridcore').GridBuffer
  label: string
}

// We'll use a module-level map so buffers persist across re-renders
const layerBuffers = new Map<string, LayerBufferEntry>()

function getOrCreateLayerBuffer(layerId: string, label: string, cols: number, rows: number) {
  if (!layerBuffers.has(layerId)) {
    const buf = createBuffer(cols, rows)
    // Seed with some demo content so layers are visible
    const seeded = fill(buf, 0, 0, cols, 1, ' ', 7, 4)
    writeString(seeded, 1, 0, `[${label}]`, 7, 4)
    layerBuffers.set(layerId, { buffer: seeded, label })
  }
  return layerBuffers.get(layerId)!
}

function updateLayerBuffer(layerId: string, buffer: import('@udos/gridcore').GridBuffer) {
  const existing = layerBuffers.get(layerId)
  if (existing) {
    layerBuffers.set(layerId, { ...existing, buffer })
  }
}

// ─── Grid Editor Panel ───────────────────────────────────────────────

export function GridEditorPanel() {
  const store = useStore()
  const [activeTab, setActiveTab] = useState<EditorTab>('layers')
  const [newLayerName, setNewLayerName] = useState('')
  const [newLayerColor, setNewLayerColor] = useState('#58a6ff')
  const [showAddLayer, setShowAddLayer] = useState(false)
  const [tooltip, setTooltip] = useState<{ char: string; index: number } | null>(null)
  const [editorSidebarOpen, setEditorSidebarOpen] = useState(true)

  // ─── Active layer for editing ─────────────────────────────────────
  const [activeLayerId, setActiveLayerId] = useState<string | null>(null)

  // Viewport-driven grid dimensions
  const vp = store.viewport
  const gridCols = vp.cols
  const gridRows = vp.rows
  const cellPx = CHAR_W  // base cell size in px

  // Font family for character preview
  const FONT_PREVIEW: Record<string, string> = {
    bedstead: "'Bedstead',monospace",
    petme128: "'PetMe128',monospace",
    teletext50: "'Teletext50',monospace",
    pressstart2p: "'Press Start 2P',monospace",
  }

  // Block graphic characters for teletext/C64
  const BLOCK_GLYPH_CHARS = '▀▄█▌▐▖▗▘▙▚▛▜▝▞▟░▒▓│┤╡╢╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀'

  const chars = Array.from({ length: 128 }, (_, i) => {
    // Teletext/C64 block graphics in the 0x20-0x7F range
    const isBlockGraphic = i >= 0x20 && i <= 0x7F && BLOCK_GLYPH_CHARS.includes(String.fromCharCode(i))
    const isPrintable = i >= 32 && i <= 126
    return {
      index: i,
      char: isPrintable ? String.fromCharCode(i) : '·',
      hasGlyph: isPrintable || isBlockGraphic,
      isBlockGraphic,
    }
  })

  // ─── Ensure layer buffers exist for all layers ────────────────────
  useMemo(() => {
    for (const layer of store.gridLayers) {
      getOrCreateLayerBuffer(layer.id, layer.name, gridCols, gridRows)
    }
  }, [store.gridLayers, gridCols, gridRows])

  // ─── Composite visible layers into a single buffer ────────────────
  const compositedBuffer = useMemo(() => {
    // Start with an empty buffer
    let result = createBuffer(gridCols, gridRows)

    // Get visible layers sorted by zIndex
    const visibleLayers = store.gridLayers
      .filter(l => l.visible)
      .sort((a, b) => a.zIndex - b.zIndex)

    for (const layer of visibleLayers) {
      const entry = layerBuffers.get(layer.id)
      if (!entry) continue

      // Resize layer buffer to match grid dimensions if needed
      const { cols: lCols, rows: lRows } = getDimensions(entry.buffer)
      let layerBuf = entry.buffer
      if (lCols !== gridCols || lRows !== gridRows) {
        // We'd need resize here, but for now just use as-is
      }

      // Composite using overlay (non-space chars replace)
      result = overlay(result, layerBuf, 0, 0)
    }

    return result
  }, [store.gridLayers, gridCols, gridRows])

  // ─── SVG Bridge ──────────────────────────────────────────────────
  const svgBridge = useSvgBridge()
  const [showSvgImport, setShowSvgImport] = useState(false)
  const [svgInput, setSvgInput] = useState('')
  const [svgImportResult, setSvgImportResult] = useState<string | null>(null)

  // ─── Import SVG as CELX into active layer ────────────────────────
  const handleSvgImport = useCallback(async () => {
    if (!svgInput.trim() || !activeLayerId) return
    setSvgImportResult(null)
    const result = await svgBridge.convert(svgInput, 'celx')
    if (!result) {
      setSvgImportResult('?SVG import failed — is Snackbar running?')
      return
    }
    if (result.error) {
      setSvgImportResult(`?${result.error}`)
      return
    }

    // Parse CELX output into the active layer buffer
    const lines = result.output.trim().split('\n')
    const entry = layerBuffers.get(activeLayerId)
    if (!entry) {
      setSvgImportResult('?Active layer not found')
      return
    }
    const buf = cloneBuffer(entry.buffer)
    for (let row = 0; row < Math.min(lines.length, buf.length); row++) {
      const line = lines[row].trim()
      if (!line || line.startsWith('#')) continue
      const cells = line.split(',')
      for (let col = 0; col < Math.min(cells.length, buf[row].length); col++) {
        const parts = cells[col].trim().split(':')
        if (parts.length >= 3) {
          const char = parts[0] === ' ' ? ' ' : parts[0]
          const fg = parseInt(parts[1], 10) || 7
          const bg = parseInt(parts[2], 10) || 0
          buf[row][col] = {
            char,
            fg,
            bg,
            bold: false,
            flash: false,
            doubleHeight: false,
            doubleWidth: false,
          }
        }
      }
    }
    updateLayerBuffer(activeLayerId, buf)
    setSvgImportResult(`OK: Imported ${lines.length} rows into "${entry.label}"`)
    setShowSvgImport(false)
    setSvgInput('')
    setTimeout(() => setSvgImportResult(null), 3000)
  }, [svgInput, svgBridge, activeLayerId])

  // ─── Handle cell click on active layer ────────────────────────────
  const handleCellClick = (col: number, row: number) => {
    if (!activeLayerId) return
    const entry = layerBuffers.get(activeLayerId)
    if (!entry) return

    const buf = cloneBuffer(entry.buffer)
    if (buf[row] && buf[row][col]) {
      // Toggle: if cell has content, clear it; otherwise place a block
      const cell = buf[row][col]
      if (cell.char !== ' ' || cell.bg !== 0) {
        buf[row][col] = createBufferCell(' ', 7, 0)
      } else {
        // Find the layer colour index (use 4=blue as default)
        const layer = store.gridLayers.find(l => l.id === activeLayerId)
        const colorIdx = 4 // blue
        buf[row][col] = createBufferCell('█', 7, colorIdx)
      }
      updateLayerBuffer(activeLayerId, buf)
      // Force re-render by toggling a state
      setActiveLayerId(activeLayerId)
    }
  }

  return (
    <div className="gridui-panel">
      <div className="gridui-editor-layout">

        {/* ─── Editor Sidebar (Layers/Chars) — now inside main content area ─── */}
        <div className="gridui-editor-sidebar" style={{ width: editorSidebarOpen ? 260 : 0, minWidth: editorSidebarOpen ? 260 : 0, overflow: 'hidden', transition: 'width 150ms ease, min-width 150ms ease' }}>
          <div style={{ display: 'flex', borderBottom: '1px solid var(--grid-border-light, #21262d)' }}>
            <button
              onClick={() => setActiveTab('layers')}
              className={`gridui-editor-tab ${activeTab === 'layers' ? 'gridui-editor-tab--active' : ''}`}
            >
              <Icon name="layers" size={14} />
              Layers
            </button>
            <button
              onClick={() => setActiveTab('chars')}
              className={`gridui-editor-tab ${activeTab === 'chars' ? 'gridui-editor-tab--active' : ''}`}
            >
              <Icon name="font_download" size={14} />
              Chars
            </button>
            <button
              onClick={() => setEditorSidebarOpen(false)}
              className="gridui-btn--icon"
              style={{ marginLeft: 'auto', padding: '4px 8px' }}
              title="Close editor sidebar"
            >
              <Icon name="chevron_right" size={12} />
            </button>
          </div>

          {activeTab === 'layers' && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderBottom: '1px solid var(--grid-border-light, #21262d)' }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Layers</span>
                <button onClick={() => setShowAddLayer(v => !v)} className="gridui-btn--icon">+</button>
              </div>
              {showAddLayer && (
                <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--grid-border-light, #21262d)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <input value={newLayerName} onChange={e => setNewLayerName(e.target.value)} placeholder="Layer name..." className="gridui-input" />
                  <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                    <input type="color" value={newLayerColor} onChange={e => setNewLayerColor(e.target.value)} style={{ width: 28, height: 28, padding: 0, border: 'none', cursor: 'pointer', background: 'transparent' }} />
                    <button onClick={() => { if (newLayerName.trim()) { store.addLayer(newLayerName.trim(), newLayerColor); setNewLayerName(''); setShowAddLayer(false) } }} className="gridui-btn gridui-btn--primary gridui-btn--small">Add</button>
                    <button onClick={() => setShowAddLayer(false)} className="gridui-btn gridui-btn--small">Cancel</button>
                  </div>
                </div>
              )}
              {store.gridLayers.map(layer => (
                <div
                  key={layer.id}
                  className={`gridui-editor-layer-row ${activeLayerId === layer.id ? 'gridui-editor-layer-row--active' : ''}`}
                  onClick={() => setActiveLayerId(layer.id)}
                  style={{
                    cursor: 'pointer',
                    background: activeLayerId === layer.id ? 'var(--grid-bg-hover, #1c2333)' : undefined,
                  }}
                >
                  <input type="checkbox" checked={layer.visible} onChange={() => store.toggleLayer(layer.id)} style={{ accentColor: '#58a6ff' }} onClick={e => e.stopPropagation()} />
                  <div style={{ width: 12, height: 12, borderRadius: 2, background: layer.color, flexShrink: 0 }} />
                  <span className="gridui-editor-layer-name">{layer.name}</span>
                  <span className="gridui-editor-layer-z">z:{layer.zIndex}</span>
                  <input type="range" min={0} max={1} step={0.1} value={layer.opacity} onChange={e => { e.stopPropagation(); store.setLayerOpacity(layer.id, Number(e.target.value)) }} style={{ width: 50, accentColor: '#58a6ff' }} />
                  <button onClick={e => { e.stopPropagation(); store.removeLayer(layer.id); if (activeLayerId === layer.id) setActiveLayerId(null) }} className="gridui-btn--close" style={{ width: 20, height: 20, fontSize: 12 }}>✕</button>
                </div>
              ))}
              {activeLayerId && (
                <div style={{ padding: '8px 12px', borderTop: '1px solid var(--grid-border-light, #21262d)', fontSize: 11, color: 'var(--grid-text-secondary, #8b949e)' }}>
                  Click cells on the grid to paint on <strong style={{ color: store.gridLayers.find(l => l.id === activeLayerId)?.color || '#58a6ff' }}>{store.gridLayers.find(l => l.id === activeLayerId)?.name}</strong>
                </div>
              )}
            </>
          )}

          {activeTab === 'chars' && (
            <div style={{ padding: '8px 12px' }}>
              <div className="gridui-charmaps-grid">
                {chars.map(c => (
                  <div key={c.index} className={`gridui-charmaps-cell ${c.hasGlyph ? 'gridui-charmaps-cell--has-glyph' : 'gridui-charmaps-cell--no-glyph'}`}
                    onMouseEnter={() => c.hasGlyph && setTooltip({ char: c.char, index: c.index })}
                    onMouseLeave={() => setTooltip(null)}>
                    <span className="gridui-charmaps-char">{c.char}</span>
                    <span className="gridui-charmaps-index">{c.index}</span>
                  </div>
                ))}
              </div>
              {tooltip && (
                <div className="gridui-tooltip">
                  <span style={{ fontSize: 24 }}>{tooltip.char}</span>
                  <span>U+{tooltip.index.toString(16).toUpperCase().padStart(4, '0')} · Dec {tooltip.index}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ─── Editor Sidebar Toggle Button (when collapsed) ─── */}
        {!editorSidebarOpen && (
          <button
            onClick={() => setEditorSidebarOpen(true)}
            className="gridui-btn--icon"
            style={{ alignSelf: 'flex-start', marginTop: 8, padding: '4px 6px' }}
            title="Open editor sidebar"
          >
            <Icon name="chevron_left" size={12} />
          </button>
        )}

        {/* SVG Import Button & Result Toast */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
          <div style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '4px 0' }}>
            <button
              onClick={() => setShowSvgImport(v => !v)}
              disabled={!activeLayerId}
              className="gridui-btn gridui-btn--small"
              style={{ fontSize: 11 }}
              title={activeLayerId ? 'Import SVG as CELX into active layer' : 'Select a layer first'}
            >
              <Icon name="file_upload" size={12} style={{ marginRight: 4 }} />
              SVG Import
            </button>
            {svgBridge.loading && (
              <span style={{ color: '#8b949e', fontSize: 11 }}>Converting…</span>
            )}
            {svgImportResult && (
              <span style={{
                fontSize: 11,
                padding: '2px 6px',
                borderRadius: 3,
                background: svgImportResult.startsWith('?') ? '#E76F5120' : '#23863620',
                border: `1px solid ${svgImportResult.startsWith('?') ? '#E76F5140' : '#3fb95040'}`,
                color: svgImportResult.startsWith('?') ? '#E76F51' : '#3fb950',
              }}>
                {svgImportResult}
              </span>
            )}
          </div>

          {/* SVG Import Modal */}
          {showSvgImport && (
            <div style={{
              position: 'absolute',
              inset: 0,
              zIndex: 200,
              background: 'rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <div style={{
                background: '#161b22',
                border: '1px solid #30363d',
                borderRadius: 8,
                padding: 16,
                width: '80%',
                maxWidth: 600,
                maxHeight: '80%',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#e6edf3' }}>
                    Import SVG as CELX Layer
                  </h3>
                  <button onClick={() => { setShowSvgImport(false); setSvgInput('') }} className="gridui-btn--close" style={{ width: 24, height: 24, fontSize: 14 }}>✕</button>
                </div>
                <p style={{ margin: 0, fontSize: 12, color: '#8b949e' }}>
                  Paste SVG markup below. It will be converted to CELX format via the uVector SVG bridge
                  and imported into the active layer: <strong style={{ color: store.gridLayers.find(l => l.id === activeLayerId)?.color || '#58a6ff' }}>{store.gridLayers.find(l => l.id === activeLayerId)?.name || 'None'}</strong>
                </p>
                <textarea
                  value={svgInput}
                  onChange={e => setSvgInput(e.target.value)}
                  placeholder={`<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">\n  <rect x="10" y="10" width="80" height="80" fill="blue"/>\n</svg>`}
                  style={{
                    width: '100%',
                    minHeight: 200,
                    background: '#0d1117',
                    border: '1px solid #30363d',
                    borderRadius: 4,
                    color: '#e6edf3',
                    fontSize: 12,
                    fontFamily: "'SF Mono','Fira Code',monospace",
                    padding: 8,
                    resize: 'vertical',
                  }}
                />
                <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => { setShowSvgImport(false); setSvgInput('') }}
                    className="gridui-btn"
                    style={{ fontSize: 12, padding: '4px 12px' }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSvgImport}
                    disabled={svgBridge.loading || !svgInput.trim()}
                    className="gridui-btn gridui-btn--primary"
                    style={{ fontSize: 12, padding: '4px 12px' }}
                  >
                    {svgBridge.loading ? 'Converting…' : 'Import'}
                  </button>
                </div>
              </div>
            </div>
          )}

        {/* Grid Canvas — composited layer view */}
        <div className="gridui-editor-canvas" style={{ flex: 1 }}>
          <div style={{
            position: 'relative',
            width: gridCols * cellPx,
            height: gridRows * cellPx,
            background: 'var(--grid-bg, #0d1117)',
            border: '1px solid var(--grid-border, #30363d)',
            borderRadius: 4,
            overflow: 'hidden',
          }}>
            {/* Grid cells — square cellPx×cellPx */}
            <svg width={gridCols * cellPx} height={gridRows * cellPx} style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
              {Array.from({ length: gridRows }).map((_, row) =>
                Array.from({ length: gridCols }).map((_, col) => (
                  <rect key={`${row}-${col}`} x={col * cellPx} y={row * cellPx} width={cellPx} height={cellPx} fill="none" stroke="var(--grid-border-light, #21262d)" strokeWidth={0.5} opacity={0.3} />
                ))
              )}
            </svg>

            {/* Composited layer content rendered via GridBufferRenderer */}
            <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
              <GridBufferRenderer
                buffer={compositedBuffer}
                paletteId="unified"
                cellWidth={cellPx}
                cellHeight={cellPx}
                gridFont={store.gridFont}
              />
            </div>

            {/* Click overlay for painting on active layer */}
            {activeLayerId && (
              <div style={{ position: 'absolute', inset: 0, zIndex: 10 }}>
                {Array.from({ length: gridRows }).map((_, row) => (
                  <div key={row} style={{ display: 'flex', height: cellPx }}>
                    {Array.from({ length: gridCols }).map((_, col) => (
                      <div
                        key={col}
                        onClick={() => handleCellClick(col, row)}
                        style={{
                          width: cellPx,
                          height: cellPx,
                          cursor: 'crosshair',
                        }}
                        title={`(${col}, ${row})`}
                      />
                    ))}
                  </div>
                ))}
              </div>
            )}

            {/* Layer overlay labels */}
            {store.gridLayers.filter(l => l.visible).map(layer => (
              <div key={layer.id} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity: layer.opacity, border: `1px solid ${layer.color}20`, borderRadius: 4 }}>
                <div style={{ position: 'absolute', top: 2, left: 4, fontSize: 10, color: layer.color, fontFamily: "'SF Mono','Fira Code',monospace", background: 'rgba(0,0,0,0.6)', padding: '1px 4px', borderRadius: 2 }}>{layer.name}</div>
              </div>
            ))}

            {/* Center text when no layers visible */}
            {store.gridLayers.filter(l => l.visible).length === 0 && (
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--grid-text-secondary, #8b949e)', fontSize: 13, fontFamily: "'SF Mono','Fira Code',monospace", pointerEvents: 'none' }}>
                <span>{gridCols} × {gridRows} Grid · Toggle layers to see content</span>
              </div>
            )}
          </div>
        </div>

        </div>{/* closes SVG import wrapper div */}

      </div>
    </div>
  )
}

