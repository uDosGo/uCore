/* ═══════════════════════════════════════════════════════════════════
   KanbanSurface — Integrated workflow + tasker board with
   right-split detail panel, prose rendering, and inline editing.
   ═══════════════════════════════════════════════════════════════════
   Fetches real data from:
   - /api/developer/tasker/tasks — .tasker markdown tasks (backlog, phases)
   - /api/developer/tasker/summary — aggregate stats
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { Icon } from '../../components/Icon'
import KanbanBoard, { KanbanItem, KanbanColumn } from '../../components/KanbanBoard'
import { renderMarkdown } from '../../utils/renderMarkdown'

interface TaskerTask {
  id: string
  title: string
  status: string
  priority: string
  board: string
  source: string
  tags: string[]
  description: string
  file: string
  metadata?: Record<string, any>
}

interface KanbanStats {
  total: number
  todo: number
  ['in-progress']: number
  completed: number
  blocked: number
  bug: number
  review: number
}

const SNACKBAR_API = 'http://localhost:8484'
const COLUMN_COLORS: Record<string, string> = {
  todo: '#8b949e',
  'in-progress': '#58a6ff',
  blocked: '#f85149',
  completed: '#3fb950',
  review: '#d29922',
  bug: '#da3633',
}

const COLUMN_ORDER = ['todo', 'in-progress', 'review', 'blocked', 'completed', 'bug']
const COLUMN_ICONS: Record<string, string> = {
  todo: 'schedule',
  'in-progress': 'play_arrow',
  review: 'visibility',
  blocked: 'error',
  completed: 'check_circle',
  bug: 'bug_report',
}

/** Render frontmatter lines from description text */
function extractFrontmatter(text: string): { frontmatter: Record<string, string>; body: string } {
  const lines = text.split('\n')
  if (lines[0]?.trim() !== '---') return { frontmatter: {}, body: text }
  const endIdx = lines.findIndex((l, i) => i > 0 && l.trim() === '---')
  if (endIdx === -1) return { frontmatter: {}, body: text }
  const fm: Record<string, string> = {}
  for (let i = 1; i < endIdx; i++) {
    const match = lines[i].match(/^([\w-]+):\s*(.+)/)
    if (match) fm[match[1].trim()] = match[2].trim()
  }
  return { frontmatter: fm, body: lines.slice(endIdx + 1).join('\n') }
}

/** Render frontmatter as a table */
function FrontmatterTable({ fm }: { fm: Record<string, string> }) {
  const keys = Object.keys(fm)
  if (keys.length === 0) return null
  return (
    <div className="kanban-detail-fm">
      {keys.map(k => (
        <div key={k} className="kanban-detail-fm-row">
          <span className="kanban-detail-fm-key">{k}</span>
          <span className="kanban-detail-fm-value">{fm[k]}</span>
        </div>
      ))}
    </div>
  )
}

