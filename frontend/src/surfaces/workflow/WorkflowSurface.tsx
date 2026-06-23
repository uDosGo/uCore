/* ═══════════════════════════════════════════════════════════════════
   WorkflowSurface — USX Schema v3.1 Workflow Surface
   ═══════════════════════════════════════════════════════════════════
   User-facing daily/workflow/mission/ucode surface.
   Tabs: Dashboard (with activity widget), Missions (linked to tasks),
         Tasks (kanban + list view, right-split detail editor)
   Project Type: Operational (OP) | Autonomy Level: L3 (Collaborator)
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
type ViewMode = 'kanban' | 'list'

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

interface Mission {
  id: string
  title: string
  status: string
  priority: string
  description: string
  taskIds: string[] // linked task IDs
}

interface ActivityEntry {
  date: string
  title: string
  icon?: string
}

const SNACKBAR_API = 'http://localhost:8484'

const COLUMN_COLORS: Record<string, string> = {
  todo: '#8b949e',
  'in-progress': '#58a6ff',
  review: '#d29922',
  blocked: '#f85149',
  completed: '#3fb950',
}

const COLUMN_ORDER = ['todo', 'in-progress', 'review', 'blocked', 'completed']

// ─── User task filter — exclude explicit dev/system ────────────
function isUserTask(task: WorkflowTask): boolean {
  const board = (task.board || '').toLowerCase()
  const tags = (task.tags || []).map(t => t.toLowerCase())
  const devPatterns = ['developer', 'dev-task', 'dev/', 'gridsmith']
  return !devPatterns.some(p => board.includes(p)) &&
         !tags.some(t => devPatterns.some(p => t.includes(p)))
}

// ─── Detail Panel (right-split editor) ─────────────────────────
function WorkflowDetailPanel({ task, onClose, onUpdate }: {
  task: WorkflowTask | null
  onClose: () => void
  onUpdate?: (task: WorkflowTask) => Promise<void>
}) {
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [saving, setSaving] = useState(false)
  const [panelMode, setPanelMode] = useState<'detail' | 'prose' | 'editor'>('detail')

  useEffect(() => {
    if (task) {
      setEditTitle(task.title)
      setEditDesc(task.description || '')
      setEditing(false)
    }
  }, [task])

  const handleSave = useCallback(async () => {
    if (!task) return
    setSaving(true)
    try {
      const updated = { ...task, title: editTitle, description: editDesc }
      if (onUpdate) {
        await onUpdate(updated)
      } else {
        await fetch(`${SNACKBAR_API}/api/developer/tasker/tasks/${task.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updated),
          signal: AbortSignal.timeout(5000),
        })
      }
      setEditing(false)
    } catch (err) {
      console.error('Save error:', err)
    } finally {
      setSaving(false)
    }
  }, [task, editTitle, editDesc, onUpdate])

  if (!task) return null

  return (
    <div className="kanban-detail-panel">
      <div className="kanban-detail-header">
        <div className="kanban-detail-header-tabs">
          <button className={`kanban-detail-tab ${panelMode === 'detail' ? 'active' : ''}`} onClick={() => setPanelMode('detail')}>
            <Icon name="info" size={14} /> Detail
          </button>
          <button className={`kanban-detail-tab ${panelMode === 'prose' ? 'active' : ''}`} onClick={() => setPanelMode('prose')}>
            <Icon name="description" size={14} /> Prose
          </button>
          <button className={`kanban-detail-tab ${panelMode === 'editor' ? 'active' : ''}`} onClick={() => setPanelMode('editor')}>
            <Icon name="edit" size={14} /> Editor
          </button>
        </div>
        <button className="kanban-detail-close" onClick={onClose} title="Close panel">
          <Icon name="close" size={16} />
        </button>
      </div>

      <div className="kanban-detail-body">
        {panelMode === 'detail' && (
          <>
            <div className="kanban-detail-section">
              {editing ? (
                <input className="kanban-detail-input" type="text" value={editTitle}
                  onChange={e => setEditTitle(e.target.value)} placeholder="Task title" autoFocus />
              ) : (
                <h3 className="kanban-detail-title">{task.title}</h3>
              )}
              <div className="kanban-detail-meta">
                <span className="kanban-detail-badge" style={{ borderColor: COLUMN_COLORS[task.status] || '#8b949e', color: COLUMN_COLORS[task.status] || '#8b949e' }}>
                  {task.status}
                </span>
                <span className="kanban-detail-badge" style={{ borderColor: task.priority === 'high' ? '#f85149' : '#8b949e', color: task.priority === 'high' ? '#f85149' : '#8b949e' }}>
                  {task.priority}
                </span>
                {task.board && <span className="kanban-detail-meta-text">{task.board}</span>}
              </div>
            </div>
            {task.tags && task.tags.length > 0 && (
              <div className="kanban-detail-section">
                <div className="kanban-detail-tags">
                  {task.tags.map(tag => <span key={tag} className="kanban-detail-tag">{tag}</span>)}
                </div>
              </div>
            )}
            {task.description && (
              <div className="kanban-detail-section kanban-detail-section--prose">
                <div className="prose" dangerouslySetInnerHTML={{ __html: renderMarkdown(task.description) }} />
              </div>
            )}
            <div className="kanban-detail-section">
              <div className="kanban-detail-file">
                <Icon name="description" size={14} /> {task.file}
              </div>
            </div>
            <div className="kanban-detail-actions">
              {editing ? (
                <>
                  <button className="kanban-detail-btn primary" onClick={handleSave} disabled={saving}>
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                  <button className="kanban-detail-btn" onClick={() => { setEditing(false); setEditTitle(task.title); setEditDesc(task.description || '') }}>
                    Cancel
                  </button>
                </>
              ) : (
                <button className="kanban-detail-btn primary" onClick={() => setEditing(true)}>
                  <Icon name="edit" size={14} /> Edit
                </button>
              )}
            </div>
          </>
        )}

        {panelMode === 'prose' && (
          <div className="kanban-detail-section kanban-detail-section--prose">
            <div className="prose" dangerouslySetInnerHTML={{ __html: renderMarkdown(task.description || task.title) }} />
          </div>
        )}

        {panelMode === 'editor' && (
          <div className="kanban-detail-editor-wrap">
            {editing ? (
              <>
                <input className="kanban-detail-input" type="text" value={editTitle}
                  onChange={e => setEditTitle(e.target.value)} placeholder="Task title" />
                <textarea className="kanban-detail-editor" value={editDesc}
                  onChange={e => setEditDesc(e.target.value)} placeholder="Markdown description..." spellCheck={false} />
                <div className="kanban-detail-actions">
                  <button className="kanban-detail-btn primary" onClick={handleSave} disabled={saving}>
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                  <button className="kanban-detail-btn" onClick={() => { setEditing(false); setEditTitle(task.title); setEditDesc(task.description || '') }}>
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="kanban-detail-editor-preview">
                  <div className="prose" dangerouslySetInnerHTML={{ __html: renderMarkdown(task.description || task.title) }} />
                </div>
                <button className="kanban-detail-btn primary" onClick={() => setEditing(true)}>
                  <Icon name="edit" size={14} /> Edit
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
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
            <span className={`workflow-stat-value ${snackbarAvailable ? 'workflow-stat-value--online' : 'workflow-stat-value--offline'}`}>
              {snackbarAvailable ? 'Online' : 'Offline'}
            </span>
            <div className="workflow-stat-bar">
              <div className="workflow-stat-bar-fill" style={{ width: '100%', background: snackbarAvailable ? '#3fb950' : '#f85149' }} />
            </div>
          </div>
        </div>
      </div>

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

// ─── Missions Tab (grouping for tasks) ─────────────────────────
function MissionsTab({ allTasks, onSelectMission }: {
  allTasks: WorkflowTask[]
  onSelectMission: (missionTitle: string) => void
}) {
  const [missions, setMissions] = useState<Mission[]>([
    { id: 'm1', title: 'Surface Consolidation', status: 'active', priority: 'high', description: 'Consolidate surfaces into canonical lineup.', taskIds: [] },
    { id: 'm2', title: 'USX Component Audit', status: 'active', priority: 'medium', description: 'Audit and standardise USX components.', taskIds: [] },
    { id: 'm3', title: 'Documentation Refresh', status: 'planned', priority: 'low', description: 'Update documentation after UI/server consolidation.', taskIds: [] },
    { id: 'm4', title: 'Vault Indexing Pipeline', status: 'active', priority: 'high', description: 'Run recurring vault sync and indexing.', taskIds: [] },
  ])

  // Link missions to tasks by matching tags/board
  const linkedMissions = useMemo(() => {
    return missions.map(m => {
      const missionSlug = m.title.toLowerCase().replace(/\s+/g, '-')
      const linkedTasks = allTasks.filter(t => {
        const board = (t.board || '').toLowerCase()
        const tags = (t.tags || []).map(x => x.toLowerCase())
        return board.includes(missionSlug) || tags.includes(missionSlug) || tags.includes(m.title.toLowerCase())
      })
      return { ...m, linkedTasks }
    })
  }, [missions, allTasks])

  const priorityColor: Record<string, string> = {
    high: '#f85149',
    medium: '#d29922',
    low: '#8b949e',
  }

  return (
    <div className="workflow-panel">
      <div className="workflow-panel-header">
        <h3>Missions</h3>
        <span className="workflow-panel-count">{missions.length}</span>
      </div>
      <div className="workflow-mission-list">
        {linkedMissions.map(m => (
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
              {m.linkedTasks.length > 0 && (
                <span className="workflow-panel-count">{m.linkedTasks.length} linked tasks</span>
              )}
            </div>
    {/* Click card to view its tasks */}
    <div style={{ marginTop: 8 }}>
      <button className="workflow-toggle-btn" onClick={() => onSelectMission(m.title)}
        style={{ width: '100%', justifyContent: 'center', padding: '6px 0' }}>
        <Icon name="list" size={14} /> View {m.linkedTasks.length} tasks
      </button>
    </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Tasks Tab (Kanban + List, right-split detail) ─────────────
