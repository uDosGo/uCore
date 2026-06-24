/* ═══════════════════════════════════════════════════════════════════
   DeveloperSurface — USX Schema v3.1 Developer Lane
   ═══════════════════════════════════════════════════════════════════
   Developer development environment surface with dev-mode chat,
   repo browser, skill runner, and code review panels.
   Project Type: Technical (TC) | Autonomy Level: L4 (Delegator)
   Binder: ⚙️ Technical/Developer | Tags: #developer #development #ide
   Wiki: [[Developer Hub]] | Backlinks: [[Skill Runner]], [[Repo Browser]]
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { GlobalToolbar } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import TaskDetailDrawer, { TaskDetailData } from '../../components/TaskDetailDrawer'
import VaultSidebar, { Binder, SidebarNavItem, VaultFile } from '../../components/VaultSidebar'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import { ModelsPanel } from './ModelsPanel'
import { AgentsPanel } from './AgentsPanel'
import { KanbanSurface } from './KanbanSurface'
import { GridSmithTab } from './GridSmithTab'
import { SkillsPanel } from './SkillsPanel'
import { USXDefaultsPanel } from './USXDefaultsPanel'
import { RulesPanel } from './RulesPanel'
import { SurfacesPanel } from './SurfacesPanel'
import TypographySettingsPanel from './TypographySettingsPanel'

// ─── Types ──────────────────────────────────────────────────────────
type DeveloperTab = 'models' | 'agents' | 'kanban' | 'repos' | 'review' | 'settings' | 'gridsmith' | 'skills' | 'usx' | 'rules' | 'surfaces'

interface WorkflowRun {
  run_id: string
  workflow_id: string
  workflow_name: string
  started_at: string
  finished_at: string
  status: string
  steps?: Array<{ step_index: number; step_name: string; status: string }>
}

interface RepoInfo {
  name: string
  path: string
  branch: string
  status: string
  changes: number
  remote: string
  fileCount?: number
}

interface ReviewEntry {
  file: string
  status: 'modified' | 'added' | 'deleted'
  lines: number
  summary: string
}

interface FilePreview {
  repo: string
  path: string
  content: string
  type: string
  size: number
  truncated: boolean
  updatedAt: string
}

interface FileDiff {
  repo: string
  path: string
  status: 'modified' | 'added' | 'deleted'
  diff: string
  hasDiff: boolean
}

type PreviewMode = 'file' | 'diff' | 'edit'

// ─── Developer Chat Prompts ─────────────────────────────────────────
const DEV_PROMPTS = [
  { id: 'review-code', icon: 'code', label: 'Review my code', context: 'Code quality check' },
  { id: 'debug', icon: 'bug_report', label: 'Debug an issue', context: 'Fix a bug' },
  { id: 'refactor', icon: 'construction', label: 'Refactor a module', context: 'Improve structure' },
  { id: 'deploy', icon: 'rocket_launch', label: 'Deploy a service', context: 'Ship to production' },
  { id: 'test', icon: 'science', label: 'Write tests', context: 'Add test coverage' },
  { id: 'docs', icon: 'description', label: 'Generate docs', context: 'Document the code' },
]

// ─── Sample Repos ───────────────────────────────────────────────────
const SAMPLE_REPOS: RepoInfo[] = [
  { name: 'Developer', path: '~/Code/Developer', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:OkAgentDigital/Developer.git' },
  { name: 'uConnect', path: '~/Code/uConnect', branch: 'main', status: 'modified', changes: 3, remote: 'origin: git@github.com:uDosGo/uConnect.git' },
  { name: 'uServer', path: '~/Code/uServer', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uServer.git' },
  { name: 'uPlace', path: '~/Code/uPlace', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uPlace.git' },
  { name: 'uCode1', path: '~/Code/uCode1', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uCode1.git' },
  { name: 'uVector', path: '~/Code/uVector', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uVector.git' },
  { name: 'Groovebox', path: '~/Code/Groovebox', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/Groovebox.git' },
  { name: 'SonicScrewdriver', path: '~/Code/SonicScrewdriver', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/SonicScrewdriver.git' },

]

const SNACKBAR_API = 'http://localhost:8484'
const DEVELOPER_TABS: DeveloperTab[] = ['models', 'agents', 'skills', 'usx', 'surfaces', 'kanban', 'gridsmith', 'repos', 'review', 'rules', 'settings']

// ─── Sample Review Entries ──────────────────────────────────────────
const SAMPLE_REVIEWS: ReviewEntry[] = [
  { file: 'ui/src/surfaces/assistui/AssistUISurface.tsx', status: 'modified', lines: 245, summary: 'Full assistant-ui redesign with agent switcher, prompt cards, prose markdown' },
  { file: 'ui/src/surfaces/browserui/BrowserUISurface.tsx', status: 'modified', lines: 156, summary: 'Centered search bar + kanban-style card stacks' },
  { file: 'ui/src/styles/gridui.css', status: 'modified', lines: 312, summary: 'Added agent switcher, prompt cards, prose markdown, card stack CSS classes' },
  { file: 'snackbar/server.py', status: 'modified', lines: 45, summary: 'Added /api/chat/prompts endpoint for dynamic prompt cards' },
  { file: 'CHANGELOG.md', status: 'modified', lines: 12, summary: 'Updated with latest changes' },
]

// ─── Simple Diff Viewer ─────────────────────────────────────────────
function parseSimpleDiff(diffText: string): Array<{ type: 'add' | 'del' | 'ctx'; lineNumOld: string; lineNumNew: string; content: string }> {
  const lines = diffText.split('\n')
  const result: Array<{ type: 'add' | 'del' | 'ctx'; lineNumOld: string; lineNumNew: string; content: string }> = []
  let oldLine = 0
  let newLine = 0

  for (const line of lines) {
    if (line.startsWith('@@')) {
      const match = line.match(/@@ -(\d+),?\d* \+(\d+),?\d* @@/)
      if (match) {
        oldLine = parseInt(match[1], 10) - 1
        newLine = parseInt(match[2], 10) - 1
      }
      result.push({ type: 'ctx', lineNumOld: '…', lineNumNew: '…', content: line })
      continue
    }
    if (line.startsWith('+')) {
      newLine++
      result.push({ type: 'add', lineNumOld: '', lineNumNew: String(newLine), content: line.slice(1) })
    } else if (line.startsWith('-')) {
      oldLine++
      result.push({ type: 'del', lineNumOld: String(oldLine), lineNumNew: '', content: line.slice(1) })
    } else if (line.startsWith(' ')) {
      oldLine++
      newLine++
      result.push({ type: 'ctx', lineNumOld: String(oldLine), lineNumNew: String(newLine), content: line.slice(1) })
    } else {
      // header or metadata line
      result.push({ type: 'ctx', lineNumOld: '', lineNumNew: '', content: line })
    }
  }
  return result
}

function SimpleDiffViewer({ diff }: { diff: FileDiff | null }) {
  if (!diff || !diff.hasDiff || !diff.diff) {
    return <div className="developer-preview-empty">No diff available for this file.</div>
  }

  const parsed = parseSimpleDiff(diff.diff)
  const added = parsed.filter(l => l.type === 'add').length
  const removed = parsed.filter(l => l.type === 'del').length

  return (
    <div className="diff-editor-simple">
      <div className="diff-editor-simple-toolbar">
        <span className="diff-editor-simple-label">{diff.repo}</span>
        <div className="diff-editor-simple-actions">
          <span style={{ color: '#3fb950', fontSize: 11 }}>+{added}</span>
          <span style={{ color: '#f85149', fontSize: 11 }}>-{removed}</span>
        </div>
      </div>
      <div className="diff-editor-simple-body">
        <div className="diff-editor-simple-unified">
          {parsed.map((line, i) => (
            <div key={i} className={`diff-editor-simple-unified-line`}
                 style={{ background: line.type === 'add' ? 'rgba(63,185,80,0.12)' : line.type === 'del' ? 'rgba(248,81,73,0.12)' : 'transparent' }}>
              <span className="diff-editor-simple-unified-nums">
                {line.lineNumOld}{line.lineNumOld && line.lineNumNew ? ',' : ''}{line.lineNumNew}
              </span>
              <span className="diff-editor-simple-unified-marker"
                    style={{ color: line.type === 'add' ? '#3fb950' : line.type === 'del' ? '#f85149' : '#8b949e' }}>
                {line.type === 'add' ? '+' : line.type === 'del' ? '-' : ' '}
              </span>
              <span className="diff-editor-simple-unified-content"
                    style={{ color: line.type === 'add' ? '#3fb950' : line.type === 'del' ? '#f85149' : 'var(--pico-color, #c9d1d9)' }}>
                {line.content}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Prose Markdown Renderer ────────────────────────────────────────
function renderProseMarkdown(text: string): string {
  // Escape HTML
  let html = text
    .replace(/&/g, '&')
    .replace(/</g, '<')
    .replace(/>/g, '>')

  // Code blocks (fenced)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const langClass = lang ? ` class="language-${lang}"` : ''
    return `<pre><code${langClass}>${code.trim()}</code></pre>`
  })

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')

  // Italic
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')

  // Strikethrough
  html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>')

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')

  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr>')

  // Blockquotes
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')

  // Unordered lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => {
    if (!match.startsWith('<ul>')) return '<ol>' + match + '</ol>'
    return match
  })

  // Headings
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // Paragraphs (double newlines)
  html = html.replace(/\n\n/g, '</p><p>')
  html = '<p>' + html + '</p>'

  // Clean up nested paragraphs inside lists
  html = html.replace(/<li><p>/g, '<li>')
  html = html.replace(/<\/p><\/li>/g, '</li>')
  html = html.replace(/<p><ul>/g, '<ul>')
  html = html.replace(/<\/ul><\/p>/g, '</ul>')
  html = html.replace(/<p><ol>/g, '<ol>')
  html = html.replace(/<\/ol><\/p>/g, '</ol>')
  html = html.replace(/<p><blockquote>/g, '<blockquote>')
  html = html.replace(/<\/blockquote><\/p>/g, '</blockquote>')
  html = html.replace(/<p><hr><\/p>/g, '<hr>')
  html = html.replace(/<p><h([1-4])>/g, '<h$1>')
  html = html.replace(/<\/h([1-4])><\/p>/g, '</h$1>')
  html = html.replace(/<p><pre>/g, '<pre>')
  html = html.replace(/<\/pre><\/p>/g, '</pre>')

  return html
}

// ─── Chat Panel ─────────────────────────────────────────────────────
function ChatPanel({ messages, onMessagesChange }: { messages: { role: string; content: string }[]; onMessagesChange: (msgs: { role: string; content: string }[]) => void }) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (messages.length > 1 || loading) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading])

  const handlePrompt = (prompt: string) => {
    setInput(prompt)
    handleSend(prompt)
  }

  const handleSend = async (text?: string) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    onMessagesChange([...messages, { role: 'user', content: msg }])
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8484/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, history: messages }),
        signal: AbortSignal.timeout(10000),
      })
      const data = await res.json()
      onMessagesChange([...messages, { role: 'assistant', content: data.response || 'No response' }])
    } catch {
      // Offline fallback — echo with dev context
      onMessagesChange([...messages, {
        role: 'assistant',
        content: `🤖 **Developer Mode** — Snackbar offline.\n\n> Received: "${msg}"\n\nRunning in offline echo mode. Start the snackbar server for AI-powered responses.\n\n**Quick commands:**\n- \`/review\` — Code review\n- \`/status\` — Repo status\n- \`/skills\` — List skills\n- \`/deploy\` — Deploy service`,
      }])
    }
    setLoading(false)
  }

  return (
    <div className="developer-chat-panel">
      {/* Messages + Prompt Cards together in one scrollable area */}
      <div className="developer-chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`developer-chat-msg developer-chat-msg--${m.role}`}>
            <div className="developer-chat-msg-avatar">
              <Icon name={m.role === 'assistant' ? 'smart_toy' : 'person'} />
            </div>
            <div className="developer-chat-msg-content">
              <div
                className="developer-chat-prose"
                dangerouslySetInnerHTML={{ __html: renderProseMarkdown(m.content) }}
              />
              <span className="developer-chat-msg-time">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        {loading && (
          <div className="developer-chat-msg developer-chat-msg--assistant">
            <div className="developer-chat-msg-avatar">
              <Icon name="smart_toy" />
            </div>
            <div className="developer-chat-msg-content">
              <div className="developer-chat-loading">
                <span className="developer-chat-loading-dot" />
                <span className="developer-chat-loading-dot" />
                <span className="developer-chat-loading-dot" />
              </div>
            </div>
          </div>
        )}

        {/* Prompt Cards — only show with intro, wrapping layout */}
        {messages.length <= 1 && (
          <div className="developer-chat-prompt-row">
            {DEV_PROMPTS.map(p => (
              <button
                key={p.id}
                className="developer-chat-prompt-card"
                onClick={() => handlePrompt(p.label)}
              >
                <Icon name={p.icon} className="developer-chat-prompt-icon" />
                <span className="developer-chat-prompt-label">{p.label}</span>
                <span className="developer-chat-prompt-ctx">{p.context}</span>
              </button>
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="developer-chat-input-row">
        <input
          type="text"
          placeholder="Ask about code, review, deploy..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          disabled={loading}
        />
        <button
          className="developer-chat-send-btn"
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  )
}

// ─── Repos Panel ────────────────────────────────────────────────────
function ReposPanel({ repos, loading, onBrowseRepo }: { repos: RepoInfo[]; loading: boolean; onBrowseRepo: (repoName: string) => void }) {
  const [filter, setFilter] = useState('')

  const filtered = filter
    ? repos.filter(r => r.name.toLowerCase().includes(filter.toLowerCase()))
    : repos

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">Workspace Repositories</h3>
        <span className="developer-panel-count">{repos.length} repos</span>
      </div>

      <div className="developer-panel-search">
        <input
          className="developer-search-input"
          type="text"
          placeholder="Filter repos..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
      </div>

      <div className="developer-repo-list">
        {loading && <div className="developer-panel-count">Loading repositories...</div>}
        {filtered.map(repo => (
          <div key={repo.name} className="developer-repo-card">
            <div className="developer-repo-card-header">
              <span className="developer-repo-name">{repo.name}</span>
              <span className={`developer-repo-badge developer-repo-badge--${repo.status}`}>
                {repo.status === 'clean' ? '✓ Clean' : `⚠ ${repo.changes} changes`}
              </span>
            </div>
            <div className="developer-repo-details">
              <span className="developer-repo-branch">⎇ {repo.branch}</span>
              <span className="developer-repo-path">{repo.path}</span>
            </div>
            <div className="developer-repo-remote">{repo.remote}</div>
            <div className="developer-repo-actions">
              <button className="developer-repo-btn" title="Browse workspace files" onClick={() => onBrowseRepo(repo.name)}>Browse</button>
              <button className="developer-repo-btn" title="Pull latest">Pull</button>
              <button className="developer-repo-btn" title="View status">Status</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Review Panel ───────────────────────────────────────────────────
function ReviewPanel({
  reviews,
  loading,
  repoName,
  onPreviewFile,
  onReviewFile,
  onStageFile,
  onUnstageFile,
  stagedFiles,
}: {
  reviews: ReviewEntry[]
  loading: boolean
  repoName: string
  onPreviewFile: (path: string) => void
  onReviewFile: (path: string) => void
  onStageFile?: (path: string) => void
  onUnstageFile?: (path: string) => void
  stagedFiles?: Set<string>
}) {

  const statusIcon: Record<string, string> = {
    modified: 'edit_note',
    added: 'add_circle',
    deleted: 'delete',
  }

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">Recent Changes</h3>
        <span className="developer-panel-count">{reviews.length} files</span>
      </div>

      {repoName && (
        <div className="developer-panel-count" style={{ width: 'fit-content' }}>
          Active repo: {repoName}
        </div>
      )}

      <div className="developer-review-list">
        {loading && <div className="developer-panel-count">Loading review status...</div>}
        {!loading && reviews.length === 0 && (
          <div className="developer-panel-count">No local git changes in this repository.</div>
        )}
        {reviews.map((entry, i) => (
          <div key={i} className="developer-review-card">
            <div className="developer-review-card-header">
              <Icon name={statusIcon[entry.status]} className="developer-review-status-icon" />
              <span className={`developer-review-status developer-review-status--${entry.status}`}>
                {entry.status}
              </span>
              <span className="developer-review-lines">+{entry.lines} lines</span>
            </div>
            <div className="developer-review-file">{entry.file}</div>
            <p className="developer-review-summary">{entry.summary}</p>
            <div className="developer-review-actions">
              <button className="developer-repo-btn" onClick={() => onPreviewFile(entry.file)}>Preview</button>
              <button className="developer-repo-btn" onClick={() => onReviewFile(entry.file)}>Review</button>
              {onStageFile && !stagedFiles?.has(entry.file) && (
                <button className="developer-repo-btn" onClick={() => onStageFile(entry.file)}>Stage</button>
              )}
              {onUnstageFile && stagedFiles?.has(entry.file) && (
                <button className="developer-repo-btn" onClick={() => onUnstageFile(entry.file)}>Unstage</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function FilePreviewPanel({
  preview,
  diff,
  loading,
  diffLoading,
  repoName,
  mode,
  onModeChange,
  draftContent,
  onDraftChange,
  onSave,
  saveLoading,
  saveNotice,
  onClose,
  offsetRight,
}: {
  preview: FilePreview | null
  diff: FileDiff | null
  loading: boolean
  diffLoading: boolean
  repoName: string
  mode: PreviewMode
  onModeChange: (mode: PreviewMode) => void
  draftContent: string
  onDraftChange: (content: string) => void
  onSave: () => void
  saveLoading: boolean
  saveNotice: string | null
  onClose: () => void
  offsetRight: number
}) {
  const editDisabled = !preview || preview.truncated

  return (
    <div className="developer-preview-panel" style={{ right: offsetRight }}>
      <div className="developer-preview-header">
        <div className="developer-preview-title-wrap">
          <span className="developer-preview-title">File Preview</span>
          <span className="developer-preview-subtitle">{repoName || 'No repo selected'}</span>
        </div>
        <div className="developer-preview-actions">
          <button className={`developer-preview-toggle ${mode === 'file' ? 'active' : ''}`} onClick={() => onModeChange('file')} disabled={!preview}>File</button>
          <button className={`developer-preview-toggle ${mode === 'diff' ? 'active' : ''}`} onClick={() => onModeChange('diff')} disabled={!preview}>Diff</button>
          <button className={`developer-preview-toggle ${mode === 'edit' ? 'active' : ''}`} onClick={() => onModeChange('edit')} disabled={editDisabled}>Edit</button>
          {mode === 'edit' && (
            <button className="developer-preview-save" onClick={onSave} disabled={saveLoading || editDisabled}>
              {saveLoading ? 'Saving...' : 'Save'}
            </button>
          )}
        </div>
        <button className="usx-header-btn" onClick={onClose} title="Close preview">
          <Icon name="close" size={16} />
        </button>
      </div>
      <div className="developer-preview-meta">
        <span>{preview?.path || 'Select a file from the sidebar or review list'}</span>
        {preview && <span>{preview.type} · {preview.size} bytes</span>}
      </div>
      <div className="developer-preview-body">
        {loading || (mode === 'diff' && diffLoading) ? (
          <div className="developer-preview-empty">Loading preview...</div>
        ) : !preview ? (
          <div className="developer-preview-empty">No file selected.</div>
        ) : mode === 'edit' ? (
          <div className="developer-preview-editor-wrap">
            {preview.truncated && <div className="developer-preview-truncated">Large file previews cannot be edited safely while truncated.</div>}
            {saveNotice && <div className="developer-preview-save-notice">{saveNotice}</div>}
            <textarea
              className="developer-preview-editor"
              value={draftContent}
              onChange={e => onDraftChange(e.target.value)}
              spellCheck={false}
              disabled={preview.truncated || saveLoading}
            />
          </div>
        ) : mode === 'diff' ? (
          <SimpleDiffViewer diff={diff} />
        ) : (
          <>
            <pre className="developer-preview-code"><code>{preview.content}</code></pre>
            {saveNotice && <div className="developer-preview-save-notice">{saveNotice}</div>}
            {preview.truncated && (
              <div className="developer-preview-truncated">Preview truncated for large file.</div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
// ─── Agent Router URL ───────────────────────────────────────────────
const AGENT_ROUTER_URL = 'http://localhost:8484'
// ─── Settings Panel ─────────────────────────────────────────────────

function SettingsPanel() {
  const [settings, setSettings] = useState({
    hivemindUrl: 'http://localhost:11435',
    ollamaUrl: 'http://localhost:11434',
    snackbarUrl: 'http://localhost:8484',
    autoSync: true,
    darkMode: true,
    teletextFont: true,
    autonomyLevel: 'L4',
  })

  const handleToggle = (key: keyof typeof settings) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] as any }))
  }

  return (
    <>
      {/* Typography Settings */}
      <TypographySettingsPanel />

      {/* Service & Preferences */}
      <div className="developer-panel" style={{ marginTop: '32px' }}>
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Settings</h3>
          <span className="developer-panel-count">Configuration</span>
        </div>

        <div className="developer-settings-section">
          <h4 className="developer-settings-section-title"><Icon name="power_settings_new" /> Service Connections</h4>
          <div className="developer-settings-field">
            <label className="developer-settings-label">Hivemind URL</label>
            <input className="developer-search-input" value={settings.hivemindUrl} onChange={e => setSettings(p => ({ ...p, hivemindUrl: e.target.value }))} />
          </div>
          <div className="developer-settings-field">
            <label className="developer-settings-label">Ollama URL</label>
            <input className="developer-search-input" value={settings.ollamaUrl} onChange={e => setSettings(p => ({ ...p, ollamaUrl: e.target.value }))} />
          </div>
          <div className="developer-settings-field">
            <label className="developer-settings-label">Snackbar URL</label>
            <input className="developer-search-input" value={settings.snackbarUrl} onChange={e => setSettings(p => ({ ...p, snackbarUrl: e.target.value }))} />
          </div>
        </div>

        <div className="developer-settings-section">
          <h4 className="developer-settings-section-title"><Icon name="settings" /> Preferences</h4>
          <div className="developer-settings-toggle-row">
            <span>Auto-sync repositories</span>
            <button className={`developer-toggle ${settings.autoSync ? 'developer-toggle--on' : ''}`} onClick={() => handleToggle('autoSync')}>
              <span className="developer-toggle-knob" />
            </button>
          </div>
          <div className="developer-settings-toggle-row">
            <span>Dark mode</span>
            <button className={`developer-toggle ${settings.darkMode ? 'developer-toggle--on' : ''}`} onClick={() => handleToggle('darkMode')}>
              <span className="developer-toggle-knob" />
            </button>
          </div>
          <div className="developer-settings-toggle-row">
            <span>Teletext font</span>
            <button className={`developer-toggle ${settings.teletextFont ? 'developer-toggle--on' : ''}`} onClick={() => handleToggle('teletextFont')}>
              <span className="developer-toggle-knob" />
            </button>
          </div>
          <div className="developer-settings-field">
            <label className="developer-settings-label">Autonomy Level</label>
            <select className="developer-search-input" value={settings.autonomyLevel} onChange={e => setSettings(p => ({ ...p, autonomyLevel: e.target.value }))}>
              <option>L1 — Observer</option>
              <option>L2 — Assistant</option>
              <option>L3 — Collaborator</option>
              <option>L4 — Delegator</option>
              <option>L5 — Autonomous</option>
            </select>
          </div>
        </div>

        <div className="developer-settings-section">
          <h4 className="developer-settings-section-title"><Icon name="badge" /> Identity</h4>
          <div className="developer-settings-info-row">
            <span>User ID</span>
            <code className="developer-settings-code">UDOS-20260613-AC00B8</code>
          </div>
          <div className="developer-settings-info-row">
            <span>Codeword</span>
            <code className="developer-settings-code">homebase</code>
          </div>
          <div className="developer-settings-info-row">
            <span>Install ID</span>
            <code className="developer-settings-code">macbook.local-arm64-af6f24a3</code>
          </div>
        </div>
      </div>
    </>
  )
}

// ─── Main Surface ───────────────────────────────────────────────────
export default function DeveloperSurface() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sidebarOpen, setSidebarOpen, toggleSidebar } = useSurfaceShell()
  const tabState = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const raw = (params.get('tab') || 'repos').toLowerCase()
    const candidate = raw as DeveloperTab
    return {
      raw,
      selectedTab: DEVELOPER_TABS.includes(candidate) ? candidate : 'repos',
      taskId: params.get('task')?.trim() || null,
    }
  }, [location.search])
  const [activeTab, setActiveTab] = useState<DeveloperTab>(tabState.selectedTab)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([
    { role: 'assistant', content: '**Developer Assistant** ready. I can help with code review, debugging, refactoring, and deployment. What would you like to work on?' },
  ])
  const [sidebarMode, setSidebarMode] = useState<'server' | 'filepicker'>('server')
  const [repos, setRepos] = useState<RepoInfo[]>([])
  const [reposLoading, setReposLoading] = useState(true)
  const [selectedRepoId, setSelectedRepoId] = useState<string>('')
  const [repoFiles, setRepoFiles] = useState<VaultFile[]>([])
  const [repoFilesLoading, setRepoFilesLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<VaultFile | null>(null)
  const [filePreview, setFilePreview] = useState<FilePreview | null>(null)
  const [filePreviewLoading, setFilePreviewLoading] = useState(false)
  const [fileDiff, setFileDiff] = useState<FileDiff | null>(null)
  const [fileDiffLoading, setFileDiffLoading] = useState(false)
  const [previewMode, setPreviewMode] = useState<PreviewMode>('file')
  const [draftContent, setDraftContent] = useState('')
  const [saveLoading, setSaveLoading] = useState(false)
  const [saveNotice, setSaveNotice] = useState<string | null>(null)
  const [commitMessage, setCommitMessage] = useState('')
  const [isCommitting, setIsCommitting] = useState(false)
  const [showCommitDialog, setShowCommitDialog] = useState(false)
  const [stagedFiles, setStagedFiles] = useState<Set<string>>(new Set())
  const [reviewEntries, setReviewEntries] = useState<ReviewEntry[]>([])
  const [reviewLoading, setReviewLoading] = useState(false)
  const [routeTask, setRouteTask] = useState<TaskDetailData | null>(null)
  const [routeTaskLoading, setRouteTaskLoading] = useState(false)
  const [routeTaskError, setRouteTaskError] = useState<string | null>(null)

  useEffect(() => {
    setSidebarOpen(true)
  }, [setSidebarOpen])

  useEffect(() => {
    if (tabState.raw !== tabState.selectedTab) {
      const params = new URLSearchParams(location.search)
      params.set('tab', tabState.selectedTab)
      navigate(`/developer?${params.toString()}`, { replace: true })
    }
  }, [location.search, navigate, tabState.raw, tabState.selectedTab])

  useEffect(() => {
    setActiveTab(tabState.selectedTab)
  }, [tabState.selectedTab])

  useEffect(() => {
    let cancelled = false

    async function fetchRouteTask(taskId: string) {
      setRouteTaskLoading(true)
      setRouteTaskError(null)
      try {
        const res = await fetch(`${SNACKBAR_API}/api/workflows/task/${encodeURIComponent(taskId)}`, {
          signal: AbortSignal.timeout(5000),
        })
        if (!res.ok) throw new Error(`Task ${taskId} unavailable (${res.status})`)
        const data = await res.json()
        if (!cancelled) setRouteTask(data)
      } catch (error: any) {
        if (!cancelled) {
          setRouteTask(null)
          setRouteTaskError(error?.message || 'Unable to load task')
        }
      } finally {
        if (!cancelled) setRouteTaskLoading(false)
      }
    }

    if (tabState.taskId) {
      fetchRouteTask(tabState.taskId)
    } else {
      setRouteTask(null)
      setRouteTaskError(null)
      setRouteTaskLoading(false)
    }

    return () => {
      cancelled = true
    }
  }, [tabState.taskId])

  const closeRouteTaskDrawer = useCallback(() => {
    const params = new URLSearchParams(location.search)
    params.delete('task')
    const query = params.toString()
    navigate(`/developer${query ? `?${query}` : ''}`)
  }, [location.search, navigate])

  const updateRouteTask = useCallback(async (task: TaskDetailData) => {
    const res = await fetch(`${SNACKBAR_API}/api/workflows/task/${encodeURIComponent(task.id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task),
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) throw new Error(`Task save failed (${res.status})`)
    const updated = await res.json()
    setRouteTask(updated)
  }, [])

  const fetchRepos = useCallback(async () => {
    setReposLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/developer/repos`, { signal: AbortSignal.timeout(4000) })
      if (!res.ok) throw new Error('Developer repos unavailable')
      const data = await res.json()
      const nextRepos = (data.repos || []) as RepoInfo[]
      setRepos(nextRepos)
      setSelectedRepoId(prev => prev || nextRepos[0]?.name || '')
    } catch {
      setRepos(SAMPLE_REPOS)
      setSelectedRepoId(prev => prev || SAMPLE_REPOS[0]?.name || '')
    } finally {
      setReposLoading(false)
    }
  }, [])

  const fetchRepoFiles = useCallback(async (repoName: string) => {
    if (!repoName) {
      setRepoFiles([])
      return
    }
    setRepoFilesLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/developer/repos/${encodeURIComponent(repoName)}/files`, {
        signal: AbortSignal.timeout(4000),
      })
      if (!res.ok) throw new Error('Developer files unavailable')
      const data = await res.json()
      setRepoFiles(data.files || [])
    } catch {
      setRepoFiles([])
    } finally {
      setRepoFilesLoading(false)
    }
  }, [])

  const fetchRepoReview = useCallback(async (repoName: string) => {
    if (!repoName) {
      setReviewEntries([])
      return
    }
    setReviewLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/developer/repos/${encodeURIComponent(repoName)}/review`, {
        signal: AbortSignal.timeout(4000),
      })
      if (!res.ok) throw new Error('Developer review unavailable')
      const data = await res.json()
      setReviewEntries(data.review || [])
    } catch {
      setReviewEntries(SAMPLE_REVIEWS)
    } finally {
      setReviewLoading(false)
    }
  }, [])

  const fetchFilePreview = useCallback(async (repoName: string, filePath: string) => {
    if (!repoName || !filePath) {
      setFilePreview(null)
      return
    }
    setFilePreviewLoading(true)
    try {
      const url = `${SNACKBAR_API}/api/developer/repos/${encodeURIComponent(repoName)}/file-preview?path=${encodeURIComponent(filePath)}`
      const res = await fetch(url, { signal: AbortSignal.timeout(4000) })
      if (!res.ok) throw new Error('Preview unavailable')
      const data = await res.json()
      setFilePreview(data)
    } catch {
      setFilePreview({
        repo: repoName,
        path: filePath,
        content: 'Preview unavailable from backend.',
        type: selectedFile?.type || 'file',
        size: selectedFile?.size || 0,
        truncated: false,
        updatedAt: selectedFile?.updatedAt || new Date().toISOString(),
      })
    } finally {
      setFilePreviewLoading(false)
    }
  }, [selectedFile?.size, selectedFile?.type, selectedFile?.updatedAt])

  const fetchFileDiff = useCallback(async (repoName: string, filePath: string) => {
    if (!repoName || !filePath) {
      setFileDiff(null)
      return
    }
    setFileDiffLoading(true)
    try {
      const url = `${SNACKBAR_API}/api/developer/repos/${encodeURIComponent(repoName)}/diff?path=${encodeURIComponent(filePath)}`
      const res = await fetch(url, { signal: AbortSignal.timeout(4000) })
      if (!res.ok) throw new Error('Diff unavailable')
      const data = await res.json()
      setFileDiff(data)
    } catch {
      setFileDiff({
        repo: repoName,
        path: filePath,
        status: 'modified',
        diff: '',
        hasDiff: false,
      })
    } finally {
      setFileDiffLoading(false)
    }
  }, [])

  const handleStageFile = useCallback(async (filePath: string) => {
    if (!selectedRepoId) return
    try {
      const url = `${SNACKBAR_API}/api/developer/repos/${encodeURIComponent(selectedRepoId)}/stage?path=${encodeURIComponent(filePath)}`
      const res = await fetch(url, { method: 'POST', signal: AbortSignal.timeout(3000) })
      if (!res.ok) throw new Error('Stage failed')
      setStagedFiles(prev => new Set(prev).add(filePath))
      await fetchRepoReview(selectedRepoId)
    } catch (error) {
      console.error('Stage error:', error)
    }
  }, [selectedRepoId, fetchRepoReview])

  const handleUnstageFile = useCallback(async (filePath: string) => {
    if (!selectedRepoId) return
    try {
      const url = `${SNACKBAR_API}/api/developer/repos/${encodeURIComponent(selectedRepoId)}/unstage?path=${encodeURIComponent(filePath)}`
      const res = await fetch(url, { method: 'POST', signal: AbortSignal.timeout(3000) })
      if (!res.ok) throw new Error('Unstage failed')
      setStagedFiles(prev => {
        const next = new Set(prev)
        next.delete(filePath)
        return next
      })
      await fetchRepoReview(selectedRepoId)
    } catch (error) {
      console.error('Unstage error:', error)
    }
  }, [selectedRepoId, fetchRepoReview])

  const handleCommit = useCallback(async () => {
    if (!selectedRepoId || !commitMessage.trim()) return
    setIsCommitting(true)
    try {
      const url = `${SNACKBAR_API}/api/developer/repos/${encodeURIComponent(selectedRepoId)}/commit`
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: commitMessage }),
        signal: AbortSignal.timeout(5000),
      })
      if (!res.ok) throw new Error('Commit failed')
      setCommitMessage('')
      setStagedFiles(new Set())
      setShowCommitDialog(false)
      await fetchRepoReview(selectedRepoId)
    } catch (error) {
      console.error('Commit error:', error)
    } finally {
      setIsCommitting(false)
    }
  }, [selectedRepoId, commitMessage, fetchRepoReview])

  const handleSaveFile = useCallback(async () => {
    if (!selectedRepoId || !selectedFile || !filePreview) return
    setSaveLoading(true)
    setSaveNotice(null)
    try {
      const url = `${SNACKBAR_API}/api/developer/repos/${encodeURIComponent(selectedRepoId)}/file-preview?path=${encodeURIComponent(selectedFile.name)}`
      const res = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: draftContent }),
        signal: AbortSignal.timeout(5000),
      })
      if (!res.ok) throw new Error(`Save failed (${res.status})`)
      const data = await res.json()
      setFilePreview(data)
      setDraftContent(data.content || '')
      setPreviewMode('file')
      setSaveNotice('Saved to workspace file.')
      setSelectedFile(prev => prev ? { ...prev, size: data.size, updatedAt: data.updatedAt, type: data.type } : prev)
      await Promise.all([
        fetchRepoFiles(selectedRepoId),
        fetchRepoReview(selectedRepoId),
        fetchFileDiff(selectedRepoId, selectedFile.name),
      ])
    } catch (error: any) {
      setSaveNotice(error?.message || 'Save failed')
    } finally {
      setSaveLoading(false)
    }
  }, [draftContent, fetchFileDiff, fetchRepoFiles, fetchRepoReview, filePreview, selectedFile, selectedRepoId])

  useEffect(() => {
    fetchRepos()
  }, [fetchRepos])

  useEffect(() => {
    fetchRepoFiles(selectedRepoId)
  }, [fetchRepoFiles, selectedRepoId])

  useEffect(() => {
    fetchRepoReview(selectedRepoId)
  }, [fetchRepoReview, selectedRepoId])

  useEffect(() => {
    if (!selectedFile || !selectedRepoId) {
      setFilePreview(null)
      setFileDiff(null)
      return
    }
    fetchFilePreview(selectedRepoId, selectedFile.name)
    fetchFileDiff(selectedRepoId, selectedFile.name)
  }, [fetchFileDiff, fetchFilePreview, selectedFile, selectedRepoId])

  useEffect(() => {
    setDraftContent(filePreview?.content || '')
  }, [filePreview?.content])

  const setTabAndRoute = (nextTab: DeveloperTab) => {
    setActiveTab(nextTab)
    const params = new URLSearchParams(location.search)
    params.set('tab', nextTab)
    navigate(`/developer?${params.toString()}`)
  }

  const repoBinders: Binder[] = repos.map(repo => ({
    id: repo.name,
    name: repo.name,
    path: repo.path,
    icon: 'folder',
    description: `${repo.branch} · ${repo.status}`,
    fileCount: repo.fileCount,
  }))

  const developerNavItems: SidebarNavItem[] = [
    { id: 'models', icon: 'database', label: 'Models', active: activeTab === 'models', onClick: () => setTabAndRoute('models') },
    { id: 'agents', icon: 'smart_toy', label: 'Agents', active: activeTab === 'agents', onClick: () => setTabAndRoute('agents') },
    { id: 'skills', icon: 'extension', label: 'Skills', active: activeTab === 'skills', onClick: () => setTabAndRoute('skills') },
    { id: 'usx', icon: 'palette', label: 'USX Defaults', active: activeTab === 'usx', onClick: () => setTabAndRoute('usx') },
    { id: 'surfaces', icon: 'dashboard_customize', label: 'Surfaces', active: activeTab === 'surfaces', onClick: () => setTabAndRoute('surfaces') },
    { id: 'kanban', icon: 'calendar_view_week', label: 'Kanban', active: activeTab === 'kanban', onClick: () => setTabAndRoute('kanban') },
    { id: 'gridsmith', icon: 'grid_view', label: 'GridSmith', active: activeTab === 'gridsmith', onClick: () => setTabAndRoute('gridsmith') },
    { id: 'repos', icon: 'folder_open', label: 'Repos', active: activeTab === 'repos', onClick: () => setTabAndRoute('repos') },
    { id: 'review', icon: 'visibility', label: 'Review', active: activeTab === 'review', onClick: () => setTabAndRoute('review') },
    { id: 'rules', icon: 'gavel', label: 'Rules', active: activeTab === 'rules', onClick: () => setTabAndRoute('rules') },
    { id: 'settings', icon: 'settings', label: 'Settings', active: activeTab === 'settings', onClick: () => setTabAndRoute('settings') },
  ]

  return (
    <div className="usx-surface-layout developer-surface">
      <GlobalToolbar
        onToggleSidebar={toggleSidebar}
        sidebarOpen={sidebarOpen}
        sidebarToggleLabel="Developer sidebar"
        rightExtra={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            {selectedRepoId && <span className="hub-status-badge">Repo: {selectedRepoId}</span>}
            {selectedFile && <span className="hub-status-badge">File: {selectedFile.name}</span>}
            <span style={{ fontSize: '12px', color: 'var(--pico-muted-color, #8b949e)' }}>Developer Studio · L4 Delegator</span>
          </div>
        }
      />

      <div className="usx-surface-body" style={{ position: 'relative' }}>
        <VaultSidebar
          open={sidebarOpen}
          showModeTabs
          sidebarMode={sidebarMode}
          onSidebarModeChange={setSidebarMode}
          serverNavItems={developerNavItems}
          binders={repoBinders}
          activeBinderId={selectedRepoId}
          onBinderChange={(binderId) => {
            setSelectedRepoId(binderId)
            setSelectedFile(null)
            setFilePreview(null)
            setFileDiff(null)
            setPreviewMode('file')
            setSaveNotice(null)
          }}
          files={repoFiles}
          loadingFiles={repoFilesLoading}
          searchPlaceholder="Filter workspace files"
          emptyHint={selectedRepoId ? 'No matching workspace files found' : 'Select a repository to browse files'}
          onFileSelect={setSelectedFile}
        />

        {(selectedFile || filePreviewLoading || fileDiffLoading) && (
          <FilePreviewPanel
            preview={filePreview}
            diff={fileDiff}
            loading={filePreviewLoading}
            diffLoading={fileDiffLoading}
            repoName={selectedRepoId}
            mode={previewMode}
            onModeChange={(mode) => {
              setPreviewMode(mode)
              setSaveNotice(null)
            }}
            draftContent={draftContent}
            onDraftChange={setDraftContent}
            onSave={handleSaveFile}
            saveLoading={saveLoading}
            saveNotice={saveNotice}
            onClose={() => {
              setSelectedFile(null)
              setFilePreview(null)
              setFileDiff(null)
              setSaveNotice(null)
              setPreviewMode('file')
            }}
            offsetRight={chatOpen ? 452 : 16}
          />
        )}

        {routeTaskLoading && (
          <div className="hub-status-badge" style={{ position: 'fixed', right: chatOpen ? 452 : 16, top: 72, zIndex: 1001 }}>
            Loading task…
          </div>
        )}

        {routeTaskError && (
          <div className="hub-status-badge" style={{ position: 'fixed', right: chatOpen ? 452 : 16, top: 72, zIndex: 1001, color: 'var(--pico-del-color, #f85149)' }}>
            {routeTaskError}
          </div>
        )}

        {routeTask && (
          <TaskDetailDrawer
            task={routeTask}
            onClose={closeRouteTaskDrawer}
            onUpdate={updateRouteTask}
          />
        )}

        {chatOpen && (
          <div className="developer-chat-float-panel">
            <div className="developer-chat-float-header">
              <span className="developer-chat-float-title">
                <Icon name="code" size={15} />
                Dev Chat
              </span>
              <button className="usx-header-btn" onClick={() => setChatOpen(false)} title="Close dev chat">
                <Icon name="close" size={16} />
              </button>
            </div>
            <div className="developer-chat-float-body">
              <ChatPanel messages={chatMessages} onMessagesChange={setChatMessages} />
            </div>
          </div>
        )}

        <main className="usx-surface-main">
        {activeTab === 'models' && <ModelsPanel />}
        {activeTab === 'agents' && <AgentsPanel />}
        {activeTab === 'skills' && <SkillsPanel />}
        {activeTab === 'usx' && <USXDefaultsPanel />}
        {activeTab === 'surfaces' && <SurfacesPanel />}
        {activeTab === 'kanban' && <KanbanSurface />}
        {activeTab === 'gridsmith' && <GridSmithTab />}
        {activeTab === 'repos' && <ReposPanel repos={repos} loading={reposLoading} onBrowseRepo={(repoName) => {
          setSelectedRepoId(repoName)
          setSidebarMode('filepicker')
          setSelectedFile(null)
          setFilePreview(null)
          setFileDiff(null)
          setSaveNotice(null)
        }} />}        {activeTab === 'review' && <ReviewPanel reviews={reviewEntries} loading={reviewLoading} repoName={selectedRepoId} onPreviewFile={(filePath) => {
          setSidebarMode('filepicker')
          setPreviewMode('file')
          setSaveNotice(null)
          const existing = repoFiles.find(file => file.name === filePath)
          if (existing) {
            setSelectedFile(existing)
          } else {
            setSelectedFile({
              id: Date.now(),
              name: filePath,
              type: filePath.split('.').pop() || 'file',
              size: 0,
              updatedAt: new Date().toISOString(),
              binder: selectedRepoId,
            })
          }
        }} onReviewFile={(filePath) => {
          setSidebarMode('filepicker')
          setPreviewMode('diff')
          setSaveNotice(null)
          const existing = repoFiles.find(file => file.name === filePath)
          if (existing) {
            setSelectedFile(existing)
          } else {
            setSelectedFile({
              id: Date.now(),
              name: filePath,
              type: filePath.split('.').pop() || 'file',
              size: 0,
              updatedAt: new Date().toISOString(),
              binder: selectedRepoId,
            })
          }
          fetchFileDiff(selectedRepoId, filePath)
        }} onStageFile={handleStageFile} onUnstageFile={handleUnstageFile} stagedFiles={stagedFiles} />}        {activeTab === 'rules' && <RulesPanel />}
        {activeTab === 'settings' && <SettingsPanel />}
        </main>

        <button
          className={`developer-chat-bubble ${chatOpen ? 'developer-chat-bubble--open' : ''}`}
          onClick={() => setChatOpen(prev => !prev)}
          title={chatOpen ? 'Close dev chat' : 'Open dev chat'}
          aria-label="Toggle developer chat"
        >
          <Icon name={chatOpen ? 'close' : 'chat'} size={22} />
        </button>
      </div>
    </div>
  )
}