/** Right-split detail panel with prose rendering + inline editing */
function DetailPanel({
  task,
  onClose,
  onUpdate,
  panelMode,
  onPanelModeChange,
}: {
  task: TaskerTask | null
  onClose: () => void
  onUpdate?: (task: TaskerTask) => Promise<void>
  panelMode: 'detail' | 'prose' | 'editor'
  onPanelModeChange: (mode: 'detail' | 'prose' | 'editor') => void
}) {
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [saving, setSaving] = useState(false)

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
        const res = await fetch(`${SNACKBAR_API}/api/developer/tasker/tasks/${task.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updated),
          signal: AbortSignal.timeout(5000),
        })
        if (!res.ok) throw new Error('Save failed')
      }
      setEditing(false)
    } catch (err) {
      console.error('Save error:', err)
    } finally {
      setSaving(false)
    }
  }, [task, editTitle, editDesc, onUpdate])

  if (!task) return null

  const { frontmatter, body } = extractFrontmatter(task.description || '')

  return (
    <div className="kanban-detail-panel">
      {/* Header */}
      <div className="kanban-detail-header">
        <div className="kanban-detail-header-tabs">
          <button
            className={`kanban-detail-tab ${panelMode === 'detail' ? 'active' : ''}`}
            onClick={() => onPanelModeChange('detail')}
          >
            <Icon name="info" size={14} /> Detail
          </button>
          <button
            className={`kanban-detail-tab ${panelMode === 'prose' ? 'active' : ''}`}
            onClick={() => onPanelModeChange('prose')}
          >
            <Icon name="description" size={14} /> Prose
          </button>
          <button
            className={`kanban-detail-tab ${panelMode === 'editor' ? 'active' : ''}`}
            onClick={() => onPanelModeChange('editor')}
          >
            <Icon name="edit" size={14} /> Editor
          </button>
        </div>
        <button className="kanban-detail-close" onClick={onClose} title="Close panel">
          <Icon name="close" size={16} />
        </button>
      </div>

      {/* Content */}
      <div className="kanban-detail-body">
        {panelMode === 'detail' && (
          <>
            {/* Title + metadata */}
            <div className="kanban-detail-section">
              {editing ? (
                <input
                  className="kanban-detail-input"
                  type="text"
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  placeholder="Task title"
                  autoFocus
                />
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
                {task.source && <span className="kanban-detail-meta-text">{task.source}</span>}
              </div>
            </div>

            {/* Frontmatter */}
            {Object.keys(frontmatter).length > 0 && (
              <div className="kanban-detail-section">
                <FrontmatterTable fm={frontmatter} />
              </div>
            )}

            {/* Tags */}
            {task.tags && task.tags.length > 0 && (
              <div className="kanban-detail-section">
                <div className="kanban-detail-tags">
                  {task.tags.map(tag => (
                    <span key={tag} className="kanban-detail-tag">{tag}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Description (prose rendered) */}
            {body && (
              <div className="kanban-detail-section kanban-detail-section--prose">
                <div
                  className="prose"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(body) }}
                />
              </div>
            )}

            {/* File reference */}
            <div className="kanban-detail-section">
              <div className="kanban-detail-file">
                <Icon name="description" size={14} /> {task.file}
              </div>
            </div>

            {/* Edit/Save actions */}
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
            <div
              className="prose"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(task.description || task.title) }}
            />
          </div>
        )}

        {panelMode === 'editor' && (
          <div className="kanban-detail-editor-wrap">
            {editing ? (
              <>
                <input
                  className="kanban-detail-input"
                  type="text"
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  placeholder="Task title"
                  style={{ marginBottom: 12 }}
                />
                <textarea
                  className="kanban-detail-editor"
                  value={editDesc}
                  onChange={e => setEditDesc(e.target.value)}
                  placeholder="Markdown description..."
                  spellCheck={false}
                />
                <div className="kanban-detail-actions" style={{ marginTop: 12 }}>
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
                  <div
                    className="prose"
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(task.description || task.title) }}
                  />
                </div>
                <button className="kanban-detail-btn primary" onClick={() => setEditing(true)} style={{ marginTop: 12 }}>
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

export function KanbanSurface() {
  const [tasks, setTasks] = useState<TaskerTask[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<KanbanStats>({
    total: 0, todo: 0, 'in-progress': 0, completed: 0, blocked: 0, bug: 0, review: 0,
  })
  const [selectedTask, setSelectedTask] = useState<TaskerTask | null>(null)
  const [detailPanelOpen, setDetailPanelOpen] = useState(false)
  const [panelMode, setPanelMode] = useState<'detail' | 'prose' | 'editor'>('detail')
  const [thirdPanelOpen, setThirdPanelOpen] = useState(false)
  const [showCompleted, setShowCompleted] = useState(true)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const taskerRes = await fetch(`${SNACKBAR_API}/api/developer/tasker/tasks`, {
        signal: AbortSignal.timeout(4000),
      })
      const summaryRes = await fetch(`${SNACKBAR_API}/api/developer/tasker/summary`, {
        signal: AbortSignal.timeout(4000),
      })

      if (taskerRes.ok) {
        const taskerData = await taskerRes.json()
        const allTasks: TaskerTask[] = taskerData.tasks || []
        setTasks(allTasks)
      }

      if (summaryRes.ok) {
        const summaryData = await summaryRes.json()
        const byStatus = summaryData.by_status || {}
        setSummary({
          total: summaryData.total || 0,
          todo: byStatus.todo || 0,
          'in-progress': (byStatus['in-progress'] || 0) + (byStatus.running || 0),
          completed: (byStatus.completed || 0) + (byStatus.done || 0),
          blocked: byStatus.blocked || 0,
          bug: byStatus.bug || 0,
          review: byStatus.review || 0,
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load task data')
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchAll()
    const interval = setInterval(() => void fetchAll(), 5000)
    return () => clearInterval(interval)
  }, [fetchAll])

  // Build KanbanBoard columns from tasks
  const visibleTasks = showCompleted
    ? tasks
    : tasks.filter(t => (t.status || 'todo').toLowerCase() !== 'completed')
  const boardColumns: KanbanColumn[] = COLUMN_ORDER
    .filter(status => visibleTasks.some(t => (t.status || 'todo').toLowerCase() === status))
    .map(status => ({
      id: status,
      title: status.charAt(0).toUpperCase() + status.slice(1),
      color: COLUMN_COLORS[status] || '#8b949e',
      items: visibleTasks
        .filter(t => (t.status || 'todo').toLowerCase() === status)
        .map(t => ({
          id: t.id,
          title: t.title,
          type: t.board || 'task',
          date: t.source || '',
        })),
    }))

  // Handle item click in KanbanBoard
  const handleItemClick = (item: KanbanItem) => {
    const task = tasks.find(t => t.id === item.id)
    if (task) {
      setSelectedTask(task)
      setDetailPanelOpen(true)
    }
  }

  const handleCloseDetail = () => {
    setDetailPanelOpen(false)
    setSelectedTask(null)
  }

  return (
    <div style={{ padding: '16px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <h2 style={{ margin: 0 }}>Tasker Kanban</h2>
          <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => setShowCompleted(v => !v)}
                style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  borderRadius: 4,
                  border: `1px solid var(--pico-form-element-border-color)`,
                  background: showCompleted ? 'rgba(63,185,80,0.15)' : 'var(--pico-form-element-background-color)',
                  color: 'var(--pico-color)',
                  cursor: 'pointer',
                }}
                title="Toggle completed tasks visibility"
              >
                <Icon name="check_circle" size={14} style={{ display: 'inline', marginRight: 4 }} />
                {showCompleted ? 'Hide completed' : 'Show completed'}
              </button>
              {detailPanelOpen && (
                <button
                  onClick={() => setThirdPanelOpen(v => !v)}
                style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  borderRadius: 4,
                  border: `1px solid var(--pico-form-element-border-color)`,
                  background: thirdPanelOpen ? 'rgba(88,166,255,0.15)' : 'var(--pico-form-element-background-color)',
                  color: 'var(--pico-color)',
                  cursor: 'pointer',
                }}
                title="Toggle side-by-side panel"
              >
                <Icon name="view_column" size={14} style={{ display: 'inline', marginRight: 4 }} />
                {thirdPanelOpen ? '2-up' : 'Prose'}
              </button>
            )}
            <button
              onClick={() => void fetchAll()}
              style={{
                padding: '6px 12px',
                fontSize: '12px',
                borderRadius: 4,
                border: '1px solid var(--pico-form-element-border-color)',
                background: 'var(--pico-form-element-background-color)',
                color: 'var(--pico-color)',
                cursor: 'pointer',
              }}
              title="Refresh"
            >
              <Icon name="refresh" size={14} style={{ display: 'inline', marginRight: 4 }} />
              Refresh
            </button>
          </div>
        </div>

        {/* Stats bar */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 12, flexWrap: 'wrap' }}>
          <div style={{ fontSize: '12px' }}>
            <span style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Total: </span>
            <span style={{ fontWeight: 600 }}>{summary.total}</span>
          </div>
          {COLUMN_ORDER.map(status => (
            <div key={status} style={{ fontSize: '12px' }}>
              <span style={{ color: COLUMN_COLORS[status] || '#8b949e' }}>●</span>
              <span style={{ color: 'var(--pico-muted-color, #8b949e)' }}> {status}: </span>
              <span style={{ fontWeight: 600 }}>{summary[status as keyof KanbanStats] || 0}</span>
            </div>
          ))}
        </div>

        {error && (
          <div style={{ padding: 8, borderRadius: 4, background: '#f855491a', color: '#f85149', fontSize: '12px' }}>
            {error}
          </div>
        )}

        {loading && tasks.length === 0 && (
          <div style={{ color: 'var(--pico-muted-color, #8b949e)', fontSize: '12px' }}>Loading tasks...</div>
        )}
      </div>

      {/* Kanban + detail panels */}
      <div style={{ display: 'flex', flex: 1, gap: 12, overflow: 'hidden', position: 'relative' }}>
        {/* Kanban board */}
        <div style={{
          flex: detailPanelOpen ? (thirdPanelOpen ? '0 0 40%' : '0 0 55%') : '1 1 100%',
          minWidth: detailPanelOpen ? '300px' : '0',
          overflow: 'auto',
          transition: 'flex 0.3s ease',
        }}>
          {tasks.length > 0 ? (
            <KanbanBoard
              columns={boardColumns}
              onItemClick={handleItemClick}
              readOnly
            />
          ) : !loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1, color: 'var(--pico-muted-color, #8b949e)', height: '100%' }}>
              No tasks found in .tasker directory. Sync boards from AppFlowy or create markdown tasks to populate this view.
            </div>
          ) : null}
        </div>

        {/* Right detail panel */}
        {detailPanelOpen && (
          <div style={{
            flex: thirdPanelOpen ? '0 0 30%' : '0 0 45%',
            minWidth: '280px',
            overflow: 'hidden',
            borderLeft: '1px solid var(--pico-border-color, #30363d)',
            transition: 'flex 0.3s ease',
          }}>
            <DetailPanel
              task={selectedTask}
              onClose={handleCloseDetail}
              panelMode={panelMode}
              onPanelModeChange={setPanelMode}
            />
          </div>
        )}

        {/* Third panel (side-by-side prose) */}
        {thirdPanelOpen && detailPanelOpen && selectedTask && (
          <div style={{
            flex: '0 0 30%',
            minWidth: '280px',
            overflow: 'auto',
            borderLeft: '1px solid var(--pico-border-color, #30363d)',
            padding: 16,
          }}>
            <div className="kanban-detail-section--prose">
              <div
                className="prose"
                dangerouslySetInnerHTML={{
                  __html: renderMarkdown(selectedTask.description || selectedTask.title)
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}