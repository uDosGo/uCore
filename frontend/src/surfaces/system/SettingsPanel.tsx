/* ═══════════════════════════════════════════════════════════════════
   SettingsPanel — Global settings view (Display, Font, Palette, etc.)
   ═══════════════════════════════════════════════════════════════════
   Extracted from UIHubManager to live as a tab in USystemSurface.
   The gear icon in GlobalToolbar navigates to /system?tab=settings.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'

const SNACKBAR_API = 'http://localhost:8484'

// ─── AIModelsStatus (extracted from UIHubManager) ──────────────────
function AIModelsStatus() {
  const [ollamaStatus, setOllamaStatus] = useState<'checking' | 'running' | 'stopped'>('checking')
  const [models, setModels] = useState<string[]>([])
  const [providers, setProviders] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchData() {
      // Check Ollama directly
      try {
        const res = await fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(2000) })
        if (res.ok) {
          const data = await res.json()
          if (!cancelled) {
            setOllamaStatus('running')
            setModels((data.models || []).map((m: any) => m.name))
          }
        } else {
          if (!cancelled) setOllamaStatus('stopped')
        }
      } catch {
        if (!cancelled) setOllamaStatus('stopped')
      }

      // Fetch providers from Snackbar
      try {
        const res = await fetch(`${SNACKBAR_API}/api/providers`, { signal: AbortSignal.timeout(2000) })
        if (res.ok) {
          const data = await res.json()
          if (!cancelled) setProviders(data.providers || [])
        }
      } catch { /* ignore */ }
    }

    fetchData()
    return () => { cancelled = true }
  }, [])

  const statusIcon = ollamaStatus === 'running' ? 'check_circle' : ollamaStatus === 'checking' ? 'sync' : 'radio_button_unchecked'
  const statusColor = ollamaStatus === 'running' ? 'var(--pico-ins-color, #3fb950)' : ollamaStatus === 'checking' ? 'var(--pico-muted-color, #8b949e)' : 'var(--pico-del-color, #f85149)'
  const statusLabel = ollamaStatus === 'running' ? 'Running' : ollamaStatus === 'checking' ? 'Checking...' : 'Stopped'

  return (
    <div className="hub-settings-connections">
      {/* Ollama Status */}
      <div className="hub-settings-connection-row">
        <span>Ollama</span>
        <span className="hub-settings-mono" style={{ color: statusColor }}>
          <Icon name={statusIcon} size={14} /> {statusLabel}
        </span>
      </div>

      {/* Available Models */}
      <div className="hub-settings-connection-row" style={{ alignItems: 'flex-start' }}>
        <span>Models</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
          {models.length > 0 ? models.map(m => (
            <span key={m} className="hub-settings-mono" style={{ fontSize: 12 }}>{m}</span>
          )) : (
            <span className="hub-settings-mono" style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
              {ollamaStatus === 'running' ? 'No models installed' : '—'}
            </span>
          )}
        </div>
      </div>

      {/* Providers */}
      <div className="hub-settings-connection-row" style={{ alignItems: 'flex-start' }}>
        <span>Providers</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
          {providers.length > 0 ? providers.map((p: any, idx: number) => (
            <span key={p.name || p.type || idx} className="hub-settings-mono" style={{ fontSize: 12 }}>
              {p.name || p.type || String(p)}
            </span>
          )) : (
            <span className="hub-settings-mono" style={{ color: 'var(--pico-muted-color, #8b949e)' }}>—</span>
          )}
        </div>
      </div>

      {error && (
        <div className="hub-settings-connection-row">
          <span className="hub-settings-mono" style={{ color: 'var(--pico-del-color, #f85149)', fontSize: 12 }}>{error}</span>
        </div>
      )}
    </div>
  )
}

