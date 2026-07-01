/* ═══════════════════════════════════════════════════════════════════
   VariablesPanel — Variable Store
   ═══════════════════════════════════════════════════════════════════
   Sub-tabs: User (profile), Global (system), Custom (key/value).
   Secrets are now in dedicated Secrets tab (/system?tab=secrets).
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { Icon } from '../../components/Icon'

const SNACKBAR_API = 'http://localhost:8484'

interface UserVariables {
  username: string
  role: string
  location: string
  timezone: string
  uid: string
  email?: string
  [key: string]: string | undefined
}

interface InstallVariables {
  hostname: string
  platform: string
  platform_release: string
  platform_version: string
  architecture: string
  processor: string
  python_version: string
  install_date: string
  udos_root: string
  [key: string]: string
}

type VariableScope = 'user' | 'system' | 'custom'

const USER_VAR_DEFS: Record<string, { label: string; description: string; icon: string }> = {
  username: { label: 'Username', description: 'System user account name', icon: 'person' },
  role: { label: 'Role', description: 'User role (developer, admin, etc.)', icon: 'badge' },
  location: { label: 'Location', description: 'Geographic location / timezone region', icon: 'location_on' },
  timezone: { label: 'Timezone', description: 'System timezone', icon: 'schedule' },
  uid: { label: 'Unique ID', description: 'Unique user identifier (UIUD-... format)', icon: 'fingerprint' },
  email: { label: 'Email', description: 'User email address', icon: 'mail' },
}

export default function VariablesPanel() {
  const [userVars, setUserVars] = useState<UserVariables | null>(null)
  const [installVars, setInstallVars] = useState<InstallVariables | null>(null)
  const [customVars, setCustomVars] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [editing, setEditing] = useState<UserVariables>({} as UserVariables)
  const [editMode, setEditMode] = useState(false)
  const [activeScope, setActiveScope] = useState<VariableScope>('user')

  const [newCustomKey, setNewCustomKey] = useState('')
  const [newCustomValue, setNewCustomValue] = useState('')

  const showStatus = useCallback((type: 'success' | 'error', text: string) => {
    setStatusMsg({ type, text })
    setTimeout(() => setStatusMsg(null), 3000)
  }, [])

  const fetchVariables = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/variables`, { signal: AbortSignal.timeout(3000) })
      if (res.ok) {
        const data = await res.json()
        setUserVars(data.user || {})
        setInstallVars(data.installation || {})
        setEditing((data.user || {}) as UserVariables)
        try {
          const raw = localStorage.getItem('ucore-custom-vars')
          if (raw) setCustomVars(JSON.parse(raw))
        } catch { /* ignore */ }
      } else {
        showStatus('error', 'Failed to fetch variables')
      }
    } catch {
      showStatus('error', 'Network error — snackbar unreachable')
    } finally {
      setLoading(false)
    }
  }, [showStatus])

  useEffect(() => { void fetchVariables() }, [fetchVariables])

  const handleSaveUserVars = async () => {
    if (!editing) return
    try {
      const res = await fetch(`${SNACKBAR_API}/api/variables/user`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editing),
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        showStatus('success', 'User variables saved')
        setUserVars({ ...editing } as UserVariables)
        setEditMode(false)
      } else {
        const data = await res.json()
        showStatus('error', data.error || 'Failed to save')
      }
    } catch {
      showStatus('error', 'Network error saving variables')
    }
  }

  const handleCancelEdit = () => {
    if (userVars) setEditing({ ...userVars } as UserVariables)
    setEditMode(false)
  }

  const handleAddCustomVar = () => {
    if (!newCustomKey.trim()) return
    const key = newCustomKey.trim().toUpperCase().replace(/\s+/g, '_')
    const updated = { ...customVars, [key]: newCustomValue.trim() }
    setCustomVars(updated)
    localStorage.setItem('ucore-custom-vars', JSON.stringify(updated))
    setNewCustomKey('')
    setNewCustomValue('')
    showStatus('success', `Custom variable $${key} added`)
  }

  const handleRemoveCustomVar = (key: string) => {
    const updated = { ...customVars }
    delete updated[key]
    setCustomVars(updated)
    localStorage.setItem('ucore-custom-vars', JSON.stringify(updated))
    showStatus('success', `$${key} removed`)
  }

  const handleExportToEnv = async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets/export-env`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: '.env', only_missing: true }),
        signal: AbortSignal.timeout(5000),
      })
      if (res.ok) {
        const data = await res.json()
        showStatus('success', `Exported ${data.written_count || 0} variable(s) to .env`)
      } else {
        showStatus('error', 'Export failed')
      }
    } catch {
      showStatus('error', 'Network error exporting to .env')
    }
  }

  const renderUserTab = () => (
    <>
      <div className="sys-var-actions">
        {editMode ? (
          <>
            <button className="btn btn-sm btn-primary" onClick={handleSaveUserVars}>
              <Icon name="check" size={14} /> Save
            </button>
            <button className="btn btn-sm" onClick={handleCancelEdit}>
              <Icon name="close" size={14} /> Cancel
            </button>
          </>
        ) : (
          <>
            <button className="btn btn-sm" onClick={() => setEditMode(true)}>
              <Icon name="edit" size={14} /> Edit
            </button>
            <button className="btn btn-sm" onClick={fetchVariables}>
              <Icon name="refresh" size={14} /> Refresh
            </button>
            <span className="sys-var-hint">
              <Icon name="info" size={12} />
              Synced to .env & Secret Store
            </span>
          </>
        )}
      </div>
      <div className="sys-page-variables-grid">
        {userVars && Object.entries(userVars).map(([key, value]) => {
          const def = USER_VAR_DEFS[key]
          return (
            <div key={key} className="sys-var-card">
              <div className="sys-var-card-icon" style={{ color: 'var(--sys-accent, #58a6ff)' }}>
                <Icon name={def?.icon || 'variable' as any} size={20} />
              </div>
              <div className="sys-var-card-info">
                <div className="sys-var-card-label">{def?.label || key}</div>
                {editMode ? (
                  <input
                    className="sys-var-input"
                    type="text"
                    value={editing[key] || ''}
                    onChange={e => setEditing(prev => ({ ...prev, [key]: e.target.value }))}
                    placeholder={def?.description || key}
                  />
                ) : (
                  <div className="sys-var-card-value">
                    <code>{value || '—'}</code>
                  </div>
                )}
                <div className="sys-var-card-desc">{def?.description || key}</div>
              </div>
            </div>
          )
        })}
      </div>
    </>
  )

  const renderSystemTab = () => (
    <>
      <div className="sys-var-actions">
        <button className="btn btn-sm" onClick={fetchVariables}>
          <Icon name="refresh" size={14} /> Refresh
        </button>
        <span className="sys-var-hint">
          <Icon name="lock" size={12} />
          System variables are read-only
        </span>
      </div>
      <div className="sys-page-variables-grid">
        {installVars && Object.entries(installVars).map(([key, value]) => (
          <div key={key} className="sys-var-card">
            <div className="sys-var-card-icon" style={{ color: 'var(--sys-accent, #3fb950)' }}>
              <Icon name="settings_suggest" size={20} />
            </div>
            <div className="sys-var-card-info">
              <div className="sys-var-card-label">
                {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
              </div>
              <div className="sys-var-card-value">
                <code>{value || '—'}</code>
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  )

  const renderCustomTab = () => (
    <>
      <div className="sys-var-actions">
        <button className="btn btn-sm btn-primary" onClick={handleExportToEnv}>
          <Icon name="upload" size={14} /> Export All to .env
        </button>
        <span className="sys-var-hint">
          <Icon name="info" size={12} />
          Stored locally in browser
        </span>
      </div>
      <div style={{
        display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap',
        padding: '12px', background: 'var(--pico-card-sectioning-background-color)',
        borderRadius: '6px',
      }}>
        <input
          className="sys-var-input"
          type="text"
          placeholder="Variable name (e.g. MY_API_URL)"
          value={newCustomKey}
          onChange={e => setNewCustomKey(e.target.value)}
          style={{ flex: '1', minWidth: '180px' }}
        />
        <input
          className="sys-var-input"
          type="text"
          placeholder="Value"
          value={newCustomValue}
          onChange={e => setNewCustomValue(e.target.value)}
          style={{ flex: '2', minWidth: '180px' }}
        />
        <button
          className="btn btn-sm btn-primary"
          onClick={handleAddCustomVar}
          disabled={!newCustomKey.trim()}
        >
          <Icon name="add" size={14} /> Add
        </button>
      </div>
      {Object.keys(customVars).length === 0 ? (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--pico-muted-color)' }}>
          No custom variables defined. Add your own key/value pairs above.
        </div>
      ) : (
        <div className="sys-page-variables-grid">
          {Object.entries(customVars).map(([key, value]) => (
            <div key={key} className="sys-var-card">
              <div className="sys-var-card-icon" style={{ color: '#a855f7' }}>
                <Icon name="variable" size={20} />
              </div>
              <div className="sys-var-card-info">
                <div className="sys-var-card-label">{key}</div>
                <div className="sys-var-card-value">
                  <code>{value}</code>
                </div>
                <div className="sys-var-card-desc">Custom variable</div>
              </div>
              <button
                className="btn btn-xs"
                onClick={() => handleRemoveCustomVar(key)}
                style={{ color: 'var(--pico-del-color)', flexShrink: 0 }}
                title="Remove variable"
              >
                <Icon name="delete" size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  )

  return (
    <div className="sys-page-section" style={{ margin: '0', padding: '0' }}>
      <div className="sys-page-section-header">
        <h3><Icon name="tune" size={16} /> Variable Store</h3>
        <span className="sys-page-section-badge">$Variables</span>
      </div>

      <p className="sys-page-section-desc">
        <strong>User:</strong> Editable profile vars. <strong>Global:</strong> Read-only installation metadata.
        <strong> Custom:</strong> User-defined key/value pairs. <strong>Secrets:</strong> See dedicated Secrets tab.
      </p>

      {statusMsg && (
        <div style={{ padding: '0 16px' }}>
          <div className={`sys-msg sys-msg--${statusMsg.type}`}>
            {statusMsg.text}
          </div>
        </div>
      )}

      <div style={{ padding: '8px 16px' }}>
        <div className="sys-var-scope-tabs">
          {(['user', 'system', 'custom'] as VariableScope[]).map(scope => (
            <button
              key={scope}
              className={`sys-var-scope-tab ${activeScope === scope ? 'sys-var-scope-tab--active' : ''}`}
              onClick={() => setActiveScope(scope)}
            >
              <Icon name={
                scope === 'user' ? 'person' :
                scope === 'system' ? 'computer' :
                'add_circle'
              } size={14} />
              <span>
                {scope === 'user' ? 'User' :
                 scope === 'system' ? 'Global' :
                 'Custom'}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: '0 16px 16px' }}>
        {loading ? (
          <div className="sys-page-loading">Loading variables...</div>
        ) : (
          <>
            {activeScope === 'user' && renderUserTab()}
            {activeScope === 'system' && renderSystemTab()}
            {activeScope === 'custom' && renderCustomTab()}
          </>
        )}
      </div>
    </div>
  )
}