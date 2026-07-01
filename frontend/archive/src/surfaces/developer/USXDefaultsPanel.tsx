/* ═══════════════════════════════════════════════════════════════════
   USXDefaultsPanel — Developer USX Style & Global Settings Defaults
   Font size, font style, palette presets — persisted to localStorage
   and synced with the system GlobalSettingsPanel via shared key.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { Icon } from '../../components/Icon'

const SETTINGS_KEY = 'ucore-global-settings'

interface GlobalSettings {
  displayMode: 'grid' | 'list' | 'compact'
  fontSize: number
  palette: string
  autoSave: boolean
  showStatusBar: boolean
  enableAnimations: boolean
}

const DEFAULT_SETTINGS: GlobalSettings = {
  displayMode: 'grid',
  fontSize: 14,
  palette: 'default',
  autoSave: true,
  showStatusBar: true,
  enableAnimations: true,
}

const FONT_STYLE_OPTIONS = [
  { id: 'system', name: 'System UI', family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif' },
  { id: 'mono', name: 'Monospace', family: "'C64 User Mono v1.0', 'SFMono-Regular', Consolas, monospace" },
  { id: 'teletext', name: 'Teletext', family: "'Teletext50', monospace" },
  { id: 'petme', name: 'Pet Me', family: "'PetMe128', monospace" },
  { id: 'press-start', name: 'Press Start', family: "'Press Start 2P', monospace" },
]

const PALETTES = [
  { id: 'default', name: 'Default', color: '#58a6ff', desc: 'Pico default blue' },
  { id: 'green', name: 'Forest', color: '#22c55e', desc: 'Green accent' },
  { id: 'orange', name: 'Sunset', color: '#f0883e', desc: 'Warm orange' },
  { id: 'purple', name: 'Twilight', color: '#a855f7', desc: 'Purple accent' },
  { id: 'cyan', name: 'Neon', color: '#00ff9d', desc: 'Cyan glow' },
]

function loadSettings(): GlobalSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch { /* ignore */ }
  return { ...DEFAULT_SETTINGS }
}

function saveSettings(settings: GlobalSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  document.documentElement.setAttribute('data-palette', settings.palette)
}

