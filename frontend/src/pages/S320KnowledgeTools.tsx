/* ═══════════════════════════════════════════════════════════════════
   S320KnowledgeTools — Knowledge & AppFlowy Tools Page
   ═══════════════════════════════════════════════════════════════════
   S320: Media — Knowledge / AppFlowy Tools
   Tabs: Workspaces | Local DB | Index Coverage | Actions
   ═══════════════════════════════════════════════════════════════════ */
import React, { useEffect, useState, useCallback } from 'react'
import USystemPage from '../components/uSystemPage'

const SNACKBAR_API = 'http://localhost:8484'

type Workspace = {
  id: string
  name: string
  icon: string | null
  member_count: number
  source: string
}

type Document = {
  id: string
  title: string
  type: string
  updated_at: string
}

type LocalDB = {
  name: string
  path: string
  tables: number
}

type IndexCoverageItem = {
  source: string
  expected: number
  indexed: number
  coverage_percent: number
}

type KnowledgeState = {
  workspaces: Workspace[]
  documents: Document[]
  searchResults: Array<{ rowid: number; content: string; source: string }>
  selectedWs: string | null
  selectedDoc: Document | null
  localDbs: LocalDB[]
  indexCoverage: IndexCoverageItem[]
}

export default function S320KnowledgeTools() {
  const [state, setState] = useState<KnowledgeState>({
    workspaces: [], documents: [], searchResults: [], selectedWs: null, selectedDoc: null,
    localDbs: [], indexCoverage: [],
  })
  const [tab, setTab] = useState<'workspaces' | 'localdb' | 'coverage' | 'actions'>('workspaces')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [importing, setImporting] = useState(false)
  const [docContent, setDocContent] = useState<string | null>(null)
  const [queryResult, setQueryResult] = useState<any>(null)
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM documents LIMIT 10;')

  const loadWorkspaces = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/workspaces`, {
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        const data = await res.json()
        setState(prev => ({ ...prev, workspaces: data.workspaces || [] }))
        if (data.workspaces?.length > 0 && !state.selectedWs) {
          setState(prev => ({ ...prev, selectedWs: data.workspaces[0].id }))
        }
      }
    } catch (err) {
      setError(`Failed to load workspaces: ${err}`)
    }
  }, [state.selectedWs])

  const loadDocuments = useCallback(async (wsId: string | null) => {
    if (!wsId) return
    try {
      const url = wsId
        ? `${SNACKBAR_API}/api/knowledge/documents?workspace_id=${wsId}`
        : `${SNACKBAR_API}/api/knowledge/documents`
      const res = await fetch(url, { signal: AbortSignal.timeout(3000) })
      if (res.ok) {
        const data = await res.json()
        setState(prev => ({ ...prev, documents: data.documents || [] }))
      }
    } catch (err) {
      setError(`Failed to load documents: ${err}`)
    }
  }, [])

  const loadLocalDatabases = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/local/databases`, {
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        const data = await res.json()
        setState(prev => ({
          ...prev,
          localDbs: Object.entries(data.databases || {}).map(([name, path]: [string, any]) => ({
            name,
            path: typeof path === 'string' ? path : path.path,
            tables: 0,
          })),
        }))
      }
    } catch (err) {
      setError(`Failed to load local databases: ${err}`)
    }
  }, [])

  const loadIndexCoverage = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/index/coverage`, {
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        const data = await res.json()
        setState(prev => ({ ...prev, indexCoverage: data.coverage || [] }))
      }
    } catch (err) {
      // Endpoint might not exist yet, that's ok
      console.log('Index coverage not yet available')
    }
  }, [])

  const loadDocumentContent = useCallback(async (docId: string) => {
    try {
      const res = await fetch(
        `${SNACKBAR_API}/api/knowledge/documents/${docId}/content?workspace_id=${state.selectedWs}`,
        { signal: AbortSignal.timeout(5000) }
      )
      if (res.ok) {
        const data = await res.json()
        setDocContent(data.content || '(No content)')
      }
    } catch (err) {
      setDocContent(`Error loading: ${err}`)
    }
  }, [state.selectedWs])

  const searchKnowledge = useCallback(async () => {
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const res = await fetch(
        `${SNACKBAR_API}/api/knowledge/search?q=${encodeURIComponent(searchQuery)}&limit=20`,
        { signal: AbortSignal.timeout(5000) }
      )
      if (res.ok) {
        const data = await res.json()
        setState(prev => ({ ...prev, searchResults: data.results || [] }))
      }
    } catch (err) {
      setError(`Search failed: ${err}`)
    } finally {
      setSearching(false)
    }
  }, [searchQuery])

  const runVaultSync = useCallback(async () => {
    setSyncing(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/skills/vault_sync/run`, {
        method: 'POST',
        signal: AbortSignal.timeout(30000),
      })
      if (res.ok) {
        const data = await res.json()
        alert(`Vault sync ${data.result?.status}: ${data.result?.message}`)
        // Refresh coverage after sync
        await loadIndexCoverage()
      }
    } catch (err) {
      setError(`Sync failed: ${err}`)
    } finally {
      setSyncing(false)
    }
  }, [loadIndexCoverage])

  const runAppFlowyImport = useCallback(async () => {
    setImporting(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mission: null, binder: null, files: null }),
        signal: AbortSignal.timeout(60000),
      })
      if (res.ok) {
        const data = await res.json()
        alert(`Import ${data.status}: ${data.message}`)
        await loadIndexCoverage()
      }
    } catch (err) {
      setError(`Import failed: ${err}`)
    } finally {
      setImporting(false)
    }
  }, [loadIndexCoverage])

  const runSQLQuery = useCallback(async () => {
    if (!sqlQuery.trim()) return
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/local/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ db: 'database', sql: sqlQuery, params: [], write: false }),
        signal: AbortSignal.timeout(10000),
      })
      if (res.ok) {
        const data = await res.json()
        setQueryResult(data)
      } else {
        setQueryResult({ error: `HTTP ${res.status}` })
      }
    } catch (err) {
      setQueryResult({ error: `Query failed: ${err}` })
    }
  }, [sqlQuery])

  useEffect(() => {
    setLoading(true)
    Promise.all([loadWorkspaces(), loadLocalDatabases(), loadIndexCoverage()]).finally(() => setLoading(false))
  }, [loadWorkspaces, loadLocalDatabases, loadIndexCoverage])

  useEffect(() => {
    if (state.selectedWs) loadDocuments(state.selectedWs)
  }, [state.selectedWs, loadDocuments])

  return (
    <USystemPage page={320} title="Knowledge Tools" subtitle="AppFlowy workspace browser, local DB, and index coverage">
      {error && (
        <div style={{ padding: 12, background: 'rgba(248, 81, 73, 0.1)', color: '#f85149', borderRadius: 6, marginBottom: 12 }}>
          {error}
          <button onClick={() => setError(null)} style={{ marginLeft: 8 }}>Dismiss</button>
        </div>
      )}

      {/* ─── Tab Navigation ─────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, borderBottom: '1px solid var(--pico-border-color, #30363d)', paddingBottom: 8 }}>
        {['workspaces', 'localdb', 'coverage', 'actions'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t as any)}
            style={{
              background: tab === t ? 'var(--pico-primary, #58a6ff)' : 'transparent',
              color: tab === t ? 'white' : 'var(--pico-text-color)',
              border: 'none',
              padding: '8px 16px',
              cursor: 'pointer',
              borderRadius: 4,
              textTransform: 'capitalize',
            }}
          >
            {t === 'workspaces' && '📂 Workspaces'}
            {t === 'localdb' && '🗄️ Local DB'}
            {t === 'coverage' && '📊 Coverage'}
            {t === 'actions' && '⚡ Actions'}
          </button>
        ))}
      </div>

      {loading ? (
        <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Loading knowledge tools...</p>
      ) : tab === 'workspaces' ? (
        <div className="nestframe-grid">
          {/* ─── Workspaces Browser ─────────────────────────────── */}
          <article>
            <header><strong>📂 AppFlowy Workspaces</strong></header>
            {state.workspaces.length === 0 ? (
              <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
                No AppFlowy workspaces found. Ensure AppFlowy is running.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {state.workspaces.map(ws => (
                  <div
                    key={ws.id}
                    onClick={() => setState(prev => ({ ...prev, selectedWs: ws.id }))}
                    style={{
                      padding: '8px 12px',
                      borderRadius: 6,
                      cursor: 'pointer',
                      background: state.selectedWs === ws.id ? 'var(--pico-card-background-color, #161b22)' : 'transparent',
                      border: '1px solid',
                      borderColor: state.selectedWs === ws.id ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-border-color, #30363d)',
                    }}
                  >
                    <strong>{ws.name}</strong>
                    <small style={{ color: 'var(--pico-muted-color, #8b949e)', marginLeft: 8 }}>
                      {ws.source} · {ws.member_count} members
                    </small>
                  </div>
                ))}
              </div>
            )}
            <footer><small><code>/api/knowledge/workspaces</code></small></footer>
          </article>

          {/* ─── Documents ──────────────────────────────────────── */}
          <article style={{ gridColumn: 'span 2' }}>
            <header><strong>📄 Documents</strong></header>
            {!state.selectedWs ? (
              <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Select a workspace.</p>
            ) : state.documents.length === 0 ? (
              <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>No documents.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 400, overflowY: 'auto' }}>
                {state.documents.map(doc => (
                  <div
                    key={doc.id}
                    onClick={() => { setState(prev => ({ ...prev, selectedDoc: doc })); loadDocumentContent(doc.id) }}
                    style={{
                      padding: '8px 10px',
                      border: '1px solid var(--pico-border-color, #30363d)',
                      borderRadius: 4,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      background: state.selectedDoc?.id === doc.id ? 'rgba(88, 166, 255, 0.1)' : 'transparent',
                    }}
                  >
                    <strong>{doc.title || '(untitled)'}</strong>
                    <small style={{ color: 'var(--pico-muted-color, #8b949e)', marginLeft: 8 }}>
                      {doc.type} · {new Date(doc.updated_at).toLocaleDateString()}
                    </small>
                  </div>
                ))}
              </div>
            )}
            <footer><small><code>/api/knowledge/documents</code> — {state.documents.length} docs</small></footer>
          </article>

          {/* ─── Document Detail ────────────────────────────────── */}
          {state.selectedDoc && (
            <article style={{ gridColumn: 'span 2' }}>
              <header>
                <strong>📖 {state.selectedDoc.title || '(untitled)'}</strong>
                <button onClick={() => { setState(prev => ({ ...prev, selectedDoc: null })); setDocContent(null) }}>Close</button>
              </header>
              <pre style={{
                background: 'var(--pico-card-background-color, #161b22)',
                padding: 12,
                borderRadius: 4,
                maxHeight: 300,
                overflowY: 'auto',
                fontSize: '0.75rem',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}>
                {docContent || 'Loading...'}
              </pre>
              <footer>
                <small>{state.selectedDoc.type} · {new Date(state.selectedDoc.updated_at).toISOString()}</small>
              </footer>
            </article>
          )}

          {/* ─── Semantic Search ────────────────────────────────── */}
          <article style={{ gridColumn: 'span 2' }}>
            <header><strong>🔍 Semantic Search</strong></header>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <input
                type="text"
                placeholder="Search knowledge base..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && searchKnowledge()}
                style={{ flex: 1, padding: '6px 10px', fontSize: '0.9rem' }}
              />
              <button className="primary" onClick={searchKnowledge} disabled={searching || !searchQuery.trim()}>
                {searching ? 'Searching...' : 'Search'}
              </button>
            </div>
            {state.searchResults.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 250, overflowY: 'auto' }}>
                {state.searchResults.slice(0, 10).map((r, i) => (
                  <div key={i} style={{
                    padding: '6px 10px',
                    border: '1px solid var(--pico-border-color, #30363d)',
                    borderRadius: 4,
                    fontSize: '0.8rem',
                  }}>
                    <code>{r.content.substring(0, 120)}...</code>
                    <small style={{ color: 'var(--pico-muted-color, #8b949e)', marginLeft: 8 }}>source: {r.source}</small>
                  </div>
                ))}
              </div>
            )}
            {!searching && searchQuery && state.searchResults.length === 0 && (
              <p style={{ color: 'var(--pico-muted-color, #8b949e)', fontSize: '0.85rem' }}>No results found.</p>
            )}
            <footer><small><code>/api/knowledge/search</code></small></footer>
          </article>
        </div>
      ) : tab === 'localdb' ? (
        <div className="nestframe-grid">
          <article>
            <header><strong>🗄️ Local AppFlowy Databases</strong></header>
            {state.localDbs.length === 0 ? (
              <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>No local databases found.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {state.localDbs.map(db => (
                  <div key={db.name} style={{
                    padding: '8px 12px',
                    border: '1px solid var(--pico-border-color, #30363d)',
                    borderRadius: 4,
                    fontSize: '0.85rem',
                  }}>
                    <strong>{db.name}</strong>
                    <small style={{ color: 'var(--pico-muted-color, #8b949e)', marginLeft: 8 }}>
                      {db.path}
                    </small>
                  </div>
                ))}
              </div>
            )}
          </article>
          <article style={{ gridColumn: 'span 2' }}>
            <header><strong>💾 SQL Query Editor</strong></header>
            <textarea
              value={sqlQuery}
              onChange={e => setSqlQuery(e.target.value)}
              placeholder="SELECT * FROM documents LIMIT 10;"
              style={{
                width: '100%',
                height: 120,
                padding: '8px',
                fontSize: '0.85rem',
                fontFamily: 'monospace',
                marginBottom: 8,
              }}
            />
            <button onClick={runSQLQuery} className="primary">Execute Query</button>
            {queryResult && (
              <pre style={{
                marginTop: 8,
                padding: 8,
                background: 'var(--pico-card-background-color, #161b22)',
                borderRadius: 4,
                fontSize: '0.75rem',
                maxHeight: 200,
                overflowY: 'auto',
              }}>
                {JSON.stringify(queryResult, null, 2)}
              </pre>
            )}
          </article>
        </div>
      ) : tab === 'coverage' ? (
        <article>
          <header><strong>📊 Index Coverage by Source</strong></header>
          {state.indexCoverage.length === 0 ? (
            <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
              No coverage data. Run a sync to populate metrics.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {state.indexCoverage.map((item, i) => (
                <div key={i} style={{ borderBottom: '1px solid var(--pico-border-color, #30363d)', paddingBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <strong>{item.source}</strong>
                    <span style={{ fontSize: '0.9rem', color: 'var(--pico-muted-color, #8b949e)' }}>
                      {item.indexed} / {item.expected}
                    </span>
                  </div>
                  <div style={{
                    width: '100%',
                    height: 8,
                    background: 'var(--pico-border-color, #30363d)',
                    borderRadius: 4,
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${Math.min(100, item.coverage_percent)}%`,
                      background: item.coverage_percent > 90 ? '#3fb950' : item.coverage_percent > 50 ? '#d29922' : '#f85149',
                      transition: 'width 0.3s ease',
                    }} />
                  </div>
                  <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
                    {item.coverage_percent.toFixed(1)}% coverage
                  </small>
                </div>
              ))}
            </div>
          )}
        </article>
      ) : (
        <article>
          <header><strong>⚡ Knowledge Actions</strong></header>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div>
              <button
                onClick={runVaultSync}
                disabled={syncing}
                className="primary"
                style={{ width: '100%', padding: '12px' }}
              >
                {syncing ? '🔄 Syncing...' : '🔄 Run Vault Sync'}
              </button>
              <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
                Synchronize AppFlowy vault with local knowledge base.
              </small>
            </div>
            <div>
              <button
                onClick={runAppFlowyImport}
                disabled={importing}
                className="primary"
                style={{ width: '100%', padding: '12px' }}
              >
                {importing ? '📥 Importing...' : '📥 Import AppFlowy Data'}
              </button>
              <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
                Import AppFlowy workspaces and documents into uCore knowledge base.
              </small>
            </div>
            <hr />
            <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
              <strong>Scheduled Syncs:</strong> vault_sync at 4:00 AM, brain_sync at 4:15 AM
            </small>
          </div>
        </article>
      )}
    </USystemPage>
  )
}
