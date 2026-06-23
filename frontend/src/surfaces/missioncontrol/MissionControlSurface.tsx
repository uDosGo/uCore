/* ═══════════════════════════════════════════════════════════════════
   MissionControlSurface — Unified Surface Hub
   ═══════════════════════════════════════════════════════════════════
  Consolidates:
  - Dashboard (surface cards, starred surfaces)
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon } from '../../components/Icon'
import { GlobalToolbar, ToolbarTab } from '../../components/GlobalToolbar'
import AssistUISurface from '../assistui/AssistUISurface'
import '../../styles/hub/index.css'

// ─── Types ──────────────────────────────────────────────────────────
type MissionTab = 'dashboard'

interface SurfaceDef {
  id: string
  name: string
  subtitle?: string
  description?: string
  port: number
  color?: string
  icon?: string
  status: string
  cell?: string | null
  embedded?: boolean
  route?: string
}

type SurfaceAction = 'start' | 'stop' | 'restart' | 'repair' | 'debug'

interface ActionProgress {
  surface_id: string
  action: SurfaceAction
  progress: number
  status: 'in_progress' | 'completed' | 'failed'
  message: string
  timestamp: string
}

// ─── Constants ──────────────────────────────────────────────────────
const SNACKBAR_API = 'http://localhost:8484'
const DEV_MODE_ENABLED = ['1', 'true', 'yes', 'on'].includes(
  String(import.meta.env.VITE_DEV_MODE || '').toLowerCase(),
)

// Map API surface IDs to display IDs (e.g. userver → server, gridui → terminal)
// Legacy aliases are normalized to canonical cards.
const API_ID_MAP: Record<string, string> = {
  userver: 'server',
}

// Display name overrides — renames the card title without changing the surface ID/route.
const DISPLAY_NAME_MAP: Record<string, string> = {
  assistui: 'Assistant',
}

// Canonical fallback surface registry used when snackbar discovery is partial or unavailable.
// Keep this aligned with routed core surfaces so dashboard cards are always visible.
const FALLBACK_REGISTRY: SurfaceDef[] = [
  { id: 'ucode', name: 'uCode', subtitle: 'GridCore Surface', description: 'Unified GridCore surface with Terminal, Teletext, and grid management toolset dashboard.', port: 0, color: '#39d2c0', icon: 'grid_view', status: 'running', embedded: true, route: '/ucode' },
  { id: 'server', name: 'Server', subtitle: 'Operations & System', description: 'Consolidated server, system tools, modules, logs, workflows, agents, and publishing', port: 0, color: '#f59e0b', icon: 'dns', status: 'running', embedded: true, route: '/server' },
  { id: 'assistui', name: 'AssistUI', subtitle: 'Canonical AI Chat', description: 'Full-page AI chat with streaming responses, model selection, conversation management, and multi-agent support.', port: 0, color: '#a855f7', icon: 'smart_toy', status: 'running', embedded: true, route: '/assistui' },
  { id: 'documentation', name: 'Documentation', subtitle: 'Learning Hub', description: 'Learning hub with tutorials, guides, courses, skill tracker, and API docs.', port: 0, color: '#a371f7', icon: 'menu_book', status: 'running', embedded: true, route: '/documentation' },
  { id: 'browserui', name: 'Web Reader', subtitle: 'Research Bookmarks', description: 'Clean browser interface with centered search and research bookmarks.', port: 5179, color: '#f97583', icon: 'language', status: 'running', embedded: true, route: '/browserui' },
  { id: 'developer', name: 'Developer', subtitle: 'Development Lane', description: 'Developer environment with chat, repos, skills, reviews, workflows, and settings.', port: 0, color: '#d29922', icon: 'tune', status: 'running', embedded: true, route: '/developer' },
  { id: 'groovebox', name: 'Groovebox', subtitle: 'Music Production', description: 'Music production environment with MIDI sequencing, synthesis, and audio processing', port: 8888, color: '#da3633', icon: 'play_arrow', status: 'stopped' },
]

const MISSION_TABS: { id: MissionTab; icon: string; label: string }[] = [
  { id: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
]

const QUICK_SURFACE_TABS: Array<{ id: string; icon: string; label: string; href: string }> = [
  { id: 'ucode', icon: 'grid_view', label: 'uCode', href: '/ucode' },
  { id: 'server', icon: 'dns', label: 'Server', href: '/server?tab=dashboard' },
]

// ─── Helpers ────────────────────────────────────────────────────────
const sortSurfaces = (list: SurfaceDef[]): SurfaceDef[] => {
  const order = ['ucode', 'server', 'assistui', 'documentation', 'browserui', 'developer', 'groovebox']
  return [...list].sort((a, b) => {
    const ai = order.indexOf(a.id)
    const bi = order.indexOf(b.id)
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi)
  })
}

const TEST_SURFACE_IDS = new Set(['terminal', 'teletext'])

const isTestSurface = (surface: Pick<SurfaceDef, 'id' | 'name'>): boolean => {
  const id = String(surface.id || '').toLowerCase()
  const name = String(surface.name || '').toLowerCase()
  return (
    TEST_SURFACE_IDS.has(id) ||
    id.includes('test') ||
    id.includes('persist') ||
    name.includes('test surface') ||
    name.includes('test persist') ||
    name.includes('test')
  )
}

const withoutUiHub = (list: SurfaceDef[]): SurfaceDef[] =>
  list.filter(
    s =>
      s.id !== 'ui-hub' &&
      s.id !== 'mission-control' &&
      s.id !== 'devstudio' &&
      s.id !== 'proseui' &&
      s.id !== 'system' &&
      !isTestSurface(s),
  )

// ─── Dashboard Panel ────────────────────────────────────────────────
function DashboardPanel({ surfaces, snackbarAvailable, onNavigate, onAction }: {
  surfaces: SurfaceDef[]
  snackbarAvailable: boolean
  onNavigate?: (tab: MissionTab) => void
  onAction?: (id: string, action: SurfaceAction) => void
}) {

  const [tasks, setTasks] = useState([
    { id: 't1', title: 'Review surface consolidation PR', done: false, priority: 'high' },
    { id: 't2', title: 'Update USX component audit', done: false, priority: 'medium' },
    { id: 't3', title: 'Write documentation for v3.1', done: false, priority: 'low' },
    { id: 't4', title: 'Validate server tab cleanup', done: true, priority: 'high' },
    { id: 't5', title: 'Deploy snackbar update', done: true, priority: 'medium' },
  ])

  const toggleTask = (id: string) => {
    setTasks(prev => prev.map(t => t.id === id ? { ...t, done: !t.done } : t))
  }

  const runningSurfaces = surfaces.filter(s => s.status === 'running' || s.embedded)
  const totalTasks = tasks.length
  const doneTasks = tasks.filter(t => t.done).length

  const activity = [
    { date: 'Today', title: 'Surface consolidation complete' },
    { date: 'Yesterday', title: 'Legacy surface links removed' },
    { date: '2d ago', title: 'Server consolidation tabs updated' },
    { date: '3d ago', title: 'FALLBACK_REGISTRY simplified' },
  ]

  const prompts = [
    { icon: 'terminal', label: 'Run system diagnostics', color: '#58a6ff' },
    { icon: 'build', label: 'Repair surface registry', color: '#22c55e' },
    { icon: 'sync', label: 'Restart all services', color: '#f59e0b' },
    { icon: 'bug_report', label: 'Debug snackbar connection', color: '#f85149' },
  ]

  const quickActions = [
    { icon: 'add', label: 'New Surface', color: '#58a6ff' },
    { icon: 'refresh', label: 'Refresh Registry', color: '#22c55e' },
    { icon: 'settings', label: 'Server Settings', color: '#f59e0b', route: '/server?tab=settings' },
    { icon: 'help', label: 'Documentation', color: '#a855f7', route: '/s600' },
  ]

  return (
    <div className="hub-dashboard">
      {/* ─── System Overview Stats ──────────────────────────────────── */}
      <div className="hub-dashboard-section">
        <div className="hub-dashboard-section-header">
          <Icon name="monitor_heart" size={18} />
          <h3>System Overview</h3>
        </div>
        <div className="hub-dashboard-stats-grid">
          <div className="hub-dashboard-stat-card">
            <span className="hub-dashboard-stat-label">Surfaces</span>
            <span className="hub-dashboard-stat-value">{surfaces.length} total</span>
            <div className="hub-dashboard-stat-bar">
              <div className="hub-dashboard-stat-bar-fill" style={{ width: `${(runningSurfaces.length / Math.max(surfaces.length, 1)) * 100}%`, background: '#3fb950' }} />
            </div>
          </div>
          <div className="hub-dashboard-stat-card">
            <span className="hub-dashboard-stat-label">Running</span>
            <span className="hub-dashboard-stat-value">{runningSurfaces.length}</span>
            <div className="hub-dashboard-stat-bar">
              <div className="hub-dashboard-stat-bar-fill" style={{ width: `${(runningSurfaces.length / Math.max(surfaces.length, 1)) * 100}%`, background: '#58a6ff' }} />
            </div>
          </div>
          <div className="hub-dashboard-stat-card">
            <span className="hub-dashboard-stat-label">Tasks</span>
            <span className="hub-dashboard-stat-value">{doneTasks}/{totalTasks}</span>
            <div className="hub-dashboard-stat-bar">
              <div className="hub-dashboard-stat-bar-fill" style={{ width: `${(doneTasks / Math.max(totalTasks, 1)) * 100}%`, background: '#d29922' }} />
            </div>
          </div>
          <div className="hub-dashboard-stat-card">
            <span className="hub-dashboard-stat-label">Snackbar</span>
            <span className="hub-dashboard-stat-value" style={{ color: snackbarAvailable ? '#3fb950' : '#f85149' }}>
              {snackbarAvailable ? 'Online' : 'Offline'}
            </span>
            <div className="hub-dashboard-stat-bar">
              <div className="hub-dashboard-stat-bar-fill" style={{ width: '100%', background: snackbarAvailable ? '#3fb950' : '#f85149' }} />
            </div>
          </div>
        </div>
      </div>

      {/* ─── 2-Column: Activity + Quick Actions ──────────────────────── */}
      <div className="hub-dashboard-grid-2">
        <div className="hub-dashboard-section">
          <div className="hub-dashboard-section-header">
            <Icon name="history" size={18} />
            <h3>Activity</h3>
          </div>
          <div className="hub-dashboard-activity">
            {activity.map(a => (
              <div key={a.title} className="hub-dashboard-activity-row">
                <span className="hub-dashboard-activity-date">{a.date}</span>
                <span className="hub-dashboard-activity-title">{a.title}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="hub-dashboard-section">
          <div className="hub-dashboard-section-header">
            <Icon name="bolt" size={18} />
            <h3>Quick Actions</h3>
          </div>
          <div className="hub-dash-card-actions">
            {quickActions.map(a => (
              a.route ? (
                <a key={a.label} href={a.route} className="hub-dash-action-btn" style={{ '--dash-card-color': a.color } as React.CSSProperties}>
                  <Icon name={a.icon} size={16} /> {a.label}
                </a>
              ) : (
                <button key={a.label} className="hub-dash-action-btn" style={{ '--dash-card-color': a.color } as React.CSSProperties}>
                  <Icon name={a.icon} size={16} /> {a.label}
                </button>
              )
            ))}
          </div>
        </div>
      </div>

      {/* ─── 2-Column: Chat Prompts + Tasks ──────────────────────────── */}
      <div className="hub-dashboard-grid-2">
        <div className="hub-dashboard-section">
          <div className="hub-dashboard-section-header">
            <Icon name="smart_toy" size={18} />
            <h3>Chat Prompts</h3>
          </div>
          <div className="hub-dash-prompts-grid">
            {prompts.map(p => (
              <button key={p.label} className="hub-dash-prompt-btn" style={{ '--prompt-color': p.color } as React.CSSProperties}>
                <Icon name={p.icon} size={16} /> {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="hub-dashboard-section">
          <div className="hub-dashboard-section-header">
            <Icon name="checklist" size={18} />
            <h3>Tasks</h3>
            <span className="hub-dashboard-section-count">{doneTasks}/{totalTasks}</span>
          </div>
          <div className="hub-dashboard-tasks">
            {tasks.map(t => (
              <div key={t.id} className="hub-dashboard-task-row">
                <label className="hub-dashboard-task-label">
                  <input type="checkbox" checked={t.done} onChange={() => toggleTask(t.id)} />
                  <span className={`hub-dashboard-task-text ${t.done ? 'hub-dashboard-task-text--done' : ''}`}>{t.title}</span>
                </label>
                <span className={`hub-dashboard-tag hub-dashboard-tag--${t.priority}`}>{t.priority}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─── Surfaces ────────────────────────────────────────────────── */}
      <div className="hub-dashboard-section">
        <div className="hub-dashboard-section-header">
          <Icon name="apps" size={18} />
          <h3>Surfaces</h3>
          <span className="hub-dashboard-section-count">{surfaces.length}</span>
        </div>
        <div className="hub-dashboard-starred-grid">
          {surfaces.map(card => {
            const isRunning = card.status === 'running' || card.embedded
            return (
              <div key={card.id} className="hub-card" style={{ '--hub-card-color': card.color || '#58a6ff' } as React.CSSProperties}>
                <div className="hub-card-header">
                  <div className="hub-card-icon" style={{ background: `${card.color || '#58a6ff'}20`, color: card.color || '#58a6ff' }}>
                    <Icon name={card.icon || 'widgets'} size={20} />
                  </div>
                  <div className="hub-card-info">
                    <h3 className="hub-card-title">{card.name}</h3>
                    {card.subtitle && <p className="hub-card-subtitle" style={{ color: card.color }}>{card.subtitle}</p>}
                  </div>
                </div>
                <p className="hub-card-desc">{card.description || ''}</p>
                <div className="hub-card-footer">
                  <div className="hub-card-meta">
                    <span className={`hub-card-status ${isRunning ? 'hub-card-status--online' : 'hub-card-status--offline'}`}>
                      <span className="hub-status-dot" /> {card.status}
                    </span>
                  </div>
                  <div className="hub-card-actions">
                    {isRunning ? (
                      <a href={card.route || `/${card.id}`} className="hub-btn hub-btn--primary">
                        <Icon name="open_in_new" size={14} /> Open
                      </a>
                    ) : onAction ? (
                      <button onClick={() => onAction(card.id, 'start')} className="hub-btn hub-btn--primary">
                        <Icon name="play_arrow" size={14} /> Start
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>


    </div>
  )
}

// ─── Main Component ────────────────────────────────────────────────
export default function MissionControlSurface() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<MissionTab>('dashboard')
  const [surfaces, setSurfaces] = useState<SurfaceDef[]>([])
  const [loading, setLoading] = useState(true)
  const [snackbarAvailable, setSnackbarAvailable] = useState(false)
  const [pendingActions, setPendingActions] = useState<Record<string, { action: SurfaceAction; progress: ActionProgress }>>({})
  const progressIntervals = useRef<Record<string, ReturnType<typeof setInterval>>>({})
  const [chatMode, setChatMode] = useState<'closed' | 'panel'>('closed')

  const toggleChat = useCallback(() => {
    setChatMode(prev => prev === 'closed' ? 'panel' : 'closed')
  }, [])

  const runningCount = surfaces.filter(s => s.status === 'running').length

  // ─── Snackbar / Surface Registry ────────────────────────────────
  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/surfaces`)
      if (!res.ok) throw new Error('Snackbar unavailable')
      const data = await res.json()
      setSnackbarAvailable(true)
      // Merge API surfaces with embedded fallback surfaces (system, server, etc.)
      // Prefer fallback registry metadata (name, description, icon, color) for surfaces
      // that have a fallback entry, since the API may return stale/incorrect names.
      // Also remap API IDs (e.g. userver → server) via API_ID_MAP.
      const apiSurfaces = (data.surfaces || []).map((s: SurfaceDef) => {
        const mappedId = API_ID_MAP[s.id]
        return mappedId ? { ...s, id: mappedId } : s
      })
      const apiIds = new Set(apiSurfaces.map((s: SurfaceDef) => s.id))
      const merged = [
        ...apiSurfaces.map((api: SurfaceDef) => {
          const fb = FALLBACK_REGISTRY.find(f => f.id === api.id)
          return fb ? { ...api, name: fb.name, subtitle: fb.subtitle, description: fb.description, icon: fb.icon, color: fb.color, embedded: true, route: fb.route } : api
        }),
        ...FALLBACK_REGISTRY.filter(fb => !apiIds.has(fb.id)),
      ]
      // Apply display name overrides without changing the ID/route.
      const renamed = merged.map(s => ({
        ...s,
        name: DISPLAY_NAME_MAP[s.id] || s.name,
      }))
      setSurfaces(withoutUiHub(sortSurfaces(renamed)))
    } catch {
      setSnackbarAvailable(false)
      setSurfaces(withoutUiHub(sortSurfaces(FALLBACK_REGISTRY)))
    }
    setLoading(false)
  }, [])

  const clearPendingAction = useCallback((id: string) => {
    setPendingActions(prev => {
      const next = { ...prev }
      delete next[id]
      return next
    })
  }, [])

  const startProgressAnimation = useCallback((id: string, action: SurfaceAction) => {
    setPendingActions(prev => ({
      ...prev,
      [id]: {
        action,
        progress: {
          surface_id: id,
          action,
          progress: 0,
          status: 'in_progress',
          message: `${action} in progress...`,
          timestamp: new Date().toISOString(),
        },
      },
    }))

    const interval = setInterval(() => {
      setPendingActions(prev => {
        if (!prev[id]) return prev
        const current = prev[id].progress.progress
        if (current >= 90) {
          clearInterval(interval)
          return prev
        }
        return {
          ...prev,
          [id]: {
            ...prev[id],
            progress: {
              ...prev[id].progress,
              progress: Math.min(current + Math.random() * 15, 90),
            },
          },
        }
      })
    }, 300)
    progressIntervals.current[id] = interval
  }, [])

  const completeAction = useCallback((id: string, message: string) => {
    setPendingActions(prev => {
      if (!prev[id]) return prev
      return {
        ...prev,
        [id]: {
          ...prev[id],
          progress: {
            ...prev[id].progress,
            progress: 100,
            status: 'completed',
            message,
          },
        },
      }
    })
    setTimeout(() => clearPendingAction(id), 1500)
  }, [clearPendingAction])

  const failAction = useCallback((id: string, message: string) => {
    setPendingActions(prev => {
      if (!prev[id]) return prev
      return {
        ...prev,
        [id]: {
          ...prev[id],
          progress: {
            ...prev[id].progress,
            progress: 100,
            status: 'failed',
            message,
          },
        },
      }
    })
    setTimeout(() => clearPendingAction(id), 3000)
  }, [clearPendingAction])

  const performAction = useCallback(async (id: string, action: SurfaceAction) => {
    if (pendingActions[id]) return
    startProgressAnimation(id, action)

    try {
      let endpoint = ''
      switch (action) {
        case 'start': endpoint = `/api/surfaces/${id}/start`; break
        case 'stop': endpoint = `/api/surfaces/${id}/stop`; break
        case 'restart': endpoint = `/api/surfaces/${id}/restart`; break
        case 'repair': endpoint = `/api/surfaces/${id}/repair`; break
        case 'debug': endpoint = `/api/surfaces/${id}/debug`; break
      }

      const res = await fetch(`${SNACKBAR_API}${endpoint}`, { method: 'POST' })
      const result = await res.json()

      if (result.error) {
        failAction(id, result.error)
        return
      }

      // Handle embedded surface response — they're always "running" via UI Hub
      // Snackbar API returns {"status": "running", "embedded": true} for embedded surfaces
      if (result.embedded === true) {
        completeAction(id, 'Embedded surface — always available')
        // Navigate to the embedded route
        const surface = surfaces.find(s => s.id === id)
        if (surface?.route) {
          window.location.href = surface.route
        }
        setTimeout(refresh, 500)
        return
      }

      setSurfaces(prev => prev.map(s => {
        if (s.id !== id) return s
        if (action === 'start' || action === 'restart') return { ...s, status: 'starting' }
        if (action === 'stop') return { ...s, status: 'stopping' }
        return s
      }))

      if (action === 'repair') {
        const skillResult = result.result
        if (skillResult?.status === 'completed') {
          completeAction(id, 'Repair completed successfully')
        } else if (skillResult?.status === 'failed') {
          failAction(id, skillResult?.stderr || 'Repair failed')
        } else {
          completeAction(id, 'Repair finished')
        }
      } else if (action === 'debug') {
        const health = result.health
        const healthy = health?.healthy
        if (healthy) {
          completeAction(id, 'Surface is healthy')
        } else {
          completeAction(id, 'Diagnostics complete — see details')
        }
      } else {
        completeAction(id, `${action} completed`)
      }

      setTimeout(refresh, 1000)
    } catch (e: any) {
      failAction(id, e.message)
    }
  }, [refresh, pendingActions, startProgressAnimation, completeAction, failAction, surfaces])

  // ─── Init ───────────────────────────────────────────────────────
  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 15000)
    return () => {
      clearInterval(interval)
      Object.values(progressIntervals.current).forEach(clearInterval)
    }
  }, [refresh])

  // ─── Render ─────────────────────────────────────────────────────
  const tabs: ToolbarTab[] = [
    ...MISSION_TABS.map(t => ({
      id: t.id,
      icon: t.icon,
      label: t.label,
      active: activeTab === t.id,
      onClick: () => setActiveTab(t.id),
    })),
    ...QUICK_SURFACE_TABS.map(t => ({
      id: t.id,
      icon: t.icon,
      label: t.label,
      active: false,
      onClick: () => navigate(t.href),
    })),
  ]

  return (
    <div className="hub-surface">
      <GlobalToolbar
        tabs={tabs}
        chatMode={chatMode}
        onToggleChat={toggleChat}
        rightExtra={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span className="hub-status-badge">
              <span className={`hub-status-dot ${runningCount > 0 ? 'hub-status-dot--online' : ''}`} />
              {runningCount}/{surfaces.length} online
            </span>
          </div>
        }
      />

      <div className="usx-surface-body" style={{ display: 'flex', overflow: 'hidden', position: 'relative' }}>
        <main className="usx-surface-main" style={{ flex: 1, overflow: 'auto' }}>
          {loading ? (
            <div className="hub-loading">
              <div className="hub-loading-spinner" />
              <p>Loading surfaces...</p>
            </div>
          ) : activeTab === 'dashboard' ? (
            <DashboardPanel
              surfaces={surfaces}
              snackbarAvailable={snackbarAvailable}
              onNavigate={setActiveTab}
              onAction={performAction}
            />
          ) : null}
        </main>
      </div>

      {/* ─── Floating Chat Panel ──────────────────────────────────── */}
      <AssistUISurface floating />

      <footer className="hub-footer">
        <span>Mission Control · Surface Hub</span>
        {snackbarAvailable ? (
          <span className="hub-footer-snackbar">Snackbar host active — dynamic surface management</span>
        ) : (
          <span className="hub-footer-static">Snackbar offline — static port fallback</span>
        )}
      </footer>
    </div>
  )
}
