/* ═══════════════════════════════════════════════════════════════════
   USXSettingsPanel — Developer USX System Configuration
   ═══════════════════════════════════════════════════════════════════
   Advanced USX (Unified Style eXtension) settings for developers.
   Configure typography scales, spacing, colors, CSS variables, and
   export/import custom themes. Locked from Global Settings panel.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useCallback } from 'react'
import { Icon } from '../../components/Icon'
import { useUSXSettings } from '../../hooks/useUSXSettings'
import './usx-settings.css'

type USXSettingsTab = 'typography' | 'colors' | 'variables' | 'stylesheet'

export function USXSettingsPanel() {
  const { settings, isLoaded, updateSetting, updateCSSVariable, resetToDefaults, exportAsCSS, defaultCSSVariables } = useUSXSettings()
  const [activeTab, setActiveTab] = useState<USXSettingsTab>('typography')
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const [expandedVar, setExpandedVar] = useState<string | null>(null)

  const showStatus = (msg: string) => {
    setStatusMsg(msg)
    setTimeout(() => setStatusMsg(null), 2000)
  }

  const handleExportCSS = useCallback(() => {
    const css = exportAsCSS()
    const blob = new Blob([css], { type: 'text/css' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'usx-theme.css'
    a.click()
    URL.revokeObjectURL(url)
    showStatus('Theme exported as CSS')
  }, [exportAsCSS])

  const handleResetDefaults = useCallback(() => {
    if (confirm('Reset all USX settings to defaults? This cannot be undone.')) {
      resetToDefaults()
      showStatus('USX settings reset to defaults')
    }
  }, [resetToDefaults])

  if (!isLoaded) {
    return <div className="developer-panel">Loading USX settings...</div>
  }

  return (
    <div className="usx-settings-panel">
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
          <Icon name="palette" size={18} />
          USX Settings
        </h3>
        <button
          className="developer-repo-btn"
          onClick={handleResetDefaults}
          title="Reset all settings to defaults"
          style={{ marginRight: 8 }}
        >
          <Icon name="restart_alt" size={14} /> Reset
        </button>
        <button
          className="developer-repo-btn"
          onClick={handleExportCSS}
          title="Export theme as CSS file"
        >
          <Icon name="download" size={14} /> Export
        </button>
      </div>

      {/* Info Box */}
      <div className="usx-settings-info">
        <p>
          <strong>💡 USX (Unified Style eXtension):</strong> Configure the global styling system that wraps all UI surfaces and components. These settings are <strong>locked from Global Settings</strong> and only accessible here in Developer mode.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="usx-settings-tabs">
        {(['typography', 'colors', 'variables', 'stylesheet'] as const).map(tab => (
          <button
            key={tab}
            className={`usx-settings-tab-btn ${activeTab === tab ? 'usx-settings-tab-btn--active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'typography' && <Icon name="text_fields" size={14} />}
            {tab === 'colors' && <Icon name="palette" size={14} />}
            {tab === 'variables' && <Icon name="tune" size={14} />}
            {tab === 'stylesheet' && <Icon name="description" size={14} />}
            <span style={{ textTransform: 'capitalize' }}>{tab}</span>
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      <div className="usx-settings-tab-content">
        {/* Typography Tab */}
        {activeTab === 'typography' && (
          <div className="usx-settings-section">
            <h4 className="usx-settings-section-title">Typography Scale</h4>
            <div className="usx-settings-field">
              <label>Scale Multiplier</label>
              <div className="usx-settings-slider-group">
                <input
                  type="range"
                  min="0.8"
                  max="1.2"
                  step="0.05"
                  value={settings.typographyScale}
                  onChange={e => updateSetting('typographyScale', parseFloat(e.target.value))}
                  className="usx-settings-slider"
                />
                <span className="usx-settings-value">{settings.typographyScale.toFixed(2)}x</span>
              </div>
              <p className="usx-settings-help">Scales all typography sizing (0.8–1.2×)</p>
            </div>

            <h4 className="usx-settings-section-title" style={{ marginTop: 24 }}>Line Height</h4>
            <div className="usx-settings-field">
              <label>Line Height Multiplier</label>
              <div className="usx-settings-slider-group">
                <input
                  type="range"
                  min="1.2"
                  max="1.8"
                  step="0.1"
                  value={settings.lineHeightMultiplier}
                  onChange={e => updateSetting('lineHeightMultiplier', parseFloat(e.target.value))}
                  className="usx-settings-slider"
                />
                <span className="usx-settings-value">{settings.lineHeightMultiplier.toFixed(1)}</span>
              </div>
              <p className="usx-settings-help">Controls line height for all text elements (1.2–1.8)</p>
            </div>

            <h4 className="usx-settings-section-title" style={{ marginTop: 24 }}>Spacing Scale</h4>
            <div className="usx-settings-field">
              <label>Spacing Multiplier</label>
              <div className="usx-settings-slider-group">
                <input
                  type="range"
                  min="0.8"
                  max="1.2"
                  step="0.05"
                  value={settings.spacingScale}
                  onChange={e => updateSetting('spacingScale', parseFloat(e.target.value))}
                  className="usx-settings-slider"
                />
                <span className="usx-settings-value">{settings.spacingScale.toFixed(2)}x</span>
              </div>
              <p className="usx-settings-help">Scales all margins and padding (0.8–1.2×)</p>
            </div>
          </div>
        )}

        {/* Colors Tab */}
        {activeTab === 'colors' && (
          <div className="usx-settings-section">
            <h4 className="usx-settings-section-title">Border Radius</h4>
            <div className="usx-settings-button-group">
              {(['sharp', 'rounded', 'smooth'] as const).map(radius => (
                <button
                  key={radius}
                  className={`usx-settings-btn-option ${settings.borderRadius === radius ? 'usx-settings-btn-option--active' : ''}`}
                  onClick={() => updateSetting('borderRadius', radius)}
                >
                  {radius.charAt(0).toUpperCase() + radius.slice(1)}
                </button>
              ))}
            </div>
            <p className="usx-settings-help">Sets border-radius for components: sharp (0px), rounded (4px), smooth (8px)</p>

            <h4 className="usx-settings-section-title" style={{ marginTop: 24 }}>Shadow Depth</h4>
            <div className="usx-settings-button-group">
              {(['none', 'shallow', 'medium', 'deep'] as const).map(depth => (
                <button
                  key={depth}
                  className={`usx-settings-btn-option ${settings.shadowDepth === depth ? 'usx-settings-btn-option--active' : ''}`}
                  onClick={() => updateSetting('shadowDepth', depth)}
                >
                  {depth.charAt(0).toUpperCase() + depth.slice(1)}
                </button>
              ))}
            </div>
            <p className="usx-settings-help">Controls component elevation via drop shadows</p>
          </div>
        )}

        {/* CSS Variables Tab */}
        {activeTab === 'variables' && (
          <div className="usx-settings-section">
            <h4 className="usx-settings-section-title">Color Variables</h4>
            <p className="usx-settings-help">Edit CSS custom properties for USX styling</p>

            <div className="usx-settings-vars-list">
              {Object.entries(settings.customCSSVariables).map(([varName, varValue]) => (
                <div key={varName} className="usx-settings-var-item">
                  <button
                    className="usx-settings-var-toggle"
                    onClick={() => setExpandedVar(expandedVar === varName ? null : varName)}
                  >
                    <Icon name={expandedVar === varName ? 'expand_less' : 'expand_more'} size={16} />
                    <code className="usx-settings-var-name">{varName}</code>
                    <div className="usx-settings-var-preview" style={{ background: varValue }} />
                  </button>

                  {expandedVar === varName && (
                    <div className="usx-settings-var-editor">
                      <input
                        type="text"
                        value={varValue}
                        onChange={e => updateCSSVariable(varName, e.target.value)}
                        className="usx-settings-var-input"
                        placeholder="#000000"
                      />
                      {varValue.startsWith('#') && (
                        <input
                          type="color"
                          value={varValue}
                          onChange={e => updateCSSVariable(varName, e.target.value)}
                          className="usx-settings-var-picker"
                        />
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stylesheet Tab */}
        {activeTab === 'stylesheet' && (
          <div className="usx-settings-section">
            <h4 className="usx-settings-section-title">Generated Stylesheet</h4>
            <p className="usx-settings-help">Current USX theme as CSS `:root` selector. Copy or export to use in other projects.</p>

            <textarea
              className="usx-settings-stylesheet-editor"
              value={exportAsCSS()}
              readOnly
              spellCheck={false}
            />

            <div style={{ fontSize: 12, color: 'var(--pico-muted-color, #8b949e)', marginTop: 12 }}>
              <p>
                <strong>Include in:</strong> Link this CSS file after Pico CSS to override theme variables globally.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Settings Info Footer */}
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
          <strong>📝 Reference:</strong>
        </p>
        <ul style={{ margin: 0, paddingLeft: 16 }}>
          <li>Base tokens: <code>styles/tokens.css</code></li>
          <li>USX baseline: <code>styles/usx/usx-base.css</code></li>
          <li>Layout system: <code>styles/usx/usx-layout-system.css</code></li>
          <li>Typography: <code>styles/usx/usx-typography.css</code></li>
        </ul>
      </div>
    </div>
  )
}

export default USXSettingsPanel
