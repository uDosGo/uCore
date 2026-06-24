/* ═══════════════════════════════════════════════════════════════════
   GlobalSettingsPanel — System-wide global settings
   Display, font, palette, auto-save, toggles.
   Persists to localStorage and optionally syncs to backend.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { Icon } from '../../components/Icon'

const SNACKBAR_API = 'http://localhost:8484'

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

function loadSettings(): GlobalSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch { /* ignore */ }
  return { ...DEFAULT_SETTINGS }
}

function saveSettings(settings: GlobalSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  // Apply palette attribute (scoped, doesn't break Pico cascade)
  document.documentElement.setAttribute('data-palette', settings.palette)
  // NOTE: Font size is stored in localStorage for future use but NOT applied
  // as a CSS override to avoid breaking Pico's cascade. Apply it only via
  // data-attribute if needed for per-component theming.
}

export default function GlobalSettingsPanel() {
  const [settings, setSettings] = useState<GlobalSettings>(DEFAULT_SETTINGS)
  const [backendConfig, setBackendConfig] = useState<any>(null)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)

  useEffect(() => {
    const loaded = loadSettings()
    setSettings(loaded)
    saveSettings(loaded) // ensure CSS props applied

    // Load backend config for display
    fetch(`${SNACKBAR_API}/api/config`, { signal: AbortSignal.timeout(2500) })
      .then(r => r.json())
      .then(d => setBackendConfig(d))
      .catch(() => {})
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

  const palettes = [
    { id: 'default', name: 'Default', color: '#58a6ff' },
    { id: 'green', name: 'Forest', color: '#22c55e' },
    { id: 'orange', name: 'Sunset', color: '#f0883e' },
    { id: 'purple', name: 'Twilight', color: '#a855f7' },
    { id: 'cyan', name: 'Neon', color: '#00ff9d' },
  ]

  const systemItems = backendConfig?.system || []
  const installItems = backendConfig?.installation || []

  return (
    <div className="hub-settings">
      {statusMsg && (
        <div className="sys-msg sys-msg--success">{statusMsg}</div>
      )}

      <div className="hub-settings-form">
        {/* Display Mode */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="grid_view" size={16} />
            <h3>Display Mode</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-display-modes">
              {(['grid', 'list', 'compact'] as const).map(mode => (
                <button
                  key={mode}
                  className={`hub-settings-display-btn ${settings.displayMode === mode ? 'hub-settings-display-btn--active' : ''}`}
                  onClick={() => updateSetting('displayMode', mode)}
                >
                  <div className="hub-settings-display-label">{mode.charAt(0).toUpperCase() + mode.slice(1)}</div>
                  <div className="hub-settings-display-desc">
                    {mode === 'grid' ? 'Card grid layout' : mode === 'list' ? 'Compact list' : 'Minimal cards'}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Font Size */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="format_size" size={16} />
            <h3>Font Size</h3>
            <span className="hub-settings-card-subtitle">{settings.fontSize}px</span>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-fontsize-controls">
              {[12, 13, 14, 15, 16, 18, 20, 22, 24].map(size => (
                <button
                  key={size}
                  className={`hub-settings-fontsize-btn ${settings.fontSize === size ? 'hub-settings-fontsize-btn--active' : ''}`}
                  onClick={() => updateSetting('fontSize', size)}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Color Palette */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="palette" size={16} />
            <h3>Color Palette</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-palettes">
              {palettes.map(p => (
                <button
                  key={p.id}
                  className={`hub-settings-palette-btn ${settings.palette === p.id ? 'hub-settings-palette-btn--active' : ''}`}
                  onClick={() => updateSetting('palette', p.id)}
                >
                  <span className="hub-settings-palette-swatch" style={{ background: p.color }} />
                  <span className="hub-settings-palette-name">{p.name}</span>
                  {settings.palette === p.id && <Icon name="check" size={16} />}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Toggles */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="toggle_on" size={16} />
            <h3>Preferences</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-connections">
              <div className="hub-settings-connection-row">
                <span>Auto-save</span>
                <label className="hub-toggle">
                  <input
                    type="checkbox"
                    checked={settings.autoSave}
                    onChange={e => updateSetting('autoSave', e.target.checked)}
                    style={{ accentColor: 'var(--pico-primary, #58a6ff)' }}
                  />
                  <span className="hub-settings-mono">{settings.autoSave ? 'Enabled' : 'Disabled'}</span>
                </label>
              </div>
              <div className="hub-settings-connection-row">
                <span>Status Bar</span>
                <label className="hub-toggle">
                  <input
                    type="checkbox"
                    checked={settings.showStatusBar}
                    onChange={e => updateSetting('showStatusBar', e.target.checked)}
                    style={{ accentColor: 'var(--pico-primary, #58a6ff)' }}
                  />
                  <span className="hub-settings-mono">{settings.showStatusBar ? 'Visible' : 'Hidden'}</span>
                </label>
              </div>
              <div className="hub-settings-connection-row">
                <span>Animations</span>
                <label className="hub-toggle">
                  <input
                    type="checkbox"
                    checked={settings.enableAnimations}
                    onChange={e => updateSetting('enableAnimations', e.target.checked)}
                    style={{ accentColor: 'var(--pico-primary, #58a6ff)' }}
                  />
                  <span className="hub-settings-mono">{settings.enableAnimations ? 'On' : 'Off'}</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* System Configuration (read-only from backend) */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="tune" size={16} />
            <h3>System Configuration</h3>
            <span className="hub-settings-card-subtitle">Backend /api/config</span>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-connections">
              {systemItems.map((item: any) => (
                <div key={item.label} className="hub-settings-connection-row">
                  <span>{item.label}</span>
                  <span className="hub-settings-mono">
                    {item.masked ? '••••••' : item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Installation Info (read-only) */}
        {installItems.length > 0 && (
          <div className="hub-settings-card">
            <div className="hub-settings-card-header">
              <Icon name="computer" size={16} />
              <h3>Installation</h3>
              <span className="hub-settings-card-subtitle">Environment</span>
            </div>
            <div className="hub-settings-card-body">
              <div className="hub-settings-connections">
                {installItems.map((item: any) => (
                  <div key={item.label} className="hub-settings-connection-row">
                    <span>{item.label}</span>
                    <span className="hub-settings-mono">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}