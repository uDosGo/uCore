/* ═══════════════════════════════════════════════════════════════════
   KanbanSurface — Integrated workflow + tasker board
   ═══════════════════════════════════════════════════════════════════
   Fetches real data from:
   - /api/developer/tasker/tasks — .tasker markdown tasks (backlog, phases)
   - /api/workflows/runs — workflow run history
   - /api/developer/tasker/summary — aggregate stats
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'

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

// Ordered columns
const COLUMN_ORDER = ['todo', 'in-progress', 'review', 'blocked', 'completed', 'bug']
const COLUMN_ICONS: Record<string, string> = {
  todo: 'schedule',
  'in-progress': 'play_arrow',
  review: 'visibility',
  blocked: 'error',
  completed: 'check_circle',
  bug: 'bug_report',
}

export function KanbanSurface() {
  const [tasks, setTasks] = useState<TaskerTask[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<KanbanStats>({
    total: 0, todo: 0, 'in-progress': 0, completed: 0, blocked: 0, bug: 0, review: 0,
  })

  const fetchAll = React.useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch .tasker tasks
      const taskerRes = await fetch(`${SNACKBAR_API}/api/developer/tasker/tasks`, {
        signal: AbortSignal.timeout(4000),
      })

      // Fetch summary in parallel
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

  // Organize into columns
  const columns: Record<string, TaskerTask[]> = {}
  for (const status of COLUMN_ORDER) {
    columns[status] = tasks.filter(t => (t.status || 'todo').toLowerCase() === status)
  }
  // Catch-all for unknown statuses
  const unknownTasks = tasks.filter(t => !COLUMN_ORDER.includes((t.status || 'todo').toLowerCase()))
  if (unknownTasks.length > 0) {
    columns['todo'] = [...(columns['todo'] || []), ...unknownTasks]
  }

  const KanbanColumn = ({
    title,
    color,
    items,
    icon,
  }: {
    title: string
    color: string
    items: TaskerTask[]
    icon: string
  }) => (
    <div
      style={{
        flex: '0 0 calc(16.66% - 10px)',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--pico-card-sectioning-background-color, #1c2128)',
        borderRadius: 8,
        border: `2px solid ${color}40`,
        padding: 12,
        minHeight: 300,
        maxHeight: 'calc(100vh - 200px)',
        overflow: 'hidden',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Icon name={icon} size={16} style={{ color }} />
        <h4 style={{ margin: '0', color, fontSize: '12px', fontWeight: 'bold' }}>
          {title}
        </h4>
        <span
          style={{
            marginLeft: 'auto',
            background: `${color}20`,
            color,
            padding: '2px 8px',
            borderRadius: 4,
            fontSize: '11px',
            fontWeight: 600,
          }}
        >
          {items.length}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1, overflow: 'auto' }}>
        {items.length === 0 ? (
          <p style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)', margin: 0 }}>
            No tasks
          </p>
        ) : (
          items.map(task => (
            <TaskCard key={task.id} task={task} color={color} />
          ))
        )}
      </div>
    </div>
  )

  return (
    <div style={{ padding: '16px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <h2 style={{ margin: 0 }}>Tasker Kanban</h2>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => void fetchAll()}
              style={{
                padding: '6px 12px',
                fontSize: '12px',
                borderRadius: 4,
                border: '1px solid var(--pico-form-element-border-color)',
                background: 'var(--pico-form-element-background-color)',
                color: 'var(--pico-form-element-valid-border-color)',
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
            <span style={{ color: 'var(--pico-muted-color)' }}>Total: </span>
            <span style={{ fontWeight: 600 }}>{summary.total}</span>
          </div>
          {COLUMN_ORDER.map(status => (
            <div key={status} style={{ fontSize: '12px' }}>
              <span style={{ color: COLUMN_COLORS[status] || '#8b949e' }}>●</span>
              <span style={{ color: 'var(--pico-muted-color)' }}> {status}: </span>
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
          <div style={{ color: 'var(--pico-muted-color)', fontSize: '12px' }}>Loading tasks...</div>
        )}
      </div>

      {/* Kanban columns */}
      {tasks.length > 0 ? (
        <div style={{ display: 'flex', gap: 12, overflow: 'auto', flex: 1, paddingBottom: 8 }}>
          {COLUMN_ORDER.filter(s => (columns[s] || []).length > 0).map(status => (
            <KanbanColumn
              key={status}
              title={status.charAt(0).toUpperCase() + status.slice(1)}
              color={COLUMN_COLORS[status] || '#8b949e'}
              items={columns[status] || []}
              icon={COLUMN_ICONS[status] || 'task'}
            />
          ))}
        </div>
      ) : !loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1, color: 'var(--pico-muted-color)' }}>
          No tasks found in .tasker directory. Sync boards from AppFlowy or create markdown tasks to populate this view.
        </div>
      ) : null}
    </div>
  )
}

// Task card component
function TaskCard({ task, color }: { task: TaskerTask; color: string }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      style={{
        padding: 10,
        borderRadius: 4,
        background: 'rgba(0,0,0,0.2)',
        borderLeft: `3px solid ${color}`,
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onClick={() => setExpanded(!expanded)}
      onMouseEnter={e => {
        if (e.currentTarget instanceof HTMLElement) {
          e.currentTarget.style.background = 'rgba(0,0,0,0.35)'
          e.currentTarget.style.transform = 'translateX(4px)'
        }
      }}
      onMouseLeave={e => {
        if (e.currentTarget instanceof HTMLElement) {
          e.currentTarget.style.background = 'rgba(0,0,0,0.2)'
          e.currentTarget.style.transform = 'translateX(0)'
        }
      }}
    >
      {/* Card header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 6 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ margin: '0 0 2px', fontSize: '12px', fontWeight: 600, whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
            {task.title || task.id || 'Untitled'}
          </p>
          <p style={{ margin: 0, fontSize: '10px', color: 'var(--pico-muted-color)' }}>
            {task.board}{task.source ? ` · ${task.source}` : ''}
          </p>
        </div>
        {task.priority !== 'medium' && (
          <span style={{
            fontSize: '9px',
            padding: '1px 4px',
            borderRadius: 3,
            background: task.priority === 'high' ? '#f8514920' : task.priority === 'low' ? '#8b949e20' : 'transparent',
            color: task.priority === 'high' ? '#f85149' : '#8b949e',
            marginLeft: 4,
          }}>
            {task.priority}
          </span>
        )}
      </div>

      {/* Expanded details */}
      {expanded && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.1)', fontSize: '10px' }}>
          {task.tags && task.tags.length > 0 && (
            <div style={{ marginBottom: 4, color: 'var(--pico-muted-color)' }}>
              Tags: {task.tags.join(', ')}
            </div>
          )}
          {task.description && (
            <div style={{ marginBottom: 4, color: 'var(--pico-muted-color)', lineHeight: 1.4 }}>
              {task.description.length > 120 ? task.description.slice(0, 120) + '…' : task.description}
            </div>
          )}
          <div style={{ color: '#58a6ff', marginTop: 4 }}>
            📄 {task.file}
          </div>
        </div>
      )}
    </div>
  )
}