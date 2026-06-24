/* ═══════════════════════════════════════════════════════════════════
   UserSettingsPanel — Per-user preferences and workspace settings
   ═══════════════════════════════════════════════════════════════════
   Separate from Global Settings (system-wide).
   Includes: theme, workspace/repo paths, vault paths (from backend),
   sidebar, language, shortcuts.
   Persists to localStorage under a user-specific key.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { Icon } from '../../components/Icon'

const SNACKBAR_API = 'http://localhost:8484'
const SETTINGS_KEY = 'ucore-user-settings'

interface UserSettings {
  themeMode: 'dark' | 'light' | 'auto'
  workspacePath: string
  repoHome: string
  sidebarWidth: number
  showHiddenFiles: boolean
  compactMode: boolean
  language: string
  customShortcuts: Record<string, string>
  vaultPaths: Record<string, string>
}

const DEFAULT_SETTINGS: UserSettings = {
  themeMode: 'dark',
  workspacePath: '~/Code',
  repoHome: '~/Code',
  sidebarWidth: 260,
  showHiddenFiles: false,
  compactMode: false,
  language: 'en',
  customShortcuts: {
    'open-palette': 'cmd+k',
    'toggle-sidebar': 'cmd+b',
    'search': 'cmd+shift+f',
  },
  vaultPaths: {
    'Global Vault': '~/Vault',
    'Public Vault': '~/Vault/Public',
    'Shared Vault': '~/Vault/Shared',
  },
}

function loadSettings(): UserSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch { /* ignore */ }
  return { ...DEFAULT_SETTINGS }
}

function saveSettings(settings: UserSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  document.documentElement.setAttribute('data-theme', settings.themeMode)
}

