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

// ─── Types ──────────────────────────────────────────────────────────
type DeveloperTab = 'repos' | 'skills' | 'review' | 'workflows' | 'benchbench' | 'creative' | 'agents' | 'settings'

// ─── Agent Router Types ─────────────────────────────────────────────
interface RouterAgent {
  id: string
  name: string
  capabilities: string[]
  status: string
  load: string
  costPerTask: number
  avgLatencyMs: number
  successRate: number
}

interface RouterStats {
  totalRouted: number
  totalErrors: number
  byAgent: Record<string, number>
  byCapability: Record<string, number>
  recentRoutes: Array<{ task: string; agent: string; capability: string; timestamp: string }>
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

interface SkillInfo {
  id: string
  name: string
  description: string
  path: string
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
const DEVELOPER_TABS: DeveloperTab[] = ['repos', 'skills', 'review', 'workflows', 'benchbench', 'creative', 'agents', 'settings']

// ─── Sample Skills ──────────────────────────────────────────────────
const SAMPLE_SKILLS: SkillInfo[] = [
  { id: 'surface-repair', name: 'Surface Repair', description: 'Diagnose and repair surface configuration issues', path: 'skills/surface-repair' },
  { id: 'dep-audit', name: 'Dependency Audit', description: 'Audit project dependencies for vulnerabilities', path: 'skills/dep-audit' },
  { id: 'circular-deps', name: 'Circular Dependencies', description: 'Detect circular dependency chains', path: 'skills/circular-deps' },
  { id: 'comment-audit', name: 'Comment Audit', description: 'Audit code comments for quality and consistency', path: 'skills/comment-audit' },
  { id: 'coupling-analyzer', name: 'Coupling Analyzer', description: 'Analyze module coupling and cohesion', path: 'skills/coupling-analyzer' },
  { id: 'dead-path-detector', name: 'Dead Path Detector', description: 'Detect dead code paths and unreachable branches', path: 'skills/dead-path-detector' },
  { id: 'bundle-analyze', name: 'Bundle Analyzer', description: 'Analyze JavaScript bundle sizes', path: 'skills/bundle-analyze' },
  { id: 'changelog-check', name: 'Changelog Check', description: 'Verify changelog entries match commits', path: 'skills/changelog-check' },
]

// ─── Sample Review Entries ──────────────────────────────────────────
const SAMPLE_REVIEWS: ReviewEntry[] = [
  { file: 'ui/src/surfaces/assistui/AssistUISurface.tsx', status: 'modified', lines: 245, summary: 'Full assistant-ui redesign with agent switcher, prompt cards, prose markdown' },
  { file: 'ui/src/surfaces/browserui/BrowserUISurface.tsx', status: 'modified', lines: 156, summary: 'Centered search bar + kanban-style card stacks' },
  { file: 'ui/src/styles/gridui.css', status: 'modified', lines: 312, summary: 'Added agent switcher, prompt cards, prose markdown, card stack CSS classes' },
  { file: 'snackbar/server.py', status: 'modified', lines: 45, summary: 'Added /api/chat/prompts endpoint for dynamic prompt cards' },
  { file: 'CHANGELOG.md', status: 'modified', lines: 12, summary: 'Updated with latest changes' },
]

// ─── Syntax Highlighter ────────────────────────────────────────────
function highlightSyntax(code: string, language: string): React.ReactNode {
  // Simple syntax highlighting for common languages
  if (language === 'diff') {
    return code.split('\n').map((line, i) => {
      const color = line.startsWith('+') ? '#3fb950' : line.startsWith('-') ? '#f85149' : line.startsWith('@@') ? '#79c0ff' : 'inherit'
      return (
        <div key={i} style={{ color, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {line}
        </div>
      )
    })
  }
  // Default: no highlighting
  return code
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
function ChatPanel() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: 'assistant', content: '**Developer Assistant** ready. I can help with code review, debugging, refactoring, and deployment. What would you like to work on?' },
  ])
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
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8484/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, history: messages }),
        signal: AbortSignal.timeout(10000),
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response || 'No response' }])
    } catch {
      // Offline fallback — echo with dev context
      setMessages(prev => [...prev, {
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

// ─── Skills Panel ───────────────────────────────────────────────────
function SkillsPanel() {
  const [skills] = useState<SkillInfo[]>(SAMPLE_SKILLS)
  const [running, setRunning] = useState<string | null>(null)
  const [output, setOutput] = useState<string | null>(null)

  const handleRun = async (skillId: string) => {
    setRunning(skillId)
    setOutput(null)
    try {
      const res = await fetch(`http://localhost:8484/api/skills/${skillId}/run`, {
        method: 'POST',
        signal: AbortSignal.timeout(30000),
      })
      const data = await res.json()
      const result = data.result || data
      setOutput(
        result.status === 'completed'
          ? `✅ Completed (exit code: ${result.returncode})\n\n${result.stdout || ''}`
          : `❌ Failed (exit code: ${result.returncode})\n\n${result.stderr || result.error || ''}`
      )
    } catch (e: any) {
      setOutput(`⚠️ Error: ${e.message || 'Could not reach snackbar'}`)
    }
    setRunning(null)
  }

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">Developer Skills</h3>
        <span className="developer-panel-count">{skills.length} skills</span>
      </div>

      <div className="developer-skills-grid">
        {skills.map(skill => (
          <div key={skill.id} className="developer-skill-card">
            <div className="developer-skill-card-header">
              <span className="developer-skill-name">{skill.name}</span>
              <span className="developer-skill-id">{skill.id}</span>
            </div>
            <p className="developer-skill-desc">{skill.description}</p>
            <div className="developer-skill-path">{skill.path}</div>
            <button
              className="developer-skill-run-btn"
              onClick={() => handleRun(skill.id)}
              disabled={running === skill.id}
            >
              {running === skill.id ? 'Running...' : '▶ Run'}
            </button>
          </div>
        ))}
      </div>

      {output && (
        <div className="developer-skill-output">
          <div className="developer-skill-output-header">
            <span>Output</span>
            <button className="developer-skill-output-close" onClick={() => setOutput(null)}><Icon name="close" /></button>
          </div>
          <pre className="developer-skill-output-text">{output}</pre>
        </div>
      )}
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
          diff?.hasDiff ? (
            <pre className="developer-preview-code developer-preview-code--diff"><code>{diff.diff}</code></pre>
          ) : (
            <div className="developer-preview-empty">No diff available for this file.</div>
          )
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

// ─── Workflows Panel ────────────────────────────────────────────────

function WorkflowsPanel() {
  const [workflows] = useState([
    { id: 'build-deploy', name: 'Build & Deploy', status: 'idle', lastRun: '2h ago', steps: 4 },
    { id: 'test-suite', name: 'Test Suite', status: 'running', lastRun: 'now', steps: 12 },
    { id: 'docs-publish', name: 'Docs Publish', status: 'completed', lastRun: '30m ago', steps: 3 },
    { id: 'archive-cleanup', name: 'Archive Cleanup', status: 'failed', lastRun: '1h ago', steps: 2 },
    { id: 'skill-audit', name: 'Skill Audit', status: 'idle', lastRun: '1d ago', steps: 6 },
  ])
  const [selectedTask, setSelectedTask] = useState<TaskDetailData | null>(null)

  const statusColor: Record<string, string> = {
    idle: 'var(--pico-muted-color, #8b949e)',
    running: 'var(--pico-primary, #58a6ff)',
    completed: 'var(--pico-ins-color, #3fb950)',
    failed: 'var(--pico-del-color, #f85149)',
  }

  const handleTaskUpdate = async (task: TaskDetailData) => {
    const res = await fetch(`http://localhost:8484/api/workflows/task/${task.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task),
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    setSelectedTask(task)
  }

  const loadTaskDetails = async (taskId: string) => {
    try {
      const res = await fetch(`http://localhost:8484/api/workflows/task/${taskId}`, {
        signal: AbortSignal.timeout(5000),
      })
      if (res.ok) {
        const data = await res.json()
        setSelectedTask(data)
      } else {
        alert(`Task not found: ${taskId}`)
      }
    } catch (e) {
      alert(`Error fetching task: ${e}`)
    }
  }

  return (
    <div className="developer-panel" style={{ position: 'relative' }}>
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">Workflow Pipelines</h3>
        <span className="developer-panel-count">{workflows.length} pipelines</span>
      </div>

      <div className="developer-workflows-list">
        {workflows.map(wf => (
          <div key={wf.id} className="developer-workflow-card">
            <div className="developer-workflow-header">
              <div
                style={{ cursor: 'pointer', flex: 1 }}
                onClick={() => loadTaskDetails(wf.id)}
              >
                <span className="developer-workflow-name">{wf.name}</span>
              </div>
              <span className="developer-workflow-status" style={{ color: statusColor[wf.status] }}>
                ● {wf.status}
              </span>
            </div>
            <div className="developer-workflow-meta">
              <span className="developer-workflow-steps">{wf.steps} steps</span>
              <span className="developer-workflow-time">Last: {wf.lastRun}</span>
            </div>
            <div className="developer-workflow-progress">
              <div className="developer-workflow-progress-bar">
                <div
                  className="developer-workflow-progress-fill"
                  style={{
                    width: wf.status === 'completed' ? '100%' : wf.status === 'running' ? '60%' : '0%',
                    background: statusColor[wf.status],
                  }}
                />
              </div>
            </div>
            <div className="developer-workflow-actions">
              <button className="developer-repo-btn" disabled={wf.status === 'running'}>
                {wf.status === 'running' ? 'Running...' : '▶ Run'}
              </button>
              <button className="developer-repo-btn" onClick={() => loadTaskDetails(wf.id)}>
                Details
              </button>
              <button className="developer-repo-btn">Configure</button>
            </div>
          </div>
        ))}
      </div>

      {selectedTask && (
        <TaskDetailDrawer
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onUpdate={handleTaskUpdate}
        />
      )}
    </div>
  )
}

// ─── BenchBench Panel ───────────────────────────────────────────────
function BenchBenchPanel() {
  const [benchmarks] = useState([
    { id: 'cpu-ai', name: 'CPU AI Inference', score: 1423, unit: 'ms', trend: 'up', change: '+12%' },
    { id: 'gpu-llm', name: 'GPU LLM Tokens/s', score: 48.2, unit: 't/s', trend: 'up', change: '+5%' },
    { id: 'disk-io', name: 'Disk I/O (seq)', score: 2850, unit: 'MB/s', trend: 'down', change: '-3%' },
    { id: 'network-latency', name: 'Network Latency', score: 12, unit: 'ms', trend: 'stable', change: '0%' },
    { id: 'memory-bw', name: 'Memory Bandwidth', score: 42.1, unit: 'GB/s', trend: 'up', change: '+8%' },
  ])

  const trendIcon: Record<string, string> = { up: 'trending_up', down: 'trending_down', stable: 'trending_flat' }
  const trendColor: Record<string, string> = {
    up: 'var(--pico-ins-color, #3fb950)',
    down: 'var(--pico-del-color, #f85149)',
    stable: 'var(--pico-muted-color, #8b949e)',
  }

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">BenchBench — Performance</h3>
        <span className="developer-panel-count">{benchmarks.length} metrics</span>
      </div>

      <div className="developer-bench-grid">
        {benchmarks.map(b => (
          <div key={b.id} className="developer-bench-card">
            <div className="developer-bench-name">{b.name}</div>
            <div className="developer-bench-value">
              <span className="developer-bench-score">{b.score}</span>
              <span className="developer-bench-unit">{b.unit}</span>
            </div>
            <div className="developer-bench-trend" style={{ color: trendColor[b.trend] }}>
              <Icon name={trendIcon[b.trend]} /> {b.change}
            </div>
            <button className="developer-repo-btn">Run Benchmark</button>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Creative Panel ─────────────────────────────────────────────────
function CreativePanel() {
  const [prompt, setPrompt] = useState('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!prompt.trim() || generating) return
    setGenerating(true)
    setResult(null)
    try {
      const res = await fetch('http://localhost:8484/api/lance/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim(), style: 'teletext' }),
        signal: AbortSignal.timeout(15000),
      })
      const data = await res.json()
      setResult(data.svg || data.image || 'Generated successfully')
    } catch {
      setResult(`🎨 **Lance SVG Generator** — Snackbar offline.\n\nPrompt: "${prompt}"\n\nStart the snackbar server for AI-powered SVG generation via uVector.`)
    }
    setGenerating(false)
  }

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">Creative AI — Lance</h3>
        <span className="developer-panel-count">SVG Generation</span>
      </div>

      <div className="developer-creative-input-row">
        <input
          className="developer-search-input"
          type="text"
          placeholder="Describe an image to generate..."
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleGenerate()}
          disabled={generating}
        />
        <button
          className="developer-chat-send-btn"
          onClick={handleGenerate}
          disabled={generating || !prompt.trim()}
          style={{ flexShrink: 0 }}
        >
          {generating ? 'Generating...' : 'Generate'}
        </button>
      </div>

      <div className="developer-creative-presets">
        <span className="developer-creative-preset-label">Styles:</span>
        {['teletext', 'pixel_art', 'mono_chrome', 'full_color', 'line_art'].map(style => (
          <button key={style} className="developer-repo-btn" onClick={() => setPrompt(`Create a ${style.replace('_', ' ')} image of...`)}>
            {style.replace('_', ' ')}
          </button>
        ))}
      </div>

      {result && (
        <div className="developer-skill-output" style={{ marginTop: 16 }}>
          <div className="developer-skill-output-header">
            <span>Generated Result</span>
            <button className="developer-skill-output-close" onClick={() => setResult(null)}><Icon name="close" /></button>
          </div>
          <pre className="developer-skill-output-text">{result}</pre>
        </div>
      )}
    </div>
  )
}

// ─── Agent Router URL ───────────────────────────────────────────────
const AGENT_ROUTER_URL = 'http://localhost:8486'

// ─── Agents Panel ───────────────────────────────────────────────────
function AgentsPanel() {
  const [routerAgents, setRouterAgents] = useState<RouterAgent[]>([])
  const [routerStats, setRouterStats] = useState<RouterStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function fetchData() {
      try {
        const [agentsRes, statsRes] = await Promise.all([
          fetch(`${AGENT_ROUTER_URL}/agents`, { signal: AbortSignal.timeout(3000) }),
          fetch(`${AGENT_ROUTER_URL}/stats`, { signal: AbortSignal.timeout(3000) }),
        ])
        if (agentsRes.ok) {
          const data = await agentsRes.json()
          if (!cancelled) setRouterAgents(data.agents || [])
        }
        if (statsRes.ok) {
          const data = await statsRes.json()
          if (!cancelled) setRouterStats(data)
        }
      } catch (e: any) {
        if (!cancelled) setError(e.message || 'Agent Router unreachable')
      }
      if (!cancelled) setLoading(false)
    }
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])

  if (loading) {
    return (
      <div className="developer-panel">
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Agent Router</h3>
          <span className="developer-panel-count">Loading...</span>
        </div>
      </div>
    )
  }

  if (error || routerAgents.length === 0) {
    return (
      <div className="developer-panel">
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Agent Router</h3>
          <span className="developer-panel-count">Offline</span>
        </div>
        <div style={{ padding: 24, textAlign: 'center', color: 'var(--pico-del-color, #f85149)' }}>
          <p>⚠️ Agent Router unavailable — start agent-router on port 8486</p>
          <p style={{ fontSize: 12, marginTop: 8, color: 'var(--pico-muted-color, #8b949e)' }}>
            {error || 'No agents registered'}
          </p>
        </div>
      </div>
    )
  }

  const onlineCount = routerAgents.filter(a => a.status === 'online').length
  const totalRouted = routerStats?.totalRouted || 0
  const totalErrors = routerStats?.totalErrors || 0

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">Agent Router</h3>
        <span className="developer-panel-count">
          {onlineCount}/{routerAgents.length} online · {totalRouted} routed
        </span>
      </div>

      {/* Summary stats */}
      <div style={{ display: 'flex', gap: 16, padding: '0 16px 12px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--pico-muted-color, #8b949e)' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--pico-ins-color, #3fb950)' }} />
          {onlineCount} Online
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--pico-muted-color, #8b949e)' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--pico-del-color, #f85149)' }} />
          {routerAgents.length - onlineCount} Offline
        </div>
        <div style={{ fontSize: 12, color: 'var(--pico-muted-color, #8b949e)' }}>
          Errors: {totalErrors}
        </div>
      </div>

      {/* Agent cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 8, padding: '0 16px 16px' }}>
        {routerAgents.map(agent => {
          const loadMatch = agent.load.match(/(\d+)\/(\d+)/)
          const currentLoad = loadMatch ? parseInt(loadMatch[1]) : 0
          const maxLoad = loadMatch ? parseInt(loadMatch[2]) : 1
          const loadPct = Math.round((currentLoad / maxLoad) * 100)
          const isOnline = agent.status === 'online'
          const agentTasks = routerStats?.byAgent?.[agent.id] || 0

          return (
            <div key={agent.id} className="developer-skill-card" style={{ borderLeft: `3px solid ${isOnline ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-del-color, #f85149)'}` }}>
              <div className="developer-skill-card-header">
                <span className="developer-skill-name">{agent.name}</span>
                <span style={{ fontSize: 11, padding: '1px 6px', borderRadius: 3, background: isOnline ? 'rgba(63,185,80,0.15)' : 'rgba(248,81,73,0.15)', color: isOnline ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-del-color, #f85149)' }}>
                  {isOnline ? 'Online' : 'Offline'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8, fontSize: 11, color: 'var(--pico-muted-color, #8b949e)', marginBottom: 6, flexWrap: 'wrap' }}>
                <span>Cost: <strong>${agent.costPerTask.toFixed(4)}</strong></span>
                <span>Latency: <strong>{agent.avgLatencyMs}ms</strong></span>
                <span>Success: <strong>{(agent.successRate * 100).toFixed(0)}%</strong></span>
                <span>Tasks: <strong>{agentTasks}</strong></span>
              </div>
              {/* Load bar */}
              <div style={{ marginBottom: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--pico-muted-color, #8b949e)', marginBottom: 2 }}>
                  <span>Load</span>
                  <span>{agent.load}</span>
                </div>
                <div style={{ height: 3, background: 'var(--pico-border-color, #30363d)', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ width: `${loadPct}%`, height: '100%', background: isOnline ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-del-color, #f85149)', borderRadius: 2, transition: 'width 0.5s' }} />
                </div>
              </div>
              {/* Capabilities */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                {agent.capabilities.map(cap => (
                  <span key={cap} style={{ fontSize: 9, padding: '1px 4px', borderRadius: 2, background: 'var(--pico-card-sectioning-background-color, #1c2128)', color: 'var(--pico-primary, #58a6ff)', fontFamily: 'monospace' }}>
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Recent Routes */}
      {routerStats?.recentRoutes && routerStats.recentRoutes.length > 0 && (
        <div style={{ padding: '0 16px 16px' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--pico-muted-color, #8b949e)', marginBottom: 6 }}>Recent Routes</div>
          {routerStats.recentRoutes.slice(-5).reverse().map((route, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '3px 0', fontSize: 11, fontFamily: 'monospace', borderBottom: '1px solid var(--pico-border-color, #30363d)' }}>
              <span style={{ color: 'var(--pico-muted-color, #8b949e)', width: 60 }}>{route.timestamp?.slice(11, 19) || '--:--:--'}</span>
              <span style={{ color: 'var(--pico-primary, #58a6ff)' }}>{route.agent}</span>
              <span style={{ padding: '1px 4px', borderRadius: 2, background: 'var(--pico-card-sectioning-background-color, #1c2128)', color: 'var(--pico-primary, #58a6ff)', fontSize: 9 }}>{route.capability}</span>
              <span style={{ color: 'var(--pico-color, #c9d1d9)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{route.task}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

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
    <div className="developer-panel">
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
  )
}

// ─── Main Surface ───────────────────────────────────────────────────
export default function DeveloperSurface() {
  const location = useLocation()
  const navigate = useNavigate()
  const tabState = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const raw = (params.get('tab') || 'repos').toLowerCase()
    const candidate = raw as DeveloperTab
    return {
      raw,
      selectedTab: DEVELOPER_TABS.includes(candidate) ? candidate : 'repos',
    }
  }, [location.search])
  const [activeTab, setActiveTab] = useState<DeveloperTab>(tabState.selectedTab)
  const [chatOpen, setChatOpen] = useState(false)
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

  useEffect(() => {
    setSidebarOpen(true)
  }, [setSidebarOpen])

  useEffect(() => {
    if (tabState.raw !== tabState.selectedTab) {
      navigate(`/developer?tab=${tabState.selectedTab}`, { replace: true })
    }
  }, [navigate, tabState.raw, tabState.selectedTab])

  useEffect(() => {
    setActiveTab(tabState.selectedTab)
  }, [tabState.selectedTab])

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
    navigate(`/developer?tab=${nextTab}`)
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
    { id: 'repos', icon: 'folder_open', label: 'Repos', active: activeTab === 'repos', onClick: () => setTabAndRoute('repos') },
    { id: 'skills', icon: 'build', label: 'Skills', active: activeTab === 'skills', onClick: () => setTabAndRoute('skills') },
    { id: 'review', icon: 'visibility', label: 'Review', active: activeTab === 'review', onClick: () => setTabAndRoute('review') },
    { id: 'workflows', icon: 'play_circle', label: 'Workflows', active: activeTab === 'workflows', onClick: () => setTabAndRoute('workflows') },
    { id: 'benchbench', icon: 'bar_chart', label: 'Bench', active: activeTab === 'benchbench', onClick: () => setTabAndRoute('benchbench') },
    { id: 'creative', icon: 'palette', label: 'Creative', active: activeTab === 'creative', onClick: () => setTabAndRoute('creative') },
    { id: 'agents', icon: 'smart_toy', label: 'Agents', active: activeTab === 'agents', onClick: () => setTabAndRoute('agents') },
    { id: 'settings', icon: 'settings', label: 'Settings', active: activeTab === 'settings', onClick: () => setTabAndRoute('settings') },
  ]

  return (
    <div className="developer-surface">
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
              <ChatPanel />
            </div>
          </div>
        )}

        <main className="usx-surface-main developer-surface-main">
        {activeTab === 'repos' && <ReposPanel repos={repos} loading={reposLoading} onBrowseRepo={(repoName) => {
          setSelectedRepoId(repoName)
          setSidebarMode('filepicker')
          setSelectedFile(null)
          setFilePreview(null)
          setFileDiff(null)
          setSaveNotice(null)
        }} />}
        {activeTab === 'skills' && <SkillsPanel />}
        {activeTab === 'review' && <ReviewPanel reviews={reviewEntries} loading={reviewLoading} repoName={selectedRepoId} onPreviewFile={(filePath) => {
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
        }} onStageFile={handleStageFile} onUnstageFile={handleUnstageFile} stagedFiles={stagedFiles} />}
        {activeTab === 'workflows' && <WorkflowsPanel />}
        {activeTab === 'benchbench' && <BenchBenchPanel />}
        {activeTab === 'creative' && <CreativePanel />}
        {activeTab === 'agents' && <AgentsPanel />}
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