// ─── Settings Panel ────────────────────────────────────────────────
export function SettingsPanel() {
  const [fontSize, setFontSize] = useState(14)
  const [displayMode, setDisplayMode] = useState<'grid' | 'list' | 'compact'>('grid')

  const [palette, setPalette] = useState('default')

  const palettes = [
    { id: 'default', name: 'Default', color: '#58a6ff' },
    { id: 'green', name: 'Forest', color: '#22c55e' },
    { id: 'orange', name: 'Sunset', color: '#f0883e' },
    { id: 'purple', name: 'Twilight', color: '#a855f7' },
  ]

  return (
    <div className="hub-settings">
      <div className="hub-settings-form">
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
                  className={`hub-settings-display-btn ${displayMode === mode ? 'hub-settings-display-btn--active' : ''}`}
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

        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="format_size" size={16} />
            <h3>Font Size</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-fontsize-controls">
              {[12, 13, 14, 15, 16, 18, 20].map(size => (
                <button
                  key={size}
                  className={`hub-settings-fontsize-btn ${fontSize === size ? 'hub-settings-fontsize-btn--active' : ''}`}
                  onClick={() => setFontSize(size)}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
        </div>

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
                  className={`hub-settings-palette-btn ${palette === p.id ? 'hub-settings-palette-btn--active' : ''}`}
                  onClick={() => setPalette(p.id)}
                >
                  <span className="hub-settings-palette-swatch" style={{ background: p.color }} />
                  <span className="hub-settings-palette-name">{p.name}</span>
                  {palette === p.id && <Icon name="check" size={16} />}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="person" size={16} />
            <h3>User Settings</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-connections">
              <div className="hub-settings-connection-row">
                <span>Username</span>
                <span className="hub-settings-mono">fredbook</span>
              </div>
              <div className="hub-settings-connection-row">
                <span>Email</span>
                <span className="hub-settings-mono">fred@okagent.digital</span>
              </div>
              <div className="hub-settings-connection-row">
                <span>GitHub Token</span>
                <span className="hub-settings-mono">••••••••••••••••</span>
              </div>
              <div className="hub-settings-connection-row">
                <span>SSH Key</span>
                <span className="hub-settings-mono">ed25519 (active)</span>
              </div>
            </div>
          </div>
        </div>

        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="tune" size={16} />
            <h3>General Settings</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-connections">
              <div className="hub-settings-connection-row">
                <span>Language</span>
                <span className="hub-settings-mono">English (US)</span>
              </div>
              <div className="hub-settings-connection-row">
                <span>Timezone</span>
                <span className="hub-settings-mono">Australia/Brisbane (UTC+10)</span>
              </div>
              <div className="hub-settings-connection-row">
                <span>Theme</span>
                <span className="hub-settings-mono">Dark (USX)</span>
              </div>
              <div className="hub-settings-connection-row">
                <span>Auto-save</span>
                <span className="hub-settings-mono">Enabled</span>
              </div>
            </div>
          </div>
        </div>

        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="dns" size={16} />
            <h3>uServer Connections</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-connections">
              <div className="hub-settings-connection-row">
                <span>uServer Host</span>
                <span className="hub-settings-mono">192.168.20.11</span>
              </div>
              <div className="hub-settings-connection-row">
                <span>Snackbar Port</span>
                <span className="hub-settings-mono">8484</span>
              </div>
              <div className="hub-settings-connection-row">
                <span>Secret Server</span>
                <span className="hub-settings-mono">:30001</span>
              </div>
              <div className="hub-settings-connection-row">
                <span>Hivemind</span>
                <span className="hub-settings-mono">:8485</span>
              </div>
            </div>
          </div>
        </div>

        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="smart_toy" size={16} />
            <h3>AI Models</h3>
            <span className="hub-settings-card-subtitle">Ollama status & available models</span>
          </div>
          <div className="hub-settings-card-body">
            <AIModelsStatus />
          </div>
        </div>

        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="build" size={16} />
            <h3>System Administration</h3>
            <span className="hub-settings-card-subtitle">Pages, tools, and system controls</span>
          </div>
          <div className="hub-settings-card-body">
            <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--pico-muted-color, #8b949e)', lineHeight: '1.5' }}>
              Browse system pages (S100-S899), tools, and administrative controls.
            </p>
            <a href="/system-tools?tab=pages" className="hub-settings-system-link" style={{ display: 'inline-block', padding: '8px 16px', background: '#79c0ff', color: 'white', borderRadius: '4px', textDecoration: 'none', fontWeight: 500, fontSize: '14px' }}>
              <Icon name="build" size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
              Open System Tools
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
