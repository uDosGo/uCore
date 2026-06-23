/* ═══════════════════════════════════════════════════════════════════
   UServerSurface — USX Schema v3.1 Server Management Surface
   ═══════════════════════════════════════════════════════════════════
   uServer backend ops: dashboard, services (with actions), logs,
   models, agents, budget, story links, and snackbar management.
   System pages/functions → /system (USystemSurface).
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { GlobalToolbar } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar, { SidebarNavItem } from '../../components/VaultSidebar'
import AssistUISurface from '../assistui/AssistUISurface'
import { ModelsPanel } from '../developer/ModelsPanel'
import { AgentsPanel } from '../developer/AgentsPanel'
import { LogsPanel } from '../shared/LogsPanel'
import '../../styles/userver.css'

// ─── Constants ───────────────────────────────────────────────────────
const SNACKBAR_API = 'http://localhost:8484'

// ─── Legacy Tab Mapping ──────────────────────────────────────────────
const LEGACY_TAB_MAP: Record<string, string> = {
  'overview': 'dashboard',
  'service-status': 'services',
}

// ─── Types ──────────────────────────────────────────────────────────
const SERVER_TABS = [
  'dashboard',
  'services',
  'logs',
  'models',
  'agents',
  'budget',
  'story',
  'snacks',
] as const
type UServerTab = typeof SERVER_TABS[number]

interface ServiceStatus {
  name: string
  status: 'up' | 'degraded' | 'down'
  port: number
  uptime: number
  type: 'system' | 'user'
  description: string
}

interface SnackEntry {
  id: string
  type: string
  priority: string
  status: string
  source: string
  timestamp: string
  content?: Record<string, unknown>
}

interface BudgetStatusResponse {
  usage: {
    period_start: string
    period_end: string
    total_cost: number
    total_calls: number
    blocked_calls: number
    monthly_limit: number
    remaining_budget: number
    over_limit: boolean
  }
  policy: {
    monthly_usd_limit: number
    default_estimated_cost: number
    guarded_endpoints: string[]
    per_model_limits: Record<string, number>
  }
}

interface BudgetUsageEntry {
  ts: string
  endpoint: string
  provider: string
  model: string
  estimated_cost: number
  actual_cost: number
  status_code: number
  blocked: number
}

// ─── Default Data ───────────────────────────────────────────────────
const DEFAULT_SERVICES: ServiceStatus[] = [
  { name: 'snackbar', status: 'up', port: 8484, uptime: 99.9, type: 'system', description: 'Container orchestrator & workflow runner' },
  { name: 'secret-server', status: 'up', port: 30001, uptime: 99.8, type: 'user', description: 'AES-256-GCM encrypted secret vault' },
  { name: 'hivemind', status: 'up', port: 8485, uptime: 99.7, type: 'system', description: 'AI orchestration & agent routing' },
  { name: 'feed-spool', status: 'up', port: 8486, uptime: 99.5, type: 'system', description: 'Feed spooler & transport' },
  { name: 'vault-mcp', status: 'degraded', port: 0, uptime: 95.2, type: 'user', description: 'MCP server for Vault access' },
  { name: 'email-feed', status: 'down', port: 0, uptime: 0, type: 'user', description: 'Email to feed processor' },
]

const DEFAULT_LOGS_SAMPLE = [
  { timestamp: '2026-05-23 16:15:22', service: 'snackbar', level: 'info' as const, message: 'Workflow "daily-docs-sync" completed successfully' },
  { timestamp: '2026-05-23 16:14:00', service: 'hivemind', level: 'info' as const, message: 'Agent "code-reviewer" dispatched to PR #42' },
  { timestamp: '2026-05-23 16:10:30', service: 'email-feed', level: 'error' as const, message: 'IMAP connection failed: invalid credentials' },
  { timestamp: '2026-05-23 16:05:00', service: 'vault-mcp', level: 'info' as const, message: 'MCP client connected: uCode2 Gateway' },
]

// ─── DashboardTab — Live Ops Dashboard ────────────────────────────────
function DashboardTab({ services, surfaces, budgetRemaining, budgetOverLimit }: {
  services: ServiceStatus[]
  surfaces: { label: string; status: string; port: number; icon: string; color: string; url: string }[]
  budgetRemaining: number | null
  budgetOverLimit: boolean
}) {
  const upCount = services.filter(s => s.status === 'up').length
  const degradedCount = services.filter(s => s.status === 'degraded').length
  const downCount = services.filter(s => s.status === 'down').length
  const runningSurfaces = surfaces.filter(s => s.status === 'running').length

  const healthPct = services.length > 0 ? Math.round((upCount / services.length) * 100) : 0

  return (
    <div className="userver-grid">
      {/* ─── Health Summary Banner ─────────────────────────────── */}
      <div className="userver-card userver-welcome-card">
        <div className="userver-card-content">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h2 className="userver-heading" style={{ margin: 0 }}>Server Operations</h2>
              <p className="userver-text" style={{ margin: '4px 0 0', color: 'var(--pico-muted-color, #8b949e)' }}>
                {services.length} services · {runningSurfaces}/{surfaces.length} surfaces online
              </p>
            </div>
            {/* Health ring */}
            <div style={{
              width: 56, height: 56, borderRadius: '50%',
              border: `3px solid ${healthPct >= 80 ? '#3fb950' : healthPct >= 50 ? '#d29922' : '#f85149'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, fontSize: 16, fontWeight: 700,
              color: healthPct >= 80 ? '#3fb950' : healthPct >= 50 ? '#d29922' : '#f85149',
            }}>
              {healthPct}%
            </div>
          </div>
          <div className="userver-stats-row" style={{ marginTop: 12 }}>
            <div className="userver-stat">
              <span className="userver-stat-value" style={{ color: '#3fb950' }}>{upCount}</span>
              <span className="userver-stat-label">Up</span>
            </div>
            <div className="userver-stat">
              <span className="userver-stat-value" style={{ color: '#d29922' }}>{degradedCount}</span>
              <span className="userver-stat-label">Degraded</span>
            </div>
            <div className="userver-stat">
              <span className="userver-stat-value" style={{ color: '#f85149' }}>{downCount}</span>
              <span className="userver-stat-label">Down</span>
            </div>
            <div className="userver-stat">
              <span className="userver-stat-value" style={{ color: budgetOverLimit ? '#f85149' : '#58a6ff' }}>
                {budgetRemaining === null ? '—' : `$${budgetRemaining.toFixed(2)}`}
              </span>
              <span className="userver-stat-label">Budget left</span>
            </div>
          </div>
        </div>
      </div>

      {/* ─── Surfaces ──────────────────────────────────────────── */}
      <div className="userver-card">
        <div className="userver-card-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
            <Icon name="grid_view" size={16} />
            Surfaces
          </h3>
          <span className="userver-card-subtitle">uDos Connect registry</span>
        </div>
        <div className="userver-card-content">
          {surfaces.length === 0 ? (
            <p className="userver-text" style={{ color: 'var(--pico-muted-color, #8b949e)' }}>No surfaces discovered.</p>
          ) : (
            surfaces.slice(0, 5).map(surface => (
              <div key={surface.label} className="userver-service-row">
                <div className="userver-service-info">
                  <span className="userver-service-name">
                    <Icon name={surface.icon} size={16} style={{ marginRight: 6, color: surface.color }} />
                    {surface.label}
                  </span>
                </div>
                <div className="userver-service-meta">
                  <a href={surface.url} style={{ color: surface.color, fontSize: 12 }}>:{surface.port}</a>
                  <span className={`userver-service-status ${surface.status}`}>
                    {surface.status === 'running' ? 'Online' : 'Offline'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ─── Service Status ────────────────────────────────────── */}
      <div className="userver-card">
        <div className="userver-card-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
            <Icon name="dns" size={16} />
            Service Status
          </h3>
          <span className="userver-card-subtitle">Live health</span>
        </div>
        <div className="userver-card-content">
          {services.slice(0, 5).map(svc => (
            <div key={svc.name} className="userver-service-row">
              <div className="userver-service-info">
                <span className="userver-service-name">{svc.name}</span>
                <span className="userver-service-desc">{svc.description}</span>
              </div>
              <div className="userver-service-meta">
                <span className={`userver-service-status ${svc.status}`}>
                  {svc.status === 'up' ? 'Online' : svc.status === 'degraded' ? 'Degraded' : 'Offline'}
                </span>
                {svc.port > 0 && <span className="userver-service-port">:{svc.port}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ─── Recent Logs ───────────────────────────────────────── */}
      <div className="userver-card">
        <div className="userver-card-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
            <Icon name="article" size={16} />
            Recent Activity
          </h3>
          <span className="userver-card-subtitle">Latest events</span>
        </div>
        <div className="userver-card-content">
          {DEFAULT_LOGS_SAMPLE.map((log, idx) => (
            <div key={idx} className="userver-log-entry">
              <span className="userver-log-time">{log.timestamp}</span>
              <span className="userver-log-service">{log.service}</span>
              <span className={`userver-log-level ${log.level}`}>{log.level}</span>
              <span className="userver-log-message">{log.message}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ─── Quick Links ───────────────────────────────────────── */}
      <div className="userver-card">
        <div className="userver-card-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
            <Icon name="bolt" size={16} />
            Quick Links
          </h3>
        </div>
        <div className="userver-card-content" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <a href="/system?tab=secrets" className="userver-action-btn" style={{ textDecoration: 'none' }}>
            <Icon name="key" size={14} style={{ marginRight: 6 }} />
            Secret Store
          </a>
          <a href="/system?tab=settings" className="userver-action-btn" style={{ textDecoration: 'none' }}>
            <Icon name="settings" size={14} style={{ marginRight: 6 }} />
            Settings
          </a>
        </div>
      </div>
    </div>
  )
}

// ─── ServicesTab — Live Services with Actions ─────────────────────────
function ServicesTab({ services }: { services: ServiceStatus[] }) {
  const [actionMsg, setActionMsg] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<'all' | 'system' | 'user'>('all')

  const filtered = typeFilter === 'all'
    ? services
    : services.filter(s => s.type === typeFilter)

  const handleAction = async (name: string, action: 'start' | 'stop' | 'restart') => {
    setActionLoading(`${name}:${action}`)
    setActionMsg(null)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/surfaces/${encodeURIComponent(name)}/${action}`, {
        method: 'POST',
        signal: AbortSignal.timeout(6000),
      })
      const data = await res.json().catch(() => ({}))
      if (res.ok) {
        setActionMsg(`${name} ${action} → ${data.status || 'ok'}`)
      } else {
        setActionMsg(`${name} ${action} failed: ${data.error || `HTTP ${res.status}`}`)
      }
    } catch (e: any) {
      setActionMsg(`${name} ${action} error: ${e?.message || 'request failed'}`)
    } finally {
      setActionLoading(null)
      setTimeout(() => setActionMsg(null), 4000)
    }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Toolbar */}
      <div className="userver-toolbar" style={{ flexShrink: 0 }}>
        <div className="userver-toolbar-left">
          <h2 className="userver-heading" style={{ margin: 0 }}>Services</h2>
          <span className="userver-card-subtitle">{filtered.length} of {services.length} services</span>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          {(['all', 'system', 'user'] as const).map(t => (
            <button
              key={t}
              className="userver-action-btn"
              onClick={() => setTypeFilter(t)}
              style={{
                borderColor: typeFilter === t ? '#58a6ff' : undefined,
                color: typeFilter === t ? '#58a6ff' : undefined,
              }}
            >
              {t === 'all' ? 'All' : t === 'system' ? 'System' : 'User'}
            </button>
          ))}
        </div>
      </div>

      {/* Action feedback */}
      {actionMsg && (
        <div className="userver-card" style={{ margin: '0 16px 12px', borderLeft: '3px solid #58a6ff', flexShrink: 0 }}>
          <div className="userver-card-content">
            <p className="userver-text" style={{ margin: 0, fontSize: 12 }}>{actionMsg}</p>
          </div>
        </div>
      )}

      {/* Service cards */}
      <div className="userver-grid" style={{ flex: 1, overflow: 'auto', padding: '0 16px 16px' }}>
        {filtered.map(svc => {
          const isLoading = actionLoading === `${svc.name}:start` || actionLoading === `${svc.name}:stop` || actionLoading === `${svc.name}:restart`
          return (
            <div key={svc.name} className="userver-card" style={{ borderLeft: `3px solid ${
              svc.status === 'up' ? '#3fb950' : svc.status === 'degraded' ? '#d29922' : '#f85149'
            }` }}>
              <div className="userver-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <h3 style={{ margin: 0 }}>{svc.name}</h3>
                  <span style={{
                    fontSize: 10,
                    padding: '2px 6px',
                    borderRadius: 4,
                    background: svc.type === 'system'
                      ? 'rgba(88,166,255,0.15)'
                      : 'rgba(240,136,62,0.15)',
                    color: svc.type === 'system' ? '#58a6ff' : '#f0883e',
                    fontWeight: 600,
                  }}>
                    {svc.type}
                  </span>
                </div>
                <span className={`userver-service-status ${svc.status}`}>
                  {svc.status === 'up' ? 'Online' : svc.status === 'degraded' ? 'Degraded' : 'Offline'}
                </span>
              </div>
              <div className="userver-card-content">
                <p className="userver-text" style={{ margin: '0 0 8px', fontSize: 12 }}>{svc.description}</p>
                <div className="userver-service-details" style={{ gap: 8, fontSize: 11 }}>
                  {svc.port > 0 && <span>Port: <strong>{svc.port}</strong></span>}
                  <span>Uptime: <strong>{svc.uptime}%</strong></span>
                </div>
                {/* Action buttons */}
                <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
                  {svc.status !== 'up' && (
                    <button
                      className="userver-action-btn"
                      onClick={() => void handleAction(svc.name, 'start')}
                      disabled={isLoading}
                      style={{ borderColor: '#3fb950', color: '#3fb950' }}
                    >
                      <Icon name="play_arrow" size={14} style={{ marginRight: 4 }} />
                      {isLoading ? '...' : 'Start'}
                    </button>
                  )}
                  {svc.status === 'up' && (
                    <button
                      className="userver-action-btn"
                      onClick={() => void handleAction(svc.name, 'restart')}
                      disabled={isLoading}
                      style={{ borderColor: '#d29922', color: '#d29922' }}
                    >
                      <Icon name="refresh" size={14} style={{ marginRight: 4 }} />
                      {isLoading ? '...' : 'Restart'}
                    </button>
                  )}
                  {svc.status === 'up' && (
                    <button
                      className="userver-action-btn"
                      onClick={() => void handleAction(svc.name, 'stop')}
                      disabled={isLoading}
                      style={{ borderColor: '#f85149', color: '#f85149' }}
                    >
                      <Icon name="stop" size={14} style={{ marginRight: 4 }} />
                      {isLoading ? '...' : 'Stop'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── BudgetTab ────────────────────────────────────────────────────────
function BudgetTab() {
  const [status, setStatus] = useState<BudgetStatusResponse | null>(null)
  const [usage, setUsage] = useState<BudgetUsageEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string>('')

  const loadBudget = useCallback(async () => {
    setLoading(true)
    try {
      const [statusRes, usageRes] = await Promise.all([
        fetch(`${SNACKBAR_API}/api/budget/status`, { signal: AbortSignal.timeout(4000) }),
        fetch(`${SNACKBAR_API}/api/budget/usage?limit=20`, { signal: AbortSignal.timeout(4000) }),
      ])
      if (!statusRes.ok) throw new Error(`status HTTP ${statusRes.status}`)
      const statusData = await statusRes.json()
      setStatus(statusData)
      if (usageRes.ok) {
        const usageData = await usageRes.json()
        setUsage(Array.isArray(usageData.entries) ? usageData.entries : [])
      }
      setMessage('')
    } catch (e: any) {
      setMessage(e?.message || 'Failed to load budget data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void loadBudget() }, [loadBudget])

  const reloadPolicy = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/budget/reload`, { method: 'POST', signal: AbortSignal.timeout(4000) })
      if (!res.ok) throw new Error(`reload HTTP ${res.status}`)
      setMessage('Budget policy reloaded')
      await loadBudget()
    } catch (e: any) {
      setMessage(e?.message || 'Failed to reload budget policy')
      setLoading(false)
    }
  }

  const runSample = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/skills/route_task/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: 'Write a simple hello world function in Python', complexity: 'simple', execute: false }),
        signal: AbortSignal.timeout(8000),
      })
      if (!res.ok) throw new Error(`run sample HTTP ${res.status}`)
      const data = await res.json()
      setMessage(`Sample executed. Budget check: ${data.success ? 'ALLOWED' : 'BLOCKED'}`)
      await loadBudget()
    } catch (e: any) {
      setMessage(e?.message || 'Failed to run sample')
      setLoading(false)
    }
  }

  const usageStats = status?.usage
  const policy = status?.policy

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Budget</h2>
          <span className="userver-card-subtitle">Usage logging and cost guardrails</span>
        </div>
        <div className="userver-toolbar-actions" style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="userver-action-btn" onClick={runSample} disabled={loading} title="Execute a sample task to test budget enforcement">
            {loading ? 'Running...' : 'Run Sample'}
          </button>
          <button className="userver-action-btn" onClick={loadBudget} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <button className="userver-action-btn" onClick={reloadPolicy} disabled={loading}>
            Reload Policy
          </button>
        </div>
      </div>

      {message && (
        <div className="userver-card" style={{ margin: '0 16px 16px' }}>
          <div className="userver-card-content">
            <p className="userver-text">{message}</p>
          </div>
        </div>
      )}

      <div className="userver-grid" style={{ padding: '0 16px' }}>
        <div className="userver-card">
          <div className="userver-card-header">
            <h3>Current Period</h3>
          </div>
          <div className="userver-card-content">
            <div className="userver-service-details" style={{ flexWrap: 'wrap', gap: 8 }}>
              <span>Total Cost: <strong>${usageStats?.total_cost?.toFixed(4) || '0.0000'}</strong></span>
              <span>Monthly Limit: <strong>${usageStats?.monthly_limit?.toFixed(2) || '0.00'}</strong></span>
              <span>Remaining: <strong>${usageStats?.remaining_budget?.toFixed(4) || '0.0000'}</strong></span>
              <span>Calls: <strong>{usageStats?.total_calls ?? 0}</strong></span>
              <span>Blocked: <strong>{usageStats?.blocked_calls ?? 0}</strong></span>
            </div>
            {usageStats?.over_limit && (
              <p className="userver-text" style={{ color: '#f85149', marginTop: 8 }}>
                Budget limit currently exceeded.
              </p>
            )}
          </div>
        </div>

        <div className="userver-card">
          <div className="userver-card-header">
            <h3>Policy</h3>
          </div>
          <div className="userver-card-content">
            <div className="userver-service-details" style={{ flexWrap: 'wrap', gap: 8 }}>
              <span>Default Cost: <strong>${policy?.default_estimated_cost?.toFixed(4) || '0.0000'}</strong></span>
              <span>Guarded Endpoints: <strong>{policy?.guarded_endpoints?.length ?? 0}</strong></span>
              <span>Per-Model Limits: <strong>{Object.keys(policy?.per_model_limits || {}).length}</strong></span>
            </div>
            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {(policy?.guarded_endpoints || []).map(endpoint => (
                <span key={endpoint} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 8, background: 'var(--pico-card-sectioning-background-color, #1c2128)' }}>
                  {endpoint}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Recent Usage</h3>
        </div>
        <div className="userver-card-content">
          {usage.length === 0 ? (
            <p className="userver-text">No usage entries recorded yet.</p>
          ) : (
            usage.slice(0, 20).map((row, idx) => (
              <div key={`${row.ts}-${idx}`} className="userver-log-entry">
                <span className="userver-log-time">{row.ts?.slice(11, 19) || '--:--:--'}</span>
                <span className="userver-log-service">{row.endpoint}</span>
                <span className={`userver-log-level ${row.blocked ? 'error' : 'info'}`}>
                  {row.blocked ? 'blocked' : `HTTP ${row.status_code}`}
                </span>
                <span className="userver-log-message">
                  cost=${Number(row.actual_cost || 0).toFixed(4)}
                  {row.model ? ` · model=${row.model}` : ''}
                  {row.provider ? ` · provider=${row.provider}` : ''}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// ─── StoryLinksTab ────────────────────────────────────────────────────
function StoryLinksTab({ onNavigate }: { onNavigate: (path: string) => void }) {
  const links = [
    { title: 'User Setup Story', subtitle: 'Legacy alias', description: 'Opens Story Builder via /user-setup-story alias.', path: '/user-setup-story', icon: 'flag' },
    { title: 'Story Builder', subtitle: 'S101 page', description: 'Core story workspace for creating and managing stories.', path: '/story-builder', icon: 'auto_stories' },
    { title: 'Story/gtx-form Styles & Examples', subtitle: 'Legacy alias', description: 'Opens the Story Builder route for gtx-form style/example workflows.', path: '/story/gtx-form', icon: 'design_services' },
  ]

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Story Links</h2>
          <span className="userver-card-subtitle">Quick links for story setup, builder, and gtx-form aliases.</span>
        </div>
      </div>
      <div className="userver-grid" style={{ padding: '0 16px' }}>
        {links.map(link => (
          <div key={link.path} className="userver-card">
            <div className="userver-card-header">
              <h3>{link.title}</h3>
              <span className="userver-card-subtitle">{link.subtitle}</span>
            </div>
            <div className="userver-card-content">
              <p className="userver-text" style={{ marginBottom: 12 }}>{link.description}</p>
              <button className="userver-action-btn" onClick={() => onNavigate(link.path)}>
                <Icon name={link.icon} size={14} style={{ marginRight: 6 }} />
                Open {link.path}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Snacks/Snackbar Tab ──────────────────────────────────────────────
function SnacksTab() {
  const [queue, setQueue] = useState<SnackEntry[]>([])
  const [history, setHistory] = useState<SnackEntry[]>([])
  const [badges, setBadges] = useState<Record<string, unknown>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSnacks = useCallback(async () => {
    try {
      setError(null)
      const [queueRes, historyRes, badgesRes] = await Promise.all([
        fetch(`${SNACKBAR_API}/api/snacks`, { signal: AbortSignal.timeout(4000) }),
        fetch(`${SNACKBAR_API}/api/snacks/history?limit=20`, { signal: AbortSignal.timeout(4000) }),
        fetch(`${SNACKBAR_API}/api/snacks/system/badges`, { signal: AbortSignal.timeout(4000) }),
      ])
      if (queueRes.ok) {
        const data = await queueRes.json()
        setQueue(Array.isArray(data.snacks) ? data.snacks : [])
      }
      if (historyRes.ok) {
        const data = await historyRes.json()
        setHistory(Array.isArray(data.snacks) ? data.snacks : [])
      }
      if (badgesRes.ok) {
        const data = await badgesRes.json()
        setBadges(data.badges && typeof data.badges === 'object' ? data.badges : {})
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load snacks data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => { await loadSnacks(); if (cancelled) return })()
    return () => { cancelled = true }
  }, [loadSnacks])

  const handleClearQueue = async () => {
    try {
      await fetch(`${SNACKBAR_API}/api/snacks/queue`, { method: 'DELETE', signal: AbortSignal.timeout(4000) })
      await loadSnacks()
    } catch (e: any) {
      setError(e?.message || 'Failed to clear queue')
    }
  }

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Snacks & Snackbar</h2>
          <span className="userver-card-subtitle">{loading ? 'Loading…' : `${queue.length} queued · ${history.length} recent`}</span>
        </div>
        <div className="userver-toolbar-actions" style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="userver-action-btn" onClick={loadSnacks} disabled={loading}>{loading ? 'Refreshing...' : 'Refresh'}</button>
          <button className="userver-action-btn" onClick={handleClearQueue} disabled={loading || queue.length === 0}>Clear Queue</button>
        </div>
      </div>

      {error && (
        <div className="userver-card" style={{ margin: '0 16px 16px', borderLeft: '3px solid #f85149' }}>
          <div className="userver-card-content"><p className="userver-text" style={{ color: '#f85149' }}>{error}</p></div>
        </div>
      )}

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header"><h3>Snackbar Service Status</h3></div>
        <div className="userver-card-content">
          <div className="userver-service-details" style={{ flexWrap: 'wrap', gap: 12 }}>
            <span>Queue: <strong>{queue.length}</strong></span>
            <span>History: <strong>{history.length}</strong></span>
            <span>Endpoint: <strong>{SNACKBAR_API}</strong></span>
          </div>
          {Object.keys(badges).length > 0 && (
            <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {Object.entries(badges).map(([key, value]) => (
                <span key={key} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 8, background: 'var(--pico-card-sectioning-background-color, #1c2128)' }}>
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header"><h3>Pending Queue</h3></div>
        <div className="userver-card-content">
          {queue.length === 0 ? <p className="userver-text">No snacks currently queued.</p> : (
            queue.slice(0, 25).map(snack => (
              <div key={snack.id} className="userver-log-entry">
                <span className="userver-log-time">{snack.timestamp?.slice(11, 19) || '--:--:--'}</span>
                <span className="userver-log-service">{snack.type}</span>
                <span className="userver-log-level info">{snack.priority}</span>
                <span className="userver-log-message">{snack.status} · {snack.source}</span>
              </div>
            ))
          )}
        </div>
      </div>
      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header"><h3>Recent History</h3></div>
        <div className="userver-card-content">
          {history.length === 0 ? <p className="userver-text">No snack history yet.</p> : (
            history.slice(0, 25).map(snack => (
              <div key={snack.id} className="userver-log-entry">
                <span className="userver-log-time">{snack.timestamp?.slice(11, 19) || '--:--:--'}</span>
                <span className="userver-log-service">{snack.type}</span>
                <span className={`userver-log-level ${snack.status === 'failed' ? 'error' : 'info'}`}>{snack.status}</span>
                <span className="userver-log-message">{snack.source}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Main Surface ───────────────────────────────────────────────────
export default function UServerSurface() {
  const location = useLocation()
  const navigate = useNavigate()
  const tabState = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const raw = (params.get('tab') || 'dashboard').toLowerCase()
    const mapped = LEGACY_TAB_MAP[raw] || raw
    const candidate = mapped as UServerTab
    return { raw, mapped, selectedTab: SERVER_TABS.includes(candidate) ? candidate : 'dashboard' }
  }, [location.search])
  const [tab, setTab] = useState<UServerTab>(tabState.selectedTab)
  const [services, setServices] = useState<ServiceStatus[]>(DEFAULT_SERVICES)
  const [surfaces, setSurfaces] = useState<{ label: string; status: string; port: number; icon: string; color: string; url: string }[]>([])
  const [budgetRemaining, setBudgetRemaining] = useState<number | null>(null)
  const [budgetOverLimit, setBudgetOverLimit] = useState<boolean>(false)
  const [chatOpen, setChatOpen] = useState(false)
  const [sidebarMode, setSidebarMode] = useState<'server' | 'filepicker'>('server')
  const { sidebarOpen, setSidebarOpen, toggleSidebar } = useSurfaceShell()
  const runningCount = surfaces.filter(s => s.status === 'running').length

  useEffect(() => {
    if (tabState.mapped !== tabState.raw) {
      navigate(`/server?tab=${tabState.mapped}`, { replace: true })
    }
  }, [navigate, tabState.mapped, tabState.raw])

  useEffect(() => { setTab(tabState.selectedTab) }, [tabState.selectedTab])
  useEffect(() => { setSidebarOpen(true) }, [setSidebarOpen])

  // ─── Live data fetches ────────────────────────────────────────
  const refreshServices = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/system`, { signal: AbortSignal.timeout(4000) })
      if (!res.ok) return
      const data = await res.json()
      const svc = data?.services || {}

      const normalize = (v: unknown): ServiceStatus['status'] => {
        const t = String(v || '').toLowerCase()
        if (t === 'running' || t === 'up') return 'up'
        if (t === 'stopped' || t === 'down' || t === 'unavailable') return 'down'
        return 'degraded'
      }

      setServices([
        { name: 'ucore', status: normalize(svc.ucore || 'running'), port: 8484, uptime: 99.0, type: 'system', description: 'uCore backend API' },
        { name: 'ollama', status: normalize(svc.ollama), port: 11434, uptime: svc.ollama === 'running' ? 99.0 : 0, type: 'system', description: 'Local model runtime' },
        { name: 'docker', status: normalize(svc.docker), port: 0, uptime: svc.docker === 'running' ? 99.0 : 0, type: 'system', description: 'Container engine' },
        { name: 'frontend-dev', status: 'up', port: 5173, uptime: 99.0, type: 'user', description: 'Vite development server' },
        { name: 'hivemind', status: 'down', port: 8485, uptime: 0, type: 'system', description: 'Standalone Agent Router' },
      ])
    } catch { /* fallback */ }
  }, [])

  const refreshSurfaces = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/surfaces`, { signal: AbortSignal.timeout(4000) })
      if (!res.ok) return
      const data = await res.json()
      const list = Array.isArray(data.surfaces) ? data.surfaces : []
      setSurfaces(list.map((s: any) => ({
        label: s.label || s.name || 'Unknown',
        status: s.status || 'stopped',
        port: s.port || 0,
        icon: s.icon || 'widgets',
        color: s.color || '#58a6ff',
        url: s.url || `http://localhost:${s.port || 0}`,
      })))
    } catch { /* keep empty */ }
  }, [])

  const refreshBudget = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/budget/status`, { signal: AbortSignal.timeout(4000) })
      if (!res.ok) return
      const data = await res.json()
      const u = data?.usage || {}
      const r = Number(u.remaining_budget)
      setBudgetRemaining(Number.isFinite(r) ? r : null)
      setBudgetOverLimit(Boolean(u.over_limit))
    } catch { /* keep */ }
  }, [])

  useEffect(() => { refreshServices(); refreshSurfaces() }, [refreshServices, refreshSurfaces])
  useEffect(() => { refreshBudget(); const iv = setInterval(refreshBudget, 30000); return () => clearInterval(iv) }, [refreshBudget])

  const setTabAndRoute = (nextTab: UServerTab) => { setTab(nextTab); navigate(`/server?tab=${nextTab}`) }

  const serverNavItems: SidebarNavItem[] = [
    { id: 'dashboard', icon: 'home', label: 'Dashboard', active: tab === 'dashboard', onClick: () => setTabAndRoute('dashboard') },
    { id: 'services', icon: 'dns', label: 'Services', active: tab === 'services', onClick: () => setTabAndRoute('services') },
    { id: 'models', icon: 'memory', label: 'Models', active: tab === 'models', onClick: () => setTabAndRoute('models') },
    { id: 'agents', icon: 'smart_toy', label: 'Agents', active: tab === 'agents', onClick: () => setTabAndRoute('agents') },
    { id: 'logs', icon: 'article', label: 'Logs', active: tab === 'logs', onClick: () => setTabAndRoute('logs') },
    { id: 'budget', icon: 'monitoring', label: 'Budget', active: tab === 'budget', onClick: () => setTabAndRoute('budget') },
    { id: 'story', icon: 'auto_stories', label: 'Story Links', active: tab === 'story', onClick: () => setTabAndRoute('story') },
    { id: 'snacks', icon: 'fast_forward', label: 'Snacks', active: tab === 'snacks', onClick: () => setTabAndRoute('snacks') },
  ]

  return (
    <div className="userver-surface">
      <GlobalToolbar
        chatMode={chatOpen ? 'panel' : 'closed'}
        onToggleChat={() => setChatOpen(prev => !prev)}
        onToggleSidebar={toggleSidebar}
        sidebarOpen={sidebarOpen}
        sidebarToggleLabel="Server sidebar"
        rightExtra={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span className="hub-status-badge">
              <span className={`hub-status-dot ${runningCount > 0 ? 'hub-status-dot--online' : ''}`} />
              {runningCount}/{surfaces.length || '?'} online
            </span>
            <span className="hub-status-badge" title="Monthly API budget remaining"
              style={budgetOverLimit ? { borderColor: '#f85149', color: '#f85149' } : undefined}>
              Budget: {budgetRemaining === null ? 'n/a' : `$${budgetRemaining.toFixed(2)}`}
            </span>
          </div>
        }
      />

      <div className="usx-surface-body" style={{ position: 'relative' }}>
        <VaultSidebar open={sidebarOpen} showModeTabs sidebarMode={sidebarMode}
          onSidebarModeChange={setSidebarMode} serverNavItems={serverNavItems} />

        {chatOpen && (
          <div className="hub-chat-panel" style={{ position: 'absolute', top: 0, right: 0, bottom: 0, width: 380, zIndex: 1000, display: 'flex', flexDirection: 'column' }}>
            <div className="hub-chat-panel-header">
              <span className="hub-chat-panel-title">Chat</span>
              <button className="usx-header-btn" onClick={() => setChatOpen(false)} title="Close chat">
                <Icon name="close" size={16} />
              </button>
            </div>
            <div className="hub-chat-panel-body" style={{ flex: 1, overflow: 'hidden' }}>
              <AssistUISurface hideToolbar />
            </div>
          </div>
        )}

        <main className="usx-surface-main">
          {tab === 'dashboard' && (
            <DashboardTab services={services} surfaces={surfaces} budgetRemaining={budgetRemaining} budgetOverLimit={budgetOverLimit} />
          )}
          {tab === 'services' && <ServicesTab services={services} />}
          {tab === 'models' && <div style={{ height: '100%', overflow: 'auto' }}><ModelsPanel /></div>}
          {tab === 'agents' && <div style={{ height: '100%', overflow: 'auto' }}><AgentsPanel /></div>}
          {tab === 'logs' && <LogsPanel title="Server Logs" max={100} pollInterval={15000} />}
          {tab === 'budget' && <BudgetTab />}
          {tab === 'story' && <StoryLinksTab onNavigate={path => navigate(path)} />}
          {tab === 'snacks' && <SnacksTab />}
        </main>
      </div>
    </div>
  )
}