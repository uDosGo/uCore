/* ═══════════════════════════════════════════════════════════════════
   WorkflowSurface — USX Schema v3.1 Workflow Surface
   ═══════════════════════════════════════════════════════════════════
   User-facing daily/workflow/mission/ucode surface.
   ISOLATED from dev tasks — uses .tasker/workflow/ directory.
   Tabs: Dashboard (with activity widget), Missions, Tasks (user-only)
   Project Type: Operational (OP) | Autonomy Level: L3 (Collaborator)
   Binder: ⚡️ Operations/Workflow | Tags: #workflow #missions #daily
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar, { type SidebarNavItem } from '../../components/VaultSidebar'
import KanbanBoard, { type KanbanItem, type KanbanColumn } from '../../components/KanbanBoard'
import { renderMarkdown } from '../../utils/renderMarkdown'
import '../../styles/surfaces/workflow.css'

// ─── Types ──────────────────────────────────────────────────────
type WorkflowTab = 'dashboard' | 'missions' | 'tasks'

interface WorkflowTask {
  id: string
  title: string
  status: string
  priority: string
  board: string
  tags: string[]
  description: string
  file: string
  metadata?: Record<string, any>
}

interface ActivityEntry {
  date: string
  title: string
  icon?: string
}

const SNACKBAR_API = 'http://localhost:8484'

export { type WorkflowTask }

// ─── Detail Panel (right-split editor) ──────────────────────────
function WorkflowDetailPanel({ task, onClose }: { task: WorkflowTask | null; onClose: () => void }) {
  if (!task) return null
  return (
    <div className="kanban-detail-panel" style={{ minWidth: 280, borderLeft: '1px solid var(--pico-border-color, #30363d)', overflow: 'auto' }}>
      <div className="kanban-detail-header">
        <div className="kanban-detail-header-tabs">
          <span className="kanban-detail-tab active"><Icon name="info" size={14} /> Detail</span>
        </div>
        <button className="kanban-detail-close" onClick={onClose} title="Close panel">
          <Icon name="close" size={16} />
        </button>
      </div>
      <div className="kanban-detail-body" style={{ padding: 16 }}>
        <h3 className="kanban-detail-title" style={{ margin: '0 0 8px', fontWeight: 600, fontSize: 15 }}>{task.title}</h3>
        <div className="kanban-detail-meta" style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <span className="kanban-detail-badge" style={{ border: '1px solid #58a6ff', color: '#58a6ff', padding: '2px 8px', borderRadius: 10, fontSize: 11 }}>{task.status}</span>
          <span className="kanban-detail-badge" style={{ border: '1px solid #d29922', color: '#d29922', padding: '2px 8px', borderRadius: 10, fontSize: 11 }}>{task.priority}</span>
          <span style={{ fontSize: 11, color: 'var(--pico-muted-color)' }}>{task.board}</span>
        </div>
        {task.tags && task.tags.length > 0 && (
          <div className="kanban-detail-tags" style={{ display: 'flex', gap: 4, marginBottom: 12, flexWrap: 'wrap' }}>
            {task.tags.map(tag => (
              <span key={tag} style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: 'var(--pico-card-sectioning-background-color, #1c2128)', color: 'var(--pico-primary)' }}>{tag}</span>
            ))}
          </div>
        )}
        {task.description && (
          <div className="prose" style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--pico-color)' }}>
            <p>{task.description}</p>
          </div>
        )}
        <div style={{ marginTop: 16, fontSize: 11, color: 'var(--pico-muted-color)' }}>
          <Icon name="description" size={14} /> {task.file || 'No file'}
        </div>
      </div>
    </div>
  )
}

const WORKFLOW_COLUMN_COLORS: Record<string, string> = {
  todo: '#8b949e',
  'in-progress': '#58a6ff',
  review: '#d29922',
  blocked: '#f85149',
  completed: '#3fb950',
}

const WORKFLOW_COLUMN_ORDER = ['todo', 'in-progress', 'review', 'blocked', 'completed']

// ─── User task filter — shows everything except dev/system tasks ─
function isUserTask(task: WorkflowTask): boolean {
  const board = (task.board || '').toLowerCase()
  const tags = (task.tags || []).map(t => t.toLowerCase())
  // Only exclude explicit dev/system boards and tags
  const devPatterns = ['developer', 'dev-task', 'dev/', 'gridsmith']
  const isDevBoard = devPatterns.some(p => board.includes(p))
  const isDevTag = tags.some(t => devPatterns.some(p => t.includes(p)))
  return !isDevBoard && !isDevTag
}

// ─── Dashboard Tab ─────────────────────────────────────────────
function DashboardTab({ tasks, snackbarAvailable }: {
  tasks: WorkflowTask[]
  snackbarAvailable: boolean
}) {
  const [taskItems, setTaskItems] = useState([
    { id: 'w1', title: 'Review daily mission brief', done: false },
    { id: 'w2', title: 'Sync workspace vault', done: false },
    { id: 'w3', title: 'Run uCode pipeline', done: false },
    { id: 'w4', title: 'Process activity feed', done: true },
    { id: 'w5', title: 'Backup AppFlowy workspace', done: false },
  ])

  const toggleTask = (id: string) => {
    setTaskItems(prev => prev.map(t => t.id === id ? { ...t, done: !t.done } : t))
  }

  const runningTasks = tasks.filter(t => t.status === 'in-progress' || t.status === 'review').length
  const totalUserTasks = taskItems.length
  const doneUserTasks = taskItems.filter(t => t.done).length

  const activity: ActivityEntry[] = [
    { date: 'Today', title: 'Mission sync completed', icon: 'sync' },
    { date: 'Today', title: 'Vault indexed 42 documents', icon: 'folder' },
    { date: 'Yesterday', title: 'Workflow pipeline green', icon: 'check_circle' },
    { date: '2d ago', title: 'AppFlowy import completed', icon: 'download' },
  ]

  const prompts = [
    { icon: 'sync', label: 'Sync workspaces', color: '#58a6ff' },
    { icon: 'search', label: 'Search vault', color: '#22c55e' },
    { icon: 'flag', label: 'Start new mission', color: '#f59e0b' },
    { icon: 'history', label: 'View activity log', color: '#a855f7' },
  ]

  return (
    <div className="workflow-dashboard">
      {/* System Overview */}
      <div className="workflow-section">
        <div className="workflow-section-header">
          <Icon name="monitor_heart" size={18} />
          <h3>Workflow Overview</h3>
        </div>
        <div className="workflow-stats-grid">
          <div className="workflow-stat-card">
            <span className="workflow-stat-label">Tasks</span>
            <span className="workflow-stat-value">{doneUserTasks}/{totalUserTasks}</span>
            <div className="workflow-stat-bar">
              <div className="workflow-stat-bar-fill" style={{ width: `${(doneUserTasks / Math.max(totalUserTasks, 1)) * 100}%`, background: '#3fb950' }} />
            </div>
          </div>
          <div className="workflow-stat-card">
            <span className="workflow-stat-label">Active</span>
            <span className="workflow-stat-value">{runningTasks}</span>
            <div className="workflow-stat-bar">
              <div className="workflow-stat-bar-fill" style={{ width: '100%', background: '#58a6ff' }} />
            </div>
          </div>
          <div className="workflow-stat-card">
            <span className="workflow-stat-label">Snackbar</span>
            <span className="workflow-stat-value" style={{ color: snackbarAvailable ? '#3fb950' : '#f85149' }}>
              {snackbarAvailable ? 'Online' : 'Offline'}
            </span>
            <div className="workflow-stat-bar">
              <div className="workflow-stat-bar-fill" style={{ width: '100%', background: snackbarAvailable ? '#3fb950' : '#f85149' }} />
            </div>
          </div>
        </div>
      </div>

      {/* 2-col: Activity + Quick Actions */}
      <div className="workflow-grid-2">
        <div className="workflow-section">
          <div className="workflow-section-header">
            <Icon name="history" size={18} />
            <h3>Activity</h3>
          </div>
          <div className="workflow-activity-list">
            {activity.map(a => (
              <div key={a.title} className="workflow-activity-row">
                {a.icon && <Icon name={a.icon} size={14} style={{ color: 'var(--pico-muted-color)' }} />}
                <span className="workflow-activity-date">{a.date}</span>
                <span className="workflow-activity-title">{a.title}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="workflow-section">
          <div className="workflow-section-header">
            <Icon name="bolt" size={18} />
            <h3>Quick Actions</h3>
          </div>
          <div className="workflow-action-grid">
            {prompts.map(p => (
              <button key={p.label} className="workflow-action-btn" style={{ '--wf-action-color': p.color } as React.CSSProperties}>
                <Icon name={p.icon} size={16} />
                <span>{p.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Daily Tasks */}
      <div className="workflow-section">
        <div className="workflow-section-header">
          <Icon name="checklist" size={18} />
          <h3>Daily Tasks</h3>
          <span className="workflow-section-count">{doneUserTasks}/{totalUserTasks}</span>
        </div>
        <div className="workflow-task-list">
          {taskItems.map(t => (
            <div key={t.id} className="workflow-task-row">
              <label className="workflow-task-label">
                <input type="checkbox" checked={t.done} onChange={() => toggleTask(t.id)} />
                <span className={`workflow-task-text ${t.done ? 'workflow-task-text--done' : ''}`}>{t.title}</span>
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Missions Tab ──────────────────────────────────────────────
function MissionsTab() {
  const [missions, setMissions] = useState([
    { id: 'm1', title: 'Surface Consolidation', status: 'active', priority: 'high', description: 'Consolidate surfaces into canonical lineup.' },
    { id: 'm2', title: 'USX Component Audit', status: 'active', priority: 'medium', description: 'Audit and standardise USX components.' },
    { id: 'm3', title: 'Documentation Refresh', status: 'planned', priority: 'low', description: 'Update documentation after UI/server consolidation.' },
    { id: 'm4', title: 'Vault Indexing Pipeline', status: 'active', priority: 'high', description: 'Run recurring vault sync and indexing.' },
  ])

  const priorityColor: Record<string, string> = {
    high: '#f85149',
    medium: '#d29922',
    low: '#8b949e',
  }

  return (
    <div className="workflow-panel">
      <div className="workflow-panel-header">
        <h3>Missions</h3>
        <span className="workflow-panel-count">{missions.length} active</span>
      </div>
      <div className="workflow-mission-list">
        {missions.map(m => (
          <div key={m.id} className="workflow-card">
            <div className="workflow-card-header">
              <span className="workflow-card-title">{m.title}</span>
              <span className="workflow-card-badge" style={{ borderColor: priorityColor[m.priority] || '#8b949e', color: priorityColor[m.priority] || '#8b949e' }}>
                {m.priority}
              </span>
            </div>
            <p className="workflow-card-desc">{m.description}</p>
            <div className="workflow-card-footer">
              <span className="workflow-card-status">{m.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Tasks Tab (Kanban — user tasks only) ──────────────────────
function TasksTab({ tasks, loading, error }: {
  tasks: WorkflowTask[]
  loading: boolean
  error: string | null
}) {
  const [showCompleted, setShowCompleted] = useState(true)

  // Filter to user tasks only (no dev/system)
  const userTasks = tasks.filter(isUserTask)
  const visibleTasks = showCompleted ? userTasks : userTasks.filter(t => t.status !== 'completed')

  const boardColumns: KanbanColumn[] = WORKFLOW_COLUMN_ORDER
    .filter(status => visibleTasks.some(t => t.status === status))
    .map(status => ({
      id: status,
      title: status.charAt(0).toUpperCase() + status.slice(1),
      color: WORKFLOW_COLUMN_COLORS[status] || '#8b949e',
      items: visibleTasks
        .filter(t => t.status === status)
        .map(t => ({
          id: t.id,
          title: t.title,
          type: t.board || 'task',
          date: t.tags?.join(', ') || '',
        })),
    }))

  const handleItemClick = (item: KanbanItem) => {
    console.log('User task clicked:', item.id)
  }

  return (
    <div className="workflow-panel">
      <div className="workflow-panel-header">
        <h3>User Tasks</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="workflow-panel-count">{userTasks.length} tasks</span>
          <button
            className="workflow-toggle-btn"
            onClick={() => setShowCompleted(v => !v)}
          >
            <Icon name="check_circle" size={14} />
            {showCompleted ? 'Hide completed' : 'Show completed'}
          </button>
        </div>
      </div>

      {error && (
        <div className="workflow-card" style={{ borderLeft: '3px solid #f85149' }}>
          <p style={{ color: '#f85149', margin: 0 }}>{error}</p>
        </div>
      )}

      {loading && userTasks.length === 0 && (
        <div className="workflow-empty">Loading user tasks...</div>
      )}

      {userTasks.length > 0 ? (
        <div className="workflow-kanban-wrap">
          <KanbanBoard
            columns={boardColumns}
            onItemClick={handleItemClick}
            readOnly
          />
        </div>
      ) : !loading ? (
        <div className="workflow-empty">
          No user tasks found. Add tasks tagged with "workflow", "mission", "daily", or "user" in .tasker/.
        </div>
      ) : null}
    </div>
  )
}

// ─── Main Surface ──────────────────────────────────────────────
export default function WorkflowSurface() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sidebarOpen, toggleSidebar } = useSurfaceShell()

  const tabState = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const raw = (params.get('tab') || 'dashboard').toLowerCase()
    const candidate = raw as WorkflowTab
    return {
      selectedTab: ['dashboard', 'missions', 'tasks'].includes(candidate) ? candidate : 'dashboard',
    }
  }, [location.search])

  const [activeTab, setActiveTab] = useState<WorkflowTab>(tabState.selectedTab)
  const [tasks, setTasks] = useState<WorkflowTask[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [snackbarAvailable, setSnackbarAvailable] = useState(false)

  useEffect(() => {
    setActiveTab(tabState.selectedTab)
  }, [tabState.selectedTab])

  const fetchWorkflowTasks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/developer/tasker/tasks`, {
        signal: AbortSignal.timeout(4000),
      })
      if (res.ok) {
        const data = await res.json()
        setTasks(data.tasks || [])
        setSnackbarAvailable(true)
      } else {
        setTasks([])
        setSnackbarAvailable(true)
      }
    } catch {
      setError('Failed to load tasks')
      setSnackbarAvailable(false)
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchWorkflowTasks()
  }, [fetchWorkflowTasks])

  const setTabAndRoute = (nextTab: WorkflowTab) => {
    setActiveTab(nextTab)
    navigate(`/workflow?tab=${nextTab}`)
  }

  const workflowNavItems: SidebarNavItem[] = [
    { id: 'dashboard', icon: 'dashboard', label: 'Dashboard', active: activeTab === 'dashboard', onClick: () => setTabAndRoute('dashboard') },
    { id: 'missions', icon: 'flag', label: 'Missions', active: activeTab === 'missions', onClick: () => setTabAndRoute('missions') },
    { id: 'tasks', icon: 'checklist', label: 'Tasks', active: activeTab === 'tasks', onClick: () => setTabAndRoute('tasks') },
  ]

  const toolbarTabs: ToolbarTab[] = [
    { id: 'dashboard', icon: 'dashboard', label: 'Dashboard', active: activeTab === 'dashboard', onClick: () => setTabAndRoute('dashboard') },
    { id: 'missions', icon: 'flag', label: 'Missions', active: activeTab === 'missions', onClick: () => setTabAndRoute('missions') },
    { id: 'tasks', icon: 'checklist', label: 'Tasks', active: activeTab === 'tasks', onClick: () => setTabAndRoute('tasks') },
  ]

  return (
    <div className="workflow-surface">
      <GlobalToolbar
        tabs={toolbarTabs}
        onToggleSidebar={toggleSidebar}
        sidebarOpen={sidebarOpen}
        sidebarToggleLabel="Workflow sidebar"
        rightExtra={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span className="hub-status-badge">
              Tasks: {tasks.length}
            </span>
          </div>
        }
      />

      <div className="usx-surface-body" style={{ position: 'relative' }}>
        <VaultSidebar
          open={sidebarOpen}
          showModeTabs
          sidebarMode="server"
          serverNavItems={workflowNavItems}
        />

        <main className="usx-surface-main workflow-surface-main">
          {activeTab === 'dashboard' && (
            <DashboardTab tasks={tasks} snackbarAvailable={snackbarAvailable} />
          )}
          {activeTab === 'missions' && <MissionsTab />}
          {activeTab === 'tasks' && (
            <TasksTab tasks={tasks} loading={loading} error={error} />
          )}
        </main>
      </div>
    </div>
  )
}