export function USXDefaultsPanel() {
  const [settings, setSettings] = useState<GlobalSettings>(DEFAULT_SETTINGS)
  const [fontStyle, setFontStyle] = useState(() => localStorage.getItem('ucore-font-style') || 'system')
  const [statusMsg, setStatusMsg] = useState<string | null>(null)

  useEffect(() => {
    const loaded = loadSettings()
    setSettings(loaded)
    saveSettings(loaded)
  }, [])

  const updateSetting = useCallback(<K extends keyof GlobalSettings>(
    key: K, value: GlobalSettings[K]
  ) => {
    setSettings(prev => {
      const next = { ...prev, [key]: value }
      saveSettings(next)
      return next
    })
  }, [])

  const handleFontStyleChange = useCallback((styleId: string) => {
    setFontStyle(styleId)
    localStorage.setItem('ucore-font-style', styleId)
    const option = FONT_STYLE_OPTIONS.find(o => o.id === styleId)
    if (option) {
      document.documentElement.style.setProperty('--usx-font-family', option.family)
    }
    setStatusMsg(`Font style set to: ${FONT_STYLE_OPTIONS.find(o => o.id === styleId)?.name || styleId}`)
    setTimeout(() => setStatusMsg(null), 2000)
  }, [])

  const handleResetDefaults = useCallback(() => {
    const defaults = { ...DEFAULT_SETTINGS }
    setSettings(defaults)
    saveSettings(defaults)
    setFontStyle('system')
    localStorage.setItem('ucore-font-style', 'system')
    document.documentElement.style.removeProperty('--usx-font-family')
    setStatusMsg('Defaults restored')
    setTimeout(() => setStatusMsg(null), 2000)
  }, [])

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">USX Style Defaults</h3>
        <button className="developer-repo-btn" onClick={handleResetDefaults} title="Reset to defaults">
          <Icon name="restart_alt" size={14} /> Reset
        </button>
      </div>

      {statusMsg && (
        <div style={{
          padding: '8px 12px',
          background: 'rgba(63,185,80,0.15)',
          color: '#3fb950',
          borderRadius: 6,
          fontSize: 12,
        }}>
          {statusMsg}
        </div>
      )}

      {/* Font Size */}
      <div className="developer-settings-section">
        <h4 className="developer-settings-section-title">
          <Icon name="format_size" size={16} /> Font Size
        </h4>
        <div className="hub-settings-fontsize-controls" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {[12, 13, 14, 15, 16, 18, 20, 22, 24].map(size => (
            <button
              key={size}
              className={`hub-settings-fontsize-btn ${settings.fontSize === size ? 'hub-settings-fontsize-btn--active' : ''}`}
              onClick={() => updateSetting('fontSize', size)}
              style={{
                padding: '6px 12px',
                borderRadius: 6,
                border: `1px solid ${settings.fontSize === size ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-border-color, #30363d)'}`,
                background: settings.fontSize === size ? 'rgba(88,166,255,0.15)' : 'var(--pico-card-sectioning-background-color, #1c2128)',
                color: settings.fontSize === size ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-color, #c9d1d9)',
                cursor: 'pointer',
                fontFamily: 'inherit',
                fontSize: `${size}px`,
              }}
            >
              {size}
            </button>
          ))}
        </div>
        <p style={{ color: 'var(--pico-muted-color, #8b949e)', fontSize: 11, margin: '6px 0 0' }}>
          Current: {settings.fontSize}px — applies to Pico base font
        </p>
      </div>

      {/* Font Style */}
      <div className="developer-settings-section">
        <h4 className="developer-settings-section-title">
          <Icon name="text_fields" size={16} /> Font Style
        </h4>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {FONT_STYLE_OPTIONS.map(opt => (
            <button
              key={opt.id}
              onClick={() => handleFontStyleChange(opt.id)}
              style={{
                padding: '10px 14px',
                borderRadius: 8,
                border: `1px solid ${fontStyle === opt.id ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-border-color, #30363d)'}`,
                background: fontStyle === opt.id ? 'rgba(88,166,255,0.1)' : 'var(--pico-card-background-color, #161b22)',
                color: 'var(--pico-color, #c9d1d9)',
                cursor: 'pointer',
                fontFamily: 'inherit',
                textAlign: 'left',
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                flex: 1,
                minWidth: 120,
              }}
            >
              <span style={{ fontWeight: 600, fontSize: 13 }}>{opt.name}</span>
              <span style={{
                fontSize: 16,
                fontFamily: opt.family,
                color: fontStyle === opt.id ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-muted-color, #8b949e)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>
                Aa Bb Cc
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Color Palette */}
      <div className="developer-settings-section">
        <h4 className="developer-settings-section-title">
          <Icon name="palette" size={16} /> Color Palette
        </h4>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {PALETTES.map(p => (
            <button
              key={p.id}
              onClick={() => updateSetting('palette', p.id)}
              style={{
                padding: '8px 12px',
                borderRadius: 8,
                border: `1px solid ${settings.palette === p.id ? p.color : 'var(--pico-border-color, #30363d)'}`,
                background: settings.palette === p.id ? 'rgba(88,166,255,0.08)' : 'var(--pico-card-background-color, #161b22)',
                color: 'var(--pico-color, #c9d1d9)',
                cursor: 'pointer',
                fontFamily: 'inherit',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                flex: 1,
                minWidth: 100,
              }}
            >
              <span style={{
                width: 16,
                height: 16,
                borderRadius: '50%',
                background: p.color,
                border: '1px solid var(--pico-border-color, #30363d)',
                flexShrink: 0,
              }} />
              <span style={{ fontWeight: settings.palette === p.id ? 600 : 400 }}>
                {p.name}
              </span>
              {settings.palette === p.id && (
                <Icon name="check" size={14} style={{ marginLeft: 'auto', color: p.color }} />
              )}
            </button>
          ))}
        </div>
        <p style={{ color: 'var(--pico-muted-color, #8b949e)', fontSize: 11, margin: '6px 0 0' }}>
          Sets data-palette attribute on document root — Pico CSS tokens respect this
        </p>
      </div>

      {/* Preferences toggles */}
      <div className="developer-settings-section">
        <h4 className="developer-settings-section-title">
          <Icon name="toggle_on" size={16} /> Preferences
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {([
            { key: 'autoSave' as const, label: 'Auto-save', onLabel: 'Enabled', offLabel: 'Disabled' },
            { key: 'showStatusBar' as const, label: 'Status Bar', onLabel: 'Visible', offLabel: 'Hidden' },
            { key: 'enableAnimations' as const, label: 'Animations', onLabel: 'On', offLabel: 'Off' },
            { key: 'displayMode' as const, label: 'Display Mode', onLabel: settings.displayMode, offLabel: settings.displayMode },
          ] as const).map(item => (
            <div key={item.key} className="developer-settings-toggle-row">
              <span>{item.label}</span>
              {item.key === 'displayMode' ? (
                <select
                  className="developer-search-input"
                  style={{ width: 'auto', padding: '4px 8px' }}
                  value={settings.displayMode}
                  onChange={e => updateSetting('displayMode', e.target.value as any)}
                >
                  <option value="grid">Grid</option>
                  <option value="list">List</option>
                  <option value="compact">Compact</option>
                </select>
              ) : (
                <label className="hub-toggle" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input
                    type="checkbox"
                    checked={settings[item.key] as boolean}
                    onChange={e => updateSetting(item.key, e.target.checked)}
                    style={{ accentColor: 'var(--pico-primary, #58a6ff)' }}
                  />
                  <span className="hub-settings-mono" style={{ fontSize: 11, color: 'var(--pico-muted-color, #8b949e)' }}>
                    {settings[item.key] ? item.onLabel : item.offLabel}
                  </span>
                </label>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* USX Standard Reference */}
      <div className="developer-settings-section">
        <h4 className="developer-settings-section-title">
          <Icon name="description" size={16} /> USX Standard Reference
        </h4>
        <div style={{ fontSize: 12, color: 'var(--pico-muted-color, #8b949e)', lineHeight: 1.6 }}>
          <p>USX (Unified Style eXtension) is the canonical styling standard for all uCore surfaces.</p>
          <ul style={{ paddingLeft: 16, margin: '4px 0' }}>
            <li>Base tokens: <code>styles/tokens.css</code></li>
            <li>Prose baseline: <code>styles/prose-ui-standard.css</code></li>
            <li>Layout: <code>styles/nestframe.css</code></li>
            <li>Icons: <code>styles/usx/usx-icons.css</code></li>
          </ul>
          <p style={{ marginTop: 8 }}>
            Run the <strong>USX Standard Builder</strong> skill from the Skills tab to audit compliance.
          </p>
        </div>
      </div>
    </div>
  )
}