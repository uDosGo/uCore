/* ═══════════════════════════════════════════════════════════════════
   StoryView — Story builder with create/delete
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState } from 'react'
import { Icon } from './Icon'

export interface StoryEntry {
  id: string
  title: string
  steps: number
  status: string
}

const INITIAL_STORIES: StoryEntry[] = [
  { id: 's1', title: 'Getting Started Walkthrough', steps: 5, status: 'draft' },
  { id: 's2', title: 'Publishing Workflow Guide', steps: 8, status: 'review' },
  { id: 's3', title: 'Vault Integration Tutorial', steps: 6, status: 'published' },
]

// ─── Story Dialog ───────────────────────────────────────────────
interface StoryDialogProps {
  onConfirm: (title: string, steps: number, status: string) => void
  onClose: () => void
}

export const StoryDialog: React.FC<StoryDialogProps> = ({ onConfirm, onClose }) => {
  const [title, setTitle] = useState('')
  const [steps, setSteps] = useState(3)
  const [status, setStatus] = useState('draft')

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 400 }}>
        <div className="modal-header">
          <h3>New Story</h3>
          <button className="btn-icon btn-sm" onClick={onClose}>
            <Icon name="close" size={16} />
          </button>
        </div>
        <div className="modal-body">
          <div className="modal-field">
            <label>Title</label>
            <input type="text" className="modal-input" value={title}
                   onChange={e => setTitle(e.target.value)}
                   placeholder="Story title..." autoFocus />
          </div>
          <div className="modal-field">
            <label>Steps</label>
            <input type="number" className="modal-input" value={steps}
                   onChange={e => setSteps(parseInt(e.target.value) || 1)}
                   min={1} max={50} />
          </div>
          <div className="modal-field">
            <label>Status</label>
            <select className="modal-select" value={status}
                    onChange={e => setStatus(e.target.value)}>
              <option value="draft">Draft</option>
              <option value="review">Review</option>
              <option value="published">Published</option>
            </select>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={() => onConfirm(title, steps, status)} disabled={!title.trim()}>Create</button>
        </div>
      </div>
    </div>
  )
}

// ─── StoryView Props ────────────────────────────────────────────
interface StoryViewProps {
  stories?: StoryEntry[]
  onNewStory?: () => void
  onDeleteStory?: (id: string) => void
}

const StoryView: React.FC<StoryViewProps> = ({
  stories = INITIAL_STORIES,
  onNewStory,
  onDeleteStory,
}) => {
  const [localStories, setLocalStories] = useState<StoryEntry[]>(stories)
  const [showDialog, setShowDialog] = useState(false)

  const effectiveStories = stories !== INITIAL_STORIES ? stories : localStories

  const handleNewStory = () => {
    if (onNewStory) {
      onNewStory()
    } else {
      setShowDialog(true)
    }
  }

  const handleDeleteStory = (id: string) => {
    if (onDeleteStory) {
      onDeleteStory(id)
    } else {
      setLocalStories(prev => prev.filter(s => s.id !== id))
    }
  }

  const confirmStory = (title: string, steps: number, status: string) => {
    const newStory: StoryEntry = {
      id: `story-${Date.now()}`,
      title: title.trim(),
      steps,
      status,
    }
    setLocalStories(prev => [...prev, newStory])
    setShowDialog(false)
  }

  return (
    <div className="story-view">
      <div className="story-header">
        <h2>Story Builder</h2>
        <p className="text-sm" style={{ color: 'var(--m3-on-surface-variant)' }}>Create step-by-step guides and walkthroughs</p>
        <button className="btn-primary btn-sm" onClick={handleNewStory} style={{ marginTop: 8 }}>
          <Icon name="add" size={14} />
          New Story
        </button>
      </div>
      <div className="story-list">
        {effectiveStories.map(story => (
          <div key={story.id} className="story-card">
            <div className="story-card-header">
              <span className="story-card-title">{story.title}</span>
              <span className={`status-badge ${story.status}`}>{story.status}</span>
            </div>
            <div className="story-card-meta">
              <span>{story.steps} steps</span>
            </div>
            <div className="story-card-actions">
              <button className="btn-icon btn-sm" onClick={() => handleDeleteStory(story.id)} title="Delete story">
                <Icon name="delete" size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {showDialog && (
        <StoryDialog onConfirm={confirmStory} onClose={() => setShowDialog(false)} />
      )}
    </div>
  )
}

export default StoryView
