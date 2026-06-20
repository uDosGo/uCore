/* ═══════════════════════════════════════════════════════════════════
   ViewportSettingsPopup — Popup panel for viewport configuration
   ═══════════════════════════════════════════════════════════════════
   Positioned top-right, toggled by Display Settings icon in toolbar.
   Shows preset icons (square with shaded shapes), manual cols/rows,
   and border mode selector (1, 2, 3).
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { useStore, VIEWPORT_PRESETS, BORDER_MODE_CONFIGS } from '../GridUIStore'
import type { BorderMode, GridFont } from '../GridUIStore'

// ─── Preset icon: renders a small square with shaded fill ───────────
function PresetIcon({ cols, rows, active }: { cols: number; rows: number; active: boolean }) {
  const maxDim = Math.max(cols, rows)
  const fillW = (cols / maxDim) * 14
  const fillH = (rows / maxDim) * 14
  const offsetX = (14 - fillW) / 2
  const offsetY = (14 - fillH) / 2
  return (
    <svg width="20" height="20" viewBox="0 0 20 20">
      <rect x="3" y="3" width="14" height="14" rx="2" fill={active ? 'var(--pico-primary, #58a6ff)' : 'var(--grid-border, #30363d)'} opacity="0.3" />
      <rect x={3 + offsetX} y={3 + offsetY} width={fillW} height={fillH} rx="1" fill={active ? 'var(--pico-primary, #58a6ff)' : 'var(--grid-text-secondary, #8b949e)'} opacity={active ? 1 : 0.6} />
    </svg>
  )
}

// ─── Border mode preview ────────────────────────────────────────────
function BorderModePreview({ mode, active }: { mode: BorderMode; active: boolean }) {
  const fillPct = BORDER_MODE_CONFIGS[mode].fillFraction * 100
  return (
    <svg width="20" height="20" viewBox="0 0 20 20">
      {/* Outer border */}
      <rect x="2" y="2" width="16" height="16" rx="2" fill="none" stroke={active ? 'var(--pico-primary, #58a6ff)' : 'var(--grid-border, #30363d)'} strokeWidth="1.5" />
      {/* Inner fill area */}
      <rect x="4" y="4" width="12" height="12" rx="1" fill={active ? 'var(--pico-primary, #58a6ff)' : 'var(--grid-text-secondary, #8b949e)'} opacity={fillPct / 100} />
    </svg>
  )
}

// ─── Preset definitions ─────────────────────────────────────────────
const PRESET_LIST = [
  { key: '28x28', label: '1:1', cols: 28, rows: 28, subtitle: '28×28' },
  { key: '48x36', label: '4:3', cols: 48, rows: 36, subtitle: '48×36' },
  { key: '64x36', label: '16:9', cols: 64, rows: 36, subtitle: '64×36' },
]

// ─── Font definitions ───────────────────────────────────────────────
const FONT_OPTIONS: { value: GridFont; label: string; preview: string }[] = [
  { value: 'bedstead', label: 'Bedstead', preview: 'Bb' },
  { value: 'petme128', label: 'PetMe128', preview: 'Bb' },
  { value: 'teletext50', label: 'Teletext50', preview: 'Bb' },
  { value: 'pressstart2p', label: 'Press Start 2P', preview: 'Bb' },
]

const BORDER_MODES: { mode: BorderMode; label: string }[] = [
  { mode: 1, label: 'Narrow' },
  { mode: 2, label: 'Medium' },
  { mode: 3, label: 'Full' },
]

