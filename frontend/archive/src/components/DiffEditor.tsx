/* ═══════════════════════════════════════════════════════════════════
   DiffEditor — Shared side-by-side diff viewer with inline edit,
   approve/reject/modify controls, and diff history tracking.
   ═══════════════════════════════════════════════════════════════════
   Ported from proseui/DiffEditor.tsx — shared component for all surfaces.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Icon } from './Icon'

/* ─── Types ─────────────────────────────────────────────────────── */

export interface DiffHunk {
  oldLine: number | null
  newLine: number | null
  content: string
  type: 'add' | 'del' | 'ctx'
}

export interface DiffEntry {
  id: string
  timestamp: number
  label: string
  original: string
  modified: string
  hunks: DiffHunk[]
  status: 'pending' | 'approved' | 'rejected' | 'modified'
}

export interface DiffEditorProps {
  original: string
  modified: string
  label?: string
  onApprove?: (modified: string) => void
  onReject?: () => void
  onModify?: (content: string) => void
  onRetry?: () => void
  initialMode?: 'split' | 'unified' | 'preview'
}

/* ─── Diff Engine ────────────────────────────────────────────────── */

function computeDiff(original: string, modified: string): DiffHunk[] {
  const origLines = original.split('\n')
  const modLines = modified.split('\n')
  const hunks: DiffHunk[] = []

  // Simple LCS-based diff
  const origLen = origLines.length
  const modLen = modLines.length
  const dp: number[][] = Array.from({ length: origLen + 1 }, () => Array(modLen + 1).fill(0))

  for (let i = 1; i <= origLen; i++) {
    for (let j = 1; j <= modLen; j++) {
      if (origLines[i - 1] === modLines[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }

  // Backtrack to build diff
  let i = origLen, j = modLen
  const reverseHunks: DiffHunk[] = []
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && origLines[i - 1] === modLines[j - 1]) {
      reverseHunks.push({ oldLine: i, newLine: j, content: origLines[i - 1], type: 'ctx' })
      i--; j--
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      reverseHunks.push({ oldLine: null, newLine: j, content: modLines[j - 1], type: 'add' })
      j--
    } else {
      reverseHunks.push({ oldLine: i, newLine: null, content: origLines[i - 1], type: 'del' })
      i--
    }
  }

  return reverseHunks.reverse()
}

/* ─── Component ──────────────────────────────────────────────────── */

const DiffEditor: React.FC<DiffEditorProps> = ({
  original,
  modified,
  label = 'Diff',
  onApprove,
  onReject,
  onModify,
  onRetry,
  initialMode = 'split',
}) => {
  const [viewMode, setViewMode] = useState<'split' | 'unified' | 'preview'>(initialMode)
  const [editMode, setEditMode] = useState(false)
  const [editContent, setEditContent] = useState(modified)
  const [history, setHistory] = useState<DiffEntry[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const previewRef = useRef<HTMLDivElement>(null)

  const hunks = useCallback(() => computeDiff(original, editMode ? editContent : modified), [original, modified, editContent, editMode])

  const handleApprove = () => {
    const content = editMode ? editContent : modified
    const entry: DiffEntry = {
      id: `diff-${Date.now()}`,
      timestamp: Date.now(),
      label,
      original,
      modified: content,
      hunks: computeDiff(original, content),
      status: 'approved',
    }
    setHistory(prev => [...prev, entry])
    onApprove?.(content)
  }

  const handleReject = () => {
    const entry: DiffEntry = {
      id: `diff-${Date.now()}`,
      timestamp: Date.now(),
      label,
      original,
      modified,
      hunks: computeDiff(original, modified),
      status: 'rejected',
    }
    setHistory(prev => [...prev, entry])
    onReject?.()
  }

  const handleModify = () => {
    const entry: DiffEntry = {
      id: `diff-${Date.now()}`,
      timestamp: Date.now(),
      label,
      original,
      modified: editContent,
      hunks: computeDiff(original, editContent),
      status: 'modified',
    }
    setHistory(prev => [...prev, entry])
    onModify?.(editContent)
    setEditMode(false)
  }

  const currentHunks = hunks()

  const renderSplitView = () => (
    <div className="diff-split">
      <div className="diff-pane diff-pane--original">
        <div className="diff-pane-header">Original</div>
        <div className="diff-pane-content">
          {currentHunks.map((hunk, idx) => (
            <div key={idx} className={`diff-line diff-line--${hunk.type}`}>
              <span className="diff-line-num">{hunk.oldLine ?? ''}</span>
              <span className="diff-line-content">{hunk.content}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="diff-pane diff-pane--modified">
        <div className="diff-pane-header">Modified</div>
        <div className="diff-pane-content">
          {currentHunks.map((hunk, idx) => (
            <div key={idx} className={`diff-line diff-line--${hunk.type}`}>
              <span className="diff-line-num">{hunk.newLine ?? ''}</span>
              <span className="diff-line-content">{hunk.content}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderUnifiedView = () => (
    <div className="diff-unified">
      <div className="diff-unified-content">
        {currentHunks.map((hunk, idx) => (
          <div key={idx} className={`diff-line diff-line--${hunk.type}`}>
            <span className="diff-line-nums">
              {hunk.oldLine ?? ''},{hunk.newLine ?? ''}
            </span>
            <span className="diff-line-marker">{hunk.type === 'add' ? '+' : hunk.type === 'del' ? '-' : ' '}</span>
            <span className="diff-line-content">{hunk.content}</span>
          </div>
        ))}
      </div>
    </div>
  )

  const renderPreviewView = () => (
    <div className="diff-preview" ref={previewRef}>
      <div className="diff-preview-content" dangerouslySetInnerHTML={{ __html: (editMode ? editContent : modified).replace(/\n/g, '<br>') }} />
    </div>
  )

  return (
    <div className="diff-editor">
      {/* Toolbar */}
      <div className="diff-toolbar">
        <div className="diff-toolbar-left">
          <span className="diff-label">{label}</span>
          <div className="diff-view-modes">
            {(['split', 'unified', 'preview'] as const).map(mode => (
              <button
                key={mode}
                className={`diff-view-btn ${viewMode === mode ? 'active' : ''}`}
                onClick={() => setViewMode(mode)}
              >
                {mode === 'split' ? 'Split' : mode === 'unified' ? 'Unified' : 'Preview'}
              </button>
            ))}
          </div>
        </div>
        <div className="diff-toolbar-right">
          {editMode ? (
            <>
              <button className="diff-btn diff-btn--primary" onClick={handleModify}>
                <Icon name="save" size={14} /> Save
              </button>
              <button className="diff-btn diff-btn--secondary" onClick={() => { setEditMode(false); setEditContent(modified) }}>
                Cancel
              </button>
            </>
          ) : (
            <>
              <button className="diff-btn diff-btn--primary" onClick={handleApprove}>
                <Icon name="check" size={14} /> Approve
              </button>
              <button className="diff-btn diff-btn--danger" onClick={handleReject}>
                <Icon name="close" size={14} /> Reject
              </button>
              <button className="diff-btn diff-btn--secondary" onClick={() => setEditMode(true)}>
                <Icon name="edit" size={14} /> Edit
              </button>
              {onRetry && (
                <button className="diff-btn diff-btn--secondary" onClick={onRetry}>
                  <Icon name="refresh" size={14} /> Retry
                </button>
              )}
              {history.length > 0 && (
                <button className="diff-btn diff-btn--secondary" onClick={() => setShowHistory(v => !v)}>
                  <Icon name="history" size={14} /> History ({history.length})
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Edit mode textarea */}
      {editMode && (
        <textarea
          className="diff-edit-textarea"
          value={editContent}
          onChange={e => setEditContent(e.target.value)}
          spellCheck={false}
        />
      )}

      {/* Diff view */}
      {!editMode && (
        <div className="diff-body">
          {viewMode === 'split' && renderSplitView()}
          {viewMode === 'unified' && renderUnifiedView()}
          {viewMode === 'preview' && renderPreviewView()}
        </div>
      )}

      {/* History panel */}
      {showHistory && history.length > 0 && (
        <div className="diff-history">
          <div className="diff-history-header">
            <h4>Diff History</h4>
            <button className="diff-btn diff-btn--secondary" onClick={() => setShowHistory(false)}>
              <Icon name="close" size={14} />
            </button>
          </div>
          <div className="diff-history-list">
            {history.map(entry => (
              <div key={entry.id} className={`diff-history-item diff-history-item--${entry.status}`}>
                <div className="diff-history-item-header">
                  <span className="diff-history-item-label">{entry.label}</span>
                  <span className={`diff-history-item-status diff-history-item-status--${entry.status}`}>
                    {entry.status}
                  </span>
                  <span className="diff-history-item-time">
                    {new Date(entry.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="diff-history-item-stats">
                  {entry.hunks.filter(h => h.type === 'add').length} additions,{' '}
                  {entry.hunks.filter(h => h.type === 'del').length} deletions
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default DiffEditor
