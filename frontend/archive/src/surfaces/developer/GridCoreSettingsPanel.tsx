/* ═══════════════════════════════════════════════════════════════════
   GridCoreSettingsPanel — GridCore Grid Algebra Configuration
   ═══════════════════════════════════════════════════════════════════
   Configure GridCore embeddable blocks (grid, teletext, terminal).
   Independent from USX styling. Controls cell dimensions, grid density,
   rendering mode, and glyph sets. Accessible only in Developer Surface.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useCallback } from 'react'
import { Icon } from '../../components/Icon'
import { useGridCoreSettings } from '../../hooks/useGridCoreSettings'
import './gridcore-settings.css'

export function GridCoreSettingsPanel() {
  const { settings, isLoaded, updateSetting, resetToDefaults, applyPreset, presets } = useGridCoreSettings()
  const [statusMsg, setStatusMsg] = React.useState<string | null>(null)

  const showStatus = (msg: string) => {
    setStatusMsg(msg)
    setTimeout(() => setStatusMsg(null), 2000)
  }

  const handleResetDefaults = useCallback(() => {
    if (confirm('Reset all GridCore settings to defaults?')) {
      resetToDefaults()
      showStatus('GridCore settings reset to defaults')
    }
  }, [resetToDefaults])

  const handleApplyPreset = useCallback((presetName: keyof typeof presets) => {
    applyPreset(presetName)
    showStatus(`GridCore preset applied: ${presetName}`)
  }, [applyPreset])

  if (!isLoaded) {
    return <div className="developer-panel">Loading GridCore settings...</div>
  }

  return (
    <div className="gridcore-settings-panel">
      {statusMsg && (
        <div style={{
          padding: '10px 14px',
          background: 'rgba(63,185,80,0.15)',
          color: '#3fb950',
          borderRadius: 6,
          fontSize: 12,
          marginBottom: 16,
        }}>
          ✓ {statusMsg}
        </div>
      )}

      {/* Header */}
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">
          <Icon name="grid_view" size={18} />
          GridCore Settings
        </h3>
        <button
          className="developer-repo-btn"
          onClick={handleResetDefaults}
          title="Reset to defaults"
          style={{ marginRight: 8 }}
        >
          <Icon name="restart_alt" size={14} /> Reset
        </button>
      </div>

      {/* Info Box */}
      <div className="gridcore-settings-info">
        <p>
          <strong>🔲 GridCore:</strong> Independent grid algebra system for embeddable teletext, terminal, and grid blocks. Separate from USX styling—configure cell dimensions, grid density, rendering mode, and glyph sets.
        </p>
      </div>

      {/* Presets */}
      <div className="gridcore-settings-section">
        <h4 className="gridcore-settings-section-title">
          <Icon name="dashboard" size={14} />
          Quick Presets
        </h4>
        <div className="gridcore-settings-preset-grid">
          {(Object.keys(presets) as Array<keyof typeof presets>).map(presetName => (
            <button
              key={presetName}
              className="gridcore-settings-preset-btn"
              onClick={() => handleApplyPreset(presetName)}
            >
              <span className="gridcore-settings-preset-name">
                {presetName.charAt(0).toUpperCase() + presetName.slice(1)}
              </span>
              <span className="gridcore-settings-preset-desc">
                {presetName === 'compact' && '8×14px, tight'}
                {presetName === 'normal' && '9×16px, standard'}
                {presetName === 'spacious' && '10×18px, loose'}
                {presetName === 'hd' && '12×20px, high-res'}
                {presetName === 'retro' && '8×16px, classic'}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Cell Dimensions */}
      <div className="gridcore-settings-section">
        <h4 className="gridcore-settings-section-title">
          <Icon name="crop_square" size={14} />
          Cell Dimensions
        </h4>

        <div className="gridcore-settings-field">
          <label>Cell Width: {settings.cellWidth}px</label>
          <div className="gridcore-settings-slider-group">
            <input
              type="range"
              min="6"
              max="20"
              value={settings.cellWidth}
              onChange={e => updateSetting('cellWidth', parseInt(e.target.value))}
              className="gridcore-settings-slider"
            />
          </div>
          <p className="gridcore-settings-help">Pixel width of each grid cell (6–20px)</p>
        </div>

        <div className="gridcore-settings-field">
          <label>Cell Height: {settings.cellHeight}px</label>
          <div className="gridcore-settings-slider-group">
            <input
              type="range"
              min="10"
              max="32"
              value={settings.cellHeight}
              onChange={e => updateSetting('cellHeight', parseInt(e.target.value))}
              className="gridcore-settings-slider"
            />
          </div>
          <p className="gridcore-settings-help">Pixel height of each grid cell (10–32px)</p>
        </div>
      </div>

      {/* Grid Density */}
      <div className="gridcore-settings-section">
        <h4 className="gridcore-settings-section-title">
          <Icon name="density_medium" size={14} />
          Grid Density
        </h4>
        <div className="gridcore-settings-button-group">
          {(['compact', 'normal', 'spacious'] as const).map(density => (
            <button
              key={density}
              className={`gridcore-settings-btn-option ${settings.gridDensity === density ? 'gridcore-settings-btn-option--active' : ''}`}
              onClick={() => updateSetting('gridDensity', density)}
            >
              {density.charAt(0).toUpperCase() + density.slice(1)}
            </button>
          ))}
        </div>
        <p className="gridcore-settings-help">Character map and spacing scaling (affects typography within cells)</p>
      </div>

      {/* Font Family */}
      <div className="gridcore-settings-section">
        <h4 className="gridcore-settings-section-title">
          <Icon name="text_fields" size={14} />
          Font Family
        </h4>
        <div className="gridcore-settings-button-group">
          {(['default', 'monospace-narrow', 'monospace-wide'] as const).map(font => (
            <button
              key={font}
              className={`gridcore-settings-btn-option ${settings.fontFamily === font ? 'gridcore-settings-btn-option--active' : ''}`}
              onClick={() => updateSetting('fontFamily', font)}
            >
              {font === 'monospace-narrow' ? 'Narrow' : font === 'monospace-wide' ? 'Wide' : 'Default'}
            </button>
          ))}
        </div>
        <p className="gridcore-settings-help">Monospace rendering variant</p>
      </div>

      {/* Glyph Set */}
      <div className="gridcore-settings-section">
        <h4 className="gridcore-settings-section-title">
          <Icon name="abc" size={14} />
          Glyph Set
        </h4>
        <div className="gridcore-settings-button-group">
          {(['ascii', 'extended', 'unicode'] as const).map(glyphSet => (
            <button
              key={glyphSet}
              className={`gridcore-settings-btn-option ${settings.glyphSet === glyphSet ? 'gridcore-settings-btn-option--active' : ''}`}
              onClick={() => updateSetting('glyphSet', glyphSet)}
            >
              {glyphSet.charAt(0).toUpperCase() + glyphSet.slice(1)}
            </button>
          ))}
        </div>
        <p className="gridcore-settings-help">Character set: ASCII (basic), Extended (CP-437), Unicode (full)</p>
      </div>

      {/* Render Mode */}
      <div className="gridcore-settings-section">
        <h4 className="gridcore-settings-section-title">
          <Icon name="render" size={14} />
          Render Mode
        </h4>
        <div className="gridcore-settings-button-group">
          {(['canvas', 'dom', 'hybrid'] as const).map(mode => (
            <button
              key={mode}
              className={`gridcore-settings-btn-option ${settings.renderMode === mode ? 'gridcore-settings-btn-option--active' : ''}`}
              onClick={() => updateSetting('renderMode', mode)}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
        <p className="gridcore-settings-help">Canvas (fast, GPU), DOM (accessible), Hybrid (auto-select)</p>
      </div>

      {/* Rendering Options */}
      <div className="gridcore-settings-section">
        <h4 className="gridcore-settings-section-title">
          <Icon name="settings" size={14} />
          Rendering Options
        </h4>

        <div className="gridcore-settings-toggle-row">
          <span>Antialiasing</span>
          <label className="gridcore-settings-toggle">
            <input
              type="checkbox"
              checked={settings.antialias}
              onChange={e => updateSetting('antialias', e.target.checked)}
            />
            <span>{settings.antialias ? 'Enabled' : 'Disabled'}</span>
          </label>
        </div>

        <div className="gridcore-settings-toggle-row">
          <span>Smooth Scroll</span>
          <label className="gridcore-settings-toggle">
            <input
              type="checkbox"
              checked={settings.smoothScroll}
              onChange={e => updateSetting('smoothScroll', e.target.checked)}
            />
            <span>{settings.smoothScroll ? 'Enabled' : 'Disabled'}</span>
          </label>
        </div>

        <div className="gridcore-settings-toggle-row">
          <span>Animations</span>
          <label className="gridcore-settings-toggle">
            <input
              type="checkbox"
              checked={settings.enableAnimations}
              onChange={e => updateSetting('enableAnimations', e.target.checked)}
            />
            <span>{settings.enableAnimations ? 'Enabled' : 'Disabled'}</span>
          </label>
        </div>
      </div>

      {/* Reference Info */}
      <div style={{
        marginTop: 24,
        padding: 12,
        background: 'var(--pico-card-sectioning-background-color, #1c2128)',
        borderRadius: 6,
        borderLeft: '3px solid var(--pico-primary, #58a6ff)',
        fontSize: 12,
        color: 'var(--pico-muted-color, #8b949e)',
        lineHeight: 1.6,
      }}>
        <p style={{ margin: '0 0 8px' }}>
          <strong>📝 References:</strong>
        </p>
        <ul style={{ margin: 0, paddingLeft: 16 }}>
          <li>Grid algebra: <code>surfaces/gridui/grid-algebra/</code></li>
          <li>Character set: <code>surfaces/gridui/grid-algebra/CharacterSet.ts</code></li>
          <li>Grid transform: <code>surfaces/gridui/grid-algebra/GridTransform.ts</code></li>
          <li>Teletext page: <code>surfaces/gridui/grid-algebra/TeletextPage.ts</code></li>
        </ul>
      </div>
    </div>
  )
}

export default GridCoreSettingsPanel
