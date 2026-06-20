/* ═══════════════════════════════════════════════════════════════════
   MissionControlSurface — Unified Surface Hub
   ═══════════════════════════════════════════════════════════════════
   Consolidates:
   - Dashboard (surface cards, starred surfaces)
   - Missions (missions, goals, tasks)
   - Kanban (document workflow board)
   - List (document table view)
   - Prose (read-only document renderer)
   - Editor (Markdown editor with preview)
   - GitHub (file tree browser)
   - Story (story builder)
   - Roadmap (project phases)
   - Schedule (calendar events)
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { Icon } from '../../components/Icon'
import { GlobalToolbar, ToolbarTab } from '../../components/GlobalToolbar'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar from '../../components/VaultSidebar'
import AssistUISurface from '../assistui/AssistUISurface'
import KanbanBoard from '../../components/KanbanBoard'
import DataTable from '../../components/DataTable'
import ProseView from '../../components/ProseView'
import EditorView from '../../components/EditorView'
import StoryView from '../../components/StoryView'
import type { KanbanItem, KanbanColumn } from '../../components/KanbanBoard'
import type { TableColumn, TableRow } from '../../components/DataTable'
import { statusColor } from '../../utils/statusColor'
import '../../styles/hub/index.css'

// ─── Types ──────────────────────────────────────────────────────────
type MissionTab = 'dashboard' | 'missions' | 'kanban' | 'list' | 'prose' | 'editor' | 'schedule'

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

interface Mission {
  id: number
  title: string
  description: string
  status: string
  priority: string
  progress?: { tasks_total: number; tasks_completed: number }
  goals?: Goal[]
}

interface Goal {
  id: number
  title: string
  status: string
  tasks?: Task[]
}

interface Task {
  id: number
  title: string
  status: string
}

// ─── Constants ──────────────────────────────────────────────────────
const SNACKBAR_API = 'http://localhost:8484'

const HIDDEN_FROM_SURFACES_TAB = ['ui-hub', 'mission-control', 'assistui']
const DEV_SURFACE_IDS: string[] = []

// Map API surface IDs to display IDs (e.g. userver → server, gridui → terminal)
// NOTE: devstudio is NOT remapped here — it's a separate repo served at /devstudio/*
// and its route must stay intact. The card name override is handled via DISPLAY_NAME_MAP.
const API_ID_MAP: Record<string, string> = {
  userver: 'server',
  gridui: 'terminal',
  gridcore: 'gridcore-operations',
}

// Display name overrides — renames the card title without changing the surface ID/route.
const DISPLAY_NAME_MAP: Record<string, string> = {
  devstudio: 'Developer',
  assistui: 'Assistant',
  proseui: 'Mission Control',
}

// FALLBACK_REGISTRY: only Server, System, Documents, and Groovebox are hardcoded here.
// All other surface cards (Terminal, Teletext, GridCore, BrowserUI, DevStudio, etc.)
// are placed dynamically by the snackbar/ui-server. This keeps the fallback minimal
// for maintenance-only scenarios when the snackbar is offline.
const FALLBACK_REGISTRY: SurfaceDef[] = [
  { id: 'system', name: 'System', subtitle: 'System Tools Hub', description: 'Install tools, manage modules, browse system pages, and build stories', port: 0, color: '#58a6ff', icon: 'settings_suggest', status: 'running', embedded: true, route: '/system' },
  { id: 'server', name: 'Server', subtitle: 'Server Management', description: 'Server management, services, logs, workflows, agents', port: 0, color: '#f59e0b', icon: 'dns', status: 'running', embedded: true, route: '/userver' },
  { id: 'proseui', name: 'Mission Control', subtitle: 'Markdown Suite', description: 'Universal Document Oriented User Interface — document viewer, schema browser, and workspace manager', port: 5184, color: '#22c55e', icon: 'article', status: 'running', embedded: true, route: '/' },
  { id: 'groovebox', name: 'Groovebox', subtitle: 'Music Production', description: 'Music production environment with MIDI sequencing, synthesis, and audio processing', port: 8888, color: '#da3633', icon: 'play_arrow', status: 'stopped' },


]

const MISSION_TABS: { id: MissionTab; icon: string; label: string }[] = [
  { id: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
  { id: 'missions', icon: 'star', label: 'Missions' },
  { id: 'kanban', icon: 'view_column', label: 'Kanban' },
  { id: 'list', icon: 'format_list_bulleted', label: 'List' },
  { id: 'prose', icon: 'article', label: 'Prose' },
  { id: 'editor', icon: 'edit_note', label: 'Editor' },
  { id: 'schedule', icon: 'calendar_month', label: 'Schedule' },
]

// ─── Mock Data ──────────────────────────────────────────────────────
const INITIAL_KANBAN: KanbanColumn[] = [
  { id: 'draft', title: 'Draft', color: '#94a3b8', items: [
    { id: 'd1', title: 'Getting Started Guide', type: 'doc', date: '2d ago' },
    { id: 'd2', title: 'API Reference v2', type: 'doc', date: '3d ago' },
    { id: 'd3', title: 'Tutorial: Kanban Setup', type: 'tutorial', date: '5d ago' },
  ]},
  { id: 'review', title: 'Review', color: '#f59e0b', items: [
    { id: 'r1', title: 'Architecture Overview', type: 'doc', date: '1d ago' },
    { id: 'r2', title: 'Workflow Automation', type: 'guide', date: '2d ago' },
  ]},
  { id: 'published', title: 'Published', color: '#22c55e', items: [
    { id: 'p1', title: 'Quickstart Guide', type: 'doc', date: '1w ago' },
    { id: 'p2', title: 'USXD Format Spec', type: 'spec', date: '2w ago' },
    { id: 'p3', title: 'uCode1 User Manual', type: 'manual', date: '3w ago' },
    { id: 'p4', title: 'Vault Integration', type: 'guide', date: '1m ago' },
  ]},
]

const INITIAL_TABLE: TableRow[] = [
  { id: '1', title: 'Getting Started Guide', status: 'draft', type: 'doc', date: '2026-05-14' },
  { id: '2', title: 'API Reference v2', status: 'draft', type: 'doc', date: '2026-05-13' },
  { id: '3', title: 'Architecture Overview', status: 'review', type: 'doc', date: '2026-05-15' },
  { id: '4', title: 'Workflow Automation', status: 'review', type: 'guide', date: '2026-05-14' },
  { id: '5', title: 'Quickstart Guide', status: 'published', type: 'doc', date: '2026-05-09' },
  { id: '6', title: 'USXD Format Spec', status: 'published', type: 'spec', date: '2026-05-02' },
  { id: '7', title: 'uCode1 User Manual', status: 'published', type: 'manual', date: '2026-04-25' },
  { id: '8', title: 'Vault Integration', status: 'published', type: 'guide', date: '2026-04-16' },
]

const TABLE_COLUMNS: TableColumn[] = [
  { key: 'title', label: 'Title' },
  { key: 'status', label: 'Status', render: (val: string) => (
    <span className={`status-badge ${val}`} style={{ background: `${statusColor(val)}20`, color: statusColor(val) }}>{val}</span>
  )},
  { key: 'type', label: 'Type' },
  { key: 'date', label: 'Date' },
]

const MOCK_MISSIONS: Mission[] = [
  { id: 1, title: 'Surface Consolidation', description: 'Consolidate surfaces into canonical lineup', status: 'active', priority: 'high', progress: { tasks_total: 16, tasks_completed: 8 } },
  { id: 2, title: 'USX Component Audit', description: 'Audit and standardise USX components', status: 'active', priority: 'medium', progress: { tasks_total: 12, tasks_completed: 4 } },
  { id: 3, title: 'Documentation Refresh', description: 'Update all documentation for v3.1', status: 'planned', priority: 'low' },
]

// ─── Helpers ────────────────────────────────────────────────────────
const sortSurfaces = (list: SurfaceDef[]): SurfaceDef[] => {
  const order = ['assistui', 'terminal', 'teletext', 'gridcore-operations', 'browserui', 'server', 'developer', 'system', 'proseui', 'groovebox']
  return [...list].sort((a, b) => {
    const ai = order.indexOf(a.id)
    const bi = order.indexOf(b.id)
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi)
  })
}

const withoutUiHub = (list: SurfaceDef[]): SurfaceDef[] =>
  list.filter(s => s.id !== 'ui-hub' && s.id !== 'mission-control' && !DEV_SURFACE_IDS.includes(s.id))

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
    { id: 't4', title: 'Test GridCore surface', done: true, priority: 'high' },
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
    { date: 'Yesterday', title: 'GridCore surface created' },
    { date: '2d ago', title: 'USystemSurface tabs updated' },
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
    { icon: 'settings', label: 'System Settings', color: '#f59e0b', route: '/system' },
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
                      card.id === 'proseui' && onNavigate ? (
                        <button onClick={() => onNavigate('missions')} className="hub-btn hub-btn--primary">
                          <Icon name="open_in_new" size={14} /> Open
                        </button>
                      ) : (
                        <a href={card.route || `/${card.id}`} className="hub-btn hub-btn--primary">
                          <Icon name="open_in_new" size={14} /> Open
                        </a>
                      )
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

// ─── Missions Panel ─────────────────────────────────────────────────
function MissionsPanel() {
  const [missions] = useState<Mission[]>(MOCK_MISSIONS)
  const [selectedMission, setSelectedMission] = useState<Mission | null>(null)

  const statusColor = (s: string) => {
    switch (s) {
      case 'active': case 'high': return '#22c55e'
      case 'planned': case 'medium': return '#f59e0b'
      case 'paused': return '#d29922'
      case 'cancelled': case 'low': return '#8b949e'
      default: return '#8b949e'
    }
  }

  if (selectedMission) {
    return (
      <div className="mc-mission-detail">
        <button className="hub-btn hub-btn--info" onClick={() => setSelectedMission(null)}>
          <Icon name="arrow_back" size={14} /> Back
        </button>
        <h2>{selectedMission.title}</h2>
        <p>{selectedMission.description}</p>
        <div className="mc-mission-meta">
          <span className="mc-mission-badge" style={{ background: `${statusColor(selectedMission.status)}20`, color: statusColor(selectedMission.status) }}>
            {selectedMission.status}
          </span>
          <span className="mc-mission-badge" style={{ background: `${statusColor(selectedMission.priority)}20`, color: statusColor(selectedMission.priority) }}>
            {selectedMission.priority}
          </span>
        </div>
        {selectedMission.progress && (
          <div className="mc-progress-bar">
            <div className="mc-progress-bar-fill" style={{ width: `${(selectedMission.progress.tasks_completed / selectedMission.progress.tasks_total) * 100}%` }} />
            <span>{selectedMission.progress.tasks_completed}/{selectedMission.progress.tasks_total} tasks</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="mc-missions">
      <div className="mc-missions-header">
        <h2>Missions</h2>
        <span className="mc-missions-count">{missions.length} total</span>
      </div>
      <div className="mc-missions-grid">
        {missions.map(m => (
          <div key={m.id} className="mc-mission-card" onClick={() => setSelectedMission(m)}>
            <div className="mc-mission-card-header">
              <h3>{m.title}</h3>
              <div className="mc-mission-meta">
                <span className="mc-mission-badge" style={{ background: `${statusColor(m.status)}20`, color: statusColor(m.status) }}>
                  {m.status}
                </span>
                <span className="mc-mission-badge" style={{ background: `${statusColor(m.priority)}20`, color: statusColor(m.priority) }}>
                  {m.priority}
                </span>
              </div>
            </div>
            <p>{m.description}</p>
            {m.progress && (
              <div className="mc-progress-bar">
                <div className="mc-progress-bar-fill" style={{ width: `${(m.progress.tasks_completed / m.progress.tasks_total) * 100}%` }} />
                <span>{m.progress.tasks_completed}/{m.progress.tasks_total}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Schedule Panel ────────────────────────────────────────────────
function SchedulePanel() {
  const events = [
    { date: '2026-06-20', title: 'Surface Consolidation Review', type: 'milestone' },
    { date: '2026-06-25', title: 'USX Component Audit Due', type: 'deadline' },
    { date: '2026-07-01', title: 'v3.1 Release Candidate', type: 'release' },
  ]

  return (
    <div className="mc-schedule">
      <div className="mc-schedule-header">
        <h2>Schedule</h2>
      </div>
      <div className="mc-schedule-events">
        {events.map(evt => (
          <div key={evt.title} className={`mc-schedule-event mc-schedule-event--${evt.type}`}>
            <div className="mc-schedule-event-date">{evt.date}</div>
            <div className="mc-schedule-event-info">
              <span className="mc-schedule-event-title">{evt.title}</span>
              <span className="mc-schedule-event-type">{evt.type}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main Component ────────────────────────────────────────────────
export default function MissionControlSurface() {
  const shell = useSurfaceShell()
  const [activeTab, setActiveTab] = useState<MissionTab>('dashboard')
  const [surfaces, setSurfaces] = useState<SurfaceDef[]>([])
  const [loading, setLoading] = useState(true)
  const [snackbarAvailable, setSnackbarAvailable] = useState(false)
  const [pendingActions, setPendingActions] = useState<Record<string, { action: SurfaceAction; progress: ActionProgress }>>({})
  const progressIntervals = useRef<Record<string, ReturnType<typeof setInterval>>>({})
  const [chatMode, setChatMode] = useState<'closed' | 'panel'>('closed')

  // Kanban state
  const [kanbanColumns, setKanbanColumns] = useState<KanbanColumn[]>(INITIAL_KANBAN)

  // Editor state
  const [editorContent, setEditorContent] = useState(() => {
    try { return localStorage.getItem('mc-editor') || '# New Document\n\nStart writing your content here...\n\n## Section 1\n\nLorem ipsum dolor sit amet.\n\n## Section 2\n\n- Item one\n- Item two\n- Item three\n' }
    catch { return '# New Document\n\nStart writing your content here...\n\n## Section 1\n\nLorem ipsum dolor sit amet.\n\n## Section 2\n\n- Item one\n- Item two\n- Item three\n' }
  })
  const [publishStatus, setPublishStatus] = useState<string | null>(null)

  // Save editor to localStorage
  useEffect(() => {
    try { localStorage.setItem('mc-editor', editorContent) } catch {}
  }, [editorContent])

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
      // Expand the terminal surface into 3 derived cards (Terminal, Teletext, GridCore Operations)
      // These all point to the same underlying uCode1/GridUI surface but with different routes.
      const expanded = merged.flatMap(s => {
        if (s.id === 'terminal') {
          return [
            { ...s, id: 'terminal', name: 'Terminal', subtitle: 'Grid Terminal', description: 'Interactive terminal with grid-based display, viewport controls, and character maps', color: '#22c55e', icon: 'terminal', route: '/gridui?panel=terminal' },
            { ...s, id: 'teletext', name: 'Teletext', subtitle: 'Teletext Viewer', description: 'Teletext-style information pages with grid rendering and navigation', color: '#a855f7', icon: 'live_tv', route: '/gridui?panel=teletext' },
            { ...s, id: 'gridcore-operations', name: 'Grid Operations', subtitle: 'Grid Tools Hub', description: 'Map navigation, grid editor, asset library, and system settings', color: '#f97316', icon: 'grid_view', route: '/gridcore' },
          ]
        }
        return [s]
      })
      // Apply display name overrides (e.g. devstudio → Developer) without changing the ID/route.
      const renamed = expanded.map(s => ({
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

  // ─── Kanban callbacks ───────────────────────────────────────────
  const handleKanbanItemClick = useCallback((item: KanbanItem, column: KanbanColumn) => {
    // Navigate to editor with the selected item
    setActiveTab('editor')
  }, [])

  const handleKanbanItemDelete = useCallback((itemId: string) => {
    setKanbanColumns(prev => prev.map(col => ({
      ...col,
      items: col.items.filter(i => i.id !== itemId),
    })))
  }, [])

  const handleKanbanItemMove = useCallback((item: KanbanItem, fromColId: string, toColId: string) => {
    setKanbanColumns(prev => {
      const next = prev.map(col => ({ ...col, items: [...col.items] }))
      const srcCol = next.find(c => c.id === fromColId)
      const tgtCol = next.find(c => c.id === toColId)
      if (!srcCol || !tgtCol) return prev
      const idx = srcCol.items.findIndex(i => i.id === item.id)
      if (idx === -1) return prev
      const [moved] = srcCol.items.splice(idx, 1)
      tgtCol.items.push(moved)
      return next
    })
  }, [])

  const handleKanbanAddCard = useCallback((colId: string, title: string) => {
    const newItem: KanbanItem = {
      id: `card-${Date.now()}`,
      title,
      type: 'doc',
      date: 'just now',
    }
    setKanbanColumns(prev => prev.map(col =>
      col.id === colId ? { ...col, items: [...col.items, newItem] } : col
    ))
  }, [])

  // ─── Publish callback ───────────────────────────────────────────
  const handlePublish = useCallback((content: string) => {
    setPublishStatus('Document published successfully!')
    setTimeout(() => setPublishStatus(null), 3000)
  }, [])

  // ─── Render ─────────────────────────────────────────────────────
  const tabs: ToolbarTab[] = MISSION_TABS.map(t => ({
    id: t.id,
    icon: t.icon,
    label: t.label,
    active: activeTab === t.id,
    onClick: () => setActiveTab(t.id),
  }))

  return (
    <div className="hub-surface">
      <GlobalToolbar
        tabs={tabs}
        chatMode={chatMode}
        onToggleChat={toggleChat}
        onToggleSidebar={shell.toggleSidebar}
        sidebarOpen={shell.sidebarOpen}
        rightExtra={
          <span className="hub-status-badge">
            <span className={`hub-status-dot ${runningCount > 0 ? 'hub-status-dot--online' : ''}`} />
            {runningCount}/{surfaces.length} online
          </span>
        }
      />

      <div className="usx-surface-body" style={{ display: 'flex', overflow: 'hidden', position: 'relative' }}>
        <VaultSidebar
          open={shell.sidebarOpen}
          onToggle={shell.toggleSidebar}
          onNewFile={(binderId) => console.log('New file in', binderId)}
          onFileSelect={(file) => console.log('Selected:', file.name)}
        />

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

          ) : activeTab === 'missions' ? (
            <MissionsPanel />
          ) : activeTab === 'kanban' ? (
            <KanbanBoard
              columns={kanbanColumns}
              onItemClick={handleKanbanItemClick}
              onItemDelete={handleKanbanItemDelete}
              onItemMove={handleKanbanItemMove}
              onAddCard={handleKanbanAddCard}
            />
          ) : activeTab === 'list' ? (
            <DataTable
              columns={TABLE_COLUMNS}
              rows={INITIAL_TABLE}
              defaultSortField="date"
              defaultSortDir="desc"
            />
          ) : activeTab === 'prose' ? (
            <ProseView />
          ) : activeTab === 'editor' ? (
            <EditorView
              content={editorContent}
              onChange={setEditorContent}
              onPublish={handlePublish}
              publishStatus={publishStatus}
            />
          ) : activeTab === 'schedule' ? (
            <SchedulePanel />
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