export default function UserSettingsPanel() {
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const [vaultSources, setVaultSources] = useState<Array<{ name: string; local_path: string; file_count: number; tags: string[] }>>([])

  useEffect(() => {
    const loaded = loadSettings()
    setSettings(loaded)
    saveSettings(loaded)

    // Fetch vault sources from backend
    fetch(`${SNACKBAR_API}/api/knowledge/status`, { signal: AbortSignal.timeout(2500) })
      .then(r => r.json())
      .then(data => {
        if (data?.sources) setVaultSources(data.sources)
      })
      .catch(() => {})
  }, [])

  const updateSetting = useCallback(<K extends keyof UserSettings>(
    key: K, value: UserSettings[K]
  ) => {
    setSettings(prev => {
      const next = { ...prev, [key]: value }
      saveSettings(next)
      return next
    })
    setStatusMsg(`Updated ${key}`)
    setTimeout(() => setStatusMsg(null), 2000)
  }, [])

  const updateVaultPath = useCallback((vaultName: string, path: string) => {
    setSettings(prev => {
      const next = { ...prev, vaultPaths: { ...prev.vaultPaths, [vaultName]: path } }
      saveSettings(next)
      return next
    })
    setStatusMsg(`Updated ${vaultName} path`)
    setTimeout(() => setStatusMsg(null), 2000)
  }, [])

  const languages = [
    { value: 'en', label: 'English' },
    { value: 'ja', label: 'Japanese' },
    { value: 'zh', label: 'Chinese' },
    { value: 'ko', label: 'Korean' },
    { value: 'de', label: 'German' },
  ]

  return (
    <div className="hub-settings">
      {statusMsg && (
        <div className="sys-msg sys-msg--success" style={{ marginBottom: '12px' }}>{statusMsg}</div>
      )}

      <div className="hub-settings-form">
        {/* Theme Mode */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="dark_mode" size={16} />
            <h3>Theme Mode</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-display-modes">
              {(['dark', 'light', 'auto'] as const).map(mode => (
                <button
                  key={mode}
                  className={`hub-settings-display-btn ${settings.themeMode === mode ? 'hub-settings-display-btn--active' : ''}`}
                  onClick={() => updateSetting('themeMode', mode)}
                >
                  <Icon name={mode === 'dark' ? 'dark_mode' : mode === 'light' ? 'light_mode' : 'brightness_auto'} size={16} />
                  <div className="hub-settings-display-label">{mode.charAt(0).toUpperCase() + mode.slice(1)}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Workspace: Repo Home */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="folder" size={16} />
            <h3>Workspace Settings</h3>
            <span className="hub-settings-card-subtitle">Repo Home & Paths</span>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-connections">
              <div className="hub-settings-connection-row">
                <span>Workspace Path</span>
                <input
                  type="text"
                  value={settings.workspacePath}
                  onChange={e => updateSetting('workspacePath', e.target.value)}
                  className="hub-user-input"
                  style={{ width: '200px' }}
                />
              </div>
              <div className="hub-settings-connection-row">
                <span>Repo Home</span>
                <input
                  type="text"
                  value={settings.repoHome}
                  onChange={e => updateSetting('repoHome', e.target.value)}
                  className="hub-user-input"
                  style={{ width: '200px' }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Vault Settings — from backend knowledge/status */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="folder_sync" size={16} />
            <h3>Vault Settings</h3>
            <span className="hub-settings-card-subtitle">AppFlowy vault locations</span>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-connections">
              {vaultSources.length > 0 ? vaultSources.map(vs => (
                <div key={vs.name} className="hub-settings-connection-row">
                  <div>
                    <span>{vs.name}</span>
                    <br />
                    <small style={{ color: 'var(--pico-muted-color)' }}>
                      {vs.file_count} files · {vs.tags.join(', ')}
                    </small>
                  </div>
                  <input
                    type="text"
                    value={settings.vaultPaths[vs.name] || vs.local_path}
                    onChange={e => updateVaultPath(vs.name, e.target.value)}
                    className="hub-user-input"
                    style={{ width: '200px' }}
                  />
                </div>
              )) : (
                <div className="hub-settings-connection-row">
                  <span>Vault sources</span>
                  <span className="hub-settings-mono">
                    {['Global Vault', 'Public Vault', 'Shared Vault'].map(name => (
                      <div key={name} style={{ marginBottom: '4px' }}>
                        <small>{name}: </small>
                        <input
                          type="text"
                          value={settings.vaultPaths[name] || ''}
                          onChange={e => updateVaultPath(name, e.target.value)}
                          className="hub-user-input"
                          style={{ width: '180px' }}
                        />
                      </div>
                    ))}
                  </span>
                </div>
              )}
              <div className="hub-settings-connection-row">
                <span>AppFlowy status</span>
                <span className="hub-settings-mono">
                  {vaultSources.length > 0 ? `${vaultSources.length} source(s) configured` : 'Backend unavailable — using local defaults'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Width */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="vertical_split" size={16} />
            <h3>Sidebar Width</h3>
            <span className="hub-settings-card-subtitle">{settings.sidebarWidth}px</span>
          </div>
          <div className="hub-settings-card-body">
            <input
              type="range"
              min="180"
              max="400"
              step="10"
              value={settings.sidebarWidth}
              onChange={e => updateSetting('sidebarWidth', parseInt(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Workspace Preferences */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="toggle_on" size={16} />
            <h3>Workspace Preferences</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-connections">
              <div className="hub-settings-connection-row">
                <span>Show Hidden Files</span>
                <label className="hub-toggle">
                  <input
                    type="checkbox"
                    checked={settings.showHiddenFiles}
                    onChange={e => updateSetting('showHiddenFiles', e.target.checked)}
                    style={{ accentColor: 'var(--pico-primary, #58a6ff)' }}
                  />
                  <span className="hub-settings-mono">{settings.showHiddenFiles ? 'Visible' : 'Hidden'}</span>
                </label>
              </div>
              <div className="hub-settings-connection-row">
                <span>Compact Mode</span>
                <label className="hub-toggle">
                  <input
                    type="checkbox"
                    checked={settings.compactMode}
                    onChange={e => updateSetting('compactMode', e.target.checked)}
                    style={{ accentColor: 'var(--pico-primary, #58a6ff)' }}
                  />
                  <span className="hub-settings-mono">{settings.compactMode ? 'On' : 'Off'}</span>
                </label>
              </div>
              <div className="hub-settings-connection-row">
                <span>Language</span>
                <select
                  value={settings.language}
                  onChange={e => updateSetting('language', e.target.value)}
                  className="hub-user-select"
                >
                  {languages.map(l => (
                    <option key={l.value} value={l.value}>{l.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Keyboard Shortcuts */}
        <div className="hub-settings-card">
          <div className="hub-settings-card-header">
            <Icon name="keyboard" size={16} />
            <h3>Keyboard Shortcuts</h3>
          </div>
          <div className="hub-settings-card-body">
            <div className="hub-settings-connections">
              {Object.entries(settings.customShortcuts).map(([action, key]) => (
                <div key={action} className="hub-settings-connection-row">
                  <span style={{ textTransform: 'capitalize' }}>{action.replace(/-/g, ' ')}</span>
                  <code className="hub-settings-mono" style={{
                    padding: '2px 8px',
                    background: 'var(--pico-card-sectioning-background-color)',
                    borderRadius: '4px',
                  }}>
                    {key}
                  </code>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}