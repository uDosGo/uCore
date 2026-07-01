/* ═══════════════════════════════════════════════════════════════════
   uSystemSettingsPanel — Developer uSystem Configuration
   ═══════════════════════════════════════════════════════════════════
   Configure uSystem Surface display options, service connections,
   and system capabilities. Independent from USX and GridCore settings.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useCallback } from 'react'
import { Icon } from '../../components/Icon'
import './system-surface-dev.css'

interface uSystemConfig {
  serviceUrl: string
  enableDebugLogs: boolean
  enableMetrics: boolean
  pageRefreshInterval: number
  serviceTimeout: number
  enableAnalytics: boolean
}

export function uSystemSettingsPanel() {
  const [config, setConfig] = useState<uSystemConfig>({
    serviceUrl: 'http://localhost:8484',
    enableDebugLogs: false,
    enableMetrics: true,
    pageRefreshInterval: 5000,
    serviceTimeout: 5000,
    enableAnalytics: true,
  })
  const [statusMsg, setStatusMsg] = useState<string | null>(null)

  const showStatus = (msg: string) => {
    setStatusMsg(msg)
    setTimeout(() => setStatusMsg(null), 2000)
  }

  const handleUpdate = useCallback(<K extends keyof uSystemConfig>(key: K, value: uSystemConfig[K]) => {
    setConfig(prev => ({ ...prev, [key]: value }))
    showStatus(`${key} updated`)
  }, [])

  const handleReset = useCallback(() => {
    setConfig({
      serviceUrl: 'http://localhost:8484',
      enableDebugLogs: false,
      enableMetrics: true,
      pageRefreshInterval: 5000,
      serviceTimeout: 5000,
      enableAnalytics: true,
    })
    showStatus('uSystem settings reset')
  }, [])

  return (
    <div className="usystem-settings-panel">
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

      <div className="developer-panel-header">
        <h3 className="developer-panel-title">
          <Icon name="settings" size={18} />
          uSystem Settings
        </h3>
        <button
          className="developer-repo-btn"
          onClick={handleReset}
          title="Reset to defaults"
        >
          <Icon name="restart_alt" size={14} /> Reset
        </button>
      </div>

      <div className="usystem-settings-info">
        <p>
          <strong>⚙️ uSystem (System Administration Surface):</strong> Configure system pages, services, variables, and fallback behaviors. These settings control the System Surface appearance and behavior, independent from USX styling and GridCore grid algebra.
        </p>
      </div>

      {/* Service Connection */}
      <div className="usystem-settings-section">
        <h4 className="usystem-settings-section-title">
          <Icon name="cloud" size={14} />
          Service Connection
        </h4>
        <div className="usystem-settings-field">
          <label>Backend Service URL</label>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input
              type="text"
              value={config.serviceUrl}
              onChange={e => handleUpdate('serviceUrl', e.target.value)}
              className="developer-search-input"
              style={{ flex: 1 }}
            />
          </div>
          <p className="usystem-settings-help">Service endpoint for system status, config, and fallback pages</p>
        </div>

        <div className="usystem-settings-field">
          <label>Service Timeout (ms)</label>
          <input
            type="number"
            min="1000"
            max="30000"
            step="500"
            value={config.serviceTimeout}
            onChange={e => handleUpdate('serviceTimeout', parseInt(e.target.value))}
            className="developer-search-input"
          />
          <p className="usystem-settings-help">How long to wait for service responses before showing fallback</p>
        </div>
      </div>

      {/* Performance */}
      <div className="usystem-settings-section">
        <h4 className="usystem-settings-section-title">
          <Icon name="speed" size={14} />
          Performance
        </h4>

        <div className="usystem-settings-field">
          <label>Page Refresh Interval (ms)</label>
          <input
            type="number"
            min="1000"
            max="60000"
            step="500"
            value={config.pageRefreshInterval}
            onChange={e => handleUpdate('pageRefreshInterval', parseInt(e.target.value))}
            className="developer-search-input"
          />
          <p className="usystem-settings-help">Auto-refresh system pages and status updates</p>
        </div>
      </div>

      {/* Monitoring & Debug */}
      <div className="usystem-settings-section">
        <h4 className="usystem-settings-section-title">
          <Icon name="monitor_heart" size={14} />
          Monitoring & Debug
        </h4>

        <div className="usystem-settings-toggle-row">
          <span>Debug Logs</span>
          <label className="usystem-settings-toggle">
            <input
              type="checkbox"
              checked={config.enableDebugLogs}
              onChange={e => handleUpdate('enableDebugLogs', e.target.checked)}
            />
            <span>{config.enableDebugLogs ? 'Enabled' : 'Disabled'}</span>
          </label>
        </div>

        <div className="usystem-settings-toggle-row">
          <span>Metrics Collection</span>
          <label className="usystem-settings-toggle">
            <input
              type="checkbox"
              checked={config.enableMetrics}
              onChange={e => handleUpdate('enableMetrics', e.target.checked)}
            />
            <span>{config.enableMetrics ? 'Enabled' : 'Disabled'}</span>
          </label>
        </div>

        <div className="usystem-settings-toggle-row">
          <span>Analytics</span>
          <label className="usystem-settings-toggle">
            <input
              type="checkbox"
              checked={config.enableAnalytics}
              onChange={e => handleUpdate('enableAnalytics', e.target.checked)}
            />
            <span>{config.enableAnalytics ? 'Enabled' : 'Disabled'}</span>
          </label>
        </div>
      </div>

      {/* Info */}
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
          <strong>📝 Related Settings:</strong>
        </p>
        <ul style={{ margin: 0, paddingLeft: 16 }}>
          <li>USX Settings: Configure typography and styling</li>
          <li>GridCore Settings: Configure grid algebra and cell dimensions</li>
          <li>Global Settings: Final user-facing switchers</li>
        </ul>
      </div>
    </div>
  )
}

export default uSystemSettingsPanel
