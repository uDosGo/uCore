/* ═══════════════════════════════════════════════════════════════════
   S320KnowledgeTools — Knowledge & AppFlowy Tools Page
   ═══════════════════════════════════════════════════════════════════
   S320: Media — Knowledge / AppFlowy Tools
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

type KnowledgeState = {
  workspaces: Workspace[]
  documents: Document[]
  searchResults: Array<{ rowid: number; content: string; source: string }>
  selectedWs: string | null
}

export default function S320KnowledgeTools() {
  const [state, setState] = useState<KnowledgeState>({
    workspaces: [], documents: [], searchResults: [], selectedWs: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searching, setSearching] = useState(false)

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
    } catch {
      // silent
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
    } catch {
      // silent
    }
  }, [])

  const searchKnowledge = useCallback(async () => {
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const res = await fetch(
        `${SNACKBAR_API}/api/knowledge/search?q=${encodeURIComponent(searchQuery)}`,
        { signal: AbortSignal.timeout(3000) }
      )
      if (res.ok) {
        const data = await res.json()
        setState(prev => ({ ...prev, searchResults: data.results || [] }))
      }
    } catch {
      // silent
    } finally {
      setSearching(false)
    }
  }, [searchQuery])

  useEffect(() => {
    setLoading(true)
    Promise.all([loadWorkspaces()]).finally(() => setLoading(false))
  }, [loadWorkspaces])

  useEffect(() => {
    if (state.selectedWs) loadDocuments(state.selectedWs)
  }, [state.selectedWs, loadDocuments])

  return (
    <USystemPage
      page={320}
      title="Knowledge Tools"
      subtitle="AppFlowy workspace browser and semantic search"
    >
      <div className="nestframe-grid">
        {/* ─── Workspaces ───────────────────────────────────────── */}
        <article>
          <header><strong>📂 AppFlowy Workspaces</strong></header>
          {loading ? (
            <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Loading workspaces...</p>
          ) : state.workspaces.length === 0 ? (
            <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
              No AppFlowy workspaces found. Ensure AppFlowy is running and has data.
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
          <footer>
            <small><code>/api/knowledge/workspaces</code> — {state.workspaces.length} found</small>
          </footer>
        </article>

        {/* ─── Documents ────────────────────────────────────────── */}
        <article style={{ gridColumn: 'span 2' }}>
          <header><strong>📄 Documents</strong></header>
          {!state.selectedWs ? (
            <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Select a workspace to view documents.</p>
          ) : state.documents.length === 0 ? (
            <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>No documents in this workspace.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 300, overflowY: 'auto' }}>
              {state.documents.map(doc => (
                <div key={doc.id} style={{
                  padding: '6px 10px',
                  border: '1px solid var(--pico-border-color, #30363d)',
                  borderRadius: 4,
                  fontSize: '0.85rem',
                }}>
                  <strong>{doc.title || '(untitled)'}</strong>
                  <small style={{ color: 'var(--pico-muted-color, #8b949e)', marginLeft: 8 }}>
                    {doc.type} · {new Date(doc.updated_at).toLocaleDateString()}
                  </small>
                </div>
              ))}
            </div>
          )}
          <footer><small><code>/api/knowledge/documents</code></small></footer>
        </article>

        {/* ─── Semantic Search ──────────────────────────────────── */}
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
          {state.searchResults.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 300, overflowY: 'auto' }}>
              {state.searchResults.map((r, i) => (
                <div key={i} style={{
                  padding: '6px 10px',
                  border: '1px solid var(--pico-border-color, #30363d)',
                  borderRadius: 4,
                  fontSize: '0.8rem',
                }}>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{r.content}</pre>
                  <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>source: {r.source}</small>
                </div>
              ))}
            </div>
          ) : (
            !searching && searchQuery && <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>No results found.</p>
          )}
          <footer><small><code>/api/knowledge/search</code></small></footer>
        </article>
      </div>
    </USystemPage>
  )
}
