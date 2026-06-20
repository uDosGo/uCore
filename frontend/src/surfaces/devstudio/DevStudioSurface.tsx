/* ═══════════════════════════════════════════════════════════════════
   DevStudioSurface — USX Schema v3.1 DevStudio Lane
   ═══════════════════════════════════════════════════════════════════
   DevStudio development environment surface with dev-mode chat,
   repo browser, skill runner, and code review panels.
   Project Type: Technical (TC) | Autonomy Level: L4 (Delegator)
   Binder: ⚙️ Technical/DevStudio | Tags: #devstudio #development #ide
   Wiki: [[DevStudio Hub]] | Backlinks: [[Skill Runner]], [[Repo Browser]]
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Icon } from '../../components/Icon'

// ─── Types ──────────────────────────────────────────────────────────
type DevStudioTab = 'chat' | 'repos' | 'skills' | 'review' | 'workflows' | 'benchbench' | 'creative' | 'agents' | 'settings'

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

// ─── DevStudio Chat Prompts ─────────────────────────────────────────
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
  { name: 'DevStudio', path: '~/Code/DevStudio', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:OkAgentDigital/DevStudio.git' },
  { name: 'uConnect', path: '~/Code/uConnect', branch: 'main', status: 'modified', changes: 3, remote: 'origin: git@github.com:uDosGo/uConnect.git' },
  { name: 'uServer', path: '~/Code/uServer', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uServer.git' },
  { name: 'uPlace', path: '~/Code/uPlace', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uPlace.git' },
  { name: 'uCode1', path: '~/Code/uCode1', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uCode1.git' },
  { name: 'uVector', path: '~/Code/uVector', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uVector.git' },
  { name: 'Groovebox', path: '~/Code/Groovebox', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/Groovebox.git' },
  { name: 'SonicScrewdriver', path: '~/Code/SonicScrewdriver', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/SonicScrewdriver.git' },

]

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

// ─── Tab Button ─────────────────────────────────────────────────────
function TabButton({ tab, current, icon, label, onClick }: {
  tab: DevStudioTab
  current: DevStudioTab
  icon: string
  label: string
  onClick: (t: DevStudioTab) => void
}) {
  const isActive = tab === current
  return (
    <button
      className={`devstudio-tab-btn ${isActive ? 'devstudio-tab-btn--active' : ''}`}
      onClick={() => onClick(tab)}
    >
      <Icon name={icon} />
      <span className="devstudio-tab-label">{label}</span>
    </button>
  )
}

// ─── Chat Panel ─────────────────────────────────────────────────────
function ChatPanel() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: 'assistant', content: '**DevStudio Assistant** ready. I can help with code review, debugging, refactoring, and deployment. What would you like to work on?' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
        content: `🤖 **DevStudio Mode** — Snackbar offline.\n\n> Received: "${msg}"\n\nRunning in offline echo mode. Start the snackbar server for AI-powered responses.\n\n**Quick commands:**\n- \`/review\` — Code review\n- \`/status\` — Repo status\n- \`/skills\` — List skills\n- \`/deploy\` — Deploy service`,
      }])
    }
    setLoading(false)
  }

  return (
    <div className="devstudio-chat-panel">
      {/* Prompt Cards */}
      <div className="devstudio-chat-prompt-row">
        {DEV_PROMPTS.map(p => (
          <button
            key={p.id}
            className="devstudio-chat-prompt-card"
            onClick={() => handlePrompt(p.label)}
          >
            <Icon name={p.icon} className="devstudio-chat-prompt-icon" />
            <span className="devstudio-chat-prompt-label">{p.label}</span>
            <span className="devstudio-chat-prompt-ctx">{p.context}</span>
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="devstudio-chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`devstudio-chat-msg devstudio-chat-msg--${m.role}`}>
            <div className="devstudio-chat-msg-avatar">
              <Icon name={m.role === 'assistant' ? 'smart_toy' : 'person'} />
            </div>
            <div className="devstudio-chat-msg-content">
              <div
                className="devstudio-chat-prose"
                dangerouslySetInnerHTML={{ __html: renderProseMarkdown(m.content) }}
              />
              <span className="devstudio-chat-msg-time">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        {loading && (
          <div className="devstudio-chat-msg devstudio-chat-msg--assistant">
            <div className="devstudio-chat-msg-avatar">
              <Icon name="smart_toy" />
            </div>
            <div className="devstudio-chat-msg-content">
              <div className="devstudio-chat-loading">
                <span className="devstudio-chat-loading-dot" />
                <span className="devstudio-chat-loading-dot" />
                <span className="devstudio-chat-loading-dot" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="devstudio-chat-input-row">
        <input
          type="text"
          placeholder="Ask about code, review, deploy..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          disabled={loading}
        />
        <button
          className="devstudio-chat-send-btn"
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
function ReposPanel() {
  const [repos] = useState<RepoInfo[]>(SAMPLE_REPOS)
  const [filter, setFilter] = useState('')

  const filtered = filter
    ? repos.filter(r => r.name.toLowerCase().includes(filter.toLowerCase()))
    : repos

  return (
    <div className="devstudio-panel">
      <div className="devstudio-panel-header">
        <h3 className="devstudio-panel-title">Workspace Repositories</h3>
        <span className="devstudio-panel-count">{repos.length} repos</span>
      </div>

      <div className="devstudio-panel-search">
        <input
          className="devstudio-search-input"
          type="text"
          placeholder="Filter repos..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
      </div>

      <div className="devstudio-repo-list">
        {filtered.map(repo => (
          <div key={repo.name} className="devstudio-repo-card">
            <div className="devstudio-repo-card-header">
              <span className="devstudio-repo-name">{repo.name}</span>
              <span className={`devstudio-repo-badge devstudio-repo-badge--${repo.status}`}>
                {repo.status === 'clean' ? '✓ Clean' : `⚠ ${repo.changes} changes`}
              </span>
            </div>
            <div className="devstudio-repo-details">
              <span className="devstudio-repo-branch">⎇ {repo.branch}</span>
              <span className="devstudio-repo-path">{repo.path}</span>
            </div>
            <div className="devstudio-repo-remote">{repo.remote}</div>
            <div className="devstudio-repo-actions">
              <button className="devstudio-repo-btn" title="Open in VS Code">Open</button>
              <button className="devstudio-repo-btn" title="Pull latest">Pull</button>
              <button className="devstudio-repo-btn" title="View status">Status</button>
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
    <div className="devstudio-panel">
      <div className="devstudio-panel-header">
        <h3 className="devstudio-panel-title">DevStudio Skills</h3>
        <span className="devstudio-panel-count">{skills.length} skills</span>
      </div>

      <div className="devstudio-skills-grid">
        {skills.map(skill => (
          <div key={skill.id} className="devstudio-skill-card">
            <div className="devstudio-skill-card-header">
              <span className="devstudio-skill-name">{skill.name}</span>
              <span className="devstudio-skill-id">{skill.id}</span>
            </div>
            <p className="devstudio-skill-desc">{skill.description}</p>
            <div className="devstudio-skill-path">{skill.path}</div>
            <button
              className="devstudio-skill-run-btn"
              onClick={() => handleRun(skill.id)}
              disabled={running === skill.id}
            >
              {running === skill.id ? 'Running...' : '▶ Run'}
            </button>
          </div>
        ))}
      </div>

      {output && (
        <div className="devstudio-skill-output">
          <div className="devstudio-skill-output-header">
            <span>Output</span>
            <button className="devstudio-skill-output-close" onClick={() => setOutput(null)}><Icon name="close" /></button>
          </div>
          <pre className="devstudio-skill-output-text">{output}</pre>
        </div>
      )}
    </div>
  )
}

// ─── Review Panel ───────────────────────────────────────────────────
function ReviewPanel() {
  const [reviews] = useState<ReviewEntry[]>(SAMPLE_REVIEWS)

  const statusIcon: Record<string, string> = {
    modified: 'edit_note',
    added: 'add_circle',
    deleted: 'delete',
  }

  return (
    <div className="devstudio-panel">
      <div className="devstudio-panel-header">
        <h3 className="devstudio-panel-title">Recent Changes</h3>
        <span className="devstudio-panel-count">{reviews.length} files</span>
      </div>

      <div className="devstudio-review-list">
        {reviews.map((entry, i) => (
          <div key={i} className="devstudio-review-card">
            <div className="devstudio-review-card-header">
              <Icon name={statusIcon[entry.status]} className="devstudio-review-status-icon" />
              <span className={`devstudio-review-status devstudio-review-status--${entry.status}`}>
                {entry.status}
              </span>
              <span className="devstudio-review-lines">+{entry.lines} lines</span>
            </div>
            <div className="devstudio-review-file">{entry.file}</div>
            <p className="devstudio-review-summary">{entry.summary}</p>
            <div className="devstudio-review-actions">
              <button className="devstudio-repo-btn">View Diff</button>
              <button className="devstudio-repo-btn">Review</button>
              <button className="devstudio-repo-btn">Approve</button>
            </div>
          </div>
        ))}
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

  const statusColor: Record<string, string> = {
    idle: 'var(--pico-muted-color, #8b949e)',
    running: 'var(--pico-primary, #58a6ff)',
    completed: 'var(--pico-ins-color, #3fb950)',
    failed: 'var(--pico-del-color, #f85149)',
  }

  return (
    <div className="devstudio-panel">
      <div className="devstudio-panel-header">
        <h3 className="devstudio-panel-title">Workflow Pipelines</h3>
        <span className="devstudio-panel-count">{workflows.length} pipelines</span>
      </div>

      <div className="devstudio-workflows-list">
        {workflows.map(wf => (
          <div key={wf.id} className="devstudio-workflow-card">
            <div className="devstudio-workflow-header">
              <span className="devstudio-workflow-name">{wf.name}</span>
              <span className="devstudio-workflow-status" style={{ color: statusColor[wf.status] }}>
                ● {wf.status}
              </span>
            </div>
            <div className="devstudio-workflow-meta">
              <span className="devstudio-workflow-steps">{wf.steps} steps</span>
              <span className="devstudio-workflow-time">Last: {wf.lastRun}</span>
            </div>
            <div className="devstudio-workflow-progress">
              <div className="devstudio-workflow-progress-bar">
                <div
                  className="devstudio-workflow-progress-fill"
                  style={{
                    width: wf.status === 'completed' ? '100%' : wf.status === 'running' ? '60%' : '0%',
                    background: statusColor[wf.status],
                  }}
                />
              </div>
            </div>
            <div className="devstudio-workflow-actions">
              <button className="devstudio-repo-btn" disabled={wf.status === 'running'}>
                {wf.status === 'running' ? 'Running...' : '▶ Run'}
              </button>
              <button className="devstudio-repo-btn">View Logs</button>
              <button className="devstudio-repo-btn">Configure</button>
            </div>
          </div>
        ))}
      </div>
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
    <div className="devstudio-panel">
      <div className="devstudio-panel-header">
        <h3 className="devstudio-panel-title">BenchBench — Performance</h3>
        <span className="devstudio-panel-count">{benchmarks.length} metrics</span>
      </div>

      <div className="devstudio-bench-grid">
        {benchmarks.map(b => (
          <div key={b.id} className="devstudio-bench-card">
            <div className="devstudio-bench-name">{b.name}</div>
            <div className="devstudio-bench-value">
              <span className="devstudio-bench-score">{b.score}</span>
              <span className="devstudio-bench-unit">{b.unit}</span>
            </div>
            <div className="devstudio-bench-trend" style={{ color: trendColor[b.trend] }}>
              <Icon name={trendIcon[b.trend]} /> {b.change}
            </div>
            <button className="devstudio-repo-btn">Run Benchmark</button>
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
    <div className="devstudio-panel">
      <div className="devstudio-panel-header">
        <h3 className="devstudio-panel-title">Creative AI — Lance</h3>
        <span className="devstudio-panel-count">SVG Generation</span>
      </div>

      <div className="devstudio-creative-input-row">
        <input
          className="devstudio-search-input"
          type="text"
          placeholder="Describe an image to generate..."
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleGenerate()}
          disabled={generating}
        />
        <button
          className="devstudio-chat-send-btn"
          onClick={handleGenerate}
          disabled={generating || !prompt.trim()}
          style={{ flexShrink: 0 }}
        >
          {generating ? 'Generating...' : 'Generate'}
        </button>
      </div>

      <div className="devstudio-creative-presets">
        <span className="devstudio-creative-preset-label">Styles:</span>
        {['teletext', 'pixel_art', 'mono_chrome', 'full_color', 'line_art'].map(style => (
          <button key={style} className="devstudio-repo-btn" onClick={() => setPrompt(`Create a ${style.replace('_', ' ')} image of...`)}>
            {style.replace('_', ' ')}
          </button>
        ))}
      </div>

      {result && (
        <div className="devstudio-skill-output" style={{ marginTop: 16 }}>
          <div className="devstudio-skill-output-header">
            <span>Generated Result</span>
            <button className="devstudio-skill-output-close" onClick={() => setResult(null)}><Icon name="close" /></button>
          </div>
          <pre className="devstudio-skill-output-text">{result}</pre>
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
      <div className="devstudio-panel">
        <div className="devstudio-panel-header">
          <h3 className="devstudio-panel-title">Agent Router</h3>
          <span className="devstudio-panel-count">Loading...</span>
        </div>
      </div>
    )
  }

  if (error || routerAgents.length === 0) {
    return (
      <div className="devstudio-panel">
        <div className="devstudio-panel-header">
          <h3 className="devstudio-panel-title">Agent Router</h3>
          <span className="devstudio-panel-count">Offline</span>
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
    <div className="devstudio-panel">
      <div className="devstudio-panel-header">
        <h3 className="devstudio-panel-title">Agent Router</h3>
        <span className="devstudio-panel-count">
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
            <div key={agent.id} className="devstudio-skill-card" style={{ borderLeft: `3px solid ${isOnline ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-del-color, #f85149)'}` }}>
              <div className="devstudio-skill-card-header">
                <span className="devstudio-skill-name">{agent.name}</span>
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
    <div className="devstudio-panel">
      <div className="devstudio-panel-header">
        <h3 className="devstudio-panel-title">Settings</h3>
        <span className="devstudio-panel-count">Configuration</span>
      </div>

      <div className="devstudio-settings-section">
        <h4 className="devstudio-settings-section-title"><Icon name="power_settings_new" /> Service Connections</h4>
        <div className="devstudio-settings-field">
          <label className="devstudio-settings-label">Hivemind URL</label>
          <input className="devstudio-search-input" value={settings.hivemindUrl} onChange={e => setSettings(p => ({ ...p, hivemindUrl: e.target.value }))} />
        </div>
        <div className="devstudio-settings-field">
          <label className="devstudio-settings-label">Ollama URL</label>
          <input className="devstudio-search-input" value={settings.ollamaUrl} onChange={e => setSettings(p => ({ ...p, ollamaUrl: e.target.value }))} />
        </div>
        <div className="devstudio-settings-field">
          <label className="devstudio-settings-label">Snackbar URL</label>
          <input className="devstudio-search-input" value={settings.snackbarUrl} onChange={e => setSettings(p => ({ ...p, snackbarUrl: e.target.value }))} />
        </div>
      </div>

      <div className="devstudio-settings-section">
        <h4 className="devstudio-settings-section-title"><Icon name="settings" /> Preferences</h4>
        <div className="devstudio-settings-toggle-row">
          <span>Auto-sync repositories</span>
          <button className={`devstudio-toggle ${settings.autoSync ? 'devstudio-toggle--on' : ''}`} onClick={() => handleToggle('autoSync')}>
            <span className="devstudio-toggle-knob" />
          </button>
        </div>
        <div className="devstudio-settings-toggle-row">
          <span>Dark mode</span>
          <button className={`devstudio-toggle ${settings.darkMode ? 'devstudio-toggle--on' : ''}`} onClick={() => handleToggle('darkMode')}>
            <span className="devstudio-toggle-knob" />
          </button>
        </div>
        <div className="devstudio-settings-toggle-row">
          <span>Teletext font</span>
          <button className={`devstudio-toggle ${settings.teletextFont ? 'devstudio-toggle--on' : ''}`} onClick={() => handleToggle('teletextFont')}>
            <span className="devstudio-toggle-knob" />
          </button>
        </div>
        <div className="devstudio-settings-field">
          <label className="devstudio-settings-label">Autonomy Level</label>
          <select className="devstudio-search-input" value={settings.autonomyLevel} onChange={e => setSettings(p => ({ ...p, autonomyLevel: e.target.value }))}>
            <option>L1 — Observer</option>
            <option>L2 — Assistant</option>
            <option>L3 — Collaborator</option>
            <option>L4 — Delegator</option>
            <option>L5 — Autonomous</option>
          </select>
        </div>
      </div>

      <div className="devstudio-settings-section">
        <h4 className="devstudio-settings-section-title"><Icon name="badge" /> Identity</h4>
        <div className="devstudio-settings-info-row">
          <span>User ID</span>
          <code className="devstudio-settings-code">UDOS-20260613-AC00B8</code>
        </div>
        <div className="devstudio-settings-info-row">
          <span>Codeword</span>
          <code className="devstudio-settings-code">homebase</code>
        </div>
        <div className="devstudio-settings-info-row">
          <span>Install ID</span>
          <code className="devstudio-settings-code">macbook.local-arm64-af6f24a3</code>
        </div>
      </div>
    </div>
  )
}

// ─── Main Surface ───────────────────────────────────────────────────
export default function DevStudioSurface() {
  const [tab, setTab] = useState<DevStudioTab>('chat')

  return (
    <div className="devstudio-surface">
      {/* USX v3.1 Surface Header */}
      <header className="usx-surface-header global-toolbar">
        <div className="usx-header-left">
          <button onClick={() => window.location.href = '/'} className="usx-header-btn" title="Back to UI Hub">
            <Icon name="home" size={18} />
          </button>
          <span className="usx-header-title">Developer</span>
        </div>
        <div className="usx-header-right">
          <span className="devstudio-status-badge">
            <span className="devstudio-status-dot" />
            L4 Delegator
          </span>
        </div>
      </header>

      <div className="devstudio-surface-body">
        {/* Tab Navigation */}
        <nav className="devstudio-tab-bar">
          <TabButton tab="benchbench" current={tab} icon="bar_chart" label="Bench" onClick={setTab} />
          <TabButton tab="repos" current={tab} icon="folder_open" label="Repos" onClick={setTab} />
          <TabButton tab="skills" current={tab} icon="build" label="Skills" onClick={setTab} />
          <TabButton tab="review" current={tab} icon="visibility" label="Review" onClick={setTab} />
          <TabButton tab="workflows" current={tab} icon="bolt" label="Workflows" onClick={setTab} />
          <TabButton tab="creative" current={tab} icon="palette" label="Creative" onClick={setTab} />
          <TabButton tab="agents" current={tab} icon="smart_toy" label="Agents" onClick={setTab} />
          <TabButton tab="settings" current={tab} icon="settings" label="Settings" onClick={setTab} />
          <TabButton tab="chat" current={tab} icon="chat" label="Chat" onClick={setTab} />
        </nav>

        <main className="devstudio-surface-main">
          {tab === 'chat' && <ChatPanel />}
          {tab === 'repos' && <ReposPanel />}
          {tab === 'skills' && <SkillsPanel />}
          {tab === 'review' && <ReviewPanel />}
          {tab === 'workflows' && <WorkflowsPanel />}
          {tab === 'benchbench' && <BenchBenchPanel />}
          {tab === 'creative' && <CreativePanel />}
          {tab === 'agents' && <AgentsPanel />}
          {tab === 'settings' && <SettingsPanel />}
        </main>
      </div>
    </div>
  )
}

