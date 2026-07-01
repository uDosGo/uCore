/* ═══════════════════════════════════════════════════════════════════
   TypographySettingsPanel — Developer Surface Font Settings
   ═══════════════════════════════════════════════════════════════════
   Font family and size controls for the Global USX system.
   Stores in localStorage and applies via CSS variables to html root.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { Icon } from '../../components/Icon'
import './typography-settings.css'

interface TypographySettings {
  fontFamily: 'inter' | 'merriweather' | 'jetbrains-mono'
  fontSize: number
}

const SETTINGS_KEY = 'ucore-typography-settings'

const FONT_FAMILIES = [
  { id: 'inter', name: 'Inter', description: 'Modern sans-serif', cssVar: 'Inter, system-ui, -apple-system, sans-serif' },
  { id: 'merriweather', name: 'Merriweather', description: 'Editorial serif', cssVar: 'Merriweather, Georgia, serif' },
  { id: 'jetbrains-mono', name: 'JetBrains Mono', description: 'Monospace code', cssVar: '"JetBrains Mono", "SF Mono", monospace' },
] as const

const DEFAULT_SETTINGS: TypographySettings = {
  fontFamily: 'inter',
  fontSize: 14,
}

function loadSettings(): TypographySettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        fontFamily: (parsed.fontFamily || DEFAULT_SETTINGS.fontFamily) as TypographySettings['fontFamily'],
        fontSize: Number(parsed.fontSize) || DEFAULT_SETTINGS.fontSize,
      }
    }
  } catch { /* ignore */ }
  return { ...DEFAULT_SETTINGS }
}

function saveSettings(settings: TypographySettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  applyTypographySettings(settings)
}

function applyTypographySettings(settings: TypographySettings) {
  const fontFamily = FONT_FAMILIES.find(f => f.id === settings.fontFamily)
  if (fontFamily) {
    document.documentElement.style.setProperty('--usx-font-family-override', fontFamily.cssVar)
  }
  document.documentElement.style.setProperty('--usx-font-size-override', `${settings.fontSize}px`)
  document.documentElement.setAttribute('data-typography-family', settings.fontFamily)
}

export function TypographySettingsPanel() {
  const [settings, setSettings] = useState<TypographySettings>(DEFAULT_SETTINGS)
  const [previewText, setPreviewText] = useState('The quick brown fox jumps over the lazy dog. 1234567890 @#$%^&*()')

  // Load and apply settings on mount
  useEffect(() => {
    const loaded = loadSettings()
    setSettings(loaded)
    applyTypographySettings(loaded)
    console.log('📝 Typography settings loaded:', loaded)
  }, [])

  // Apply settings whenever they change
  useEffect(() => {
    applyTypographySettings(settings)
    console.log('🎨 Typography applied:', settings)
  }, [settings])

  const updateSetting = useCallback(<K extends keyof TypographySettings>(key: K, value: TypographySettings[K]) => {
    setSettings(prev => {
      const next = { ...prev, [key]: value }
      saveSettings(next)
      return next
    })
  }, [])

  const fontFamily = FONT_FAMILIES.find(f => f.id === settings.fontFamily)

  return (
    <div className="developer-settings-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">
          <Icon name="format_size" size={18} />
          Typography Settings
        </h3>
        <span className="developer-panel-count">Global Font Control</span>
      </div>

      <div className="developer-settings-section">
        {/* Font Family Selector */}
        <h4 className="developer-settings-section-title">
          <Icon name="text_fields" size={16} />
          Font Family
        </h4>
        <div className="typography-family-grid">
          {FONT_FAMILIES.map(f => (
            <button
              key={f.id}
              className={`typography-family-btn ${settings.fontFamily === f.id ? 'typography-family-btn--active' : ''}`}
              onClick={() => updateSetting('fontFamily', f.id as any)}
              style={{
                fontFamily: f.cssVar,
                fontWeight: f.id === 'merriweather' ? 'normal' : 500,
              }}
              title={f.description}
            >
              <div className="typography-family-name">{f.name}</div>
              <div className="typography-family-desc">{f.description}</div>
            </button>
          ))}
        </div>

        {/* Font Size Slider & Presets */}
        <h4 className="developer-settings-section-title" style={{ marginTop: '24px' }}>
          <Icon name="zoom_in" size={16} />
          Font Size: <strong>{settings.fontSize}px</strong>
        </h4>
        <div className="typography-fontsize-presets">
          {[12, 13, 14, 15, 16, 18, 20].map(size => (
            <button
              key={size}
              className={`typography-fontsize-preset-btn ${settings.fontSize === size ? 'typography-fontsize-preset-btn--active' : ''}`}
              onClick={() => updateSetting('fontSize', size)}
              style={{ fontSize: `${size * 0.85}px` }}
            >
              {size}px
            </button>
          ))}
        </div>

        {/* Slider */}
        <div className="typography-fontsize-slider-container">
          <input
            type="range"
            min="10"
            max="24"
            step="1"
            value={settings.fontSize}
            onChange={e => updateSetting('fontSize', parseInt(e.target.value))}
            className="typography-fontsize-slider"
          />
          <div className="typography-fontsize-labels">
            <span>10px</span>
            <span>24px</span>
          </div>
        </div>
      </div>

      {/* Live Preview */}
      <div className="developer-settings-section" style={{ marginTop: '32px' }}>
        <h4 className="developer-settings-section-title">
          <Icon name="preview" size={16} />
          Live Preview
        </h4>
        <div
          className="typography-preview-box"
          style={{
            fontFamily: fontFamily?.cssVar || 'inherit',
            fontSize: `${settings.fontSize}px`,
          }}
        >
          <div className="typography-preview-text">{previewText}</div>
          <input
            type="text"
            className="typography-preview-input"
            value={previewText}
            onChange={e => setPreviewText(e.target.value)}
            placeholder="Edit preview text..."
            style={{
              fontFamily: fontFamily?.cssVar || 'inherit',
              fontSize: `${settings.fontSize}px`,
            }}
          />
        </div>
      </div>

      {/* Info */}
      <div className="developer-settings-section" style={{ marginTop: '24px', padding: '12px', background: 'var(--pico-card-background-color, #161b22)', borderRadius: '4px', borderLeft: '3px solid var(--pico-primary, #58a6ff)' }}>
        <p style={{ margin: 0, fontSize: '0.9em', lineHeight: '1.5', color: 'var(--pico-muted-color, #8b949e)' }}>
          <strong>💡 Tip:</strong> These settings apply globally across all USX surfaces. Changes are saved to your browser's local storage and persist across sessions.
        </p>
      </div>
    </div>
  )
}

export default TypographySettingsPanel
