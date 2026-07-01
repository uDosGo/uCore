/* ═══════════════════════════════════════════════════════════════════
   TaskDetailDrawer — Task Detail & Management Component
   ═══════════════════════════════════════════════════════════════════
   Reusable task detail drawer with full metadata editing
   ═══════════════════════════════════════════════════════════════════ */
import React, { useEffect, useState, useCallback } from 'react'

export type TaskDetailData = {
  id: string
  title: string
  description?: string
  status: 'todo' | 'in-progress' | 'done' | 'blocked'
  priority: 'low' | 'medium' | 'high' | 'critical'
  board?: string
  assignee?: string
  dueDate?: string
  tags?: string[]
  metadata?: Record<string, any>
}

export interface TaskDetailDrawerProps {
  task: TaskDetailData | null
  onClose: () => void
  onUpdate?: (task: TaskDetailData) => Promise<void>
  readOnly?: boolean
}

const SNACKBAR_API = 'http://localhost:8484'

export const TaskDetailDrawer: React.FC<TaskDetailDrawerProps> = ({
  task,
  onClose,
  onUpdate,
  readOnly = false,
}) => {
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formData, setFormData] = useState<TaskDetailData | null>(task)

  useEffect(() => {
    setFormData(task)
    setEditing(false)
  }, [task])

  const handleSave = useCallback(async () => {
    if (!formData) return
    setSaving(true)
    try {
      if (onUpdate) {
        await onUpdate(formData)
      } else {
        // Call backend API
        const res = await fetch(`${SNACKBAR_API}/api/workflows/task/${formData.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
          signal: AbortSignal.timeout(5000),
        })
        if (!res.ok) throw new Error(`Failed to save task`)
      }
      setEditing(false)
    } catch (err) {
      alert(`Error saving task: ${err}`)
    } finally {
      setSaving(false)
    }
  }, [formData, onUpdate])

  if (!task) return null

  return (
    <div style={{
      position: 'fixed',
      right: 0,
      top: 0,
      width: '400px',
      height: '100vh',
      background: 'var(--pico-card-background-color, #0d1117)',
      borderLeft: '1px solid var(--pico-border-color, #30363d)',
      boxShadow: '-4px 0 12px rgba(0,0,0,0.3)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      animation: 'slideInRight 0.3s ease',
    }}>
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>

      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid var(--pico-border-color, #30363d)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Task Details</h3>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '1.2rem',
            cursor: 'pointer',
            color: 'var(--pico-text-color)',
          }}
        >
          ✕
        </button>
      </div>

      {/* Content */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}>
        {/* Title */}
        <div>
          <label style={{ fontSize: '0.85rem', fontWeight: 'bold', display: 'block', marginBottom: 4 }}>
            Title
          </label>
          {editing ? (
            <input
              type="text"
              value={formData?.title || ''}
              onChange={e => setFormData(prev => prev ? { ...prev, title: e.target.value } : null)}
              style={{ width: '100%', padding: '6px 8px' }}
            />
          ) : (
            <div style={{ padding: '6px 8px', background: 'rgba(88, 166, 255, 0.05)', borderRadius: 4 }}>
              {formData?.title}
            </div>
          )}
        </div>

        {/* Status */}
        <div>
          <label style={{ fontSize: '0.85rem', fontWeight: 'bold', display: 'block', marginBottom: 4 }}>
            Status
          </label>
          {editing ? (
            <select
              value={formData?.status || 'todo'}
              onChange={e => setFormData(prev => prev ? { ...prev, status: e.target.value as any } : null)}
              style={{ width: '100%', padding: '6px 8px' }}
            >
              <option value="todo">Todo</option>
              <option value="in-progress">In Progress</option>
              <option value="done">Done</option>
              <option value="blocked">Blocked</option>
            </select>
          ) : (
            <div style={{
              padding: '6px 8px',
              borderRadius: 4,
              fontSize: '0.85rem',
              background: formData?.status === 'done' ? 'rgba(63, 185, 80, 0.1)' : formData?.status === 'in-progress' ? 'rgba(88, 166, 255, 0.1)' : 'rgba(200, 200, 200, 0.1)',
              color: formData?.status === 'done' ? '#3fb950' : formData?.status === 'in-progress' ? '#58a6ff' : 'inherit',
            }}>
              {formData?.status || 'todo'}
            </div>
          )}
        </div>

        {/* Priority */}
        <div>
          <label style={{ fontSize: '0.85rem', fontWeight: 'bold', display: 'block', marginBottom: 4 }}>
            Priority
          </label>
          {editing ? (
            <select
              value={formData?.priority || 'medium'}
              onChange={e => setFormData(prev => prev ? { ...prev, priority: e.target.value as any } : null)}
              style={{ width: '100%', padding: '6px 8px' }}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          ) : (
            <div style={{ padding: '6px 8px' }}>
              {formData?.priority || 'medium'}
            </div>
          )}
        </div>

        {/* Board */}
        <div>
          <label style={{ fontSize: '0.85rem', fontWeight: 'bold', display: 'block', marginBottom: 4 }}>
            Board
          </label>
          <div style={{ padding: '6px 8px', fontSize: '0.85rem', color: 'var(--pico-muted-color, #8b949e)' }}>
            {formData?.board || '(no board)'}
          </div>
        </div>

        {/* Assignee */}
        <div>
          <label style={{ fontSize: '0.85rem', fontWeight: 'bold', display: 'block', marginBottom: 4 }}>
            Assignee
          </label>
          {editing ? (
            <input
              type="text"
              placeholder="Name or email"
              value={formData?.assignee || ''}
              onChange={e => setFormData(prev => prev ? { ...prev, assignee: e.target.value } : null)}
              style={{ width: '100%', padding: '6px 8px' }}
            />
          ) : (
            <div style={{ padding: '6px 8px', fontSize: '0.85rem', color: 'var(--pico-muted-color, #8b949e)' }}>
              {formData?.assignee || '(unassigned)'}
            </div>
          )}
        </div>

        {/* Due Date */}
        <div>
          <label style={{ fontSize: '0.85rem', fontWeight: 'bold', display: 'block', marginBottom: 4 }}>
            Due Date
          </label>
          {editing ? (
            <input
              type="date"
              value={formData?.dueDate || ''}
              onChange={e => setFormData(prev => prev ? { ...prev, dueDate: e.target.value } : null)}
              style={{ width: '100%', padding: '6px 8px' }}
            />
          ) : (
            <div style={{ padding: '6px 8px', fontSize: '0.85rem', color: 'var(--pico-muted-color, #8b949e)' }}>
              {formData?.dueDate ? new Date(formData.dueDate).toLocaleDateString() : '(no due date)'}
            </div>
          )}
        </div>

        {/* Description */}
        <div>
          <label style={{ fontSize: '0.85rem', fontWeight: 'bold', display: 'block', marginBottom: 4 }}>
            Description
          </label>
          {editing ? (
            <textarea
              value={formData?.description || ''}
              onChange={e => setFormData(prev => prev ? { ...prev, description: e.target.value } : null)}
              style={{ width: '100%', height: 100, padding: '6px 8px', fontFamily: 'monospace', fontSize: '0.8rem' }}
              placeholder="Markdown supported"
            />
          ) : (
            <pre style={{
              padding: '6px 8px',
              background: 'rgba(200, 200, 200, 0.05)',
              borderRadius: 4,
              fontSize: '0.8rem',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              maxHeight: 150,
              overflowY: 'auto',
            }}>
              {formData?.description || '(no description)'}
            </pre>
          )}
        </div>

        {/* Tags */}
        {formData?.tags && formData.tags.length > 0 && (
          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 'bold', display: 'block', marginBottom: 4 }}>
              Tags
            </label>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {formData.tags.map(tag => (
                <span
                  key={tag}
                  style={{
                    fontSize: '0.75rem',
                    padding: '2px 6px',
                    background: 'rgba(88, 166, 255, 0.1)',
                    color: '#58a6ff',
                    borderRadius: 3,
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--pico-border-color, #30363d)',
        display: 'flex',
        gap: 8,
      }}>
        {!readOnly && (
          <>
            {editing ? (
              <>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="primary"
                  style={{ flex: 1 }}
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button
                  onClick={() => { setEditing(false); setFormData(task) }}
                  className="secondary"
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setEditing(true)}
                  className="primary"
                  style={{ flex: 1 }}
                >
                  Edit
                </button>
                <button onClick={onClose} className="secondary">
                  Close
                </button>
              </>
            )}
          </>
        )}
        {readOnly && (
          <button onClick={onClose} className="primary" style={{ flex: 1 }}>
            Close
          </button>
        )}
      </div>
    </div>
  )
}

export default TaskDetailDrawer
