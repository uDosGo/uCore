/* ═══════════════════════════════════════════════════════════════════
   DashboardPanel — System stats, tasks, activity feed
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState } from 'react'
import { useStore } from '../GridUIStore'

export function DashboardPanel() {
  const store = useStore()
  const [stats, setStats] = useState({ cpu: 45, memory: 62, disk: 38, uptime: '3d 14h 22m' })
  const [tasks, setTasks] = useState([
    { id: 1, title: 'Complete project documentation', completed: false, priority: 'high' as const },
    { id: 2, title: 'Review pull requests', completed: false, priority: 'medium' as const },
    { id: 3, title: 'Update dependencies', completed: true, priority: 'low' as const },
    { id: 4, title: 'Fix login bug', completed: false, priority: 'high' as const },
    { id: 5, title: 'Write unit tests', completed: false, priority: 'medium' as const },
  ])
  const [activity] = useState([
    { title: 'gridui v1.0 released!', date: '2026-05-20' },
    { title: 'New USX grid renderer available', date: '2026-05-19' },
    { title: 'Community showcase: Retro dashboards', date: '2026-05-18' },
    { title: 'uCode v1.2 deployment complete', date: '2026-05-17' },
    { title: 'MCP Bridge connected to gridui', date: '2026-05-16' },
  ])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [newTaskTitle, setNewTaskTitle] = useState('')
  const [newTaskPriority, setNewTaskPriority] = useState<'low'|'medium'|'high'>('medium')

  const barColor = (val: number) => val > 80 ? '#E76F51' : val > 60 ? '#E9C46A' : '#2A9D8F'
  const toggleTask = (id: number) => setTasks(t => t.map(x => x.id === id ? { ...x, completed: !x.completed } : x))
  const addTask = () => {
    if (!newTaskTitle.trim()) return
    setTasks(t => [...t, { id: Date.now(), title: newTaskTitle.trim(), completed: false, priority: newTaskPriority }])
    store.showSnackbar({ message: `Task "${newTaskTitle.trim()}" added`, type: 'success', action: 'OK' })
    setNewTaskTitle(''); setNewTaskPriority('medium'); setDialogOpen(false)
  }
  const refreshData = () => {
    setStats(s => ({ cpu: Math.floor(Math.random() * 100), memory: Math.floor(Math.random() * 100), disk: Math.floor(Math.random() * 100), uptime: s.uptime }))
    store.showSnackbar({ message: 'Dashboard data refreshed', type: 'info', action: 'OK' })
  }

  return (
    <div className="gridui-panel">
      <div className="gridui-panel-body">

        <div className="gridui-dashboard-grid">
          {/* Stats Card */}
          <div className="gridui-card">
            <div className="gridui-card-header">
              <span>💻</span><h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>System Stats</h3>
            </div>
            <div className="gridui-card-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {(['cpu','memory','disk','uptime'] as const).map(k => (
                  <div key={k} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <div style={{ fontSize: 11, color: 'var(--grid-text-secondary, #8b949e)', textTransform: 'uppercase', letterSpacing: 0.5 }}>{k === 'uptime' ? 'Uptime' : k}</div>
                    <div className="gridui-stat-value">{k === 'uptime' ? stats.uptime : `${stats[k]}%`}</div>
                    {k !== 'uptime' && (
                      <div className="gridui-stat-bar">
                        <div className="gridui-stat-bar-fill" style={{ background: barColor(stats[k]), width: `${stats[k]}%` }}></div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
          {/* Tasks Card */}
          <div className="gridui-card">
            <div className="gridui-card-header">
              <span>✅</span><h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>Tasks</h3>
              <button className="gridui-btn gridui-btn--small" onClick={() => setDialogOpen(true)}><span>+</span> Add</button>
            </div>
            <div className="gridui-card-body">
              {tasks.map(task => (
                <div key={task.id} className="gridui-task-row">
                  <label className="gridui-task-label">
                    <input type="checkbox" checked={task.completed} onChange={() => toggleTask(task.id)} style={{ accentColor: '#58a6ff' }} />
                    <span className={`gridui-task-text ${task.completed ? 'gridui-task-text--done' : ''}`}>{task.title}</span>
                  </label>
                  <span className={`gridui-tag gridui-tag--${task.priority}`}>{task.priority}</span>
                </div>
              ))}
              {tasks.length === 0 && (
                <div className="gridui-empty" style={{ padding: 24 }}>
                  <span>📥</span><span>No tasks yet</span>
                </div>
              )}
            </div>
          </div>
          {/* Activity Card */}
          <div className="gridui-card">
            <div className="gridui-card-header">
              <span>📰</span><h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--grid-text-secondary, #8b949e)', flex: 1 }}>Activity</h3>
            </div>
            <div className="gridui-card-body">
              {activity.map((item, idx) => (
                <div key={idx} className="gridui-activity-row">
                  <span className="gridui-activity-date">{item.date}</span>
                  <span className="gridui-activity-title">{item.title}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* Add Task Dialog */}
        {dialogOpen && (
          <div className="gridui-dialog-overlay" onClick={() => setDialogOpen(false)}>
            <div className="gridui-dialog" onClick={e => e.stopPropagation()}>
              <h3 className="gridui-dialog-title">Add Task</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
                <label className="gridui-settings-label">Title</label>
                <input value={newTaskTitle} onChange={e => setNewTaskTitle(e.target.value)} placeholder="Enter task title..." className="gridui-input" />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 16 }}>
                <label className="gridui-settings-label">Priority</label>
                <div style={{ display: 'flex', gap: 4 }}>
                  {(['low','medium','high'] as const).map(p => (
                    <button key={p} onClick={() => setNewTaskPriority(p)} className={`gridui-palette-btn ${newTaskPriority === p ? 'gridui-palette-btn--active' : 'gridui-palette-btn--inactive'}`} style={{ flex: 1, textTransform: 'capitalize' }}>{p}</button>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button className="gridui-btn" onClick={() => setDialogOpen(false)}>Cancel</button>
                <button className="gridui-btn gridui-btn--primary" onClick={addTask}>Add Task</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
