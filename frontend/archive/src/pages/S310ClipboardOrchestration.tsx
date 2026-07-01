/* ═══════════════════════════════════════════════════════════════════
   S310ClipboardOrchestration — Clipboard & System Orchestration Page
   ═══════════════════════════════════════════════════════════════════
   S310: Media — Clipboard / System Orchestration
   ═══════════════════════════════════════════════════════════════════ */
import React, { useEffect, useState, useCallback } from 'react'
import USystemPage from '../components/uSystemPage'

const SNACKBAR_API = 'http://localhost:8484'

type ClipboardEntry = {
  id: string
  content: string
  content_type: string
  pinned: boolean
  created_at: string
}

type MaintenanceStatus = {
  status: string
  last_run: string | null
  tray?: {
    status?: string
    pid?: number | null
    lockfile?: string
  }
  jobs: Array<{
    skill_id: string
    last_run: string | null
    last_result: { success?: boolean; error?: string } | null
  }>
}

export default function S310ClipboardOrchestration() {
  const [clipboard, setClipboard] = useState<ClipboardEntry[]>([])
  const [clipLoading, setClipLoading] = useState(true)
  const [clipError, setClipError] = useState<string | null>(null)
  const [maintenance, setMaintenance] = useState<MaintenanceStatus | null>(null)
  const [maintLoading, setMaintLoading] = useState(true)

  // Search / filter
  const [search, setSearch] = useState('')
  const [showPinnedOnly, setShowPinnedOnly] = useState(false)

  const loadClipboard = useCallback(async () => {
    setClipLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/snacks/clipboard`, {
        signal: AbortSignal.timeout(2500),
      })
      if (res.ok) {
        const data = await res.json()
        setClipboard(data.entries || data.clipboard || [])
        setClipError(null)
      } else {
        setClipError(`HTTP ${res.status}`)
      }
    } catch (e: any) {
      setClipError(e.message || 'Failed to load clipboard')
    } finally {
      setClipLoading(false)
    }
  }, [])

  const loadMaintenance = useCallback(async () => {
    setMaintLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/system/maintenance`, {
        signal: AbortSignal.timeout(2500),
      })
      if (res.ok) {
        const data = await res.json()
        setMaintenance(data)
      }
    } catch {
      // Maintenance is optional
    } finally {
      setMaintLoading(false)
    }
  }, [])

  useEffect(() => {
    loadClipboard()
    loadMaintenance()
  }, [loadClipboard, loadMaintenance])

  const togglePin = useCallback(async (id: string, currentlyPinned: boolean) => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/snacks/clipboard/${id}/pin`, {
        method: currentlyPinned ? 'DELETE' : 'POST',
        signal: AbortSignal.timeout(2000),
      })
      if (res.ok) {
        setClipboard(prev => prev.map(e => e.id === id ? { ...e, pinned: !currentlyPinned } : e))
      }
    } catch {
      // silent
    }
  }, [])

  const deleteEntry = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/snacks/clipboard/${id}`, {
        method: 'DELETE',
        signal: AbortSignal.timeout(2000),
      })
      if (res.ok) {
        setClipboard(prev => prev.filter(e => e.id !== id))
      }
    } catch {
      // silent
    }
  }, [])

  const captureClipboard = useCallback(async () => {
    try {
      await fetch(`${SNACKBAR_API}/api/snacks/clipboard/capture`, {
        method: 'POST',
        signal: AbortSignal.timeout(2000),
      })
      loadClipboard()
    } catch {
      // silent
    }
  }, [loadClipboard])

  const cleanupClipboard = useCallback(async () => {
    try {
      await fetch(`${SNACKBAR_API}/api/snacks/clipboard/cleanup`, {
        method: 'POST',
        signal: AbortSignal.timeout(2000),
      })
      loadClipboard()
    } catch {
      // silent
    }
  }, [loadClipboard])

  // Filter entries
  const filtered = clipboard.filter(e => {
    if (showPinnedOnly && !e.pinned) return false
    if (search && !e.content.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const pinnedCount = clipboard.filter(e => e.pinned).length

  return (
    <USystemPage
      page={310}
      title="Clipboard & Orchestration"
      subtitle="System clipboard buffer and overnight maintenance chain"
      headerExtra={
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="secondary" onClick={captureClipboard}>📋 Capture</button>
          <button className="outline" onClick={cleanupClipboard}>🧹 Cleanup</button>
          <button className="outline" onClick={() => { loadClipboard(); loadMaintenance() }}>🔄</button>
        </div>
      }
    >
      <div className="nestframe-grid">
        {/* ─── Clipboard Stats ──────────────────────────────────── */}
        <article>
          <header><strong>📋 Clipboard Buffer</strong></header>
          <p>System clipboard history with pin, search, and cleanup.</p>
          <ul>
            <li><strong>Total entries:</strong> {clipboard.length}</li>
            <li><strong>Pinned:</strong> {pinnedCount}</li>
            <li><strong>Unpinned:</strong> {clipboard.length - pinnedCount}</li>
          </ul>
          <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
            <input
              type="text"
              placeholder="Search clipboard..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ flex: 1, padding: '4px 8px', fontSize: '0.85rem' }}
            />
            <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.85rem', whiteSpace: 'nowrap' }}>
              <input type="checkbox" checked={showPinnedOnly} onChange={e => setShowPinnedOnly(e.target.checked)} />
              Pinned only
            </label>
          </div>
          {clipLoading && <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Loading clipboard...</p>}
          {clipError && <p style={{ color: 'var(--pico-del-color, #f85149)' }}>Error: {clipError}</p>}
        </article>

        {/* ─── Clipboard Entry List ─────────────────────────────── */}
        <article style={{ gridColumn: 'span 2' }}>
          <header><strong>📄 Entries</strong></header>
          {filtered.length === 0 && !clipLoading ? (
            <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
              {search || showPinnedOnly ? 'No matching entries.' : 'Clipboard is empty. Click "Capture" to save current clipboard.'}
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 400, overflowY: 'auto' }}>
              {filtered.map(entry => (
                <div key={entry.id} style={{
                  padding: '8px 12px',
                  background: entry.pinned ? 'var(--pico-card-background-color, #161b22)' : 'transparent',
                  border: '1px solid var(--pico-border-color, #30363d)',
                  borderRadius: 6,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 8,
                }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <pre style={{
                      margin: 0, fontSize: '0.8rem', whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word', maxHeight: 60, overflow: 'hidden',
                      color: 'var(--pico-color, #c9d1d9)',
                    }}>
                      {entry.content?.substring(0, 300)}
                    </pre>
                    <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
                      {entry.content_type} · {new Date(entry.created_at).toLocaleString()}
                    </small>
                  </div>
                  <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                    <button
                      onClick={() => togglePin(entry.id, entry.pinned)}
                      style={{
                        background: 'none', border: 'none', cursor: 'pointer',
                        color: entry.pinned ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-muted-color, #8b949e)',
                        fontSize: '1rem', padding: 2,
                      }}
                      title={entry.pinned ? 'Unpin' : 'Pin'}
                    >
                      {entry.pinned ? '★' : '☆'}
                    </button>
                    <button
                      onClick={() => deleteEntry(entry.id)}
                      style={{
                        background: 'none', border: 'none', cursor: 'pointer',
                        color: 'var(--pico-del-color, #f85149)', fontSize: '1rem', padding: 2,
                      }}
                      title="Delete"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <footer><small><code>/api/snacks/clipboard</code> — {clipboard.length} entries</small></footer>
        </article>

        {/* ─── Overnight Orchestration ──────────────────────────── */}
        <article>
          <header><strong>🌙 Overnight Maintenance</strong></header>
          <p>Scheduled maintenance chain: backup → vault sync → brain sync.</p>
          {maintLoading ? (
            <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Loading...</p>
          ) : maintenance ? (
            <>
              <p><strong>Status:</strong> {maintenance.status}</p>
              <p><strong>Last run:</strong> {maintenance.last_run || 'never'}</p>
              <p>
                <strong>Tray:</strong> {maintenance.tray?.status || 'unknown'}
                {maintenance.tray?.pid ? ` (pid ${maintenance.tray.pid})` : ''}
              </p>
              <ul>
                {(maintenance.jobs || []).map(job => (
                  <li key={job.skill_id}>
                    <strong>{job.skill_id}</strong>
                    <small style={{ color: 'var(--pico-muted-color, #8b949e)', marginLeft: 8 }}>
                      last: {job.last_run || 'never'}
                      {job.last_result?.success === false && ' ❌'}
                      {job.last_result?.success === true && ' ✅'}
                    </small>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Maintenance scheduler not available.</p>
          )}
          <footer><small><code>/api/system/maintenance</code></small></footer>
        </article>
      </div>
    </USystemPage>
  )
}
