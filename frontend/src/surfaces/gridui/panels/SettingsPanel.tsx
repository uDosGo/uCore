/* ═══════════════════════════════════════════════════════════════════
   SettingsPanel — Viewport, display, and surface configuration
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { useStore } from '../GridUIStore'

export function SettingsPanel() {
  const store = useStore()

  return (
    <div className="gridui-panel">
      <div className="gridui-panel-body">

        <div className="gridui-settings-form">
          {/* Viewport Dimensions */}
          <div className="gridui-card">
            <div className="gridui-card-header">
              <span>🖥</span><h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>Viewport</h3>
            </div>
            <div className="gridui-card-body">
              <div className="gridui-settings-grid">
                <div className="gridui-settings-field">
                  <label className="gridui-settings-field-label">Columns</label>
                  <input type="number" value={store.viewport.cols} onChange={e => store.setViewport({ cols: Math.max(40, Math.min(160, Number(e.target.value))) })} className="gridui-settings-number-input" />
                </div>
                <div className="gridui-settings-field">
                  <label className="gridui-settings-field-label">Rows</label>
                  <input type="number" value={store.viewport.rows} onChange={e => store.setViewport({ rows: Math.max(12, Math.min(60, Number(e.target.value))) })} className="gridui-settings-number-input" />
                </div>
              </div>
            </div>
          </div>

          {/* Display Mode */}
          <div className="gridui-card">
            <div className="gridui-card-header">
              <span>🎨</span><h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>Display Mode</h3>
            </div>
            <div className="gridui-card-body">
              <div style={{ display: 'flex', gap: 8 }}>
                {(['teletext', 'mono', 'wireframe'] as const).map(mode => (
                  <button key={mode} onClick={() => store.setGridDisplayMode(mode)} className={`gridui-display-mode-btn ${store.displayMode === mode ? 'gridui-display-mode-btn--active' : 'gridui-display-mode-btn--inactive'}`}>
                    <div className="gridui-display-mode-label">{mode === 'teletext' ? 'Teletext' : mode === 'mono' ? 'Monochrome' : 'Wireframe'}</div>
                    <div className="gridui-display-mode-desc">{mode === 'teletext' ? 'Full color' : mode === 'mono' ? 'Grayscale' : 'High contrast'}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Font Size */}
          <div className="gridui-card">
            <div className="gridui-card-header">
              <span>🔤</span><h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>Font Size</h3>
            </div>
            <div className="gridui-card-body">
              <div className="gridui-fontsize-controls">
                {[12, 14, 16, 18, 20, 24].map(size => (
                  <button key={size} onClick={() => store.setFontSize(size)} className={`gridui-fontsize-btn ${store.fontSize === size ? 'gridui-fontsize-btn--active' : ''}`} style={store.fontSize === size ? { background: 'var(--grid-bg-hover, #1c2333)' } : {}}>{size}</button>
                ))}
              </div>
            </div>
          </div>

          {/* Color Palette (unified) */}
          <div className="gridui-card">
            <div className="gridui-card-header">
              <span>🎨</span><h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>Color Palette</h3>
            </div>
            <div className="gridui-card-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', gap: 2, padding: '4px 0' }}>
                  {['#0d1117','#da3633','#238636','#d29922','#58a6ff','#bc8cff','#39d2c0','#e6edf3'].map((c, i) => (
                    <div key={i} style={{ width: 20, height: 20, borderRadius: 3, background: c, border: '1px solid #30363d' }} title={`Colour ${i}`} />
                  ))}
                </div>
                <span style={{ fontSize: 12, color: 'var(--grid-text-secondary, #8b949e)' }}>Unified Dark · Bootstrap/GitHub Dark</span>
              </div>
            </div>
          </div>

          {/* Toggles */}
          <div className="gridui-card">
            <div className="gridui-card-header">
              <span>🔘</span><h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>Options</h3>
            </div>
            <div className="gridui-card-body">
              <div className="gridui-settings-row">
                <span style={{ fontSize: 13, color: 'var(--grid-text, #e6edf3)' }}>Show border</span>
                <button onClick={() => store.setViewport({ borderMode: store.viewport.borderMode === 3 ? 1 : 3 })} className={`gridui-toggle ${store.viewport.borderMode === 3 ? 'gridui-toggle--on' : 'gridui-toggle--off'}`}>
                  <div className={`gridui-toggle-knob ${store.viewport.borderMode === 3 ? 'gridui-toggle-knob--on' : 'gridui-toggle-knob--off'}`} />
                </button>
              </div>
              <div className="gridui-settings-row">
                <span style={{ fontSize: 13, color: 'var(--grid-text, #e6edf3)' }}>Show chat sheet</span>
                <span style={{ fontSize: 11, color: 'var(--grid-text-secondary, #8b949e)' }}>Use toolbar chat toggle</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
