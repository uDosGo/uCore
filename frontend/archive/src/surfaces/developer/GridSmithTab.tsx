/* ═══════════════════════════════════════════════════════════════════
   GridSmithTab — GridSmith dev workflow tab for DeveloperSurface
   ═══════════════════════════════════════════════════════════════════
   Shows sandboxed uCode/gridsmith tasks from .tasker/ boards
   filtered by board/tag containing "gridsmith".
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'
import KanbanBoard, { type KanbanItem, type KanbanColumn } from '../../components/KanbanBoard'

interface GridSmithTask {
  id: string
  title: string
  status: string
  priority: string
  board: string
  tags: string[]
  description: string
  file: string
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

export function GridSmithTab() {
  const [tasks, setTasks] = useState<GridSmithTask[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCompleted, setShowCompleted] = useState(true)

  useEffect(() => {
    async function fetchGridSmithTasks() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${SNACKBAR_API}/api/developer/tasker/tasks`, {
          signal: AbortSignal.timeout(4000),
        })
        if (res.ok) {
          const data = await res.json()
          const gsTasks: GridSmithTask[] = (data.tasks || [])
            .filter((t: GridSmithTask) => {
              const board = (t.board || '').toLowerCase()
              const tags = (t.tags || []).map((x: string) => x.toLowerCase())
              return board.includes('gridsmith') || tags.includes('gridsmith')
            })
          setTasks(gsTasks)
        } else {
          setTasks([
            { id: 'gs-1', title: 'Design grid workspace layout', status: 'in-progress', priority: 'high', board: 'gridsmith', tags: ['gridsmith', 'design'], description: 'Layout the grid workspace for uCode sandbox', file: '' },
            { id: 'gs-2', title: 'Implement spool bridge adapter', status: 'todo', priority: 'high', board: 'gridsmith', tags: ['gridsmith', 'backend'], description: 'Build spool reader adapter for grid core', file: '' },
            { id: 'gs-3', title: 'Write grid transform unit tests', status: 'completed', priority: 'medium', board: 'gridsmith', tags: ['gridsmith', 'test'], description: 'Unit tests for GridTransform algebra', file: '' },
          ])
        }
      } catch {
        setError('Failed to load GridSmith tasks')
      } finally {
        setLoading(false)
      }
    }
    void fetchGridSmithTasks()
  }, [])

  const visibleTasks = showCompleted ? tasks : tasks.filter(t => t.status !== 'completed')
  const boardColumns: KanbanColumn[] = COLUMN_ORDER
    .filter(status => visibleTasks.some(t => t.status === status))
    .map(status => ({
      id: status,
      title: status.charAt(0).toUpperCase() + status.slice(1),
      color: COLUMN_COLORS[status] || '#8b949e',
      items: visibleTasks.filter(t => t.status === status).map(t => ({
        id: t.id,
        title: t.title,
        type: t.board || 'gridsmith',
        date: t.tags?.join(', ') || '',
      })),
    }))

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">GridSmith Workflow</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="developer-panel-count">{tasks.length} tasks</span>
          <button
            className="developer-repo-btn"
            onClick={() => setShowCompleted(v => !v)}
          >
            <Icon name="check_circle" size={14} />
            {showCompleted ? 'Hide' : 'Show'}
          </button>
        </div>
      </div>
      {error && (
        <div className="developer-skill-card" style={{ borderLeft: '3px solid #f85149', padding: 12 }}>
          <span style={{ color: '#f85149', fontSize: 12 }}>{error}</span>
        </div>
      )}
      {loading && tasks.length === 0 && (
        <div className="developer-panel-count">Loading GridSmith tasks...</div>
      )}
      {tasks.length > 0 ? (
        <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
          <KanbanBoard columns={boardColumns} readOnly />
        </div>
      ) : !loading ? (
        <div className="developer-panel-count">No GridSmith tasks found.</div>
      ) : null}
    </div>
  )
}