function TasksTab({ tasks, loading, error }: {
  tasks: WorkflowTask[]
  loading: boolean
  error: string | null
}) {
  const [viewMode, setViewMode] = useState<ViewMode>('kanban')
  const [showCompleted, setShowCompleted] = useState(true)
  const [selectedTask, setSelectedTask] = useState<WorkflowTask | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  const userTasks = tasks.filter(isUserTask)
  const visibleTasks = showCompleted ? userTasks : userTasks.filter(t => t.status !== 'completed')

  const boardColumns: KanbanColumn[] = COLUMN_ORDER
    .filter(status => visibleTasks.some(t => t.status === status))
    .map(status => ({
      id: status,
      title: status.charAt(0).toUpperCase() + status.slice(1),
      color: COLUMN_COLORS[status] || '#8b949e',
      items: visibleTasks.filter(t => t.status === status).map(t => ({
        id: t.id,
        title: t.title,
        type: t.board || 'task',
        date: t.tags?.join(', ') || '',
      })),
    }))

  const handleItemClick = (item: KanbanItem) => {
    const task = userTasks.find(t => t.id === item.id)
    if (task) { setSelectedTask(task); setDetailOpen(true) }
  }

  const handleCloseDetail = () => { setDetailOpen(false); setSelectedTask(null) }

  return (
    <div className="workflow-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="workflow-panel-header">
        <h3>User Tasks</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="workflow-panel-count">{userTasks.length} tasks</span>
          <div className="workflow-view-toggle" style={{ display: 'flex', border: '1px solid var(--pico-border-color)', borderRadius: 6, overflow: 'hidden' }}>
            <button className={`workflow-view-btn ${viewMode === 'kanban' ? 'active' : ''}`} onClick={() => setViewMode('kanban')}
              style={{ padding: '4px 10px', border: 'none', background: viewMode === 'kanban' ? 'var(--pico-card-sectioning-background-color)' : 'transparent', color: 'var(--pico-color)', cursor: 'pointer', fontFamily: 'inherit' }}>
              <Icon name="grid_view" size={14} />
            </button>
            <button className={`workflow-view-btn ${viewMode === 'list' ? 'active' : ''}`} onClick={() => setViewMode('list')}
              style={{ padding: '4px 10px', border: 'none', background: viewMode === 'list' ? 'var(--pico-card-sectioning-background-color)' : 'transparent', color: 'var(--pico-color)', cursor: 'pointer', fontFamily: 'inherit' }}>
              <Icon name="list" size={14} />
            </button>
          </div>
          <button className="workflow-toggle-btn" onClick={() => setShowCompleted(v => !v)}>
            <Icon name="check_circle" size={14} />
            {showCompleted ? 'Hide' : 'Show'}
          </button>
        </div>
      </div>

      {error && <div className="workflow-card" style={{ borderLeft: '3px solid #f85149' }}><p style={{ color: '#f85149', margin: 0 }}>{error}</p></div>}
      {loading && userTasks.length === 0 && <div className="workflow-empty">Loading user tasks...</div>}

      <div className="workflow-tasks-body" style={{ display: 'flex', flex: 1, minHeight: 0, gap: 12, overflow: 'hidden' }}>
        {/* Main content */}
        <div className="workflow-tasks-main" style={{ flex: detailOpen ? '0 0 55%' : '1', minWidth: detailOpen ? 300 : 0, overflow: 'auto', transition: 'flex 0.3s ease' }}>
          {userTasks.length > 0 ? (
            viewMode === 'kanban' ? (
              <KanbanBoard columns={boardColumns} onItemClick={handleItemClick} readOnly />
            ) : (
              <div className="workflow-task-list-view" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {visibleTasks.map(t => (
                  <div key={t.id} className="workflow-task-list-item"
                    onClick={() => { setSelectedTask(t); setDetailOpen(true) }}
                    style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'var(--pico-card-background-color)', border: '1px solid var(--pico-border-color)', borderRadius: 6, cursor: 'pointer' }}>
                    <span className="workflow-card-badge" style={{ borderColor: COLUMN_COLORS[t.status] || '#8b949e', color: COLUMN_COLORS[t.status] || '#8b949e', flexShrink: 0 }}>
                      {t.status}
                    </span>
                    <span className="workflow-card-title" style={{ fontWeight: 400, flex: 1 }}>{t.title}</span>
                    {t.priority === 'high' && <Icon name="priority_high" size={14} style={{ color: '#f85149', flexShrink: 0 }} />}
                    {t.tags && t.tags.length > 0 && (
                      <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                        {t.tags.slice(0, 2).map(tag => <span key={tag} className="kanban-detail-tag" style={{ fontSize: 'var(--pico-font-size-condensed)' }}>{tag}</span>)}
                      </div>
                    )}
                    <span className="workflow-panel-count" style={{ flexShrink: 0 }}>{t.board}</span>
                  </div>
                ))}
              </div>
            )
          ) : !loading ? (
            <div className="workflow-empty">No user tasks found in .tasker/.</div>
          ) : null}
        </div>

        {/* Right detail panel */}
        {detailOpen && (
          <div className="workflow-detail-panel" style={{ flex: '0 0 45%', minWidth: 280, overflow: 'hidden', borderLeft: '1px solid var(--pico-border-color)', transition: 'flex 0.3s ease' }}>
            <WorkflowDetailPanel task={selectedTask} onClose={handleCloseDetail} />
          </div>
        )}
      </div>
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
    return { selectedTab: ['dashboard', 'missions', 'tasks'].includes(candidate) ? candidate : 'dashboard' }
  }, [location.search])

  const [activeTab, setActiveTab] = useState<WorkflowTab>(tabState.selectedTab)
  const [tasks, setTasks] = useState<WorkflowTask[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [snackbarAvailable, setSnackbarAvailable] = useState(false)
  const [selectedMission, setSelectedMission] = useState<string | null>(null)

  useEffect(() => { setActiveTab(tabState.selectedTab) }, [tabState.selectedTab])

  const fetchTasks = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/developer/tasker/tasks`, { signal: AbortSignal.timeout(4000) })
      if (res.ok) { const data = await res.json(); setTasks(data.tasks || []); setSnackbarAvailable(true) }
      else { setTasks([]); setSnackbarAvailable(true) }
    } catch { setError('Failed to load tasks'); setSnackbarAvailable(false); setTasks([]) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { void fetchTasks() }, [fetchTasks])

  const setTabAndRoute = (nextTab: WorkflowTab) => {
    setActiveTab(nextTab)
    navigate(`/workflow?tab=${nextTab}`)
  }

  const handleSelectMission = (missionTitle: string) => {
    setSelectedMission(missionTitle)
    setTabAndRoute('tasks')
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
      <GlobalToolbar tabs={toolbarTabs} onToggleSidebar={toggleSidebar} sidebarOpen={sidebarOpen} sidebarToggleLabel="Workflow sidebar"
        rightExtra={<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}><span className="hub-status-badge">Tasks: {tasks.length}</span></div>} />
      <div className="usx-surface-body" style={{ position: 'relative' }}>
        <VaultSidebar open={sidebarOpen} showModeTabs sidebarMode="server" serverNavItems={workflowNavItems} />
        <main className="usx-surface-main workflow-surface-main">
          {activeTab === 'dashboard' && <DashboardTab tasks={tasks} snackbarAvailable={snackbarAvailable} />}
          {activeTab === 'missions' && <MissionsTab allTasks={tasks} onSelectMission={handleSelectMission} />}
          {activeTab === 'tasks' && <TasksTab tasks={tasks} loading={loading} error={error} />}
        </main>
      </div>
    </div>
  )
}