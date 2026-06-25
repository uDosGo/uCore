/* ═══════════════════════════════════════════════════════════════════
   GlobalSettingsPanel — System-wide Global Switchers
   ═══════════════════════════════════════════════════════════════════
   Final user-facing controls for core display preferences.
   Font Style (3 options), Base Font Size (5 presets), Color Palette
   (4 options with light/dark variants), and Light/Dark Mode.
   
   All advanced USX and GridCore settings are locked in Developer Surface.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'
import { useGlobalSettings, FontStyle, BaseFontSize, ColorPalette, LightDarkMode } from '../../hooks/useGlobalSettings'

const SNACKBAR_API = 'http://localhost:8484'

export default function GlobalSettingsPanel() {
  const { settings, isLoaded, updateSetting, fontStyleConfig, paletteConfig } = useGlobalSettings()
  const [backendConfig, setBackendConfig] = useState<any>(null)

  useEffect(() => {
    // Load backend config for display
    fetch(`${SNACKBAR_API}/api/config`, { signal: AbortSignal.timeout(2500) })
      .then(r => r.json())
      .then(d => setBackendConfig(d))
      .catch(() => {})
  }, [])

  if (!isLoaded) {
    return <div className="hub-settings">Loading settings...</div>
  }

  const systemItems = backendConfig?.system || []
  const installItems = backendConfig?.installation || []

  const fontStyleOptions: FontStyle[] = ['inter', 'merriweather', 'jetbrains-mono']
  const fontSizeOptions: BaseFontSize[] = ['xs', 's', 'm', 'l', 'xl']
  const paletteOptions: ColorPalette[] = ['gh-dark', 'pico-green', 'pico-sunset', 'pico-twilight']
  const modeOptions: LightDarkMode[] = ['light', 'dark']

  return (
    <div className="hub-settings">
      <div className="hub-settings-form">
        {/* Font Style Switcher */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="text_fields" size={16} />
            <h3>Font Style</h3>
          </div>
          <div className="hub-settings-card-body">
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {fontStyleOptions.map(style => {
                const config = fontStyleConfig[style]
                return (
                  <button
                    key={style}
                    className={`hub-settings-toggle-btn ${settings.fontStyle === style ? 'hub-settings-toggle-btn--active' : ''}`}
                    onClick={() => updateSetting('fontStyle', style)}
                    style={{
                      fontFamily: config.cssVar,
                      padding: '10px 16px',
                      borderRadius: 6,
                      border: `2px solid ${settings.fontStyle === style ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-border-color, #30363d)'}`,
                      background: settings.fontStyle === style ? 'rgba(88,166,255,0.1)' : 'transparent',
                      color: 'var(--pico-color, #c9d1d9)',
                      cursor: 'pointer',
                      fontWeight: 500,
                    }}
                  >
                    {config.name}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Base Font Size Switcher */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="format_size" size={16} />
            <h3>Base Font Size</h3>
          </div>
          <div className="hub-settings-card-body">
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {fontSizeOptions.map(size => {
                const labels = { xs: 'XS', s: 'S', m: 'M', l: 'L', xl: 'XL' }
                return (
                  <button
                    key={size}
                    className={`hub-settings-toggle-btn ${settings.baseFontSize === size ? 'hub-settings-toggle-btn--active' : ''}`}
                    onClick={() => updateSetting('baseFontSize', size)}
                    style={{
                      padding: '8px 12px',
                      borderRadius: 6,
                      border: `2px solid ${settings.baseFontSize === size ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-border-color, #30363d)'}`,
                      background: settings.baseFontSize === size ? 'rgba(88,166,255,0.1)' : 'transparent',
                      color: 'var(--pico-color, #c9d1d9)',
                      cursor: 'pointer',
                      fontWeight: 600,
                      minWidth: 44,
                      textAlign: 'center',
                    }}
                  >
                    {labels[size]}
                  </button>
                )
              })}
            </div>
            <p style={{ fontSize: 12, color: 'var(--pico-muted-color, #8b949e)', margin: '8px 0 0' }}>
              Default: M (14px) — Adjusts base typography across all surfaces
            </p>
          </div>
        </div>

        {/* Color Palette & Light/Dark Mode */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="palette" size={16} />
            <h3>Color Palette & Mode</h3>
          </div>
          <div className="hub-settings-card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              {/* Palette Selection */}
              <div>
                <h4 style={{ fontSize: 13, fontWeight: 600, margin: '0 0 12px', color: 'var(--pico-muted-color, #8b949e)' }}>Palette</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {paletteOptions.map(palette => {
                    const config = paletteConfig[palette]
                    return (
                      <button
                        key={palette}
                        onClick={() => updateSetting('colorPalette', palette)}
                        style={{
                          padding: '8px 12px',
                          borderRadius: 6,
                          border: `2px solid ${settings.colorPalette === palette ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-border-color, #30363d)'}`,
                          background: settings.colorPalette === palette ? 'rgba(88,166,255,0.1)' : 'transparent',
                          color: 'var(--pico-color, #c9d1d9)',
                          cursor: 'pointer',
                          textAlign: 'left',
                          fontWeight: settings.colorPalette === palette ? 600 : 400,
                        }}
                      >
                        {config.name}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Light/Dark Mode */}
              <div>
                <h4 style={{ fontSize: 13, fontWeight: 600, margin: '0 0 12px', color: 'var(--pico-muted-color, #8b949e)' }}>Mode</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {modeOptions.map(mode => (
                    <button
                      key={mode}
                      onClick={() => updateSetting('mode', mode)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: 6,
                        border: `2px solid ${settings.mode === mode ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-border-color, #30363d)'}`,
                        background: settings.mode === mode ? 'rgba(88,166,255,0.1)' : 'transparent',
                        color: 'var(--pico-color, #c9d1d9)',
                        cursor: 'pointer',
                        textAlign: 'center',
                        fontWeight: settings.mode === mode ? 600 : 400,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                      }}
                    >
                      <Icon name={mode === 'dark' ? 'dark_mode' : 'light_mode'} size={16} />
                      {mode.charAt(0).toUpperCase() + mode.slice(1)}
                    </button>
                  ))}
                </div>
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

        {/* Developer Settings Info */}
        <div className="hub-settings-card" style={{ background: 'rgba(88,166,255,0.05)', borderLeft: '3px solid var(--pico-primary, #58a6ff)' }}>
          <div className="hub-settings-card-header">
            <Icon name="info" size={16} />
            <h3>Advanced Settings</h3>
          </div>
          <div className="hub-settings-card-body">
            <p style={{ fontSize: 12, color: 'var(--pico-muted-color, #8b949e)', margin: 0, lineHeight: 1.6 }}>
              <strong>USX Settings</strong> (typography scales, spacing, CSS variables) and <strong>GridCore Settings</strong> (grid algebra, cell dimensions) are available in Developer Surface.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
