/* ═══════════════════════════════════════════════════════════════════
   WorkflowSurface — USX Schema v3.1 Workflow Surface
   ═══════════════════════════════════════════════════════════════════
   Tabs: Mission Control (renamed from Dashboard) — Drop Panel + live stats,
         Missions (linked to tasks),
         Tasks (kanban + list view, right-split detail editor),
         Binder — compiler that collates/processes dropped files
   Project Type: Operational (OP) | Autonomy Level: L3 (Collaborator)
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar, { type SidebarNavItem } from '../../components/VaultSidebar'
import KanbanBoard, { type KanbanItem, type KanbanColumn } from '../../components/KanbanBoard'
import { renderMarkdown } from '../../utils/renderMarkdown'
import '../../styles/surfaces/workflow.css'

// ─── Types ──────────────────────────────────────────────────────
type WorkflowTab = 'mission-control' | 'missions' | 'tasks' | 'binder' | 'publish'
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

/** A file queued for processing into a binder / mission */
interface QueuedFile {
  id: string
  name: string
  size: number
  type: string
  addedAt: Date
}

/** A compiled binder from processed files */
interface Binder {
  id: string
  name: string
  description: string
  sourceCount: number
  createdAt: Date
  status: 'active' | 'pending' | 'complete'
  color: string
  icon: string
  files: QueuedFile[]
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

const ACCEPTED_FORMATS = ['.md', '.txt', '.json', '.yaml', '.yml', '.csv', '.log', '.py', '.js', '.ts', '.jsx', '.tsx', '.css', '.html']

// ─── User task filter — exclude explicit dev/system ────────────
function isUserTask(task: WorkflowTask): boolean {
  const board = (task.board || '').toLowerCase()
  const tags = (task.tags || []).map(t => t.toLowerCase())
  const devPatterns = ['developer', 'dev-task', 'dev/', 'gridsmith']
  return !devPatterns.some(p => board.includes(p)) &&
         !tags.some(t => devPatterns.some(p => t.includes(p)))
}

// ─── Helpers — format file size ─────────────────────────────────
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
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
              <Icon name="info" /> Detail
            </button>
            <button className={`kanban-detail-tab ${panelMode === 'prose' ? 'active' : ''}`} onClick={() => setPanelMode('prose')}>
              <Icon name="description" /> Prose
            </button>
            <button className={`kanban-detail-tab ${panelMode === 'editor' ? 'active' : ''}`} onClick={() => setPanelMode('editor')}>
              <Icon name="edit" /> Editor
            </button>
        </div>
        <button className="kanban-detail-close" onClick={onClose} title="Close panel">
          <Icon name="close" />
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
                <Icon name="description" /> {task.file}
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
                  <Icon name="edit" /> Edit
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
                  <Icon name="edit" /> Edit
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── New Mission Drop Panel ──────────────────────────────────────
function NewMissionDropPanel({ onFilesQueued }: {
  onFilesQueued: (files: QueuedFile[]) => void
}) {
  const [dragging, setDragging] = useState(false)
  const [queuedFiles, setQueuedFiles] = useState<QueuedFile[]>([])
  const dragCounter = useRef(0)

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounter.current++
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setDragging(true)
    }
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounter.current--
    if (dragCounter.current === 0) {
      setDragging(false)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const processFiles = useCallback((fileList: FileList) => {
    const newFiles: QueuedFile[] = Array.from(fileList).map(f => ({
      id: `qf-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      name: f.name,
      size: f.size,
      type: f.type || f.name.split('.').pop() || 'unknown',
      addedAt: new Date(),
    }))
    setQueuedFiles(prev => [...prev, ...newFiles])
    onFilesQueued(newFiles)
  }, [onFilesQueued])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(false)
    dragCounter.current = 0
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files)
      e.dataTransfer.clearData()
    }
  }, [processFiles])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files)
      e.target.value = ''
    }
  }, [processFiles])

  const removeFile = useCallback((id: string) => {
    setQueuedFiles(prev => prev.filter(f => f.id !== id))
  }, [])

  const clearAll = useCallback(() => {
    setQueuedFiles([])
  }, [])

  const totalSize = queuedFiles.reduce((sum, f) => sum + f.size, 0)

  return (
    <div className="mc-section">
      <div className="mc-section-header">
        <Icon name="add" />
        <h3>Launchpad</h3>
        <span>Drop files to create a mission binder</span>
      </div>

      <div
        className={`mc-drop-panel ${dragging ? 'mc-drop-panel--dragging' : ''} ${queuedFiles.length > 0 ? 'mc-drop-panel--has-files' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div className="mc-drop-panel-icon">
          <Icon name={dragging ? 'cloud_upload' : queuedFiles.length > 0 ? 'check_circle' : 'upload_file'} />
        </div>
        <p className="mc-drop-panel-title">
          {dragging ? 'Drop files to queue them' : queuedFiles.length > 0 ? `${queuedFiles.length} file(s) queued` : 'Drag & drop files here'}
        </p>
        <p className="mc-drop-panel-subtitle">or click to browse</p>
        <div className="mc-drop-panel-formats">
          {ACCEPTED_FORMATS.map(fmt => (
            <span key={fmt} className="mc-drop-panel-format-badge">{fmt}</span>
          ))}
        </div>
        <input
          type="file"
          className="mc-drop-panel-input"
          multiple
          onChange={handleInputChange}
          accept={ACCEPTED_FORMATS.join(',')}
        />
      </div>

      {queuedFiles.length > 0 && (
        <div className="mc-queue">
          <div className="mc-queue-header">
            <h4>Queued Files ({queuedFiles.length})</h4>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span className="mc-drop-panel-subtitle" style={{ fontSize: 11 }}>{formatSize(totalSize)} total</span>
              <button className="mc-queue-clear" onClick={clearAll}>Clear all</button>
            </div>
          </div>
          {queuedFiles.map(f => (
            <div key={f.id} className="mc-queue-item">
              <div className="mc-queue-item-icon">
                <Icon name="description" />
              </div>
              <div className="mc-queue-item-info">
                <div className="mc-queue-item-name">{f.name}</div>
                <div className="mc-queue-item-meta">{f.type}</div>
              </div>
              <div className="mc-queue-item-size">{formatSize(f.size)}</div>
              <button className="mc-queue-item-remove" onClick={() => removeFile(f.id)} title="Remove">
                <Icon name="close" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Live Mission / Workflow Stats ──────────────────────────────
function LiveWorkflowStats({ tasks, snackbarAvailable }: {
  tasks: { done: number; total: number } | null
  snackbarAvailable: boolean
}) {
  const tasksDone = tasks ? tasks.done : 0
  const tasksTotal = tasks ? tasks.total : 0
  const tasksPct = tasksTotal > 0 ? Math.round((tasksDone / tasksTotal) * 100) : 0

  const activeMissions = 4
  const workflowsRunning = 2
  const filesProcessed = 128

  return (
    <div className="mc-section">
      <div className="mc-section-header">
        <Icon name="monitor_heart" />
        <h3>Mission Control</h3>
        <span>Real-time system overview</span>
      </div>

      <div className="mc-stats-grid">
        <div className="mc-stat-card">
          <span className="mc-stat-label"><Icon name="flag" /> Active Missions</span>
          <span className="mc-stat-value">{activeMissions}</span>
          <div className="mc-stat-bar"><div className="mc-stat-bar-fill" style={{ width: '100%', background: 'var(--pico-primary, #58a6ff)' }} /></div>
        </div>
        <div className="mc-stat-card">
          <span className="mc-stat-label"><Icon name="account_tree" /> Workflows Running</span>
          <span className="mc-stat-value">{workflowsRunning}</span>
          <div className="mc-stat-bar"><div className="mc-stat-bar-fill" style={{ width: `${(workflowsRunning / 10) * 100}%`, background: 'var(--pico-ins-color, #3fb950)' }} /></div>
        </div>
        <div className="mc-stat-card">
          <span className="mc-stat-label"><Icon name="folder" /> Files Processed</span>
          <span className="mc-stat-value">{filesProcessed}</span>
          <div className="mc-stat-bar"><div className="mc-stat-bar-fill" style={{ width: '100%', background: 'var(--pico-warning-color, #d29922)' }} /></div>
        </div>
        <div className="mc-stat-card">
          <span className="mc-stat-label"><Icon name="checklist" /> Tasks</span>
          <span className="mc-stat-value">{tasksDone}/{tasksTotal}</span>
          <div className="mc-stat-bar"><div className="mc-stat-bar-fill" style={{ width: `${tasksPct}%`, background: 'var(--pico-primary-focus, #a855f7)' }} /></div>
        </div>
        <div className="mc-stat-card">
          <span className="mc-stat-label"><Icon name="restaurant_menu" /> Snackbar</span>
          <span className="mc-stat-value" style={{ color: snackbarAvailable ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-del-color, #f85149)' }}>
            {snackbarAvailable ? 'Online' : 'Offline'}
          </span>
          <div className="mc-stat-bar"><div className="mc-stat-bar-fill" style={{ width: '100%', background: snackbarAvailable ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-del-color, #f85149)' }} /></div>
        </div>
      </div>
    </div>
  )
}

// ─── Mission Control Tab (renamed from Dashboard) ─────────────
function MissionControlTab({ tasks, snackbarAvailable }: {
  tasks: WorkflowTask[]
  snackbarAvailable: boolean
}) {
  const [taskCounts, setTaskCounts] = useState<{ done: number; total: number } | null>(null)

  useEffect(() => {
    const total = tasks.length
    const done = tasks.filter(t => t.status === 'completed').length
    setTaskCounts({ total, done })
  }, [tasks])

  const handleFilesQueued = useCallback((files: QueuedFile[]) => {
    console.log(`Queued ${files.length} file(s) for mission processing`)
  }, [])

  const quickActions = [
    { icon: 'add', label: 'New Mission', color: '#58a6ff' },
    { icon: 'refresh', label: 'Sync Workflows', color: '#22c55e' },
    { icon: 'search', label: 'Search Binders', color: '#f59e0b', route: '/workflow?tab=binder' },
    { icon: 'help', label: 'Mission Docs', color: '#a855f7', route: '/s600' },
  ]

  const activity: ActivityEntry[] = [
    { date: 'Today', title: 'Mission sync completed', icon: 'sync' },
    { date: 'Today', title: 'Vault indexed 42 documents', icon: 'folder' },
    { date: 'Yesterday', title: 'Workflow pipeline green', icon: 'check_circle' },
    { date: '2d ago', title: 'AppFlowy import completed', icon: 'download' },
    { date: '3d ago', title: 'Binder compiled: Surface Audit', icon: 'auto_awesome' },
  ]

  return (
    <div className="workflow-dashboard">
      <LiveWorkflowStats tasks={taskCounts} snackbarAvailable={snackbarAvailable} />
      <NewMissionDropPanel onFilesQueued={handleFilesQueued} />

      <div className="mc-grid-2">
        <div className="mc-section">
          <div className="mc-section-header">
            <Icon name="bolt" />
            <h3>Quick Actions</h3>
          </div>
          <div className="workflow-action-grid">
            {quickActions.map(a => (
              a.route ? (
                <a key={a.label} href={a.route} className="workflow-action-btn" style={{ '--wf-action-color': a.color } as React.CSSProperties}>
                  <Icon name={a.icon} /> {a.label}
                </a>
              ) : (
                <button key={a.label} className="workflow-action-btn" style={{ '--wf-action-color': a.color } as React.CSSProperties}>
                  <Icon name={a.icon} /> {a.label}
                </button>
              )
            ))}
          </div>
        </div>

        <div className="mc-section">
          <div className="mc-section-header">
            <Icon name="history" />
            <h3>Activity</h3>
          </div>
          <div className="workflow-activity-list">
            {activity.map(a => (
              <div key={a.title} className="workflow-activity-row">
                {a.icon && <Icon name={a.icon} style={{ color: 'var(--pico-muted-color)' }} />}
                <span className="workflow-activity-date">{a.date}</span>
                <span className="workflow-activity-title">{a.title}</span>
              </div>
            ))}
          </div>
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
        <h3>Active Missions</h3>
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
            <div style={{ marginTop: 8 }}>
              <button className="workflow-toggle-btn" onClick={() => onSelectMission(m.title)}
                style={{ width: '100%', justifyContent: 'center', padding: '6px 0' }}>
                <Icon name="list" /> View {m.linkedTasks.length} tasks
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
              <Icon name="grid_view" />
            </button>
            <button className={`workflow-view-btn ${viewMode === 'list' ? 'active' : ''}`} onClick={() => setViewMode('list')}
              style={{ padding: '4px 10px', border: 'none', background: viewMode === 'list' ? 'var(--pico-card-sectioning-background-color)' : 'transparent', color: 'var(--pico-color)', cursor: 'pointer', fontFamily: 'inherit' }}>
              <Icon name="list" />
            </button>
          </div>
          <button className="workflow-toggle-btn" onClick={() => setShowCompleted(v => !v)}>
            <Icon name="check_circle" />
            {showCompleted ? 'Hide' : 'Show'}
          </button>
        </div>
      </div>

      {error && <div className="workflow-card" style={{ borderLeft: '3px solid var(--pico-del-color, #f85149)' }}><p style={{ color: 'var(--pico-del-color, #f85149)', margin: 0 }}>{error}</p></div>}
      {loading && userTasks.length === 0 && <div className="workflow-empty">Loading user tasks...</div>}

      <div className="workflow-tasks-body" style={{ display: 'flex', flex: 1, minHeight: 0, gap: 12, overflow: 'hidden' }}>
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
                    {t.priority === 'high' && <Icon name="priority_high" style={{ color: 'var(--pico-del-color, #f85149)', flexShrink: 0 }} />}
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

        {detailOpen && (
          <div className="workflow-detail-panel" style={{ flex: '0 0 45%', minWidth: 280, overflow: 'hidden', borderLeft: '1px solid var(--pico-border-color)', transition: 'flex 0.3s ease' }}>
            <WorkflowDetailPanel task={selectedTask} onClose={handleCloseDetail} />
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Binder Compiler Tab ────────────────────────────────────────
function BinderCompilerTab() {
  const [incomingFiles, setIncomingFiles] = useState<QueuedFile[]>([])
  const [binders, setBinders] = useState<Binder[]>([
    {
      id: 'b1',
      name: 'Surface Audit 2026',
      description: 'Consolidated audit findings from surface restructuring',
      sourceCount: 12,
      createdAt: new Date('2026-06-20'),
      status: 'active',
      color: '#58a6ff',
      icon: 'fact_check',
      files: [],
    },
    {
      id: 'b2',
      name: 'USX Component Specs',
      description: 'Component specifications and migration notes',
      sourceCount: 8,
      createdAt: new Date('2026-06-18'),
      status: 'complete',
      color: '#3fb950',
      icon: 'component_exchange',
      files: [],
    },
    {
      id: 'b3',
      name: 'Vault Index Pipeline',
      description: 'Pipeline config and indexing rules for vault sync',
      sourceCount: 4,
      createdAt: new Date('2026-06-15'),
      status: 'pending',
      color: '#d29922',
      icon: 'folder_sync',
      files: [],
    },
  ])

  const [processing, setProcessing] = useState(false)
  const [processingFileId, setProcessingFileId] = useState<string | null>(null)

  const handleFilesQueued = useCallback((files: QueuedFile[]) => {
    setIncomingFiles(prev => [...prev, ...files])
  }, [])

  const processFiles = useCallback(async () => {
    if (incomingFiles.length === 0 || processing) return
    setProcessing(true)

    for (const file of incomingFiles) {
      setProcessingFileId(file.id)
      await new Promise(resolve => setTimeout(resolve, 300))
    }

    const newBinder: Binder = {
      id: `b-${Date.now()}`,
      name: `Binder ${binders.length + 1} — ${new Date().toLocaleDateString()}`,
      description: `Auto-compiled from ${incomingFiles.length} source files`,
      sourceCount: incomingFiles.length,
      createdAt: new Date(),
      status: 'active',
      color: '#a855f7',
      icon: 'auto_awesome',
      files: [...incomingFiles],
    }

    setBinders(prev => [newBinder, ...prev])
    setIncomingFiles([])
    setProcessingFileId(null)
    setProcessing(false)
  }, [incomingFiles, processing, binders.length])

  const removeIncoming = useCallback((id: string) => {
    setIncomingFiles(prev => prev.filter(f => f.id !== id))
  }, [])

  const statusLabel: Record<string, string> = { active: 'Active', pending: 'Pending', complete: 'Complete' }

  return (
    <div className="workflow-dashboard binder-compiler">
      <div className="binder-compiler-header">
        <h3><Icon name="folder_special" /> Binder Compiler</h3>
        <div className="binder-compiler-stats">
          <span><Icon name="folder" /> {binders.length} binders</span>
          <span><Icon name="description" /> {binders.reduce((s, b) => s + b.sourceCount, 0)} sources</span>
        </div>
      </div>

      <div className="mc-section">
        <NewMissionDropPanel onFilesQueued={handleFilesQueued} />
      </div>

      {incomingFiles.length > 0 && (
        <div className="binder-incoming">
          <div className="binder-incoming-header">
            <h4><Icon name="input" /> Incoming Files</h4>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span className="binder-incoming-count">{incomingFiles.length} file(s)</span>
              <button className="binder-process-all" onClick={processFiles} disabled={processing}>
                <Icon name={processing ? 'sync' : 'auto_awesome'} className={processing ? 'hub-spin' : ''} />
                {processing ? 'Processing...' : 'Compile Binder'}
              </button>
            </div>
          </div>
          <div className="binder-incoming-list">
            {incomingFiles.map(f => (
              <div key={f.id} className="binder-incoming-item">
                <div className="binder-incoming-item-icon"><Icon name="description" /></div>
                <span className="binder-incoming-item-name">{f.name}</span>
                <span className="binder-incoming-item-meta" style={{ fontSize: 10, color: 'var(--pico-muted-color)' }}>{formatSize(f.size)}</span>
                <span className={`binder-incoming-item-status binder-incoming-item-status--${processingFileId === f.id ? 'processing' : 'queued'}`}>
                  {processingFileId === f.id ? 'Processing...' : 'Queued'}
                </span>
                <button className="mc-queue-item-remove" onClick={() => removeIncoming(f.id)} title="Remove"><Icon name="close" /></button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mc-section">
        <div className="mc-section-header">
          <Icon name="folder" />
          <h3>Compiled Binders</h3>
          <span>{binders.length} total</span>
        </div>

        {binders.length > 0 ? (
          <div className="binder-list">
            {binders.map(b => (
              <div key={b.id} className="binder-item">
                <div className="binder-item-icon" style={{ background: `${b.color}18`, color: b.color }}>
                  <Icon name={b.icon} />
                </div>
                <div className="binder-item-info">
                  <div className="binder-item-name">{b.name}</div>
                  <div className="binder-item-meta">
                    <span>{b.description}</span>
                    <span>{b.sourceCount} source file(s)</span>
                    <span>Created {b.createdAt.toLocaleDateString()}</span>
                  </div>
                </div>
                <span className={`binder-item-status binder-item-status--${b.status}`}>{statusLabel[b.status]}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="binder-empty">
            <div className="binder-empty-icon"><Icon name="folder_open" /></div>
            <h4>No binders yet</h4>
            <p>Drop files above to create your first binder. Binders collate source files into organized mission or task groups.</p>
          </div>
        )}
      </div>

      <div className="mc-section">
        <div className="mc-section-header">
          <Icon name="info" />
          <h3>How it works</h3>
        </div>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {[
            { step: '1', title: 'Drop Files', desc: 'Drag & drop or browse to queue source files (.md, .json, .py, etc.)' },
            { step: '2', title: 'Compile Binder', desc: 'Click "Compile Binder" to process and collate files into a named binder' },
            { step: '3', title: 'Link to Mission', desc: 'Binders can be assigned to missions or task groups for structured work' },
          ].map(s => (
            <div key={s.step} style={{ flex: '1 1 200px', display: 'flex', gap: 10, alignItems: 'flex-start', padding: 12, background: 'var(--pico-card-background-color, #0d1117)', border: '1px solid var(--pico-border-color, #30363d)', borderRadius: 8 }}>
              <span style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--pico-primary, #58a6ff)', color: 'var(--pico-primary-inverse, #fff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>{s.step}</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--pico-color, #e6edf3)' }}>{s.title}</div>
                <div style={{ fontSize: 12, color: 'var(--pico-muted-color, #8b949e)' }}>{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Publish Tab (placeholder) ──────────────────────────────────
function PublishTab() {
  return (
    <div className="workflow-panel">
      <div className="workflow-panel-header">
        <h3>Publish</h3>
        <span className="workflow-panel-count">Coming soon</span>
      </div>
      <div className="workflow-empty" style={{ padding: '40px 20px', textAlign: 'center' }}>
        <p>Publish functionality will be consolidated here in a future round.</p>
      </div>
    </div>
  )
}

// ─── Main Surface ──────────────────────────────────────────────
export default function WorkflowSurface() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sidebarOpen, toggleSidebar } = useSurfaceShell()

  const VALID_TABS: WorkflowTab[] = ['mission-control', 'missions', 'tasks', 'binder', 'publish']

  const tabState = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const raw = (params.get('tab') || 'mission-control').toLowerCase()
    const candidate = raw as WorkflowTab
    return { selectedTab: VALID_TABS.includes(candidate) ? candidate : 'mission-control' as WorkflowTab }
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
    { id: 'mission-control', icon: 'rocket_launch', label: 'Mission Control', active: activeTab === 'mission-control', onClick: () => setTabAndRoute('mission-control') },
    { id: 'binder', icon: 'folder_special', label: 'Binder', active: activeTab === 'binder', onClick: () => setTabAndRoute('binder') },
    { id: 'missions', icon: 'flag', label: 'Projects', active: activeTab === 'missions', onClick: () => setTabAndRoute('missions') },
    { id: 'tasks', icon: 'checklist', label: 'Tasks', active: activeTab === 'tasks', onClick: () => setTabAndRoute('tasks') },
    { id: 'publish', icon: 'publish', label: 'Publish', active: activeTab === 'publish', onClick: () => setTabAndRoute('publish') },
  ]

  const toolbarTabs: ToolbarTab[] = [
    { id: 'mission-control', icon: 'rocket_launch', label: 'Mission Control', active: activeTab === 'mission-control', onClick: () => setTabAndRoute('mission-control') },
    { id: 'binder', icon: 'folder_special', label: 'Binder', active: activeTab === 'binder', onClick: () => setTabAndRoute('binder') },
    { id: 'missions', icon: 'flag', label: 'Projects', active: activeTab === 'missions', onClick: () => setTabAndRoute('missions') },
    { id: 'tasks', icon: 'checklist', label: 'Tasks', active: activeTab === 'tasks', onClick: () => setTabAndRoute('tasks') },
    { id: 'publish', icon: 'publish', label: 'Publish', active: activeTab === 'publish', onClick: () => setTabAndRoute('publish') },
  ]

  return (
    <div className="usx-surface-layout workflow-surface">
      <GlobalToolbar tabs={toolbarTabs} onToggleSidebar={toggleSidebar} sidebarOpen={sidebarOpen} sidebarToggleLabel="Workflow sidebar"
        rightExtra={<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}><span className="hub-status-badge">Tasks: {tasks.length}</span></div>} />
      <div className="usx-surface-body" style={{ position: 'relative' }}>
        <VaultSidebar open={sidebarOpen} showModeTabs sidebarMode="server" serverNavItems={workflowNavItems} />
        <main className="usx-surface-main">
          {activeTab === 'mission-control' && <MissionControlTab tasks={tasks} snackbarAvailable={snackbarAvailable} />}
          {activeTab === 'missions' && <MissionsTab allTasks={tasks} onSelectMission={handleSelectMission} />}
          {activeTab === 'tasks' && <TasksTab tasks={tasks} loading={loading} error={error} />}
          {activeTab === 'binder' && <BinderCompilerTab />}
          {activeTab === 'publish' && <PublishTab />}
        </main>
      </div>
    </div>
  )
}