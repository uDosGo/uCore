/* ═══════════════════════════════════════════════════════════════════
   AssetsPanel — Font manager, sprite library, import/export
   ═══════════════════════════════════════════════════════════════════
   Unified assets tab for the GridUI surface. Provides:
     - Font manager (installed fonts, preview, activation)
     - Sprite library (character set sprites, glyph browser)
     - Import/export tools (font files, sprite sheets, grid data)
     - Symbol registry browser
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo, useCallback } from 'react'
import { useStore } from '../GridUIStore'
import { getAllFonts, getDefaultFont, type FontConfig } from '../grid-algebra/FontResolver'
import { TELETEXT_G0 } from '../grid-algebra/CharacterSet'
import { useSvgBridge } from '../hooks/useSvgBridge'

// ─── AssetsPanel Component ───────────────────────────────────────────
export function AssetsPanel() {
  const store = useStore()
  const [activeSection, setActiveSection] = useState<'fonts' | 'sprites' | 'import' | 'symbols'>('fonts')
  const [fontSearch, setFontSearch] = useState('')
  const [spriteSearch, setSpriteSearch] = useState('')
  const [activeFontId, setActiveFontId] = useState<string>(getDefaultFont('gridui'))
  const [importResult, setImportResult] = useState<string | null>(null)

  // ─── Fonts ───────────────────────────────────────────────────────
  const fonts = useMemo(() => {
    const all = getAllFonts()
    if (!fontSearch.trim()) return all
    const q = fontSearch.toLowerCase()
    return all.filter(f => f.name.toLowerCase().includes(q) || f.id.toLowerCase().includes(q))
  }, [fontSearch])

  // ─── Sprites / Glyphs ────────────────────────────────────────────
  const allGlyphs = useMemo(() => {
    return Object.entries(TELETEXT_G0).map(([code, char]) => ({
      codePoint: parseInt(code),
      char,
      name: `Teletext G0 0x${parseInt(code).toString(16).padStart(2, '0').toUpperCase()}`,
      category: parseInt(code) < 0x20 ? 'control' : parseInt(code) < 0x80 ? 'latin' : 'graphics',
    }))
  }, [])

  const filteredGlyphs = useMemo(() => {
    if (!spriteSearch.trim()) return allGlyphs.slice(0, 200)
    const q = spriteSearch.toLowerCase()
    return allGlyphs.filter(g =>
      g.name.toLowerCase().includes(q) ||
      g.codePoint.toString(16).includes(q) ||
      g.category.toLowerCase().includes(q)
    ).slice(0, 200)
  }, [spriteSearch, allGlyphs])

  // ─── Symbol registry ─────────────────────────────────────────────
  const [symbolSearch, setSymbolSearch] = useState('')

  // ─── Handle font activation ──────────────────────────────────────
  const handleActivateFont = useCallback((fontId: string) => {
    setActiveFontId(fontId)
    setImportResult(`OK: Activated font "${fontId}"`)
    setTimeout(() => setImportResult(null), 2000)
  }, [])

  // ─── SVG Bridge ──────────────────────────────────────────────────
  const svgBridge = useSvgBridge()
  const [svgExportResult, setSvgExportResult] = useState<string | null>(null)
  const [svgPreview, setSvgPreview] = useState<string | null>(null)
  const [showSvgPreview, setShowSvgPreview] = useState(false)

  // ─── Export font glyphs as SVG ───────────────────────────────────
  const handleExportFontAsSvg = useCallback(async (fontId: string) => {
    setSvgExportResult(null)
    setSvgPreview(null)
    // Build a simple SVG showing the font's glyphs
    const glyphs = Object.entries(TELETEXT_G0).slice(0, 96) // first 96 glyphs
    const cols = 16
    const rows = Math.ceil(glyphs.length / cols)
    const cellSize = 40
    const fontSize = 24
    const svgWidth = cols * cellSize
    const svgHeight = rows * cellSize

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${svgWidth}" height="${svgHeight}" viewBox="0 0 ${svgWidth} ${svgHeight}">
  <rect width="100%" height="100%" fill="#0d1117"/>
  <g font-family="monospace" font-size="${fontSize}" fill="#e6edf3">\n`
    glyphs.forEach(([code, char], i) => {
      const col = i % cols
      const row = Math.floor(i / cols)
      const x = col * cellSize + 4
      const y = row * cellSize + cellSize / 2 + fontSize / 3
      svg += `    <text x="${x}" y="${y}">${char === ' ' ? '·' : char}</text>\n`
    })
    svg += `  </g>
</svg>`

    // Try to convert via SVG bridge for a richer representation
    const result = await svgBridge.convert(svg, 'describe')
    if (result && !result.error) {
      setSvgExportResult(`OK: Font "${fontId}" exported as SVG (${glyphs.length} glyphs)`)
    } else {
      setSvgExportResult(`OK: Font "${fontId}" — ${glyphs.length} glyphs rendered as SVG`)
    }
    setSvgPreview(svg)
    setShowSvgPreview(true)
    setTimeout(() => setSvgExportResult(null), 3000)
  }, [svgBridge])

  // ─── Handle import ───────────────────────────────────────────────
  const handleImport = useCallback((type: string) => {
    setImportResult(`?${type.toUpperCase()} import not yet implemented (file picker TBD)`)
    setTimeout(() => setImportResult(null), 3000)
  }, [])

  return (
    <div className="gridui-panel">
      <div className="gridui-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 16 }}>

        {/* ─── Section Tabs ──────────────────────────────────────── */}
        <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid var(--grid-border, #30363d)', paddingBottom: 8 }}>
          {([
            { id: 'fonts' as const, label: '🔤 Fonts' },
            { id: 'sprites' as const, label: '🎨 Sprites' },
            { id: 'symbols' as const, label: '🔣 Symbols' },
            { id: 'import' as const, label: '📦 Import/Export' },
          ]).map(s => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className={`gridui-editor-tab ${activeSection === s.id ? 'gridui-editor-tab--active' : ''}`}
              style={{ fontSize: '0.8rem', padding: '4px 12px' }}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* ─── Result Toast ──────────────────────────────────────── */}
        {importResult && (
          <div style={{
            padding: '8px 12px',
            borderRadius: 6,
            background: importResult.startsWith('?') ? '#E76F5120' : '#23863620',
            border: `1px solid ${importResult.startsWith('?') ? '#E76F5140' : '#3fb95040'}`,
            color: importResult.startsWith('?') ? '#E76F51' : '#3fb950',
            fontSize: '0.8rem',
          }}>
            {importResult}
          </div>
        )}

        {/* ─── Fonts Section ─────────────────────────────────────── */}
        {activeSection === 'fonts' && (
          <div className="gridui-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="gridui-card-header">
              <span>🔤</span>
              <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                Font Manager
              </h3>
              <span style={{ fontSize: '0.7rem', color: 'var(--grid-text-secondary, #8b949e)' }}>
                Active: <strong style={{ color: '#58a6ff' }}>{activeFontId || 'None'}</strong>
              </span>
            </div>
            <div className="gridui-card-body" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              {/* Search */}
              <input
                type="text"
                value={fontSearch}
                onChange={e => setFontSearch(e.target.value)}
                placeholder="Search fonts..."
                className="gridui-settings-number-input"
                style={{ width: '100%', marginBottom: 8 }}
              />

              {/* Font list */}
              <div style={{ flex: 1, overflowY: 'auto', maxHeight: 400 }}>
                {fonts.length === 0 ? (
                  <div style={{ color: 'var(--grid-text-secondary, #8b949e)', fontSize: '0.8rem', padding: '16px 0', textAlign: 'center' }}>
                    No fonts found
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {fonts.map(font => (
                      <div
                        key={font.id}
                        onClick={() => handleActivateFont(font.id)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          padding: '6px 8px',
                          background: font.id === activeFontId ? '#1c2333' : 'var(--grid-bg-secondary, #161b22)',
                          borderRadius: 4,
                          border: `1px solid ${font.id === activeFontId ? '#58a6ff40' : 'var(--grid-border, #30363d)'}`,
                          cursor: 'pointer',
                          transition: 'background 100ms',
                        }}
                        onMouseEnter={e => (e.currentTarget.style.background = '#1c2333')}
                        onMouseLeave={e => (e.currentTarget.style.background = font.id === activeFontId ? '#1c2333' : 'var(--grid-bg-secondary, #161b22)')}
                      >
                        <span style={{
                          fontSize: '0.85rem',
                          color: font.id === activeFontId ? '#58a6ff' : 'var(--grid-text-primary, #e6edf3)',
                        }}>
                          {font.id === activeFontId ? '●' : '○'}
                        </span>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>{font.name}</div>
                          <div style={{ fontSize: '0.65rem', color: 'var(--grid-text-secondary, #8b949e)' }}>
                            {font.category} · {font.isBitmap ? 'bitmap' : 'vector'} · {font.id === activeFontId ? 'Active' : 'Click to activate'}
                          </div>
                        </div>
                        <button
                          onClick={e => { e.stopPropagation(); handleExportFontAsSvg(font.id) }}
                          className="gridui-btn gridui-btn--small"
                          style={{ fontSize: 10, padding: '2px 6px' }}
                          title="Export font glyphs as SVG"
                        >
                          SVG
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ─── Sprites Section ───────────────────────────────────── */}
        {activeSection === 'sprites' && (
          <div className="gridui-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="gridui-card-header">
              <span>🎨</span>
              <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                Teletext G0 Glyph Browser
              </h3>
              <span style={{ fontSize: '0.7rem', color: 'var(--grid-text-secondary, #8b949e)' }}>
                {allGlyphs.length} glyphs
              </span>
            </div>
            <div className="gridui-card-body" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              {/* Search */}
              <input
                type="text"
                value={spriteSearch}
                onChange={e => setSpriteSearch(e.target.value)}
                placeholder="Search glyphs by name, code point, or category..."
                className="gridui-settings-number-input"
                style={{ width: '100%', marginBottom: 8 }}
              />

              {/* Glyph grid */}
              <div style={{ flex: 1, overflowY: 'auto', maxHeight: 400 }}>
                {filteredGlyphs.length === 0 ? (
                  <div style={{ color: 'var(--grid-text-secondary, #8b949e)', fontSize: '0.8rem', padding: '16px 0', textAlign: 'center' }}>
                    No glyphs found
                  </div>
                ) : (
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(48px, 1fr))',
                    gap: 4,
                  }}>
                    {filteredGlyphs.map((glyph, i) => (
                      <div
                        key={glyph.codePoint}
                        title={`${glyph.name} (U+${glyph.codePoint.toString(16).padStart(4, '0').toUpperCase()})`}
                        style={{
                          width: 48,
                          height: 48,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background: 'var(--grid-bg-secondary, #161b22)',
                          borderRadius: 4,
                          border: '1px solid var(--grid-border, #30363d)',
                          fontSize: 20,
                          cursor: 'pointer',
                          transition: 'background 100ms',
                        }}
                        onMouseEnter={e => (e.currentTarget.style.background = '#1c2333')}
                        onMouseLeave={e => (e.currentTarget.style.background = 'var(--grid-bg-secondary, #161b22)')}
                      >
                        {glyph.char || '?'}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ─── Symbols Section ────────────────────────────────────── */}
        {activeSection === 'symbols' && (
          <div className="gridui-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="gridui-card-header">
              <span>🔣</span>
              <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                Symbol Registry
              </h3>
            </div>
            <div className="gridui-card-body" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <input
                type="text"
                value={symbolSearch}
                onChange={e => setSymbolSearch(e.target.value)}
                placeholder="Search symbols..."
                className="gridui-settings-number-input"
                style={{ width: '100%', marginBottom: 8 }}
              />
              <div style={{ color: 'var(--grid-text-secondary, #8b949e)', fontSize: '0.8rem', padding: '16px 0', textAlign: 'center' }}>
                Symbol registry browser — coming soon
              </div>
            </div>
          </div>
        )}

        {/* ─── Import/Export Section ──────────────────────────────── */}
        {activeSection === 'import' && (
          <div className="gridui-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="gridui-card-header">
              <span>📦</span>
              <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                Import / Export
              </h3>
            </div>
            <div className="gridui-card-body" style={{ flex: 1 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {/* Import buttons */}
                <div className="gridui-card" style={{ marginBottom: 0 }}>
                  <div className="gridui-card-header">
                    <span>📥</span>
                    <h4 style={{ margin: 0, fontSize: '0.8rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                      Import
                    </h4>
                  </div>
                  <div className="gridui-card-body">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {['font', 'sprite', 'grid', 'palette'].map(type => (
                        <button
                          key={type}
                          onClick={() => handleImport(type)}
                          className="gridui-display-mode-btn gridui-display-mode-btn--inactive"
                          style={{ fontSize: '0.7rem', padding: '4px 12px' }}
                        >
                          {type.charAt(0).toUpperCase() + type.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Export buttons */}
                <div className="gridui-card" style={{ marginBottom: 0 }}>
                  <div className="gridui-card-header">
                    <span>📤</span>
                    <h4 style={{ margin: 0, fontSize: '0.8rem', fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
                      Export
                    </h4>
                  </div>
                  <div className="gridui-card-body">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {['grid as JSON', 'grid as PNG', 'font manifest', 'sprite sheet'].map(type => (
                        <button
                          key={type}
                          onClick={() => handleImport(type)}
                          className="gridui-display-mode-btn gridui-display-mode-btn--inactive"
                          style={{ fontSize: '0.7rem', padding: '4px 12px' }}
                        >
                          {type}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Info */}
                <div style={{ color: 'var(--grid-text-secondary, #8b949e)', fontSize: '0.7rem', padding: '8px 0', textAlign: 'center' }}>
                  File picker integration and actual import/export logic coming soon.
                </div>
              </div>
            </div>
          </div>
        )}

      </div>

      {/* SVG Preview Modal */}
      {showSvgPreview && svgPreview && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 300,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <div style={{
            background: '#161b22',
            border: '1px solid #30363d',
            borderRadius: 8,
            padding: 16,
            width: '90%',
            maxWidth: 800,
            maxHeight: '90%',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#e6edf3' }}>
                SVG Font Glyph Preview
              </h3>
              <button onClick={() => setShowSvgPreview(false)} className="gridui-btn--close" style={{ width: 24, height: 24, fontSize: 14 }}>✕</button>
            </div>
            <div style={{
              flex: 1,
              overflow: 'auto',
              background: '#0d1117',
              borderRadius: 4,
              padding: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: 300,
            }}>
              <div dangerouslySetInnerHTML={{ __html: svgPreview }} style={{ maxWidth: '100%' }} />
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(svgPreview)
                  setSvgExportResult('OK: SVG copied to clipboard')
                  setTimeout(() => setSvgExportResult(null), 2000)
                }}
                className="gridui-btn"
                style={{ fontSize: 12, padding: '4px 12px' }}
              >
                Copy SVG
              </button>
              <button
                onClick={() => setShowSvgPreview(false)}
                className="gridui-btn gridui-btn--primary"
                style={{ fontSize: 12, padding: '4px 12px' }}
              >
                Close
              </button>
            </div>
            {svgExportResult && (
              <div style={{
                padding: '4px 8px',
                borderRadius: 4,
                fontSize: 11,
                background: svgExportResult.startsWith('?') ? '#E76F5120' : '#23863620',
                border: `1px solid ${svgExportResult.startsWith('?') ? '#E76F5140' : '#3fb95040'}`,
                color: svgExportResult.startsWith('?') ? '#E76F51' : '#3fb950',
              }}>
                {svgExportResult}
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  )
}

