/* ═══════════════════════════════════════════════════════════════════
   RulesPanel — Developer Cline Rules Viewer
   Displays .clinerules content from the project root, fetched
   via the backend API or direct file read.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'

const SNACKBAR_API = 'http://localhost:8484'

// Default rules fallback — mirrors .clinerules content from project root
const DEFAULT_RULES = `# Cline Rules - uCore Baseline

Use this repository in local-first, auditable mode.

## Operating Principles

1. Prefer safe, reversible changes and keep diffs small.
2. Keep durable workflow state in .tasker/ Markdown files.
3. Treat Cline Kanban as orchestration UI, not source of truth.
4. Keep MCP integrations localhost-only by default.
5. Preserve Git history clarity with focused, test-backed changes.

## Workflow Defaults

1. For new work, start from a Kanban card linked to a .tasker item.
2. Use isolated worktrees/branches for card execution when available.
3. Validate with targeted tests before proposing merges.
4. Report blockers with concrete next actions.

## MCP Usage

1. Prefer the uCore MCP server for skills and knowledge access.
2. Verify MCP health before relying on tools.
3. Do not broaden network exposure of MCP services without explicit opt-in.

## Cost-Aware Routing

1. Simple tasks: local/free model when practical.
2. Medium tasks: Codex/Roundtable tier.
3. Complex tasks: premium reasoning tier only when justified.`

export function RulesPanel() {
  const [rules, setRules] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [saveStatus, setSaveStatus] = useState<string | null>(null)

  useEffect(() => {
    async function fetchRules() {
      setLoading(true)
      setError(null)
      try {
        // Try fetching via developer API
        const res = await fetch(`${SNACKBAR_API}/api/developer/repos/ucore/file-preview?path=.clinerules`, {
          signal: AbortSignal.timeout(3000),
        })
        if (res.ok) {
          const data = await res.json()
          setRules(data.content || DEFAULT_RULES)
          return
        }
      } catch { /* fall through to fallback */ }

      // Try direct fetch of .clinerules (works in dev with vite)
      try {
        const res = await fetch('/.clinerules', { signal: AbortSignal.timeout(3000) })
        if (res.ok) {
          const text = await res.text()
          setRules(text)
          return
        }
      } catch { /* fallthrough */ }

      // Fallback to hardcoded default
      setRules(DEFAULT_RULES)
      setError('Could not fetch live .clinerules — showing bundled default')
      setLoading(false)
    }
    void fetchRules()
  }, [])

  const handleEdit = () => {
    setEditContent(rules || '')
    setEditing(true)
  }

  const handleCancel = () => {
    setEditing(false)
    setEditContent('')
  }

  const handleSave = () => {
    // Persist to localStorage so it survives
    localStorage.setItem('ucore-clinerules-override', editContent)
    setRules(editContent)
    setEditing(false)
    setSaveStatus('Saved locally (requires sync to backend to persist to file)')
    setTimeout(() => setSaveStatus(null), 3000)
  }

  // Check for local override
  useEffect(() => {
    const overridden = localStorage.getItem('ucore-clinerules-override')
    if (overridden && rules) {
      // If we have rules loaded and an override exists, use override
      setRules(overridden)
    }
  }, [rules])

  if (loading && !rules) {
    return (
      <div className="developer-panel">
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Cline Rules</h3>
          <span className="developer-panel-count">.clinerules</span>
        </div>
        <div className="developer-panel-count">Loading rules...</div>
      </div>
    )
  }

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">
          <Icon name="gavel" size={16} /> Cline Rules
        </h3>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span className="developer-panel-count">.clinerules</span>
          {!editing && (
            <button className="developer-repo-btn" onClick={handleEdit}>
              <Icon name="edit" size={14} /> Edit
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={{
          padding: '8px 12px',
          background: 'rgba(210,153,34,0.1)',
          color: '#d29922',
          borderRadius: 6,
          fontSize: 12,
          marginBottom: 8,
        }}>
          <Icon name="warning" size={14} /> {error}
        </div>
      )}

      {saveStatus && (
        <div style={{
          padding: '8px 12px',
          background: 'rgba(63,185,80,0.15)',
          color: '#3fb950',
          borderRadius: 6,
          fontSize: 12,
          marginBottom: 8,
        }}>
          {saveStatus}
        </div>
      )}

      {editing ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
          <textarea
            className="developer-preview-editor"
            style={{ flex: 1, minHeight: 400, fontFamily: 'monospace', fontSize: 12 }}
            value={editContent}
            onChange={e => setEditContent(e.target.value)}
            spellCheck={false}
          />
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="developer-skill-run-btn" onClick={handleSave}>
              <Icon name="save" size={14} /> Save Local
            </button>
            <button className="developer-repo-btn" onClick={handleCancel}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div style={{
          flex: 1,
          overflow: 'auto',
          background: 'var(--pico-background-color, #0d1117)',
          border: '1px solid var(--pico-border-color, #30363d)',
          borderRadius: 8,
        }}>
          <pre style={{
            margin: 0,
            padding: 16,
            fontFamily: "'C64 User Mono v1.0', 'SFMono-Regular', Consolas, monospace",
            fontSize: 12,
            lineHeight: 1.55,
            color: 'var(--pico-color, #c9d1d9)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}>
            <code>{rules}</code>
          </pre>
        </div>
      )}
    </div>
  )
}