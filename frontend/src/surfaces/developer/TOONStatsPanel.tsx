import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'

interface TOONStats {
  total_requests: number
  total_hits: number
  total_misses: number
  cache_hit_rate: number
  total_bytes_saved: number
  avg_compression_ratio: number
  recent_encodes: Array<{
    key: string
    compression_ratio: number
    original_size: number
    toon_size: number
    created_at: string
  }>
}

const SNACKBAR_API = 'http://localhost:8484'

export function TOONStatsPanel() {
  const [stats, setStats] = useState<TOONStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchStats() {
      try {
        const res = await fetch(`${SNACKBAR_API}/api/toon/stats`, {
          signal: AbortSignal.timeout(3000),
        })
        if (!res.ok) throw new Error(`TOON stats unavailable (${res.status})`)
        const data = await res.json()
        if (!cancelled) {
          setStats(data)
          setError(null)
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message || 'Failed to load TOON stats')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchStats()
    const interval = autoRefresh ? setInterval(fetchStats, 5000) : undefined
    return () => {
      cancelled = true
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh])

  const handleClearCache = async () => {
    if (!window.confirm('Clear TOON cache? This will remove all cached encodings.')) return
    try {
      const res = await fetch(`${SNACKBAR_API}/api/toon/clear`, {
        method: 'POST',
        signal: AbortSignal.timeout(3000),
      })
      if (!res.ok) throw new Error(`Clear failed (${res.status})`)
      setStats(null)
      setTimeout(() => window.location.reload(), 500)
    } catch (err: any) {
      alert(err.message || 'Clear failed')
    }
  }

  if (loading) {
    return (
      <div className="developer-panel">
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">TOON Context Optimization</h3>
          <span className="developer-panel-count">Loading...</span>
        </div>
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="developer-panel" style={{ border: '1px solid var(--pico-form-element-invalid-border-color, #f85149)' }}>
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">TOON Context Optimization</h3>
          <span className="developer-panel-count" style={{ color: 'var(--pico-form-element-invalid-border-color, #f85149)' }}>Error</span>
        </div>
        <div style={{ padding: '12px', color: 'var(--pico-form-element-invalid-border-color, #f85149)', fontSize: '12px' }}>
          {error || 'TOON service unavailable'}
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Overview Stats */}
      <div className="developer-panel">
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">TOON Context Optimization</h3>
          <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            <label style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
              <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} style={{ margin: 0 }} />
              Auto-refresh
            </label>
            <button
              className="usx-header-btn"
              onClick={handleClearCache}
              title="Clear TOON cache"
              style={{ padding: '2px 4px', minWidth: 'auto' }}
            >
              <Icon name="delete" size={14} />
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, padding: '12px' }}>
          {/* Requests */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Total Requests</span>
            <span style={{ fontSize: '18px', fontWeight: 'bold', fontFamily: 'monospace' }}>{stats.total_requests}</span>
          </div>

          {/* Cache Hit Rate */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Cache Hit Rate</span>
            <span style={{ fontSize: '18px', fontWeight: 'bold', fontFamily: 'monospace', color: 'var(--pico-ins-color, #3fb950)' }}>
              {(stats.cache_hit_rate * 100).toFixed(1)}%
            </span>
          </div>

          {/* Hits */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Cache Hits</span>
            <span style={{ fontSize: '14px', fontFamily: 'monospace' }}>{stats.total_hits}</span>
          </div>

          {/* Misses */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Cache Misses</span>
            <span style={{ fontSize: '14px', fontFamily: 'monospace' }}>{stats.total_misses}</span>
          </div>

          {/* Bytes Saved */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Bytes Saved</span>
            <span style={{ fontSize: '14px', fontFamily: 'monospace', color: 'var(--pico-ins-color, #3fb950)' }}>
              {(stats.total_bytes_saved / 1024).toFixed(1)} KB
            </span>
          </div>

          {/* Avg Compression */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Avg Compression</span>
            <span style={{ fontSize: '14px', fontFamily: 'monospace' }}>{(stats.avg_compression_ratio * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Recent Encodes */}
      <div className="developer-panel" style={{ marginTop: '16px' }}>
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Recent Encodes</h3>
          <span className="developer-panel-count">{stats.recent_encodes.length}</span>
        </div>

        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          {stats.recent_encodes.length === 0 ? (
            <div style={{ padding: '12px', color: 'var(--pico-muted-color, #8b949e)', fontSize: '12px' }}>
              No recent encodes
            </div>
          ) : (
            stats.recent_encodes.map((encode, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  borderBottom: '1px solid var(--pico-border-color, #30363d)',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: 'var(--pico-primary, #58a6ff)', wordBreak: 'break-all' }}>
                    {encode.key.substring(0, 50)}...
                  </div>
                  <div style={{ color: 'var(--pico-muted-color, #8b949e)', marginTop: 2 }}>
                    {encode.original_size} → {encode.toon_size} bytes ({(encode.compression_ratio * 100).toFixed(1)}%)
                  </div>
                </div>
                <span
                  style={{
                    marginLeft: 8,
                    whiteSpace: 'nowrap',
                    color: 'var(--pico-ins-color, #3fb950)',
                    fontSize: '10px',
                  }}
                >
                  {new Date(encode.created_at).toLocaleTimeString()}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Info */}
      <div className="developer-panel" style={{ marginTop: '16px', background: 'var(--pico-code-background, #0d1117)', padding: '12px' }}>
        <div style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)', lineHeight: '1.6' }}>
          <p style={{ margin: '0 0 8px 0' }}>
            <strong>TOON (Token-Optimized Object Notation)</strong> reduces token usage by 30-60% through intelligent compression
            while preserving semantic meaning.
          </p>
          <p style={{ margin: '0 0 8px 0' }}>
            • <strong>Cache Hits</strong>: Reusing previously encoded content saves 100% of encoding tokens
          </p>
          <p style={{ margin: '0 0 8px 0' }}>
            • <strong>Compression Ratio</strong>: Lower is better (50% = 50% of original tokens)
          </p>
          <p style={{ margin: 0 }}>
            • <strong>Use Cases</strong>: Markdown docs, JSON configs, CSV data, large context windows
          </p>
        </div>
      </div>
    </>
  )
}
