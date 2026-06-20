/* ═══════════════════════════════════════════════════════════════════
   TeletextGrid — Higher-level teletext page renderer for GridUI
   ═══════════════════════════════════════════════════════════════════
   Wraps GridBufferRenderer with:
     - Auto-fetch from Snackbar Ceefax API
     - Auto-zoom to fit container
     - Page navigation (3-digit dialer)
     - Live polling (every 10s)
     - Feed ticker at bottom
     - SVG import via uVector bridge
     - Cell editor mode
   ═══════════════════════════════════════════════════════════════════ */
import React, { useEffect } from 'react'
import { useStore, BORDER_MODE_CONFIGS } from '../GridUIStore'
import { GridBufferRenderer } from './GridBufferRenderer'
import { getColor } from '../grid-algebra/ColourPalette'
import { useTeletextPage, FG_COLOURS, BG_COLOURS } from '../hooks/useTeletextPage'
import type { UseTeletextPageOptions } from '../hooks/useTeletextPage'

// ─── TeletextGrid Component ──────────────────────────────────────────

export interface TeletextGridProps extends UseTeletextPageOptions {
  /** CSS class name override */
  className?: string
}

export const TeletextGrid: React.FC<TeletextGridProps> = ({
  initialPage = 100,
  autoRotate: enableAutoRotate = true,
  enableEditor = false,
  enableSvgImport = false,
  onPageChange,
  className,
}) => {
  const store = useStore()
  const page = useTeletextPage({
    initialPage,
    autoRotate: enableAutoRotate,
    enableEditor,
    enableSvgImport,
    onPageChange,
  })

  const vp = store.viewport
  const borderCfg = BORDER_MODE_CONFIGS[vp.borderMode]
  const borderPadFraction = (1 - borderCfg.fillFraction) / 2

  // ─── Keyboard shortcut ────────────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (/^[0-9]$/.test(e.key) && document.activeElement !== page.inputRef.current) {
        page.setShowNav(true)
        setTimeout(() => page.inputRef.current?.focus(), 0)
      }
      if (e.key === 'Escape') {
        page.setShowNav(false)
        page.setCellEditor(null)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [page])

  return (
    <div className={`gridui-panel ${className || ''}`}>
      {/* Viewport area */}
      <div
        ref={page.containerRef as React.RefObject<HTMLDivElement>}
        className="gridui-terminal-viewport"
        style={{
          padding: `${page.containerSize.h * borderPadFraction}px ${page.containerSize.w * borderPadFraction}px`,
          cursor: page.editorMode ? 'cell' : 'default',
        }}
      >
        <div
          className="gridui-terminal-screen"
          style={{
            width: page.zoomedW,
            height: page.zoomedH,
            ...page.displayModeFilter,
            position: 'relative',
          }}
        >
          {/* Click overlay for editor mode */}
          {page.editorMode && (
            <div style={{ position: 'absolute', inset: 0, zIndex: 10 }}>
              {Array.from({ length: vp.rows }).map((_, row) => (
                <div key={row} style={{ display: 'flex', height: page.scaledCellH }}>
                  {Array.from({ length: vp.cols }).map((_, col) => (
                    <div
                      key={col}
                      onClick={() => page.handleCellClick(row, col)}
                      style={{ width: page.scaledCellW, height: page.scaledCellH, cursor: 'pointer' }}
                      title={`(${col}, ${row})`}
                    />
                  ))}
                </div>
              ))}
            </div>
          )}

          <GridBufferRenderer
            buffer={page.displayBuffer}
            paletteId={page.paletteId}
            cellWidth={page.scaledCellW}
            cellHeight={page.scaledCellH}
            gridFont={store.gridFont}
          />
        </div>
      </div>

      {/* Cell Editor Popup */}
      {page.cellEditor && (
        <div
          ref={page.cellEditorRef as React.RefObject<HTMLDivElement>}
          className="gridui-cell-editor-popup"
          style={{
            position: 'absolute',
            bottom: 80,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 100,
            background: '#161b22',
            border: '1px solid #30363d',
            borderRadius: 8,
            padding: 12,
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            minWidth: 320,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ color: '#e6edf3', fontSize: 13, fontWeight: 600 }}>
              Cell ({page.cellEditor.col}, {page.cellEditor.row})
            </span>
            <button onClick={() => page.setCellEditor(null)} className="gridui-btn--close" style={{ marginLeft: 'auto', width: 20, height: 20, fontSize: 12 }}>✕</button>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
            <label style={{ color: '#8b949e', fontSize: 12, minWidth: 60 }}>Character</label>
            <input value={page.cellEditor.char} onChange={e => page.applyCellEdit({ char: e.target.value.slice(0, 1) || ' ' })} maxLength={1} className="gridui-input" style={{ width: 40, textAlign: 'center', fontSize: 16 }} />
            <span style={{ fontSize: 20, color: getColor(page.paletteId, page.cellEditor.fg), fontFamily: "'Bedstead','PetMe128',monospace", padding: '2px 8px', background: getColor(page.paletteId, page.cellEditor.bg), borderRadius: 4 }}>{page.cellEditor.char}</span>
          </div>
          <div style={{ marginBottom: 8 }}>
            <label style={{ color: '#8b949e', fontSize: 12, display: 'block', marginBottom: 4 }}>Foreground</label>
            <div style={{ display: 'flex', gap: 4 }}>
              {FG_COLOURS.map(c => (
                <button key={c.index} onClick={() => page.applyCellEdit({ fg: c.index })} style={{ width: 28, height: 28, borderRadius: 4, background: c.hex, border: page.cellEditor!.fg === c.index ? '2px solid #e6edf3' : '1px solid #30363d', cursor: 'pointer' }} title={c.label} />
              ))}
            </div>
          </div>
          <div style={{ marginBottom: 8 }}>
            <label style={{ color: '#8b949e', fontSize: 12, display: 'block', marginBottom: 4 }}>Background</label>
            <div style={{ display: 'flex', gap: 4 }}>
              {BG_COLOURS.map(c => (
                <button key={c.index} onClick={() => page.applyCellEdit({ bg: c.index })} style={{ width: 28, height: 28, borderRadius: 4, background: c.hex, border: page.cellEditor!.bg === c.index ? '2px solid #e6edf3' : '1px solid #30363d', cursor: 'pointer' }} title={c.label} />
              ))}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#e6edf3', fontSize: 12, cursor: 'pointer' }}>
              <input type="checkbox" checked={page.cellEditor.bold} onChange={e => page.applyCellEdit({ bold: e.target.checked })} style={{ accentColor: '#58a6ff' }} /> Bold
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#e6edf3', fontSize: 12, cursor: 'pointer' }}>
              <input type="checkbox" checked={page.cellEditor.flash} onChange={e => page.applyCellEdit({ flash: e.target.checked })} style={{ accentColor: '#58a6ff' }} /> Flash
            </label>
          </div>
        </div>
      )}

      {/* Page Navigation Overlay */}
      {page.showNav && (
        <div className="gridui-teletext-nav-overlay">
          <span className="gridui-teletext-nav-label">PAGE</span>
          <input ref={page.inputRef as React.RefObject<HTMLInputElement>} value={page.pageInput} onChange={e => page.handlePageInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && page.pageInput.length > 0) page.goToPage(parseInt(page.pageInput, 10)); if (e.key === 'Escape') { page.setShowNav(false); page.setCellEditor(null) } }} placeholder="---" maxLength={3} className="gridui-teletext-nav-input" />
          <button onClick={() => { page.setShowNav(false) }} className="gridui-teletext-nav-close">✕</button>
        </div>
      )}

      {/* Page Info Bar */}
      <div className="gridui-teletext-info-bar">
        <span>P{page.currentPage.meta.pageNumber.toString().padStart(3, '0')}</span>
        <span>{page.currentPage.meta.title}</span>
        <span className="gridui-teletext-poll-time">@{page.pollTimeStr}</span>
        {page.liveConnected && <span className="gridui-teletext-live-badge">LIVE</span>}
        {page.isLiveFeedPage && page.autoRotate && <span className="gridui-teletext-feed-badge">LIVE FEED</span>}
        {page.isLiveFeedPage && !page.autoRotate && <span className="gridui-teletext-feed-badge gridui-teletext-feed-badge-paused">FEED (PAUSED)</span>}
        <button onClick={() => page.setShowNav(!page.showNav)} className="gridui-teletext-goto-btn">GO TO PAGE</button>
        {enableEditor && (
          <button onClick={() => { page.setEditorMode(!page.editorMode); page.setCellEditor(null) }} className={`gridui-teletext-goto-btn ${page.editorMode ? 'gridui-teletext-goto-btn--active' : ''}`} style={{ marginLeft: 4, background: page.editorMode ? '#238636' : undefined, color: page.editorMode ? '#fff' : undefined }}>{page.editorMode ? 'EDITING' : 'EDIT'}</button>
        )}
        {enableSvgImport && (
          <button onClick={() => page.setShowSvgImport(!page.showSvgImport)} className="gridui-teletext-goto-btn" style={{ marginLeft: 4 }} title="Import SVG as teletext block graphics">SVG</button>
        )}
      </div>

      {/* SVG Import Modal */}
      {page.showSvgImport && (
        <div style={{ position: 'absolute', inset: 0, zIndex: 200, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16, width: '80%', maxWidth: 600, maxHeight: '80%', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#e6edf3' }}>Import SVG as Teletext Block Graphics</h3>
              <button onClick={() => { page.setShowSvgImport(false); page.setSvgInput('') }} className="gridui-btn--close" style={{ width: 24, height: 24, fontSize: 14 }}>✕</button>
            </div>
            <p style={{ margin: 0, fontSize: 12, color: '#8b949e' }}>Paste SVG markup below. It will be converted to CELX format via the uVector SVG bridge and rendered as teletext block graphics on the current page.</p>
            <textarea value={page.svgInput} onChange={e => page.setSvgInput(e.target.value)} placeholder={`<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">\n  <rect x="10" y="10" width="80" height="80" fill="blue"/>\n</svg>`} style={{ width: '100%', minHeight: 200, background: '#0d1117', border: '1px solid #30363d', borderRadius: 4, color: '#e6edf3', fontSize: 12, fontFamily: "'SF Mono','Fira Code',monospace", padding: 8, resize: 'vertical' }} />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              {page.svgBridge.loading && <span style={{ color: '#8b949e', fontSize: 12 }}>Converting…</span>}
              <button onClick={() => { page.setShowSvgImport(false); page.setSvgInput('') }} className="gridui-btn" style={{ fontSize: 12, padding: '4px 12px' }}>Cancel</button>
              <button onClick={page.handleSvgImport} disabled={page.svgBridge.loading || !page.svgInput.trim()} className="gridui-btn gridui-btn--primary" style={{ fontSize: 12, padding: '4px 12px' }}>{page.svgBridge.loading ? 'Converting…' : 'Import'}</button>
            </div>
            {page.svgImportResult && (
              <div style={{ padding: '6px 10px', borderRadius: 4, fontSize: 12, background: page.svgImportResult.startsWith('?') ? '#E76F5120' : '#23863620', border: `1px solid ${page.svgImportResult.startsWith('?') ? '#E76F5140' : '#3fb95040'}`, color: page.svgImportResult.startsWith('?') ? '#E76F51' : '#3fb950' }}>
                {page.svgImportResult}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scrolling Feed Ticker */}
      {page.currentFeedItem && (
        <div className="gridui-teletext-feed-ticker">
          <span className="gridui-teletext-ticker-source">{page.currentFeedItem.source}</span>
          <span className="gridui-teletext-ticker-title">{page.currentFeedItem.title}</span>
          <span className="gridui-teletext-ticker-body">{page.currentFeedItem.body}</span>
          <span className="gridui-teletext-ticker-time">{new Date(page.currentFeedItem.timestamp).toLocaleTimeString()}</span>
        </div>
      )}
    </div>
  )
}

export default TeletextGrid