// ─── Component ──────────────────────────────────────────────────────
export function ViewportSettingsPopup() {
  const store = useStore()
  const popupRef = React.useRef<HTMLDivElement>(null)

  // Close on click outside
  React.useEffect(() => {
    if (!store.viewportPopupOpen) return
    function handleClick(e: MouseEvent) {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        store.toggleViewportPopup()
      }
    }
    // Delay to avoid immediate close from toggle button
    const timer = setTimeout(() => document.addEventListener('mousedown', handleClick), 0)
    return () => { clearTimeout(timer); document.removeEventListener('mousedown', handleClick) }
  }, [store.viewportPopupOpen, store.toggleViewportPopup])

  // Close on Escape
  React.useEffect(() => {
    if (!store.viewportPopupOpen) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') store.toggleViewportPopup()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [store.viewportPopupOpen, store.toggleViewportPopup])

  if (!store.viewportPopupOpen) return null

  const vp = store.viewport
  const panelLabel = store.activePanel === 'teletext' ? 'Teletext' : 'Terminal'

  return (
    <div className="gridui-viewport-popup-overlay">
      <div ref={popupRef} className="gridui-viewport-popup">
        {/* Header */}
        <div className="gridui-viewport-popup-header">
          <span className="gridui-viewport-popup-title">Viewport — {panelLabel}</span>
          <button className="gridui-viewport-popup-close" onClick={store.toggleViewportPopup}>✕</button>
        </div>

        {/* Presets */}
        <div className="gridui-viewport-popup-section">
          <div className="gridui-viewport-popup-section-label">Presets</div>
          <div className="gridui-viewport-popup-presets">
            {PRESET_LIST.map(p => {
              const active = vp.cols === p.cols && vp.rows === p.rows
              return (
                <button
                  key={p.key}
                  className={`gridui-viewport-preset-btn ${active ? 'active' : ''}`}
                  onClick={() => store.applyViewportPreset(p.key)}
                  title={`${p.cols}×${p.rows}`}
                >
                  <PresetIcon cols={p.cols} rows={p.rows} active={active} />
                  <span className="gridui-viewport-preset-label">{p.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Manual size */}
        <div className="gridui-viewport-popup-section">
          <div className="gridui-viewport-popup-section-label">Manual Size (chars)</div>
          <div className="gridui-viewport-popup-manual">
            <div className="gridui-viewport-manual-field">
              <label>Cols</label>
              <input
                type="number"
                min={24}
                max={128}
                value={vp.cols}
                onChange={e => store.setViewport({ cols: Math.max(24, Math.min(128, Number(e.target.value))) })}
                className="gridui-viewport-manual-input"
              />
            </div>
            <span className="gridui-viewport-manual-sep">×</span>
            <div className="gridui-viewport-manual-field">
              <label>Rows</label>
              <input
                type="number"
                min={4}
                max={128}
                value={vp.rows}
                onChange={e => store.setViewport({ rows: Math.max(4, Math.min(128, Number(e.target.value))) })}
                className="gridui-viewport-manual-input"
              />
            </div>
          </div>
        </div>

        {/* Font selector */}
        <div className="gridui-viewport-popup-section">
          <div className="gridui-viewport-popup-section-label">Font</div>
          <div className="gridui-viewport-popup-fonts">
            {FONT_OPTIONS.map(f => {
              const active = store.gridFont === f.value
              return (
                <button
                  key={f.value}
                  className={`gridui-viewport-font-btn ${active ? 'active' : ''}`}
                  onClick={() => store.setGridFont(f.value)}
                >
                  <span className="gridui-viewport-font-preview" style={{ fontFamily: `'${f.label}', monospace` }}>
                    {f.preview}
                  </span>
                  <span className="gridui-viewport-font-label">{f.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Border mode */}
        <div className="gridui-viewport-popup-section">
          <div className="gridui-viewport-popup-section-label">Border Mode</div>
          <div className="gridui-viewport-popup-border-modes">
            {BORDER_MODES.map(bm => (
              <button
                key={bm.mode}
                className={`gridui-viewport-border-btn ${vp.borderMode === bm.mode ? 'active' : ''}`}
                onClick={() => store.setViewport({ borderMode: bm.mode })}
              >
                <BorderModePreview mode={bm.mode} active={vp.borderMode === bm.mode} />
                <span>{bm.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
