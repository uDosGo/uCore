/* ═══════════════════════════════════════════════════════════════════
   LogsPanel — Reusable real-time log viewer with level filters
   ═══════════════════════════════════════════════════════════════════
   Consumed by: UServerSurface (Logs tab), DeveloperSurface
   API: GET /api/spool/feed?max=N
   Features: level-tab filtering, service filter, auto-refresh,
   copy-to-clipboard, real-time polling.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { Icon } from '../../components/Icon'

const SNACKBAR_API = 'http://localhost:8484'

export interface LogEntry {
  timestamp: string
  service: string
  level: 'info' | 'warn' | 'error'
  message: string
}

type LogLevel = 'all' | 'info' | 'warn' | 'error'

interface LogsPanelProps {
  /** Max log entries to fetch */
  max?: number
  /** Polling interval in ms (default 15s) */
  pollInterval?: number
  /** Optional title override */
  title?: string
}

const LEVEL_CONFIG: Record<LogLevel, { label: string; color: string }> = {
  all:   { label: 'All',    color: '#8b949e' },
  info:  { label: 'Info',   color: '#3fb950' },
  warn:  { label: 'Warn',   color: '#d29922' },
  error: { label: 'Error',  color: '#f85149' },
}

export function LogsPanel({ max = 100, pollInterval = 15000, title = 'Logs' }: LogsPanelProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [levelFilter, setLevelFilter] = useState<LogLevel>('all')
  const [serviceFilter, setServiceFilter] = useState('')
  const [copied, setCopied] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/spool/feed?max=${max}`, {
        signal: AbortSignal.timeout(5000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const entries = Array.isArray(data.entries) ? data.entries : []
      const mapped: LogEntry[] = entries.map((entry: any) => {
        const rawLevel = String(entry.level || 'INFO').toLowerCase()
        let level: LogEntry['level'] = 'info'
        if (rawLevel.includes('error') || rawLevel.includes('critical')) level = 'error'
        else if (rawLevel.includes('warn')) level = 'warn'
        return {
          timestamp: String(entry.timestamp || ''),
          service: String(entry.module || entry.source || 'unknown'),
          level,
          message: String(entry.message || ''),
        }
      })
      setLogs(mapped)
    } catch (e: any) {
      setError(e?.message || 'Failed to load logs')
    } finally {
      setLoading(false)
    }
  }, [max])

  useEffect(() => {
    void fetchLogs()
    const interval = setInterval(fetchLogs, pollInterval)
    return () => clearInterval(interval)
  }, [fetchLogs, pollInterval])

  // Derive unique service names from logs
  const services = useMemo(() => {
    const set = new Set<string>()
    logs.forEach(log => set.add(log.service))
    return Array.from(set).sort()
  }, [logs])

  const filtered = useMemo(() => {
    let result = logs
    if (levelFilter !== 'all') {
      result = result.filter(log => log.level === levelFilter)
    }
    if (serviceFilter) {
      const q = serviceFilter.toLowerCase()
      result = result.filter(log =>
        log.service.toLowerCase().includes(q) || log.message.toLowerCase().includes(q)
      )
    }
    return result
  }, [logs, levelFilter, serviceFilter])

  const levelCounts = useMemo(() => ({
    all: logs.length,
    info: logs.filter(l => l.level === 'info').length,
    warn: logs.filter(l => l.level === 'warn').length,
    error: logs.filter(l => l.level === 'error').length,
  }), [logs])

  const handleCopyAll = async () => {
    const text = filtered
      .map(log => `${log.timestamp} [${log.level.toUpperCase()}] ${log.service} — ${log.message}`)
      .join('\n')
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleCopyRow = async (log: LogEntry) => {
    const text = `${log.timestamp} [${log.level.toUpperCase()}] ${log.service} — ${log.message}`
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <div className="userver-toolbar" style={{ flexShrink: 0 }}>
        <div className="userver-toolbar-left">
          <h2 className="userver-heading" style={{ margin: 0 }}>{title}</h2>
          <span className="userver-card-subtitle">
            {loading ? 'Loading…' : `${filtered.length} entries`}
            {' · '}polling {pollInterval / 1000}s
          </span>
        </div>
        <div className="userver-toolbar-actions" style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center' }}>
          <button className="userver-action-btn" onClick={() => void fetchLogs()} disabled={loading} title="Refresh now">
            <Icon name="refresh" size={14} />
          </button>
          <button className="userver-action-btn" onClick={handleCopyAll} title="Copy filtered logs">
            <Icon name="content_copy" size={14} />
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Level filter tabs */}
      <div style={{ display: 'flex', gap: 4, padding: '4px 16px', flexShrink: 0, borderBottom: '1px solid var(--pico-border-color, #30363d)' }}>
        {(Object.entries(LEVEL_CONFIG) as [LogLevel, typeof LEVEL_CONFIG[LogLevel]][]).map(([key, cfg]) => (
          <button
            key={key}
            onClick={() => setLevelFilter(key)}
            style={{
              padding: '4px 12px',
              fontSize: 11,
              fontWeight: 600,
              borderRadius: 999,
              border: 'none',
              cursor: 'pointer',
              background: levelFilter === key ? cfg.color : 'transparent',
              color: levelFilter === key ? '#fff' : cfg.color,
              transition: 'all 120ms',
            }}
          >
            {cfg.label} ({levelCounts[key]})
          </button>
        ))}
        <div style={{ flex: 1 }} />
        {/* Service filter input */}
        <input
          type="text"
          placeholder="Filter service/message…"
          value={serviceFilter}
          onChange={e => setServiceFilter(e.target.value)}
          style={{
            width: 200,
            fontSize: 11,
            padding: '3px 8px',
            borderRadius: 6,
            border: '1px solid var(--pico-border-color, #30363d)',
            background: 'var(--pico-card-sectioning-background-color, #1c2128)',
            color: 'var(--pico-color, #c9d1d9)',
          }}
        />
      </div>

      {/* Error banner */}
      {error && (
        <div className="userver-card" style={{ margin: '8px 16px 0', borderLeft: '3px solid #f85149', flexShrink: 0 }}>
          <div className="userver-card-content">
            <p className="userver-text" style={{ color: '#f85149', margin: 0, fontSize: 12 }}>
              {error}
            </p>
          </div>
        </div>
      )}

      {/* Log entries */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '8px 16px',
        }}
      >
        {filtered.length === 0 ? (
          <p className="userver-text" style={{ textAlign: 'center', padding: 32, color: 'var(--pico-muted-color, #8b949e)' }}>
            {logs.length === 0 ? 'No log entries yet.' : 'No entries match your filter.'}
          </p>
        ) : (
          filtered.map((log, idx) => (
            <div
              key={idx}
              className="userver-log-entry"
              style={{
                cursor: 'pointer',
                borderRadius: 4,
                padding: '2px 4px',
                marginBottom: 1,
              }}
              onClick={() => void handleCopyRow(log)}
              title="Click to copy this entry"
            >
              <span className="userver-log-time">{log.timestamp?.slice(11, 19) || log.timestamp || '--:--:--'}</span>
              <span className="userver-log-service">{log.service}</span>
              <span className={`userver-log-level ${log.level}`}>{log.level}</span>
              <span className="userver-log-message">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}