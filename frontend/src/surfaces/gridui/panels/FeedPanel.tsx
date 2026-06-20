/* ═══════════════════════════════════════════════════════════════════
   FeedPanel — Feed source configuration and management
   ═══════════════════════════════════════════════════════════════════
   Configure feed sources, preview feed items, and route them to
   Teletext pages. Communicates with the Snackbar Ceefax API.

   Features:
     - List configured feed sources (email, RSS, GitHub, Slack)
     - Enable/disable individual feeds
     - Preview latest feed items from each source
     - Push test feed items to verify the pipeline
     - View feed item history with timestamps
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { useStore } from '../GridUIStore'
import { TeletextPageStore } from '../grid-algebra/TeletextPage'
import { Icon } from '../../../components/Icon'

// ─── Types ────────────────────────────────────────────────────────────

interface FeedSource {
  id: string
  name: string
  enabled: boolean
  icon: string
}

interface FeedItem {
  id: string
  source: string
  title: string
  body: string
  timestamp: string
  page: number
}

// ─── Constants ────────────────────────────────────────────────────────

const SNACKBAR_URL = 'http://127.0.0.1:8484'
const pageStore = new TeletextPageStore()

// ─── Feed Panel ───────────────────────────────────────────────────────

export function FeedPanel() {
  const store = useStore()
  const [feeds, setFeeds] = useState<FeedSource[]>([])
  const [feedItems, setFeedItems] = useState<FeedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [testSource, setTestSource] = useState('email')
  const [testTitle, setTestTitle] = useState('')
  const [testBody, setTestBody] = useState('')
  const [testPage, setTestPage] = useState(500)
  const [pushing, setPushing] = useState(false)
  const [snackbarConnected, setSnackbarConnected] = useState(false)

  // ─── Fetch feeds from Snackbar API ──────────────────────────────

  const fetchFeeds = useCallback(async () => {
    try {
      const resp = await fetch(`${SNACKBAR_URL}/api/ceefax/feeds`)
      if (!resp.ok) {
        setSnackbarConnected(false)
        return
      }
      const data = await resp.json()
      setFeeds(data.feeds || [])
      setSnackbarConnected(true)
      setError(null)
    } catch (err) {
      setSnackbarConnected(false)
      setError('Cannot connect to Snackbar API')
    }
  }, [])

  const fetchFeedItems = useCallback(async () => {
    try {
      const resp = await fetch(`${SNACKBAR_URL}/api/ceefax/feed/latest?limit=20`)
      if (!resp.ok) return
      const data = await resp.json()
      setFeedItems(data.items || [])
    } catch {
      // Silently fail — items will be empty
    }
  }, [])

  const refreshAll = useCallback(async () => {
    setLoading(true)
    await Promise.all([fetchFeeds(), fetchFeedItems()])
    setLoading(false)
  }, [fetchFeeds, fetchFeedItems])

  useEffect(() => {
    refreshAll()
    const interval = setInterval(refreshAll, 15000)
    return () => clearInterval(interval)
  }, [refreshAll])

  // ─── Toggle feed enabled/disabled ───────────────────────────────

  const toggleFeed = async (feedId: string, currentEnabled: boolean) => {
    // Optimistic update
    setFeeds(prev => prev.map(f =>
      f.id === feedId ? { ...f, enabled: !currentEnabled } : f
    ))
    // In a full implementation, this would POST to the Snackbar API
    // For now, we just update local state
    store.showSnackbar({
      message: `Feed "${feedId}" ${currentEnabled ? 'disabled' : 'enabled'}`,
      type: 'success',
      action: 'OK',
    })
  }

  // ─── Push a test feed item ──────────────────────────────────────

  const pushTestItem = async () => {
    if (!testTitle.trim() || !testBody.trim()) {
      store.showSnackbar({ message: 'Title and body required', type: 'warning', action: 'OK' })
      return
    }
    setPushing(true)
    const success = await pageStore.pushFeedItem(testSource, testTitle, testBody, testPage)
    setPushing(false)
    if (success) {
      store.showSnackbar({
        message: `Feed item pushed to P${testPage}`,
        type: 'success',
        action: 'OK',
      })
      setTestTitle('')
      setTestBody('')
      await fetchFeedItems()
    } else {
      store.showSnackbar({ message: 'Failed to push feed item', type: 'error', action: 'OK' })
    }
  }

  // ─── Format timestamp ───────────────────────────────────────────

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts)
      return d.toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch {
      return ts
    }
  }

  const formatDate = (ts: string) => {
    try {
      const d = new Date(ts)
      return d.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
    } catch {
      return ts
    }
  }

  // ─── Group feed items by source ─────────────────────────────────

  const itemsBySource = feedItems.reduce<Record<string, FeedItem[]>>((acc, item) => {
    if (!acc[item.source]) acc[item.source] = []
    acc[item.source].push(item)
    return acc
  }, {})

  // ─── Render ─────────────────────────────────────────────────────

  return (
    <div className="gridui-panel">
      <div className="gridui-panel-body">

        {/* Header */}
        <div className="gridui-card" style={{ marginBottom: 12 }}>
          <div className="gridui-card-header">
            <Icon name="rss_feed" size={16} />
            <h3 style={{ margin: 0, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
              Feed Sources
            </h3>
            <button
              onClick={refreshAll}
              className="gridui-display-mode-btn gridui-display-mode-btn--inactive"
              style={{ padding: '2px 8px' }}
              disabled={loading}
            >
              <Icon name="refresh" size={12} /> Refresh
            </button>
          </div>
          <div className="gridui-card-body">
            {/* Connection status */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginBottom: 10,
              color: snackbarConnected ? '#3fb950' : '#E76F51',
            }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: snackbarConnected ? '#3fb950' : '#E76F51',
                display: 'inline-block',
                animation: snackbarConnected ? 'gridui-live-pulse 2s infinite' : 'none',
              }} />
              {snackbarConnected ? 'Connected to Snackbar' : 'Disconnected'}
            </div>

            {/* Feed source list */}
            {feeds.length === 0 ? (
              <div style={{ color: 'var(--grid-text-secondary, #8b949e)', padding: '8px 0' }}>
                {snackbarConnected ? 'No feed sources configured' : 'Cannot load feeds — Snackbar unavailable'}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {feeds.map(feed => (
                  <div key={feed.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '6px 8px',
                    background: 'var(--grid-bg-secondary, #161b22)',
                    borderRadius: 6,
                    border: '1px solid var(--grid-border, #30363d)',
                  }}>
                    <Icon name={feed.icon} size={16} />
                    <span style={{ flex: 1, fontWeight: 500 }}>{feed.name}</span>
                    <span style={{
                      padding: '1px 6px',
                      borderRadius: 4,
                      background: feed.enabled ? '#23863620' : '#30363d40',
                      color: feed.enabled ? '#3fb950' : '#8b949e',
                    }}>
                      {feed.enabled ? 'Active' : 'Disabled'}
                    </span>
                    <button
                      onClick={() => toggleFeed(feed.id, feed.enabled)}
                      className="gridui-display-mode-btn"
                      style={{
                        padding: '2px 8px',
                        background: feed.enabled ? '#E76F5120' : '#23863620',
                        color: feed.enabled ? '#E76F51' : '#3fb950',
                        border: `1px solid ${feed.enabled ? '#E76F5140' : '#3fb95040'}`,
                      }}
                    >
                      {feed.enabled ? 'Disable' : 'Enable'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Push Test Feed Item */}
        <div className="gridui-card" style={{ marginBottom: 12 }}>
          <div className="gridui-card-header">
            <Icon name="science" size={16} />
            <h3 style={{ margin: 0, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
              Push Test Feed Item
            </h3>
          </div>
          <div className="gridui-card-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {/* Source selector */}
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <label style={{ color: 'var(--grid-text-secondary, #8b949e)', minWidth: 50 }}>Source</label>
                <select
                  value={testSource}
                  onChange={e => setTestSource(e.target.value)}
                  className="gridui-settings-number-input"
                  style={{ flex: 1 }}
                >
                  {feeds.map(f => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                  {feeds.length === 0 && (
                    <option value="email">Email</option>
                  )}
                </select>
                <label style={{ color: 'var(--grid-text-secondary, #8b949e)', minWidth: 30 }}>Page</label>
                <input
                  type="number"
                  value={testPage}
                  onChange={e => setTestPage(Math.max(500, Math.min(599, Number(e.target.value))))}
                  className="gridui-settings-number-input"
                  style={{ width: 70 }}
                  min={500}
                  max={599}
                />
              </div>
              {/* Title */}
              <input
                type="text"
                value={testTitle}
                onChange={e => setTestTitle(e.target.value)}
                placeholder="Feed item title..."
                className="gridui-settings-number-input"
                style={{ width: '100%' }}
              />
              {/* Body */}
              <textarea
                value={testBody}
                onChange={e => setTestBody(e.target.value)}
                placeholder="Feed item body text..."
                className="gridui-settings-number-input"
                style={{ width: '100%', minHeight: 48, resize: 'vertical', fontFamily: 'inherit' }}
                rows={2}
              />
              {/* Push button */}
              <button
                onClick={pushTestItem}
                className="gridui-display-mode-btn gridui-display-mode-btn--active"
                style={{ alignSelf: 'flex-end', padding: '4px 16px' }}
                disabled={pushing || !snackbarConnected}
              >
                {pushing ? 'Pushing...' : <><Icon name="send" size={14} /> Push to Teletext</>}
              </button>
            </div>
          </div>
        </div>

        {/* Feed Item History */}
        <div className="gridui-card">
          <div className="gridui-card-header">
            <Icon name="list_alt" size={16} />
            <h3 style={{ margin: 0, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>
              Recent Feed Items
            </h3>
            <span style={{ color: 'var(--grid-text-secondary, #8b949e)' }}>
              {feedItems.length} items
            </span>
          </div>
          <div className="gridui-card-body">
            {feedItems.length === 0 ? (
              <div style={{ color: 'var(--grid-text-secondary, #8b949e)', padding: '8px 0' }}>
                No feed items yet. Push a test item above, or wait for skills to broadcast.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 300, overflowY: 'auto' }}>
                {feedItems.map(item => (
                  <div key={item.id} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 8,
                    padding: '6px 8px',
                    background: 'var(--grid-bg-secondary, #161b22)',
                    borderRadius: 4,
                    border: '1px solid var(--grid-border, #30363d)',
                  }}>
                    {/* Source icon */}
                    <Icon name={feeds.find(f => f.id === item.source)?.icon || 'rss_feed'} size={14} style={{ marginTop: 1 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, marginBottom: 2 }}>{item.title}</div>
                      <div style={{ color: 'var(--grid-text-secondary, #8b949e)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {item.body}
                      </div>
                      <div style={{ display: 'flex', gap: 8, marginTop: 3, color: 'var(--grid-text-secondary, #8b949e)' }}>
                        <span>P{item.page}</span>
                        <span>{formatDate(item.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
