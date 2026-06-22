/* ═══════════════════════════════════════════════════════════════════
   UIHubManager — React USX Surface for the UI Hub
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Icon } from './components/Icon'
import { USXThemeProvider } from './components/USXThemeProvider'
import { SurfaceSnackbar } from './components/SurfaceSnackbar'
import { useSurfaceStore } from './hooks/useSurfaceStore'
import './styles/hub/index.css'
import './styles/global-toolbar.css'
import { GlobalToolbar, type ToolbarTab } from './components/GlobalToolbar'


// ─── Types ──────────────────────────────────────────────────────────
interface SurfaceDef {
  id: string
  name: string
  subtitle: string
  description: string
  port: number
  color: string
  icon: string
  status: string
  cell: string | null
  embedded?: boolean
  route?: string
}

type SurfaceAction = 'start' | 'stop' | 'restart' | 'repair' | 'debug'

interface ActionProgress {
  surface_id: string
  action: string
  progress: number
  status: 'in_progress' | 'completed' | 'failed'
  message: string
  timestamp: string
}

// ─── Core Surface IDs (always shown in order) ─────────────────────
// Consolidated lineup: GridUI, Server, AssistUI, BrowserUI, Developer
const CORE_SURFACE_IDS = ['gridui', 'server', 'assistui', 'browserui', 'developer']

// ─── Surfaces hidden from Surfaces tab (accessible via toolbar icons/tabs) ──
// These are hidden unless the user has starred them.
// 'browserui' is hidden because it's accessible via the Globe icon in the toolbar.
// 'developer' is hidden because it's a dev-only surface.
const HIDDEN_FROM_SURFACES_TAB = ['browserui', 'developer']

// ─── Fallback Surface Registry ─────────────────────────────────────
const FALLBACK_REGISTRY: SurfaceDef[] = [
  { id: 'gridui',    name: 'Terminal Teletext - Grid view', subtitle: 'Grid Layer Composer',       description: 'Chat sheets, nav rails, teledesk panels, terminal, vault docs, and maps layers.', port: 5178, color: '#f0883e', icon: 'widgets',     status: 'stopped', cell: 'L100-AA10-0101-1', embedded: true, route: '/gridui' },
  { id: 'server',    name: 'Server',         subtitle: 'Server Management',         description: 'Consolidated backend operations, ingest, workflows, agents, and logs.', port: 0, color: '#58a6ff', icon: 'layers',      status: 'stopped', cell: 'L100-AA10-0103-1', embedded: true, route: '/server' },
  { id: 'assistui',  name: 'AssistUI',       subtitle: 'Canonical AI Chat',         description: 'Full-page AI chat with streaming responses, model selection, conversation management, and multi-agent support. Absorbed FloatingChatPanel + ChatUISurface.', port: 0, color: '#a855f7', icon: 'smart_toy',   status: 'stopped', cell: 'L100-AA10-0104-1', embedded: true, route: '/assistui' },
  { id: 'browserui', name: 'Web Reader',     subtitle: 'Research Bookmarks',        description: 'Clean browser interface with centered search bar and research bookmarks.', port: 5179, color: '#f59e0b', icon: 'visibility',  status: 'stopped', cell: 'L100-AA10-0106-1', embedded: true, route: '/browserui' },
  { id: 'developer', name: 'Developer',      subtitle: 'Development Lane',          description: 'Developer development environment with dev-mode chat, repo browser, skill runner, and code review.', port: 0, color: '#f97583', icon: 'tune',       status: 'stopped', cell: 'L100-AA10-0109-1', embedded: true, route: '/developer' },
  { id: 'groovebox', name: 'Groovebox',      subtitle: 'Music Production',          description: 'Music production environment with MIDI sequencing, synthesis, and audio processing.', port: 8888, color: '#da3633', icon: 'play_arrow', status: 'stopped', cell: 'L100-AA10-0113-1' },
]

// ─── Sort surfaces: core first (in order), then the rest ──────────
function sortSurfaces(list: SurfaceDef[]): SurfaceDef[] {
  const core: SurfaceDef[] = []
  const rest: SurfaceDef[] = []
  for (const s of list) {
    const idx = CORE_SURFACE_IDS.indexOf(s.id)
    if (idx !== -1) {
      core[idx] = s
    } else {
      rest.push(s)
    }
  }
  return [...core.filter(Boolean), ...rest]
}

// ─── Filter out the ui-hub (uDosConnect) from surface lists ──────
function withoutUiHub(list: SurfaceDef[]): SurfaceDef[] {
  return list.filter(s => s.id !== 'ui-hub' && s.id !== 'terminal' && s.id !== 'teletext')
}

const SNACKBAR_API = 'http://localhost:8484'

function systemPageUrl(code: string, surface?: SurfaceDef, error?: string): string {
  const params = new URLSearchParams()
  if (surface) {
    params.set('name', surface.name)
    params.set('port', String(surface.port))
  }
  if (error) params.set('error', error)
  const qs = params.toString()
  return `/p${code}${qs ? '?' + qs : ''}`
}

function surfaceErrorUrl(surface: SurfaceDef): string {
  return systemPageUrl('804', surface)
}

// ─── Status Badge Component ────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string; icon: string }> = {
    running:  { label: 'Online',   className: 'hub-card-status--online',  icon: 'check_circle' },
    starting: { label: 'Starting', className: 'hub-card-status--starting', icon: 'sync' },
    stopping: { label: 'Stopping', className: 'hub-card-status--stopping', icon: 'stop_circle' },
    stopped:  { label: 'Offline',  className: 'hub-card-status--offline', icon: 'radio_button_unchecked' },
    failed:   { label: 'Failed',   className: 'hub-card-status--failed',  icon: 'error' },
  }
  const cfg = config[status] || config.stopped
  return (
    <div className={`hub-card-status ${cfg.className}`}>
      <Icon name={cfg.icon} size={14} />
      <span>{cfg.label}</span>
    </div>
  )
}

// ─── Animated Progress Bar ─────────────────────────────────────────
function ProgressBar({ progress, status }: { progress: number; status?: string }) {
  const isFailed = status === 'failed'
  const isCompleted = status === 'completed'
  const barClass = isFailed ? 'hub-progress-fill hub-progress-fill--failed'
    : isCompleted ? 'hub-progress-fill hub-progress-fill--completed'
    : 'hub-progress-fill'

  return (
    <div className="hub-progress-bar">
      <div
        className={barClass}
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      />
    </div>
  )
}

// ─── Action Progress Indicator ─────────────────────────────────────
function ActionProgressIndicator({ progress, action }: {
  progress: ActionProgress
  action: SurfaceAction
}) {
  const isFailed = progress.status === 'failed'
  const isCompleted = progress.status === 'completed'
  const statusIcon = isFailed ? 'error' : isCompleted ? 'check_circle' : 'sync'
  const statusClass = isFailed ? 'hub-action-progress--failed'
    : isCompleted ? 'hub-action-progress--completed'
    : 'hub-action-progress--active'

  const actionLabels: Record<string, string> = {
    start: 'Starting',
    stop: 'Stopping',
    restart: 'Restarting',
    repair: 'Repairing',
    debug: 'Running diagnostics',
  }

  return (
    <div className={`hub-action-progress ${statusClass}`}>
      <div className="hub-action-progress-header">
        <Icon name={statusIcon} size={14} className={isCompleted || isFailed ? '' : 'hub-spin'} />
        <span className="hub-action-progress-label">
          {isCompleted ? `${actionLabels[action]} — Complete` :
           isFailed ? `${actionLabels[action]} — Failed` :
           actionLabels[action]}
        </span>
        <span className="hub-action-progress-pct">{progress.progress}%</span>
      </div>
      <ProgressBar progress={progress.progress} status={progress.status} />
      {progress.message && (
        <p className="hub-action-progress-msg">{progress.message}</p>
      )}
    </div>
  )
}

// ─── Surface Card ──────────────────────────────────────────────────
function SurfaceCard({ surface, snackbarAvailable, onAction, pendingAction, actionProgress, starred, onToggleStar }: {
  surface: SurfaceDef
  snackbarAvailable: boolean
  onAction: (id: string, action: SurfaceAction) => void
  pendingAction: SurfaceAction | null
  actionProgress: ActionProgress | null
  starred?: boolean
  onToggleStar?: (id: string) => void
}) {
  const isRunning = surface.status === 'running'
  const isPending = pendingAction !== null
  const isEmbedded = surface.embedded === true
  const url = isEmbedded && surface.route
    ? surface.route
    : `http://localhost:${surface.port}`

  function handleClick() {
    if (isPending) return
    // Embedded surfaces always navigate to their route
    if (isEmbedded) {
      if (window.top && window.top !== window) {
        window.top.location.href = url
      } else {
        window.location.href = url
      }
      return
    }
    if (isRunning) {
      if (window.top && window.top !== window) {
        window.top.location.href = url
      } else {
        window.location.href = url
      }
    } else if (snackbarAvailable) {
      onAction(surface.id, 'start')
    } else {
      if (window.top && window.top !== window) {
        window.top.location.href = surfaceErrorUrl(surface)
      } else {
        window.location.href = surfaceErrorUrl(surface)
      }
    }
  }

  function handleAction(e: React.MouseEvent, action: SurfaceAction) {
    e.stopPropagation()
    if (!isPending) {
      onAction(surface.id, action)
    }
  }

  const statusClass = isPending
    ? 'hub-card--pending'
    : isRunning
      ? 'hub-card--running'
      : 'hub-card--stopped'

  return (
    <div
      className={`hub-card ${statusClass}`}
      onClick={handleClick}
      style={{ '--hub-card-color': surface.color } as React.CSSProperties}
    >
      <div className="hub-card-header">
        <div className="hub-card-icon" style={{ background: `${surface.color}20`, color: surface.color }}>
          <Icon name={surface.icon} size={24} />
        </div>
        <div className="hub-card-info">
          <div className="hub-card-title">{surface.name}</div>
          <p className="hub-card-subtitle" style={{ color: surface.color }}>{surface.subtitle}</p>
        </div>
        <StatusBadge status={surface.status} />
        {onToggleStar && (
          <button className={`hub-star-btn ${starred ? 'hub-star-btn--active' : ''}`} onClick={(e) => { e.stopPropagation(); onToggleStar(surface.id) }} title={starred ? 'Unstar' : 'Star'}>
            <Icon name={starred ? 'star' : 'star_border'} size={16} />
          </button>
        )}
      </div>

      {isPending && actionProgress && (
        <ActionProgressIndicator progress={actionProgress} action={pendingAction!} />
      )}

      <p className="hub-card-desc">{surface.description}</p>
      <div className="hub-card-footer">
        <div className="hub-card-meta">
          {isEmbedded ? (
            <span className="hub-card-port">Embedded</span>
          ) : (
            <span className="hub-card-port">:{surface.port}</span>
          )}
          {surface.cell && <span className="hub-card-cell">{surface.cell}</span>}
          {!isRunning && !isPending && !isEmbedded && <span className="hub-card-port">P804</span>}
        </div>
        <div className="hub-card-actions">
          {isEmbedded ? (
            <a href={url} className="hub-btn hub-btn--primary" onClick={(e) => e.stopPropagation()}>Open</a>
          ) : isPending ? (
            <span className="hub-card-pending-spinner">
              <Icon name="sync" size={16} className="hub-spin" />
            </span>
          ) : isRunning ? (
            <>
              <a href={url} className="hub-btn hub-btn--primary" onClick={(e) => e.stopPropagation()}>Open</a>
              {snackbarAvailable && (
                <>
                  <button className="hub-btn hub-btn--warning" onClick={(e) => handleAction(e, 'restart')} title="Restart surface">
                    <Icon name="refresh" size={14} /> Restart
                  </button>
                  <button className="hub-btn hub-btn--danger" onClick={(e) => handleAction(e, 'stop')}>
                    Stop
                  </button>
                </>
              )}
            </>
          ) : (
            snackbarAvailable ? (
              <>
                <button className="hub-btn hub-btn--success" onClick={(e) => handleAction(e, 'start')}>
                  Start
                </button>
                <button className="hub-btn hub-btn--info" onClick={(e) => handleAction(e, 'repair')} title="Run repair skill">
                  <Icon name="build" size={14} /> Repair
                </button>
                <button className="hub-btn hub-btn--info" onClick={(e) => handleAction(e, 'debug')} title="Run diagnostics">
                  <Icon name="bug_report" size={14} /> Debug
                </button>
              </>
            ) : (
              <a href={surfaceErrorUrl(surface)} className="hub-btn hub-btn--primary" onClick={(e) => e.stopPropagation()}>
                P804
              </a>
            )
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Loading Overlay ───────────────────────────────────────────────
function LoadingOverlay({ message, progress }: { message: string; progress: number }) {
  return (
    <div className="hub-loading-overlay">
      <div className="hub-loading-overlay-content">
        <div className="hub-loading-overlay-spinner">
          <Icon name="sync" size={32} className="hub-spin" />
        </div>
        <h3 className="hub-loading-overlay-title">Loading Surfaces</h3>
        <p className="hub-loading-overlay-msg">{message}</p>
        <div className="hub-loading-overlay-bar">
          <ProgressBar progress={progress} />
        </div>
        <div className="hub-loading-overlay-steps">
          <div className={`hub-loading-step ${progress >= 10 ? 'hub-loading-step--done' : ''}`}>
            <Icon name={progress >= 10 ? 'check_circle' : 'radio_button_unchecked'} size={12} />
            <span>Connecting to Snackbar</span>
          </div>
          <div className={`hub-loading-step ${progress >= 40 ? 'hub-loading-step--done' : ''}`}>
            <Icon name={progress >= 40 ? 'check_circle' : 'radio_button_unchecked'} size={12} />
            <span>Discovering surfaces</span>
          </div>
          <div className={`hub-loading-step ${progress >= 70 ? 'hub-loading-step--done' : ''}`}>
            <Icon name={progress >= 70 ? 'check_circle' : 'radio_button_unchecked'} size={12} />
            <span>Probing ports</span>
          </div>
          <div className={`hub-loading-step ${progress >= 100 ? 'hub-loading-step--done' : ''}`}>
            <Icon name={progress >= 100 ? 'check_circle' : 'radio_button_unchecked'} size={12} />
            <span>Ready</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Hub Tab Types ─────────────────────────────────────────────────
type HubTab = 'dashboard' | 'surfaces' | 'install' | 'docs'

const HUB_TABS: { id: HubTab; icon: string; label: string }[] = [
  { id: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
  { id: 'surfaces', icon: 'grid_view', label: 'Surfaces' },
  { id: 'install', icon: 'download', label: 'Install' },
  { id: 'docs', icon: 'menu_book', label: 'Documentation' },
]

// ─── Starred Surfaces (localStorage) ───────────────────────────────
function loadStarred(): string[] {
  try {
    const raw = localStorage.getItem('hub-starred')
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function saveStarred(ids: string[]) {
  localStorage.setItem('hub-starred', JSON.stringify(ids))
}

// ─── Dashboard Card Types ──────────────────────────────────────────
interface DashboardCard {
  id: string
  type: 'surface' | 'stats' | 'chat-prompt' | 'quick-action' | 'tasks' | 'activity'
  title: string
  subtitle?: string
  icon?: string
  color?: string
  size?: 'small' | 'medium' | 'large'
  data?: any
}

// ─── Dashboard Panel ───────────────────────────────────────────────
function DashboardPanel({ surfaces, snackbarAvailable, performAction, pendingActions }: {
  surfaces: SurfaceDef[]
  snackbarAvailable: boolean
  performAction: (id: string, action: SurfaceAction) => void
  pendingActions: Record<string, { action: SurfaceAction; progress: ActionProgress }>
}) {
  const [starred, setStarred] = useState<string[]>(loadStarred)
  const [expandedCard, setExpandedCard] = useState<string | null>(null)
  const [cardOrder, setCardOrder] = useState<string[]>(() => {
    try {
      const raw = localStorage.getItem('hub-dashboard-order')
      return raw ? JSON.parse(raw) : []
    } catch { return [] }
  })
  const running = surfaces.filter(s => s.status === 'running')
  const stopped = surfaces.filter(s => s.status === 'stopped')
  const starredSurfaces = surfaces.filter(s => starred.includes(s.id))

  const toggleStar = (id: string) => {
    setStarred(prev => {
      const next = prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
      saveStarred(next)
      return next
    })
  }

  // ─── Tasks state (from GridUI Dashboard) ───────────────────────
  const [tasks, setTasks] = useState([
    { id: 1, title: 'Complete project documentation', completed: false, priority: 'high' as const },
    { id: 2, title: 'Review pull requests', completed: false, priority: 'medium' as const },
    { id: 3, title: 'Update dependencies', completed: true, priority: 'low' as const },
    { id: 4, title: 'Fix login bug', completed: false, priority: 'high' as const },
    { id: 5, title: 'Write unit tests', completed: false, priority: 'medium' as const },
  ])
  const toggleTask = (id: number) => setTasks(t => t.map(x => x.id === id ? { ...x, completed: !x.completed } : x))

  // ─── Activity feed (from GridUI Dashboard) ─────────────────────
  const activity = [
    { title: 'gridui v1.0 released!', date: '2026-05-20' },
    { title: 'New USX grid renderer available', date: '2026-05-19' },
    { title: 'Community showcase: Retro dashboards', date: '2026-05-18' },
    { title: 'uCode v1.2 deployment complete', date: '2026-05-17' },
    { title: 'MCP Bridge connected to gridui', date: '2026-05-16' },
  ]

  // ─── Chat prompt starters ──────────────────────────────────────
  const chatPrompts = [
    { id: 'prompt-1', label: 'What surfaces are running?', icon: 'query_stats', color: '#58a6ff' },
    { id: 'prompt-2', label: 'Start uCode1 surface', icon: 'play_arrow', color: '#22c55e' },
    { id: 'prompt-3', label: 'Show system health', icon: 'monitor_heart', color: '#f0883e' },
    { id: 'prompt-4', label: 'Run diagnostics', icon: 'bug_report', color: '#f59e0b' },

    { id: 'prompt-6', label: 'Check Snackbar status', icon: 'restaurant_menu', color: '#a855f7' },
  ]

  // ─── Build dashboard cards ─────────────────────────────────────
  const dashboardCards: DashboardCard[] = [
    // Stats overview card
    {
      id: 'stats-overview',
      type: 'stats',
      title: 'System Overview',
      subtitle: `${running.length} running · ${stopped.length} stopped`,
      icon: 'analytics',
      color: '#58a6ff',
      size: 'medium',
      data: { running: running.length, stopped: stopped.length, total: surfaces.length, snackbar: snackbarAvailable },
    },
    // Starred surfaces card
    ...(starredSurfaces.length > 0 ? [{
      id: 'starred-surfaces',
      type: 'surface' as const,
      title: 'Starred Surfaces',
      subtitle: `${starredSurfaces.length} surfaces`,
      icon: 'star',
      color: '#f59e0b',
      size: 'large' as const,
      data: starredSurfaces,
    }] : []),
    // Running services card
    ...(running.length > 0 ? [{
      id: 'running-services',
      type: 'surface' as const,
      title: 'Running Services',
      subtitle: `${running.length} active`,
      icon: 'play_circle',
      color: '#22c55e',
      size: 'medium' as const,
      data: running,
    }] : []),
    // Tasks card (from GridUI Dashboard)
    {
      id: 'tasks',
      type: 'tasks',
      title: 'Tasks',
      subtitle: `${tasks.filter(t => !t.completed).length} pending`,
      icon: 'checklist',
      color: '#22c55e',
      size: 'medium',
      data: { tasks, toggleTask },
    },
    // Activity feed card (from GridUI Dashboard)
    {
      id: 'activity',
      type: 'activity',
      title: 'Activity',
      subtitle: 'Recent updates',
      icon: 'history',
      color: '#58a6ff',
      size: 'medium',
      data: activity,
    },
    // Chat prompt starters card
    {
      id: 'chat-prompts',
      type: 'chat-prompt',
      title: 'Quick Prompts',
      subtitle: 'Ask the AI assistant',
      icon: 'chat',
      color: '#58a6ff',
      size: 'medium',
      data: chatPrompts,
    },
    // Quick actions card
    {
      id: 'quick-actions',
      type: 'quick-action',
      title: 'Quick Actions',
      subtitle: 'Common tasks',
      icon: 'bolt',
      color: '#f0883e',
      size: 'small',
      data: [
        { id: 'refresh-all', label: 'Refresh All Surfaces', icon: 'refresh', action: () => window.location.reload() },
        { id: 'open-chat', label: 'Open Chat Panel', icon: 'chat', action: null },
        { id: 'view-surfaces', label: 'View All Surfaces', icon: 'grid_view', action: null },
      ],
    },
  ]

  // ─── Sort cards by saved order ─────────────────────────────────
  const sortedCards = [...dashboardCards].sort((a, b) => {
    const aIdx = cardOrder.indexOf(a.id)
    const bIdx = cardOrder.indexOf(b.id)
    if (aIdx === -1 && bIdx === -1) return 0
    if (aIdx === -1) return 1
    if (bIdx === -1) return -1
    return aIdx - bIdx
  })

  // ─── Save card order ───────────────────────────────────────────
  const saveCardOrder = (ids: string[]) => {
    setCardOrder(ids)
    localStorage.setItem('hub-dashboard-order', JSON.stringify(ids))
  }

  // ─── Move card ─────────────────────────────────────────────────
  const moveCard = (id: string, direction: 'up' | 'down') => {
    const ids = sortedCards.map(c => c.id)
    const idx = ids.indexOf(id)
    if (idx === -1) return
    const newIdx = direction === 'up' ? Math.max(0, idx - 1) : Math.min(ids.length - 1, idx + 1)
    if (newIdx === idx) return
    ids.splice(idx, 1)
    ids.splice(newIdx, 0, id)
    saveCardOrder(ids)
  }

  // ─── Render card content based on type ─────────────────────────
  const renderCardContent = (card: DashboardCard) => {
    const isExpanded = expandedCard === card.id

    switch (card.type) {
      case 'stats':
        return (
          <div className="hub-dash-card-stats">
            <div className="hub-dash-card-stats-grid">
              <div className="hub-dash-stat-item">
                <span className="hub-dash-stat-value" style={{ color: 'var(--pico-ins-color, #3fb950)' }}>{card.data.running}</span>
                <span className="hub-dash-stat-label">Running</span>
                <div className="hub-dash-stat-bar">
                  <div className="hub-dash-stat-bar-fill" style={{ width: `${card.data.total > 0 ? (card.data.running / card.data.total) * 100 : 0}%`, background: 'var(--pico-ins-color, #3fb950)' }} />
                </div>
              </div>
              <div className="hub-dash-stat-item">
                <span className="hub-dash-stat-value" style={{ color: 'var(--pico-muted-color, #8b949e)' }}>{card.data.stopped}</span>
                <span className="hub-dash-stat-label">Stopped</span>
                <div className="hub-dash-stat-bar">
                  <div className="hub-dash-stat-bar-fill" style={{ width: `${card.data.total > 0 ? (card.data.stopped / card.data.total) * 100 : 0}%`, background: 'var(--pico-border-color, #30363d)' }} />
                </div>
              </div>
              <div className="hub-dash-stat-item">
                <span className="hub-dash-stat-value">{card.data.total}</span>
                <span className="hub-dash-stat-label">Total</span>
              </div>
              <div className="hub-dash-stat-item">
                <span className="hub-dash-stat-value" style={{ color: card.data.snackbar ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-del-color, #f85149)' }}>
                  {card.data.snackbar ? 'Online' : 'Offline'}
                </span>
                <span className="hub-dash-stat-label">Snackbar</span>
              </div>
            </div>
          </div>
        )

      case 'surface':
        if (isExpanded) {
          return (
            <div className="hub-dash-card-list">
              {card.data.map((s: SurfaceDef) => (
                <div key={s.id} className="hub-dash-list-item" onClick={() => {
                  if (s.status === 'running') {
                    window.location.href = `http://localhost:${s.port}`
                  } else if (snackbarAvailable) {
                    performAction(s.id, 'start')
                  }
                }}>
                  <div className="hub-dash-list-icon" style={{ color: s.color }}>
                    <Icon name={s.icon} size={18} />
                  </div>
                  <div className="hub-dash-list-info">
                    <div className="hub-dash-list-name">{s.name}</div>
                    <div className="hub-dash-list-subtitle">{s.subtitle}</div>
                  </div>
                  <StatusBadge status={s.status} />
                  <button className="hub-star-btn" onClick={(e) => { e.stopPropagation(); toggleStar(s.id) }} title={starred.includes(s.id) ? 'Unstar' : 'Star'}>
                    <Icon name={starred.includes(s.id) ? 'star' : 'star_border'} size={14} />
                  </button>
                </div>
              ))}
            </div>
          )
        }
        return (
          <div className="hub-dash-card-preview">
            <div className="hub-dash-card-preview-items">
              {card.data.slice(0, 3).map((s: SurfaceDef) => (
                <div key={s.id} className="hub-dash-preview-item" style={{ borderLeftColor: s.color }}>
                  <span className="hub-dash-preview-name">{s.name}</span>
                  <StatusBadge status={s.status} />
                </div>
              ))}
              {card.data.length > 3 && (
                <div className="hub-dash-preview-more">+{card.data.length - 3} more</div>
              )}
            </div>
          </div>
        )

      case 'chat-prompt':
        return (
          <div className="hub-dash-card-prompts">
            <div className="hub-dash-prompts-grid">
              {card.data.map((p: any) => (
                <button key={p.id} className="hub-dash-prompt-btn" style={{ '--prompt-color': p.color } as React.CSSProperties}>
                  <Icon name={p.icon} size={14} />
                  <span>{p.label}</span>
                </button>
              ))}
            </div>
          </div>
        )

      case 'quick-action':
        return (
          <div className="hub-dash-card-actions">
            {card.data.map((a: any) => (
              <button key={a.id} className="hub-dash-action-btn" onClick={a.action || undefined}>
                <Icon name={a.icon} size={14} />
                <span>{a.label}</span>
              </button>
            ))}
          </div>
        )

      case 'tasks':
        const { tasks: taskList, toggleTask: toggleTaskFn } = card.data
        return (
          <div className="hub-dash-card-tasks">
            {taskList.map((task: any) => (
              <div key={task.id} className="hub-dash-task-row">
                <label className="hub-dash-task-label">
                  <input type="checkbox" checked={task.completed} onChange={() => toggleTaskFn(task.id)} style={{ accentColor: 'var(--pico-primary, #58a6ff)' }} />
                  <span className={`hub-dash-task-text ${task.completed ? 'hub-dash-task-text--done' : ''}`}>{task.title}</span>
                </label>
                <span className={`hub-dash-task-priority hub-dash-task-priority--${task.priority}`}>{task.priority}</span>
              </div>
            ))}
            {taskList.length === 0 && (
              <div className="hub-dash-empty">
                <Icon name="checklist" size={18} />
                <span>No tasks yet</span>
              </div>
            )}
          </div>
        )

      case 'activity':
        return (
          <div className="hub-dash-card-activity">
            {card.data.map((item: any, idx: number) => (
              <div key={idx} className="hub-dash-activity-row">
                <span className="hub-dash-activity-date">{item.date}</span>
                <span className="hub-dash-activity-title">{item.title}</span>
              </div>
            ))}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="hub-dashboard">
      {/* ─── Dashboard Cards Grid ───────────────────────────────── */}
      <div className="hub-dash-cards-grid">
        {sortedCards.map(card => (
          <div
            key={card.id}
            className={`hub-dash-card hub-dash-card--${card.size || 'medium'} ${expandedCard === card.id ? 'hub-dash-card--expanded' : ''}`}
            style={{ '--dash-card-color': card.color || 'var(--pico-primary, #58a6ff)' } as React.CSSProperties}
          >
            {/* Card Header */}
            <div className="hub-dash-card-header" onClick={() => setExpandedCard(expandedCard === card.id ? null : card.id)}>
              <div className="hub-dash-card-header-left">
                {card.icon && <Icon name={card.icon} size={16} />}
                <div className="hub-dash-card-header-info">
                  <h3 className="hub-dash-card-title">{card.title}</h3>
                  {card.subtitle && <span className="hub-dash-card-subtitle">{card.subtitle}</span>}
                </div>
              </div>
              <div className="hub-dash-card-header-right">
                <button className="hub-dash-move-btn" onClick={(e) => { e.stopPropagation(); moveCard(card.id, 'up') }} title="Move up">
                  <Icon name="chevron_up" size={14} />
                </button>
                <button className="hub-dash-move-btn" onClick={(e) => { e.stopPropagation(); moveCard(card.id, 'down') }} title="Move down">
                  <Icon name="chevron_down" size={14} />
                </button>
                <button className="hub-dash-expand-btn" title={expandedCard === card.id ? 'Collapse' : 'Expand'}>
                  <Icon name={expandedCard === card.id ? 'unfold_less' : 'unfold_more'} size={16} />
                </button>
              </div>
            </div>

            {/* Card Body */}
            <div className="hub-dash-card-body">
              {renderCardContent(card)}
            </div>
          </div>
        ))}
      </div>

      {/* ─── Starred Surfaces Section (always visible) ──────────── */}
      {starredSurfaces.length > 0 && (
        <div className="hub-dashboard-section">
          <div className="hub-dashboard-section-header">
            <Icon name="star" size={16} />
            <h3>Starred Surfaces</h3>
            <span className="hub-dashboard-section-count">{starredSurfaces.length}</span>
          </div>
          <div className="hub-dashboard-starred-grid">
            {starredSurfaces.map(s => (
              <SurfaceCard
                key={s.id}
                surface={s}
                snackbarAvailable={snackbarAvailable}
                onAction={performAction}
                pendingAction={pendingActions[s.id]?.action || null}
                actionProgress={pendingActions[s.id]?.progress || null}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Modules Panel ─────────────────────────────────────────────────
function ModulesPanel() {
  const modules = [
    { id: 'terminal', name: 'Terminal', subtitle: 'System Terminal', icon: 'terminal', color: '#58a6ff', desc: 'Full system terminal with SSH, tmux, and command history.' },
    { id: 'vault', name: 'Vault', subtitle: 'Document Store', icon: 'folder', color: '#22c55e', desc: 'Browse, search, and manage documents across all binders.' },
    { id: 'maps', name: 'Maps', subtitle: 'Spatial Grid', icon: 'map', color: '#f0883e', desc: 'Visual spatial grid system for surface layout management.' },
    { id: 'settings', name: 'Settings', subtitle: 'System Config', icon: 'tune', color: '#f59e0b', desc: 'Configure system preferences, themes, and surface settings.' },
    { id: 'system-pages', name: 'System Pages', subtitle: 'System Pages Hub', icon: 'settings_suggest', color: '#58a6ff', desc: 'System information, diagnostics, maintenance, and workflow pages.', route: '/s100' },
    { id: 'vibe-agent', name: 'Vibe Agent', subtitle: 'Chat UI · OK Assistant', icon: 'school', color: '#a855f7', desc: 'AI-powered chat interface with Vibe Agent and Developer modes. Ask questions, run commands, and manage your workspace.', route: '/assistui' },
    { id: 'assistui', name: 'Assist', subtitle: 'Full-Page AI Chat', icon: 'smart_toy', color: '#a855f7', desc: 'Full-page AI chat with streaming responses, model selection, conversation management, and multi-agent support.', route: '/assistui' },
    { id: 'story-builder', name: 'Story Builder', subtitle: 'Step-by-step guides', icon: 'menu_book', color: '#22c55e', desc: 'Create step-by-step guides and walkthroughs for your workspace.', route: '/s101' },
    { id: 'workflow-builder', name: 'Workflow Builder', subtitle: 'Automated workflows', icon: 'account_tree', color: '#58a6ff', desc: 'Create and manage automated workflows with triggers for time, GitHub, vault, and more.', route: '/s300' },
    { id: 'tool-builder', name: 'Tool Builder', subtitle: 'Custom tool registry', icon: 'puzzle', color: '#f0883e', desc: 'Build and register custom tools for your workspace.', route: '/s100' },
  ]
  // Update the Open button to navigate to the route if present
  const openModule = (mod: any) => {
    if (mod.route) {
      window.location.href = mod.route
    }
  }
  return (
    <div className="hub-apps">
      <div className="hub-apps-section">
        <div className="hub-apps-section-header">
          <Icon name="apps" size={18} />
          <h3>Installed Modules</h3>
          <p>Tools and utilities available across surfaces</p>
        </div>

        <div className="hub-apps-grid">
          {modules.map(mod => (
            <div key={mod.id} className="hub-app-card" style={{ '--hub-app-color': mod.color } as React.CSSProperties}>
              <div className="hub-app-card-header">
                <div className="hub-app-card-icon" style={{ background: `${mod.color}20`, color: mod.color }}>
                  <Icon name={mod.icon} size={24} />
                </div>
                <div className="hub-app-card-info">
                  <h3 className="hub-app-card-title">{mod.name}</h3>
                  <p className="hub-app-card-subtitle" style={{ color: mod.color }}>{mod.subtitle}</p>
                </div>
              </div>
              <p className="hub-app-card-desc">{mod.desc}</p>
              <div className="hub-app-card-footer">
                <span className="hub-app-card-badge">System</span>
                <button className="hub-btn hub-btn--primary" onClick={() => openModule(mod)}>Open</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}


// ─── Settings Panel — REMOVED from UIHubManager ────────────────────
// SettingsPanel + AIModelsStatus have been moved to
// src/surfaces/system/SettingsPanel.tsx and are now served from
// the consolidated server surface settings tab (/server?tab=settings).
// The gear icon in GlobalToolbar navigates there from any surface.

// ─── Install Panel ─────────────────────────────────────────────────
function InstallPanel() {
  const [activeSection, setActiveSection] = useState<'apps' | 'browser'>('apps')

  // ─── Probe local installations via Snackbar API + direct port checks ──
  const [appStatuses, setAppStatuses] = useState<Record<string, 'checking' | 'installed' | 'running' | 'missing'>>({})
  const [ollamaModels, setOllamaModels] = useState<string[]>([])
  const [dockerContainers, setDockerContainers] = useState<number>(0)

  useEffect(() => {
    let cancelled = false

    async function probeAll() {
      const status: Record<string, 'checking' | 'installed' | 'running' | 'missing'> = {}

      // Ollama — probe port 11434
      try {
        const res = await fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(2000) })
        if (res.ok) {
          const data = await res.json()
          status.ollama = 'running'
          if (!cancelled) setOllamaModels((data.models || []).map((m: any) => m.name))
        } else {
          status.ollama = 'installed'
        }
      } catch {
        status.ollama = 'missing'
      }

      // Docker — probe socket via snackbar
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/docker/ps`, { signal: AbortSignal.timeout(2000) })
        if (res.ok) {
          const data = await res.json()
          status.docker = 'running'
          if (!cancelled) setDockerContainers(data.containers?.length || 0)
        } else {
          status.docker = 'installed'
        }
      } catch {
        // Fallback: check if docker binary exists via snackbar
        try {
          const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'which docker' }),
            signal: AbortSignal.timeout(2000),
          })
          if (res.ok) {
            const data = await res.json()
            status.docker = data.stdout ? 'installed' : 'missing'
          } else {
            status.docker = 'missing'
          }
        } catch {
          status.docker = 'missing'
        }
      }

      // Node.js — probe via snackbar
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'node --version' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.nodejs = data.stdout ? 'installed' : 'missing'
        } else {
          status.nodejs = 'missing'
        }
      } catch {
        status.nodejs = 'missing'
      }

      // Git — probe via snackbar
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'git --version' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.git = data.stdout ? 'installed' : 'missing'
        } else {
          status.git = 'missing'
        }
      } catch {
        status.git = 'missing'
      }

      // GitHub CLI — probe via snackbar
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'gh --version' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.gh = data.stdout ? 'installed' : 'missing'
        } else {
          status.gh = 'missing'
        }
      } catch {
        status.gh = 'missing'
      }

      // VS Code — probe via snackbar
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'which code' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.vscode = data.stdout ? 'installed' : 'missing'
        } else {
          status.vscode = 'missing'
        }
      } catch {
        status.vscode = 'missing'
      }

      // Zen Browser — probe via snackbar
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'mdfind "kMDItemKind == Application" | grep -i zen' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status['zen-browser'] = data.stdout ? 'installed' : 'missing'
        } else {
          status['zen-browser'] = 'missing'
        }
      } catch {
        status['zen-browser'] = 'missing'
      }

      // QQcode — probe via pip
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'qqcode --help' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.qqcode = data.stdout ? 'installed' : 'missing'
        } else {
          status.qqcode = 'missing'
        }
      } catch {
        status.qqcode = 'missing'
      }

      // uConnect Mod — always local (part of Developer)
      status['uconnect-mod'] = 'installed'

      if (!cancelled) setAppStatuses(status)
    }

    probeAll()
    return () => { cancelled = true }
  }, [])

  const installableApps = [
    { id: 'zen-browser', name: 'Zen Browser', subtitle: 'uConnect Shell', icon: 'language', color: '#6c63ff', category: 'Browser', desc: 'Privacy-first, Gecko-based browser with radical customisable UI. Transform it into the ultimate shell for uConnect with workspace isolation, vertical tabs, and split view.', url: 'https://zen-browser.app' },
    { id: 'uconnect-mod', name: 'uConnect Shell Mod', subtitle: 'Zen Browser Extension', icon: 'puzzle', color: '#f59e0b', category: 'Extension', desc: 'Zen Browser mod that integrates the uDos ecosystem directly into the browser. Provides vault sidebar, tab interception, udos:// protocol routing, and workspace management.', url: '/uconnect-mod.xpi' },
    { id: 'ollama', name: 'Ollama', subtitle: 'Local AI Models', icon: 'smart_toy', color: '#22c55e', category: 'AI', desc: 'Run large language models locally. Supports Llama, Mistral, Gemma, and many more. Required for AI-powered features across uConnect surfaces.', url: 'https://ollama.ai' },
    { id: 'docker', name: 'Docker', subtitle: 'Container Runtime', icon: 'view_in_ar', color: '#58a6ff', category: 'Infrastructure', desc: 'Container platform for running uServer, Snackbar, and other uDos services. Required for surface management and dynamic service orchestration.', url: 'https://docker.com' },
    { id: 'nodejs', name: 'Node.js', subtitle: 'JavaScript Runtime', icon: 'javascript', color: '#22c55e', category: 'Runtime', desc: 'JavaScript runtime for running uConnect UI Hub, uServer backend, and Snackbar services. Required version 18+.', url: 'https://nodejs.org' },
    { id: 'vscode', name: 'VS Code', subtitle: 'Code Editor', icon: 'code', color: '#58a6ff', category: 'Editor', desc: 'Primary code editor for uDos development. Integrates with Developer surface for seamless development workflow.', url: 'https://code.visualstudio.com' },
    { id: 'git', name: 'Git', subtitle: 'Version Control', icon: 'commit', color: '#f0883e', category: 'Tools', desc: 'Distributed version control system. Required for all uDos repositories and Developer project management.', url: 'https://git-scm.com' },
    { id: 'gh', name: 'GitHub CLI', subtitle: 'GitHub from Terminal', icon: 'terminal', color: '#a855f7', category: 'Tools', desc: 'Command-line interface for GitHub. Used for release management, issue tracking, and repository operations.', url: 'https://cli.github.com' },
    { id: 'qqcode', name: 'QQcode', subtitle: 'Terminal AI Agent', icon: 'terminal', color: '#22c55e', category: 'AI', desc: 'Lightweight CLI coding agent focused on speed, determinism, and developer control. Bring your own backends — Ollama, OpenRouter, DeepSeek. No forced API calls.', url: 'https://github.com/qnguyen3/qqcode' },
  ]

  const browserMods = [
    { id: 'userjs', name: 'user.js Config', subtitle: 'Zen Browser Settings', icon: 'settings', color: '#6c63ff', category: 'Configuration', desc: 'Pre-configured about:config settings that transform Zen into a dedicated uConnect shell. Hides top bar, disables new tabs, configures sidebar, and optimises performance.', path: '~/Code/uCore/zen-config/user.js' },
    { id: 'userchrome', name: 'userChrome.css', subtitle: 'Browser Chrome Styling', icon: 'palette', color: '#f59e0b', category: 'Styling', desc: 'CSS that hides browser chrome elements (nav bar, tab bar, menu bar) and styles the sidebar with uConnect branding and workspace badges.', path: '~/Code/uCore/zen-config/userChrome.css' },
    { id: 'usercontent', name: 'userContent.css', subtitle: 'Page Content Styling', icon: 'web', color: '#22c55e', category: 'Styling', desc: 'CSS for styling web pages within the uConnect shell, including Web Reader integration and workspace-aware page overrides.', path: '~/Code/uCore/zen-config/userContent.css' },
    { id: 'sidebar', name: 'Vault Sidebar', subtitle: 'uConnect Navigation', icon: 'folder', color: '#58a6ff', category: 'Extension', desc: 'Zen Browser sidebar panel providing navigation to all vaults in the ~/Vaults/ container, system folders, and uConnect tools.', path: '~/Code/uCore/uconnect-mod/sidebar/sidebar.html' },
    { id: 'background', name: 'Background Script', subtitle: 'Tab & Protocol Handler', icon: 'sync', color: '#f0883e', category: 'Extension', desc: 'Background script that intercepts new tabs, handles udos:// protocol routing, manages context menus, and provides workspace detection.', path: '~/Code/uCore/uconnect-mod/background.js' },
    { id: 'content', name: 'Content Script', subtitle: 'Link Interception', icon: 'link', color: '#a855f7', category: 'Extension', desc: 'Content script that intercepts link clicks, prevents new tab/window openings, and routes udos:// URLs to the vault system.', path: '~/Code/uCore/uconnect-mod/content.js' },
  ]

  function getAppStatus(appId: string): { label: string; icon: string; color: string; bg: string } {
    const s = appStatuses[appId]
    if (!s || s === 'checking') return { label: 'Checking...', icon: 'sync', color: 'var(--pico-muted-color, #8b949e)', bg: 'var(--pico-card-background-color, #161b22)' }
    if (s === 'running') return { label: 'Running', icon: 'check_circle', color: 'var(--pico-ins-color, #3fb950)', bg: 'var(--pico-ins-color, #3fb950)' }
    if (s === 'installed') return { label: 'Installed', icon: 'check_circle', color: 'var(--pico-primary, #58a6ff)', bg: 'var(--pico-primary, #58a6ff)' }
    return { label: 'Not Found', icon: 'radio_button_unchecked', color: 'var(--pico-muted-color, #8b949e)', bg: 'var(--pico-card-background-color, #161b22)' }
  }

  return (
    <div className="hub-install">
      <div className="hub-install-section">
        <div className="hub-install-section-header">
          <Icon name="download" size={18} />
          <h3>Install & Configure</h3>
          <p>Tools, runtimes, and browser mods for the uConnect ecosystem</p>
        </div>

        <div className="hub-tab-bar" style={{ justifyContent: 'flex-start', padding: '0 0 16px' }}>
          <button
            className={`hub-tab-btn ${activeSection === 'apps' ? 'hub-tab-btn--active' : ''}`}
            onClick={() => setActiveSection('apps')}
          >
            <Icon name="apps" size={16} />
            <span>Applications</span>
          </button>
          <button
            className={`hub-tab-btn ${activeSection === 'browser' ? 'hub-tab-btn--active' : ''}`}
            onClick={() => setActiveSection('browser')}
          >
            <Icon name="language" size={16} />
            <span>Zen Browser Mods</span>
          </button>
        </div>

        {activeSection === 'apps' && (
          <div className="hub-install-grid">
            {installableApps.map(app => {
              const status = getAppStatus(app.id)
              const isInstalled = appStatuses[app.id] === 'installed' || appStatuses[app.id] === 'running'
              const isRunning = appStatuses[app.id] === 'running'
              return (
                <div key={app.id} className="hub-install-card" style={{ '--hub-install-color': app.color } as React.CSSProperties}>
                  <div className="hub-install-card-header">
                    <div className="hub-install-card-icon" style={{ background: `${app.color}20`, color: app.color }}>
                      <Icon name={app.icon} size={26} />
                    </div>
                    <div className="hub-install-card-info">
                      <h3 className="hub-install-card-title">{app.name}</h3>
                      <span className="hub-install-card-category" style={{ background: `${app.color}20`, color: app.color }}>{app.category}</span>
                    </div>
                  </div>
                  <p className="hub-install-card-desc">{app.desc}</p>

                  {/* ─── Extra info for running services ──────────── */}
                  {app.id === 'ollama' && isRunning && ollamaModels.length > 0 && (
                    <div style={{ padding: '4px 0 8px', display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {ollamaModels.map(m => (
                        <span key={m} style={{ fontSize: 11, padding: '2px 6px', borderRadius: 4, background: 'var(--pico-card-background-color, #161b22)', color: 'var(--pico-muted-color, #8b949e)', fontFamily: 'monospace' }}>{m}</span>
                      ))}
                    </div>
                  )}
                  {app.id === 'docker' && isRunning && dockerContainers > 0 && (
                    <div style={{ padding: '4px 0 8px', fontSize: 12, color: 'var(--pico-muted-color, #8b949e)' }}>
                      {dockerContainers} container{dockerContainers !== 1 ? 's' : ''} running
                    </div>
                  )}

                  <div className="hub-install-card-footer">
                    <span className="hub-app-card-badge" style={{ background: status.bg, color: status.color }}>
                      <Icon name={status.icon} size={12} style={{ marginRight: 4 }} />
                      {status.label}
                    </span>
                    <a
                      href={app.url}
                      target={app.url.startsWith('http') ? '_blank' : undefined}
                      rel={app.url.startsWith('http') ? 'noopener noreferrer' : undefined}
                      className="hub-btn hub-btn--primary"
                      style={isInstalled ? { background: 'var(--pico-ins-color, #3fb950)', color: 'var(--pico-ins-color, #3fb950)' } : undefined}
                    >
                      {isInstalled ? 'Open' : 'Install'}
                      <Icon name="open_in_new" size={14} />
                    </a>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {activeSection === 'browser' && (
          <>
            {/* ─── Zen Browser Setup Guide ─────────────────────────── */}
            <div className="hub-install-card" style={{ '--hub-install-color': '#6c63ff', marginBottom: 16 } as React.CSSProperties}>
              <div className="hub-install-card-header">
                <div className="hub-install-card-icon" style={{ background: '#6c63ff20', color: '#6c63ff' }}>
                  <Icon name="auto_awesome" size={26} />
                </div>
                <div className="hub-install-card-info">
                  <h3 className="hub-install-card-title">Setup Guide</h3>
                  <span className="hub-install-card-category" style={{ background: '#6c63ff20', color: '#6c63ff' }}>Quick Start</span>
                </div>
              </div>
              <p className="hub-install-card-desc">
                Transform Zen Browser into a dedicated uConnect shell. Follow these steps:
              </p>
              <div style={{ padding: '8px 0', display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '1rem', color: 'var(--pico-color, #c9d1d9)' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 24, height: 24, borderRadius: '50%', background: 'var(--pico-primary, #58a6ff)', color: '#ffffff', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>1</span>
                  <span>Install Zen Browser from <a href="https://zen-browser.app" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--pico-primary, #58a6ff)' }}>zen-browser.app</a></span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '1rem', color: 'var(--pico-color, #c9d1d9)' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 24, height: 24, borderRadius: '50%', background: 'var(--pico-primary, #58a6ff)', color: '#ffffff', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>2</span>
                  <span>Copy <code style={{ background: 'var(--pico-background-color, #0d1117)', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace' }}>zen-config/user.js</code> to your Zen profile</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '1rem', color: 'var(--pico-color, #c9d1d9)' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 24, height: 24, borderRadius: '50%', background: 'var(--pico-primary, #58a6ff)', color: '#ffffff', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>3</span>
                  <span>Copy <code style={{ background: 'var(--pico-background-color, #0d1117)', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace' }}>zen-config/userChrome.css</code> to <code style={{ background: 'var(--pico-background-color, #0d1117)', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace' }}>~/Library/Application Support/Zen/chrome/</code></span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '1rem', color: 'var(--pico-color, #c9d1d9)' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 24, height: 24, borderRadius: '50%', background: 'var(--pico-primary, #58a6ff)', color: '#ffffff', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>4</span>
                  <span>Load the uConnect Mod via <code style={{ background: 'var(--pico-background-color, #0d1117)', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace' }}>about:debugging</code> → This Firefox → Load Temporary Add-on</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '1rem', color: 'var(--pico-color, #c9d1d9)' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 24, height: 24, borderRadius: '50%', background: 'var(--pico-primary, #58a6ff)', color: '#ffffff', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>5</span>
                  <span>Navigate to <code style={{ background: 'var(--pico-background-color, #0d1117)', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace' }}>http://localhost:3000</code> — the uConnect UI Hub</span>
                </div>
              </div>
            </div>

            {/* ─── Browser Mods Grid ──────────────────────────────── */}
            <div className="hub-install-grid">
              {browserMods.map(mod => (
                <div key={mod.id} className="hub-install-card" style={{ '--hub-install-color': mod.color } as React.CSSProperties}>
                  <div className="hub-install-card-header">
                    <div className="hub-install-card-icon" style={{ background: `${mod.color}20`, color: mod.color }}>
                      <Icon name={mod.icon} size={26} />
                    </div>
                    <div className="hub-install-card-info">
                      <h3 className="hub-install-card-title">{mod.name}</h3>
                      <span className="hub-install-card-category" style={{ background: `${mod.color}20`, color: mod.color }}>{mod.category}</span>
                    </div>
                  </div>
                  <p className="hub-install-card-desc">{mod.desc}</p>
                  <div className="hub-install-card-footer">
                    <span className="hub-app-card-badge" style={{ background: 'var(--pico-primary, #58a6ff)', color: 'var(--pico-primary, #58a6ff)' }}>
                      Local
                    </span>
                    <span className="hub-card-port" style={{ fontSize: 11 }}>{mod.path}</span>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ─── Docs Panel ────────────────────────────────────────────────────
function DocsPanel() {
  const [docView, setDocView] = useState<'library' | 'list' | 'site'>('library')
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'synced' | 'failed'>('idle')
  const [lastSynced, setLastSynced] = useState<string | null>(() => localStorage.getItem('docs-last-synced'))
  const [syncMessage, setSyncMessage] = useState('')

  // ─── Sync docs via Snackbar API ──────────────────────────────────
  const syncDocs = useCallback(async () => {
    setSyncStatus('syncing')
    setSyncMessage('Syncing documentation...')
    try {
      const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: `cd ~/Code/uCore && ./skills/docs-site-sync/run.sh 2>&1`,
        }),
        signal: AbortSignal.timeout(30000),
      })
      if (res.ok) {
        const data = await res.json()
        const now = new Date().toLocaleString()
        setLastSynced(now)
        localStorage.setItem('docs-last-synced', now)
        setSyncStatus('synced')
        setSyncMessage(data.stdout?.split('\n').filter((l: string) => l.includes('✅') || l.includes('❌')).slice(-3).join(' | ') || 'Docs synced successfully')
      } else {
        setSyncStatus('failed')
        setSyncMessage('Snackbar API returned an error')
      }
    } catch {
      setSyncStatus('failed')
      setSyncMessage('Snackbar unavailable — start snackbar first')
    }
  }, [])

  const docSections = [
    {
      id: 'guides',
      title: 'Guides',
      icon: 'auto_stories',
      color: '#58a6ff',
      desc: 'Development environment setup, workflow, surface architecture, configuration, and end-user guides.',
      docs: [      ],
    },
    {
      id: 'references',
      title: 'References',
      icon: 'menu_book',
      color: '#22c55e',
      desc: 'System architecture, roadmap, changelog, narrator system, and skills pipeline reference.',
      docs: [      ],
    },
    {
      id: 'system',
      title: 'System',
      icon: 'settings_suggest',
      color: '#f0883e',
      desc: 'Snackbar API, CLI tools, utility scripts, extension system, and module system documentation.',
      docs: [      ],
    },
    {
      id: 'zen',
      title: 'Zen Browser',
      icon: 'language',
      color: '#6c63ff',
      desc: 'Setup guide, uConnect mod, user.js configuration, chrome CSS, and workspace-to-vault mapping.',
      docs: [      ],
    },
  ]

  // ─── List view: show docs for a specific section ──────────────
  if (docView === 'list' && activeSection) {
    const section = docSections.find(s => s.id === activeSection)
    if (!section) {
      setDocView('library')
      return null
    }
    return (
      <div className="hub-docs">
        <div className="hub-docs-section">
          <div className="hub-docs-section-header">
            <button className="hub-btn hub-btn--info" onClick={() => setDocView('library')}>
              <Icon name="arrow_back" size={14} /> Back
            </button>
            <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600, color: section.color }}>{section.title}</h3>
            <p>{section.docs.length} documents</p>
          </div>
          <div className="hub-docs-grid">
            {section.docs.map(doc => (
              <a key={doc.id} href={doc.url} className="hub-doc-card" style={{ '--hub-doc-color': section.color } as React.CSSProperties}>
                <div className="hub-doc-card-header">
                  <div className="hub-doc-card-icon" style={{ background: `${section.color}20`, color: section.color }}>
                    <Icon name={doc.icon} size={22} />
                  </div>
                  <div className="hub-doc-card-info">
                    <h3 className="hub-doc-card-title">{doc.name}</h3>
                    <p className="hub-doc-card-subtitle" style={{ color: section.color }}>{doc.subtitle}</p>
                  </div>
                </div>
                <div className="hub-doc-card-footer">
                  <span className="hub-doc-card-badge">{section.title}</span>
                  <span className="hub-doc-card-open">Open →</span>
                </div>
              </a>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // ─── Site view: full docs portal ──────────────────────────────
  if (docView === 'site') {
    return (
      <div className="hub-docs" style={{ padding: 0, maxWidth: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div className="hub-docs-site-header">
          <button className="hub-btn hub-btn--info" onClick={() => setDocView('library')}>
            <Icon name="arrow_back" size={14} /> Back to Docs
          </button>
          <span className="hub-docs-site-title">Developer Documentation Site</span>
        </div>
        <iframe
          src="http://localhost:5185"
          className="hub-docs-site-iframe"
          title="Documentation Site"
          sandbox="allow-scripts allow-same-origin allow-forms"
        />
      </div>
    )
  }

  // ─── Library view: one card per section ───────────────────────
  return (
    <div className="hub-docs">
      <div className="hub-docs-section">
        <div className="hub-docs-section-header">
          <Icon name="menu_book" size={18} />
          <h3>Documentation Library</h3>
          <p>Guides, references, and system documentation</p>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            {lastSynced && (
              <span style={{ fontSize: 11, color: 'var(--pico-muted-color, #8b949e)', whiteSpace: 'nowrap' }}>
                Synced: {lastSynced}
              </span>
            )}
            <button
              className={`hub-btn ${syncStatus === 'syncing' ? 'hub-btn--warning' : syncStatus === 'failed' ? 'hub-btn--danger' : 'hub-btn--info'}`}
              onClick={syncDocs}
              disabled={syncStatus === 'syncing'}
              title="Sync docs from Developer via Snackbar"
              style={{ fontSize: 12, gap: 4 }}
            >
              <Icon name={syncStatus === 'syncing' ? 'sync' : syncStatus === 'failed' ? 'error' : 'refresh'} size={14} className={syncStatus === 'syncing' ? 'hub-spin' : ''} />
              {syncStatus === 'syncing' ? 'Syncing...' : syncStatus === 'failed' ? 'Retry' : 'Sync Docs'}
            </button>
          </div>
        </div>
        {syncMessage && syncStatus !== 'idle' && (
          <div style={{
            padding: '8px 12px', marginBottom: 12, borderRadius: 6, fontSize: 12,
            background: syncStatus === 'synced' ? 'var(--pico-ins-color, #3fb950)' :
                        syncStatus === 'failed' ? 'var(--pico-del-color, #f85149)' :
                        'var(--pico-card-background-color, #161b22)',
            color: syncStatus === 'synced' ? 'var(--pico-ins-color, #3fb950)' :
                   syncStatus === 'failed' ? 'var(--pico-del-color, #f85149)' :
                   'var(--pico-muted-color, #8b949e)',
          }}>
            <Icon name={syncStatus === 'synced' ? 'check_circle' : syncStatus === 'failed' ? 'error' : 'sync'} size={12} style={{ marginRight: 6 }} />
            {syncMessage}
          </div>
        )}

        <div className="hub-docs-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))' }}>
          {docSections.map(section => (
            <div
              key={section.id}
              className="hub-doc-card"
              style={{ '--hub-doc-color': section.color, cursor: 'pointer' } as React.CSSProperties}
              onClick={() => { setActiveSection(section.id); setDocView('list') }}
            >
              <div className="hub-doc-card-header">
                <div className="hub-doc-card-icon" style={{ background: `${section.color}20`, color: section.color }}>
                  <Icon name={section.icon} size={26} />
                </div>
                <div className="hub-doc-card-info">
                  <h3 className="hub-doc-card-title">{section.title}</h3>
                  <p className="hub-doc-card-subtitle" style={{ color: section.color }}>{section.docs.length} documents</p>
                </div>
              </div>
              <p className="hub-install-card-desc">{section.desc}</p>
              <div className="hub-doc-card-footer">
                <span className="hub-doc-card-badge">{section.docs.length} docs</span>
                <span className="hub-doc-card-open">Browse →</span>
              </div>
            </div>
          ))}

          {/* Docs Site Portal Card */}
          <div className="hub-doc-card" style={{ '--hub-doc-color': '#58a6ff', cursor: 'pointer' } as React.CSSProperties} onClick={() => setDocView('site')}>
            <div className="hub-doc-card-header">
              <div className="hub-doc-card-icon" style={{ background: '#58a6ff20', color: '#58a6ff' }}>
                <Icon name="web" size={26} />
              </div>
              <div className="hub-doc-card-info">
                <h3 className="hub-doc-card-title">Docs Site</h3>
                <p className="hub-doc-card-subtitle" style={{ color: '#58a6ff' }}>Full documentation portal</p>
              </div>
            </div>
            <p className="hub-install-card-desc">VitePress-powered documentation site with full-text search, navigation, and all Developer documentation.</p>
            <div className="hub-doc-card-footer">
              <span className="hub-doc-card-badge">Portal</span>
              <span className="hub-doc-card-open">Open →</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Inner App ─────────────────────────────────────────────────────
function UIHubInner() {
  const store = useSurfaceStore()
  const [surfaces, setSurfaces] = useState<SurfaceDef[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [loadingMessage, setLoadingMessage] = useState('Initialising...')
  const [snackbarAvailable, setSnackbarAvailable] = useState(false)
  const [pendingActions, setPendingActions] = useState<Record<string, { action: SurfaceAction; progress: ActionProgress }>>({})
  const progressIntervals = useRef<Record<string, ReturnType<typeof setInterval>>>({})
  const [activeTab, setActiveTab] = useState<HubTab>(() => {
    // Check URL for ?tab=surfaces (set by Home icon in GlobalToolbar)
    const params = new URLSearchParams(window.location.search)
    const tabParam = params.get('tab')
    if (tabParam === 'surfaces') return 'surfaces'
    return 'dashboard'
  })
  const [starred, setStarred] = useState<string[]>(loadStarred)


  const runningCount = surfaces.filter(s => s.status === 'running').length

  const toggleStar = (id: string) => {
    setStarred(prev => {
      const next = prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
      saveStarred(next)
      return next
    })
  }

  // ─── Filter surfaces for Surfaces tab: hide HIDDEN_FROM_SURFACES_TAB unless starred ──
  // Legacy IDs are explicitly hidden from active nav.
  const surfacesForTab = surfaces.filter(s => {
    if (['devstudio', 'proseui', 'usystem', 'userver'].includes(s.id)) return false
    // Hide hidden surfaces unless starred
    if (HIDDEN_FROM_SURFACES_TAB.includes(s.id)) {
      return starred.includes(s.id)
    }
    return true
  })

  // ─── Snackbar Health Check (with retry) ─────────────────────────
  const checkSnackbarHealth = useCallback(async (retries = 3, delay = 1000) => {
    for (let attempt = 0; attempt < retries; attempt++) {
      for (const endpoint of ['/v1/health', '/health']) {
        try {
          const res = await fetch(`${SNACKBAR_API}${endpoint}`, { signal: AbortSignal.timeout(2000) })
          if (res.status >= 200 && res.status < 400) return true
        } catch { /* ignore */ }
      }
      if (attempt < retries - 1) {
        await new Promise(r => setTimeout(r, delay))
      }
    }
    return false
  }, [])

  // ─── Discover Surfaces (from snackbar) ──────────────────────────
  const tryDiscover = useCallback(async (): Promise<SurfaceDef[] | null> => {
    try {
      const res = await fetch(`${SNACKBAR_API}/v1/surfaces`)
      if (!res.ok) throw new Error('HTTP ' + res.status)
      const data = await res.json()
      if (data && data.surfaces) {
        const statusMap: Record<string, string> = {}
        for (const s of data.surfaces) {
          statusMap[s.id] = (s.status || (s.running ? 'running' : 'stopped')).toLowerCase()
        }
        return data.surfaces.map((def: any) => ({
          id: def.id,
          name: def.name,
          subtitle: def.subtitle,
          description: def.description,
          port: def.port,
          color: def.color,
          icon: def.icon,
          status: statusMap[def.id] || 'stopped',
          cell: def.cell || null,
          embedded: def.embedded || false,
          route: def.route || '',
        }))
      }
    } catch { /* ignore */ }
    return null
  }, [])

  // ─── Probe Ports ────────────────────────────────────────────────
  const probePorts = useCallback(async (list: SurfaceDef[]): Promise<SurfaceDef[]> => {
    const results = await Promise.all(list.map(async (s) => {
      // Embedded surfaces (port 0) are always "running" since they're part of the UI Hub
      if (s.embedded || s.port === 0) return { ...s, status: 'running' }
      if (pendingActions[s.id]) return { ...s, status: pendingActions[s.id].action === 'start' ? 'starting' : 'stopping' }
      try {
        const res = await fetch(`http://localhost:${s.port}`, { method: 'GET', signal: AbortSignal.timeout(1500) })
        if (res.status >= 200 && res.status < 400) return { ...s, status: 'running' }
      } catch { /* fall through */ }
      return { ...s, status: 'stopped' }
    }))
    return results
  }, [pendingActions])

  // ─── Refresh ────────────────────────────────────────────────────
  const refresh = useCallback(async () => {
    const available = await checkSnackbarHealth()
    setSnackbarAvailable(available)

    if (available) {
      const discovered = await tryDiscover()
      if (discovered && discovered.length > 0) {
        const filtered = withoutUiHub(discovered)
        const discoveredIds = new Set(filtered.map(s => s.id))
        const merged = [
          ...filtered,
          ...FALLBACK_REGISTRY.filter(fb => !discoveredIds.has(fb.id)),
        ]
        setSurfaces(sortSurfaces(merged))
        setLoading(false)
        return
      }
    }

    const probed = await probePorts(FALLBACK_REGISTRY)
    setSurfaces(probed)
    setLoading(false)
  }, [checkSnackbarHealth, tryDiscover, probePorts])

  // ─── Animated Loading Sequence ──────────────────────────────────
  useEffect(() => {
    if (!loading) return

    const steps = [
      { at: 0,  msg: 'Connecting to Snackbar...' },
      { at: 10, msg: 'Snackbar connected' },
      { at: 25, msg: 'Discovering surfaces...' },
      { at: 40, msg: 'Surfaces discovered' },
      { at: 55, msg: 'Probing surface ports...' },
      { at: 70, msg: 'Ports probed' },
      { at: 85, msg: 'Finalising...' },
      { at: 100, msg: 'Ready' },
    ]

    let stepIndex = 0
    const interval = setInterval(() => {
      stepIndex++
      if (stepIndex < steps.length) {
        setLoadingProgress(steps[stepIndex].at)
        setLoadingMessage(steps[stepIndex].msg)
      }
      if (stepIndex >= steps.length - 1) {
        clearInterval(interval)
      }
    }, 400)

    return () => clearInterval(interval)
  }, [loading])

  // ─── Start / Stop / Restart / Repair / Debug ────────────────────
  const clearPendingAction = useCallback((id: string) => {
    if (progressIntervals.current[id]) {
      clearInterval(progressIntervals.current[id])
      delete progressIntervals.current[id]
    }
    setPendingActions(prev => {
      const next = { ...prev }
      delete next[id]
      return next
    })
  }, [])

  const startProgressAnimation = useCallback((id: string, action: SurfaceAction) => {
    const initial: ActionProgress = {
      surface_id: id,
      action,
      progress: 0,
      status: 'in_progress',
      message: `${action} initiated...`,
      timestamp: new Date().toISOString(),
    }
    setPendingActions(prev => ({ ...prev, [id]: { action, progress: initial } }))

    let progress = 0
    const messages: Record<string, string[]> = {
      start: ['Initialising process...', 'Starting dev server...', 'Waiting for port...', 'Almost ready...'],
      stop: ['Sending terminate signal...', 'Waiting for process exit...', 'Cleaning up...'],
      restart: ['Stopping process...', 'Waiting for port release...', 'Starting process...', 'Waiting for port...'],
      repair: ['Running diagnostics...', 'Checking dependencies...', 'Repairing configuration...', 'Verifying...'],
      debug: ['Collecting system info...', 'Checking port status...', 'Running health checks...', 'Analysing results...'],
    }
    const msgs = messages[action] || ['Working...']

    const interval = setInterval(() => {
      progress += Math.random() * 8 + 2
      if (progress >= 90) {
        progress = 90
        clearInterval(interval)
      }
      const msgIndex = Math.min(Math.floor(progress / (90 / msgs.length)), msgs.length - 1)
      setPendingActions(prev => {
        if (!prev[id]) return prev
        return {
          ...prev,
          [id]: {
            ...prev[id],
            progress: {
              ...prev[id].progress,
              progress,
              message: msgs[msgIndex] || 'Working...',
            },
          },
        }
      })
    }, 600)
    progressIntervals.current[id] = interval
  }, [])

  const completeAction = useCallback((id: string, message?: string) => {
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
            message: message || 'Complete',
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
        case 'start':
          endpoint = `/v1/surfaces/${id}/start`
          break
        case 'stop':
          endpoint = `/v1/surfaces/${id}/stop`
          break
        case 'restart':
          endpoint = `/v1/surfaces/${id}/restart`
          break
        case 'repair':
          endpoint = `/v1/surfaces/${id}/repair`
          break
        case 'debug':
          endpoint = `/v1/surfaces/${id}/debug`
          break
      }

      const res = await fetch(`${SNACKBAR_API}${endpoint}`, { method: 'POST' })
      const result = await res.json()

      if (result.error) {
        store.showSnackbar({ message: `${action} ${id}: ${result.error}`, type: 'error' })
        failAction(id, result.error)
        return
      }

      // Handle embedded surface response — they're always "running" via UI Hub
      // Snackbar API returns {"status": "running", "embedded": true} for embedded surfaces
      if (result.embedded === true) {
        store.showSnackbar({ message: `${id} is embedded — already available via UI Hub`, type: 'info' })
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
        if (action === 'start' || action === 'restart') {
          return { ...s, status: 'starting' }
        }
        if (action === 'stop') {
          return { ...s, status: 'stopping' }
        }
        return s
      }))

      store.showSnackbar({ message: `${action} ${id}...`, type: 'info' })

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
      store.showSnackbar({ message: `Failed to ${action} ${id}: ${e.message}`, type: 'error' })
      failAction(id, e.message)
    }
  }, [store, refresh, pendingActions, startProgressAnimation, completeAction, failAction, surfaces])

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
  const hubTabs: ToolbarTab[] = HUB_TABS.map(t => ({
    id: t.id,
    icon: t.icon,
    label: t.label,
    active: activeTab === t.id,
    onClick: () => setActiveTab(t.id),
  }))

  return (
    <div className="hub-surface">
      <GlobalToolbar
        tabs={hubTabs}
        rightExtra={
          <span className="hub-status-badge">
            <span className={`hub-status-dot ${runningCount > 0 ? 'hub-status-dot--online' : ''}`} />
            {runningCount}/{surfaces.length} online
          </span>
        }
      />


      <div className="usx-surface-body" style={{ display: 'flex', overflow: 'hidden', position: 'relative' }}>
        <main className="usx-surface-main" style={{ flex: 1, overflow: 'auto' }}>
          {loading ? (
            <LoadingOverlay message={loadingMessage} progress={loadingProgress} />
          ) : activeTab === 'surfaces' ? (

            <div className="hub-grid">
              {surfacesForTab.map(s => (
                <SurfaceCard
                  key={s.id}
                  surface={s}
                  snackbarAvailable={snackbarAvailable}
                  onAction={performAction}
                  pendingAction={pendingActions[s.id]?.action || null}
                  actionProgress={pendingActions[s.id]?.progress || null}
                  starred={starred.includes(s.id)}
                  onToggleStar={toggleStar}
                />
              ))}
            </div>
          ) : activeTab === 'dashboard' ? (
            <DashboardPanel
              surfaces={surfaces}
              snackbarAvailable={snackbarAvailable}
              performAction={performAction}
              pendingActions={pendingActions}
            />
          ) : activeTab === 'install' ? (
            <InstallPanel />
          ) : activeTab === 'docs' ? (
            <DocsPanel />
          ) : null}
        </main>
      </div>

      <footer className="hub-footer">
        <span>uDosConnect · uCode Surface Hub · Spatial Grid System</span>
        {snackbarAvailable ? (
          <span className="hub-footer-snackbar">Snackbar host active — dynamic surface management</span>
        ) : (
          <span className="hub-footer-static">Snackbar offline — static port fallback</span>
        )}
      </footer>

      <SurfaceSnackbar
        snackbar={store.snackbar}
        onDismiss={store.dismissSnackbar}
      />
    </div>
  )
}

// ─── Exported Component ────────────────────────────────────────────
export default function UIHubManager() {
  return (
    <USXThemeProvider>
      <UIHubInner />
    </USXThemeProvider>
  )
}
