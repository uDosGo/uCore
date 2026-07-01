/* ═══════════════════════════════════════════════════════════════════
   SecretStorePanel — Manage API keys and credentials
   Tab for USystemSurface, navigated to via /system?tab=secrets
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'

const SNACKBAR_API = 'http://localhost:8484'

interface SecretItem {
  name: string
  masked: string
}

interface EnvVarItem {
  name: string
  masked: string
  present?: boolean
  missing?: boolean
  source?: 'store' | 'env' | 'dotenv' | 'missing'
  in_store?: boolean
  in_env?: boolean
  in_dotenv?: boolean
}

export default function SecretStorePanel() {
  const [secrets, setSecrets] = useState<SecretItem[]>([])
  const [envVars, setEnvVars] = useState<EnvVarItem[]>([])
  const [dotenvSources, setDotenvSources] = useState<string[]>([])
  const [dotenvCandidates, setDotenvCandidates] = useState<string[]>([])
  const [dotenvTarget, setDotenvTarget] = useState('')
  const [dotenvOverwrite, setDotenvOverwrite] = useState(false)
  const [editingName, setEditingName] = useState('')
  const [editingValue, setEditingValue] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [revealedValues, setRevealedValues] = useState<Record<string, string>>({})

  const showStatus = useCallback((type: 'success' | 'error', text: string) => {
    setStatusMsg({ type, text })
    setTimeout(() => setStatusMsg(null), 3000)
  }, [])

  const fetchSecrets = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets`)
      if (res.ok) {
        const data = await res.json()
        setSecrets(data.secrets || [])
      }
    } catch (e) {
      console.error('Failed to fetch secrets', e)
    }
  }, [])

  const fetchEnvVars = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets/env`)
      if (res.ok) {
        const data = await res.json()
        setEnvVars(data.env_vars || [])
        setDotenvSources(data.dotenv_sources || [])
        const candidates = data.dotenv_candidates || []
        setDotenvCandidates(candidates)
        setDotenvTarget(prev => (prev && candidates.includes(prev)) ? prev : (candidates[0] || ''))
      }
    } catch (e) {
      console.error('Failed to fetch env vars', e)
    }
  }, [])

  const loadAll = useCallback(async () => {
    setLoading(true)
    await Promise.all([fetchSecrets(), fetchEnvVars()])
    setLoading(false)
  }, [fetchSecrets, fetchEnvVars])

  useEffect(() => { loadAll() }, [loadAll])

  const handleAddSecret = async () => {
    if (!editingName.trim() || !editingValue.trim()) {
      showStatus('error', 'Name and value are required')
      return
    }
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets/${encodeURIComponent(editingName.trim())}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: editingValue.trim() }),
      })
      if (res.ok) {
        showStatus('success', `Secret "${editingName}" saved`)
        setEditingName('')
        setEditingValue('')
        setShowAddForm(false)
        await loadAll()
      } else {
        const data = await res.json()
        showStatus('error', data.error || 'Failed to save secret')
      }
    } catch (e) {
      showStatus('error', 'Network error')
    }
  }

  const handleDeleteSecret = async (name: string) => {
    if (!window.confirm(`Delete secret "${name}"?`)) return
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets/${encodeURIComponent(name)}`, { method: 'DELETE' })
      if (res.ok) {
        showStatus('success', `Secret "${name}" deleted`)
        await fetchSecrets()
      }
    } catch (e) {
      showStatus('error', 'Network error')
    }
  }

  const handleReveal = async (name: string) => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets/${encodeURIComponent(name)}`)
      if (res.ok) {
        const data = await res.json()
        setRevealedValues(prev => ({ ...prev, [name]: data.value }))
        setTimeout(() => {
          setRevealedValues(prev => {
            const next = { ...prev }
            delete next[name]
            return next
          })
        }, 8000)
      }
    } catch (e) { /* ignore */ }
  }

  const handleImportFromEnv = async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets/import-env`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        const importedCount = Number(data.imported_count || 0)
        showStatus('success', `Merged provider vars from env/.env (${importedCount} imported)`)
        await loadAll()
      }
    } catch (e) {
      showStatus('error', 'Failed to import env vars')
    }
  }

  const handleSyncGithub = async () => {
    const repo = window.prompt('GitHub repository (owner/repo) - leave empty for user secrets:')
    if (repo === null) return // Cancelled
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets/sync-github`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repository: repo || undefined }),
      })
      if (res.ok) {
        const data = await res.json()
        showStatus('success', `Synced ${data.synced_count || 0} GitHub secrets`)
        await loadAll()
      } else {
        const data = await res.json()
        showStatus('error', data.error || 'Failed to sync GitHub secrets')
      }
    } catch (e) {
      showStatus('error', 'Failed to sync GitHub secrets')
    }
  }

  const handleExportToEnv = async () => {
    if (!dotenvTarget) {
      showStatus('error', 'Choose a .env target first')
      return
    }
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets/export-env`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: dotenvTarget, only_missing: !dotenvOverwrite }),
      })
      const data = await res.json()
      if (res.ok) {
        showStatus(
          'success',
          `Wrote ${Number(data.written_count || 0)} key(s) to ${dotenvTarget} (${dotenvOverwrite ? 'overwrite enabled' : 'only missing'})`,
        )
        await loadAll()
      } else {
        showStatus('error', data.error || 'Failed to export to .env')
      }
    } catch (e) {
      showStatus('error', 'Failed to export to .env')
    }
  }

  const handleCopyToClipboard = async (name: string) => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/secrets/${encodeURIComponent(name)}`)
      if (res.ok) {
        const data = await res.json()
        await navigator.clipboard.writeText(data.value)
        showStatus('success', 'Copied to clipboard')
      }
    } catch (e) {
      showStatus('error', 'Failed to copy')
    }
  }

  return (
    <div className="hub-settings-section" style={{ padding: '16px' }}>
      <h3 style={{ margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>key</span>
        Secret Store
      </h3>
      <p style={{ margin: '0 0 16px 0', color: 'var(--pico-muted-color)', fontSize: '13px' }}>
        Manage API keys and credentials. Stored encrypted at rest.
      </p>

      {statusMsg && (
        <div style={{
          padding: '8px 12px', marginBottom: '12px', borderRadius: '6px',
          fontSize: '13px',
          background: statusMsg.type === 'success'
            ? 'var(--pico-ins-color, #3fb95033)'
            : 'var(--pico-del-color, #f8514933)',
          color: statusMsg.type === 'success'
            ? 'var(--pico-ins-color, #3fb950)'
            : 'var(--pico-del-color, #f85149)',
        }}>
          {statusMsg.text}
        </div>
      )}

      {/* Actions bar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button className="btn btn-sm" onClick={() => setShowAddForm(!showAddForm)}>
          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>add</span>
          Add Secret
        </button>
        <button className="btn btn-sm" onClick={handleImportFromEnv}>
          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>download</span>
          Merge Env + .env
        </button>
        <button className="btn btn-sm" onClick={handleSyncGithub}>
          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>sync</span>
          Sync GitHub Secrets
        </button>
        <button className="btn btn-sm" onClick={loadAll}>
          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>refresh</span>
          Refresh
        </button>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <label style={{ fontSize: '12px', color: 'var(--pico-muted-color)' }}>Sync store to .env</label>
        <select
          value={dotenvTarget}
          onChange={e => setDotenvTarget(e.target.value)}
          style={{ minWidth: '260px', padding: '6px 8px', fontSize: '13px' }}
        >
          {dotenvCandidates.map(path => (
            <option key={path} value={path}>{path}</option>
          ))}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--pico-muted-color)' }}>
          <input
            type="checkbox"
            checked={dotenvOverwrite}
            onChange={e => setDotenvOverwrite(e.target.checked)}
          />
          Overwrite existing keys
        </label>
        <button className="btn btn-sm" onClick={handleExportToEnv} disabled={!dotenvTarget}>
          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>upload</span>
          {dotenvOverwrite ? 'Write Store Keys To .env (Overwrite)' : 'Write New Store Keys To .env'}
        </button>
      </div>

      {/* Add form */}
      {showAddForm && (
        <div style={{
          padding: '12px', marginBottom: '16px',
          background: 'var(--pico-card-background-color, #1a1a2e)',
          borderRadius: '8px', border: '1px solid var(--pico-border-color, #30363d)',
        }}>
          <div style={{ marginBottom: '8px' }}>
            <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--pico-muted-color)' }}>
              Secret Name
            </label>
            <input
              type="text"
              value={editingName}
              onChange={e => setEditingName(e.target.value)}
              placeholder="e.g. OPENROUTER_API_KEY"
              style={{ width: '100%', padding: '6px 8px', fontSize: '13px' }}
              list="known-keys"
            />
            <datalist id="known-keys">
              <option value="OPENROUTER_API_KEY" />
              <option value="ANTHROPIC_API_KEY" />
              <option value="OPENAI_API_KEY" />
              <option value="GEMINI_API_KEY" />
              <option value="MISTRAL_API_KEY" />
              <option value="DEEPSEEK_API_KEY" />
              <option value="GROQ_API_KEY" />
              <option value="GITHUB_TOKEN" />
              <option value="GITHUB_OAUTH_CLIENT_ID" />
              <option value="GITHUB_OAUTH_CLIENT_SECRET" />
              <option value="GOOGLE_OAUTH_CLIENT_ID" />
              <option value="GOOGLE_OAUTH_CLIENT_SECRET" />
              <option value="SLACK_OAUTH_CLIENT_ID" />
              <option value="SLACK_OAUTH_CLIENT_SECRET" />
              <option value="NOTION_OAUTH_CLIENT_ID" />
              <option value="NOTION_OAUTH_CLIENT_SECRET" />
              {/* Cline-specific keys */}
              <option value="CLINE_API_KEY" />
              <option value="CONTINUAI_API_KEY" />
              <option value="UCORE_CRED_PATH" />
              {/* GitHub Copilot keys */}
              <option value="GITHUB_COPILOT_TOKEN" />
              <option value="COPILOT_API_KEY" />
              <option value="COPILOT_HOST" />
            </datalist>
          </div>
          <div style={{ marginBottom: '8px' }}>
            <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--pico-muted-color)' }}>
              Secret Value
            </label>
            <input
              type="password"
              value={editingValue}
              onChange={e => setEditingValue(e.target.value)}
              placeholder="sk-or-v1-..."
              style={{ width: '100%', padding: '6px 8px', fontSize: '13px' }}
            />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-sm btn-primary" onClick={handleAddSecret}>Save</button>
            <button className="btn btn-sm" onClick={() => { setShowAddForm(false); setEditingName(''); setEditingValue('') }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Stored Secrets */}
      <h4 style={{ fontSize: '14px', margin: '0 0 8px 0' }}>Stored Secrets</h4>
      {loading ? (
        <div style={{ color: 'var(--pico-muted-color)', fontSize: '13px' }}>Loading...</div>
      ) : secrets.length === 0 ? (
        <div style={{
          padding: '24px', textAlign: 'center', color: 'var(--pico-muted-color)',
          fontSize: '13px', border: '1px dashed var(--pico-border-color)', borderRadius: '8px',
        }}>
          No secrets stored yet. Add one above or import from environment.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {secrets.map(secret => (
            <div key={secret.name} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '8px 12px',
              background: 'var(--pico-card-background-color, #1a1a2e)',
              borderRadius: '6px', border: '1px solid var(--pico-border-color, #30363d)',
            }}>
              <div>
                <div style={{ fontWeight: 500, fontSize: '14px', fontFamily: 'monospace' }}>
                  {secret.name}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--pico-muted-color)', fontFamily: 'monospace' }}>
                  {revealedValues[secret.name] ? revealedValues[secret.name] : secret.masked}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '4px' }}>
                <button
                  className="btn btn-xs"
                  onClick={() => handleReveal(secret.name)}
                  title="Reveal (8s)"
                  style={{ fontSize: '11px', padding: '2px 6px' }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '12px' }}>visibility</span>
                </button>
                <button
                  className="btn btn-xs"
                  onClick={() => handleCopyToClipboard(secret.name)}
                  title="Copy"
                  style={{ fontSize: '11px', padding: '2px 6px' }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '12px' }}>content_copy</span>
                </button>
                <button
                  className="btn btn-xs"
                  onClick={() => handleDeleteSecret(secret.name)}
                  title="Delete"
                  style={{ fontSize: '11px', padding: '2px 6px', color: 'var(--pico-del-color, #f85149)' }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '12px' }}>delete</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Provider Variables (.env + env + store) */}
      {envVars.length > 0 && (
        <>
          <h4 style={{ fontSize: '14px', margin: '16px 0 8px 0' }}>
            Provider Variables
            <span style={{ fontWeight: 'normal', fontSize: '12px', color: 'var(--pico-muted-color)', marginLeft: '8px' }}>
              (missing keys can be added from here)
            </span>
          </h4>

          {dotenvSources.length > 0 && (
            <div style={{ marginBottom: '8px', fontSize: '12px', color: 'var(--pico-muted-color)' }}>
              .env sources: {dotenvSources.join(', ')}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {envVars
              .filter(ev => ev.missing || (!ev.in_store && (ev.in_env || ev.in_dotenv)))
              .map(ev => (
                <div key={ev.name} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '6px 12px',
                  background: 'var(--pico-card-background-color, #1a1a2e)',
                  borderRadius: '6px', border: '1px solid var(--pico-border-color, #30363d)',
                  opacity: ev.missing ? 0.95 : 0.7,
                }}>
                  <div>
                    <span style={{ fontFamily: 'monospace', fontSize: '13px' }}>{ev.name}</span>
                    <span style={{ fontSize: '12px', color: 'var(--pico-muted-color)', marginLeft: '8px' }}>
                      {ev.missing ? 'missing' : `${ev.source}: ${ev.masked}`}
                    </span>
                  </div>
                  <button
                    className="btn btn-xs"
                    onClick={() => {
                      setEditingName(ev.name)
                      setShowAddForm(true)
                    }}
                    style={{ fontSize: '11px', padding: '2px 6px' }}
                  >
                    Add
                  </button>
                </div>
              ))}
          </div>
        </>
      )}
    </div>
  )
}
