/* ═══════════════════════════════════════════════════════════════════
   AssistUISurface — USX Schema v3.1 Full-Page AI Chat
   ═══════════════════════════════════════════════════════════════════
   assistant-ui inspired design with streaming responses, model selector,
   conversation management, and full-page layout.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Icon } from '../../components/Icon'
import { GlobalToolbar, ToolbarTab } from '../../components/GlobalToolbar'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import '../../styles/assistui.css'


// ─── Types ──────────────────────────────────────────────────────────

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface PromptCard {
  id: string
  icon: string
  label: string
  context?: string
}

interface ModelOption {
  id: string
  provider: string
  name: string
}

interface Conversation {
  id: string
  title: string
  messages: ChatMessage[]
  model: string
  createdAt: Date
  updatedAt: Date
}

type AgentMode = 'vault' | 'developer' | 'agent'

// ─── Constants ──────────────────────────────────────────────────────

const SNACKBAR_API = 'http://localhost:8484'

const AGENTS: { id: AgentMode; icon: string; label: string; desc: string }[] = [
  { id: 'vault', icon: 'chat', label: 'Vault', desc: 'User mode — personal docs, projects, knowledge' },
  { id: 'developer', icon: 'code', label: 'Developer', desc: 'Dev mode — code, repos, skills, automation' },
  { id: 'agent', icon: 'smart_toy', label: 'Agent', desc: 'Custom agent builder & configuration' },
]

const DEFAULT_PROMPTS: PromptCard[] = [
  { id: 'resume', icon: 'edit_note', label: 'Pick up where you left off', context: 'Continue your last project' },
  { id: 'new-project', icon: 'add', label: 'Start a new project', context: 'Create from template' },
  { id: 'research', icon: 'search', label: 'Research a topic & compile binder', context: 'Gather and organise' },
  { id: 'review', icon: 'visibility', label: 'Review recent changes', context: 'Check activity log' },
  { id: 'brainstorm', icon: 'bolt', label: 'Brainstorm ideas', context: 'Creative exploration' },
  { id: 'plan', icon: 'format_list_bulleted', label: 'Plan your week', context: 'Schedule & priorities' },
]

/**
 * Map emoji unicode characters to Material Icon names.
 * The snackbar API returns emoji strings (e.g. "📝") in the icon field,
 * but we render via the <Icon> component which expects Material Icon names.
 * This map converts common emojis to their closest Material Icon equivalent.
 */
const EMOJI_TO_ICON: Record<string, string> = {
  '📝': 'edit_note',
  '🚀': 'rocket_launch',
  '🔍': 'search',
  '👁': 'visibility',
  '💡': 'lightbulb',
  '📋': 'format_list_bulleted',
  '📄': 'description',
  '📁': 'folder_open',
  '📊': 'bar_chart',
  '📌': 'push_pin',
  '⭐': 'star',
  '🎯': 'track_changes',
  '🔧': 'build',
  '⚡': 'bolt',
  '🛠': 'construction',
  '📚': 'library_books',
  '🎨': 'palette',
  '🔗': 'link',
  '💬': 'chat',
  '📰': 'article',
  '🗂': 'folder_special',
  '📅': 'calendar_month',
  '✅': 'check_circle',
  '❌': 'cancel',
  '🔄': 'sync',
  '📤': 'publish',
  '📥': 'download',
  '🔒': 'lock',
  '🔓': 'lock_open',
  '🌐': 'language',
  '🤖': 'smart_toy',
  '🧠': 'psychology',
  '📈': 'trending_up',
  '📉': 'trending_down',
  '🏷': 'label',
  '✏️': 'edit',
  '🗑': 'delete',
  '🔔': 'notifications',
  '🔕': 'notifications_off',
}

/**
 * Resolve a prompt card icon to a Material Icon name.
 * If the icon is an emoji, map it via EMOJI_TO_ICON.
 * If it's already a Material Icon name, pass it through.
 */
function resolveIcon(icon: string): string {
  return EMOJI_TO_ICON[icon] || icon
}

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content: `# Hi friend

I'm your OK assistant with streaming MCP protocol, model selection, and agent management.

What would you like to do, today?`,
  timestamp: new Date(),
}

// ─── Simple Markdown Renderer ───────────────────────────────────────

function renderMarkdown(text: string): React.ReactNode {
  if (!text) return null
  const lines = text.split('\n')
  const nodes: React.ReactNode[] = []
  let inCodeBlock = false
  let codeBuffer: string[] = []
  let codeLang = ''
  let inTable = false
  let tableBuffer: string[] = []
  let listStack: { type: 'ul' | 'ol'; items: React.ReactNode[] }[] = []

  const flushList = () => {
    while (listStack.length > 0) {
      const list = listStack.pop()!
      const Tag = list.type === 'ul' ? 'ul' : 'ol'
      const listKey = `list-${nodes.length}`
      nodes.push(<Tag key={listKey}>{list.items.map((item, i) => <li key={`${listKey}-item-${i}`}>{item}</li>)}</Tag>)
    }
  }

  const processInline = (line: string): React.ReactNode => {
    const parts: React.ReactNode[] = []
    let remaining = line
    let key = 0

    const inlineRegex = /(\*\*(.+?)\*\*)|(\*(.+?)\*)|(`(.+?)`)|(\[([^\]]+)\]\(([^)]+)\))|(~~(.+?)~~)/g
    let lastIndex = 0
    let match: RegExpExecArray | null

    while ((match = inlineRegex.exec(remaining)) !== null) {
      if (match.index > lastIndex) {
        parts.push(<span key={key++}>{remaining.slice(lastIndex, match.index)}</span>)
      }
      if (match[2]) {
        parts.push(<strong key={key++}>{match[2]}</strong>)
      } else if (match[4]) {
        parts.push(<em key={key++}>{match[4]}</em>)
      } else if (match[6]) {
        parts.push(<code key={key++}>{match[6]}</code>)
      } else if (match[8] && match[9]) {
        parts.push(<a key={key++} href={match[9]}>{match[9]}</a>)
      } else if (match[11]) {
        parts.push(<del key={key++}>{match[11]}</del>)
      }
      lastIndex = match.index + match[0].length
    }
    if (lastIndex < remaining.length) {
      parts.push(<span key={key++}>{remaining.slice(lastIndex)}</span>)
    }
    return parts.length === 1 ? parts[0] : <>{parts}</>
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    if (line.startsWith('```')) {
      if (inCodeBlock) {
        nodes.push(
          <pre key={`code-${i}`}>
            <code className={codeLang || undefined}>{codeBuffer.join('\n')}</code>
          </pre>
        )
        codeBuffer = []
        inCodeBlock = false
        codeLang = ''
      } else {
        flushList()
        inCodeBlock = true
        codeLang = line.slice(3).trim()
      }
      continue
    }
    if (inCodeBlock) {
      codeBuffer.push(line)
      continue
    }

    if (line.startsWith('|') && line.endsWith('|')) {
      tableBuffer.push(line)
      inTable = true
      continue
    }
    if (inTable && !line.startsWith('|')) {
      inTable = false
      nodes.push(renderTable(tableBuffer, `table-${i}`))
      tableBuffer = []
    }

    if (/^[-*_]{3,}$/.test(line.trim())) {
      flushList()
      nodes.push(<hr key={`hr-${i}`} />)
      continue
    }

    const headingMatch = line.match(/^(#{1,4})\s+(.+)/)
    if (headingMatch) {
      flushList()
      const level = headingMatch[1].length as 1 | 2 | 3 | 4
      const Tag = `h${level}` as keyof JSX.IntrinsicElements
      nodes.push(<Tag key={`h-${i}`}>{processInline(headingMatch[2])}</Tag>)
      continue
    }

    if (line.startsWith('> ')) {
      flushList()
      const content = line.slice(2)
      nodes.push(<blockquote key={`bq-${i}`}>{processInline(content)}</blockquote>)
      continue
    }

    const ulMatch = line.match(/^[-*+]\s+(.+)/)
    if (ulMatch) {
      if (listStack.length === 0 || listStack[listStack.length - 1].type !== 'ul') {
        flushList()
        listStack.push({ type: 'ul', items: [] })
      }
      listStack[listStack.length - 1].items.push(processInline(ulMatch[1]))
      continue
    }

    const olMatch = line.match(/^\d+[.)]\s+(.+)/)
    if (olMatch) {
      if (listStack.length === 0 || listStack[listStack.length - 1].type !== 'ol') {
        flushList()
        listStack.push({ type: 'ol', items: [] })
      }
      listStack[listStack.length - 1].items.push(processInline(olMatch[1]))
      continue
    }

    if (line.trim() === '') {
      flushList()
      continue
    }

    flushList()
    nodes.push(<p key={`p-${i}`}>{processInline(line)}</p>)
  }

  if (inCodeBlock) {
    nodes.push(
      <pre key={`code-end`}>
        <code>{codeBuffer.join('\n')}</code>
      </pre>
    )
  }
  if (inTable && tableBuffer.length > 0) {
    nodes.push(renderTable(tableBuffer, 'table-end'))
  }
  flushList()

  return <>{nodes}</>
}

function renderTable(rows: string[], key: string): React.ReactNode {
  const parsed = rows.map(row =>
    row.split('|').filter(cell => cell.trim()).map(cell => cell.trim())
  )
  const dataRows = parsed.filter(row => !row[0]?.match(/^[-:]+$/))
  if (dataRows.length === 0) return null

  const [header, ...body] = dataRows
  return (
    <table key={key}>
      <thead>
        <tr>{header.map((cell, i) => <th key={`${key}-h-${i}`}>{cell}</th>)}</tr>
      </thead>
      <tbody>
        {body.map((row, ri) => (
          <tr key={`${key}-r-${ri}`}>{row.map((cell, ci) => <td key={`${key}-c-${ri}-${ci}`}>{cell}</td>)}</tr>
        ))}
      </tbody>
    </table>
  )
}

// ─── Conversation Manager ───────────────────────────────────────────

function generateId(): string {
  return `conv-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem('assistui-conversations')
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return parsed.map((c: any) => ({
      ...c,
      createdAt: new Date(c.createdAt),
      updatedAt: new Date(c.updatedAt),
      messages: c.messages.map((m: any) => ({ ...m, timestamp: new Date(m.timestamp) })),
    }))
  } catch { return [] }
}

function saveConversations(conversations: Conversation[]) {
  localStorage.setItem('assistui-conversations', JSON.stringify(conversations))
}

// ─── Component ──────────────────────────────────────────────────────

interface AssistUISurfaceProps {
  /** When true, hides the GlobalToolbar (used when embedded as a panel) */
  hideToolbar?: boolean
  /** When true, renders as a floating chat bubble (Intercom-style) */
  floating?: boolean
}

export default function AssistUISurface({ hideToolbar, floating }: AssistUISurfaceProps = {}) {
  const [floatingOpen, setFloatingOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [snackbarStatus, setSnackbarStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const [activeAgent, setActiveAgent] = useState<AgentMode>('vault')
  const [prompts, setPrompts] = useState<PromptCard[]>(DEFAULT_PROMPTS)
  const shell = useSurfaceShell()

  // Model selection
  const [models, setModels] = useState<ModelOption[]>([
    { id: 'llama3.2', provider: 'ollama', name: 'Llama 3.2' },
    { id: 'mistral', provider: 'ollama', name: 'Mistral' },
    { id: 'gpt-4o', provider: 'openrouter', name: 'GPT-4o' },
  ])
  const [selectedModel, setSelectedModel] = useState<string>('llama3.2')
  const [modelPickerOpen, setModelPickerOpen] = useState(false)

  // Conversation management
  const [conversations, setConversations] = useState<Conversation[]>(loadConversations)
  const [activeConversation, setActiveConversation] = useState<string | null>(null)
  const [conversationListOpen, setConversationListOpen] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check snackbar status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`${SNACKBAR_API}/api/health`, { signal: AbortSignal.timeout(2000) })
        setSnackbarStatus(res.ok ? 'online' : 'offline')
      } catch {
        setSnackbarStatus('offline')
      }
    }
    checkStatus()
    const interval = setInterval(checkStatus, 10000)
    return () => clearInterval(interval)
  }, [])

  // Fetch prompts for active agent
  useEffect(() => {
    const fetchPrompts = async () => {
      try {
        const res = await fetch(`${SNACKBAR_API}/api/chat/prompts?agent=${activeAgent}`, {
          signal: AbortSignal.timeout(3000),
        })
        if (res.ok) {
          const data = await res.json()
          if (Array.isArray(data.prompts) && data.prompts.length > 0) {
            const validPrompts = data.prompts.filter((p: any) => p.id && p.label && p.icon)
            if (validPrompts.length > 0) setPrompts(validPrompts)
          }
        }
      } catch (err) {
        console.error('Failed to fetch prompts:', err)
      }
    }
    fetchPrompts()
  }, [activeAgent])

  // Fetch available models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await fetch(`${SNACKBAR_API}/api/models`, { signal: AbortSignal.timeout(3000) })
        if (res.ok) {
          const data = await res.json()
          if (data.models?.length > 0) setModels(data.models)
        }
      } catch { /* keep defaults */ }
    }
    fetchModels()
  }, [])

  // Save conversations on change
  useEffect(() => {
    saveConversations(conversations)
  }, [conversations])

  // ─── Send Message ──────────────────────────────────────────────

  const sendMessage = useCallback(async (text?: string) => {
    const message = (text || input).trim()
    if (!message || loading) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    // Create placeholder assistant message for streaming
    const assistantId = `assistant-${Date.now()}`
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, assistantMsg])

    try {
      // Try streaming via SSE
      const history = messages.map(m => ({ role: m.role, content: m.content }))
      const params = new URLSearchParams({ message, agent: activeAgent })
      const res = await fetch(`${SNACKBAR_API}/api/chat/stream?${params}`, {
        signal: AbortSignal.timeout(60000),
      })

      if (!res.ok) throw new Error(`API returned ${res.status}`)

      const reader = res.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (!data) continue
            try {
              const parsed = JSON.parse(data)
              if (parsed.token) {
                setMessages(prev =>
                  prev.map(m =>
                    m.id === assistantId
                      ? { ...m, content: m.content + parsed.token }
                      : m
                  )
                )
              }
            } catch { /* skip malformed */ }
          }
        }
      }
    } catch {
      // Fallback to non-streaming POST
      try {
        const res = await fetch(`${SNACKBAR_API}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message,
            agent: activeAgent,
            history: messages.map(m => ({ role: m.role, content: m.content })),
          }),
          signal: AbortSignal.timeout(15000),
        })

        if (res.ok) {
          const data = await res.json()
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? { ...m, content: data.response || data.message || 'No response received.' }
                : m
            )
          )
        } else {
          throw new Error(`API returned ${res.status}`)
        }
      } catch {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, content: `**Echo:** ${message}\n\n> _AI is offline. Start the snackbar server for AI-powered responses._` }
              : m
          )
        )
      }
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [input, loading, messages, activeAgent])

  // ─── Conversation Management ───────────────────────────────────

  const saveCurrentConversation = useCallback(() => {
    if (messages.length <= 1) return // Don't save empty or welcome-only conversations

    const title = messages.find(m => m.role === 'user')?.content.slice(0, 60) || 'New conversation'
    const now = new Date()

    if (activeConversation) {
      setConversations(prev =>
        prev.map(c =>
          c.id === activeConversation
            ? { ...c, messages, title, model: selectedModel, updatedAt: now }
            : c
        )
      )
    } else {
      const newConv: Conversation = {
        id: generateId(),
        title,
        messages,
        model: selectedModel,
        createdAt: now,
        updatedAt: now,
      }
      setConversations(prev => [...prev, newConv])
      setActiveConversation(newConv.id)
    }
  }, [messages, activeConversation, selectedModel])

  const loadConversation = useCallback((convId: string) => {
    const conv = conversations.find(c => c.id === convId)
    if (!conv) return
    setMessages(conv.messages)
    setActiveConversation(convId)
    setConversationListOpen(false)
  }, [conversations])

  const newConversation = useCallback(() => {
    saveCurrentConversation()
    setMessages([WELCOME_MESSAGE])
    setActiveConversation(null)
  }, [saveCurrentConversation])

  const deleteConversation = useCallback((convId: string) => {
    setConversations(prev => prev.filter(c => c.id !== convId))
    if (activeConversation === convId) {
      setMessages([WELCOME_MESSAGE])
      setActiveConversation(null)
    }
  }, [activeConversation])

  // ─── Event Handlers ────────────────────────────────────────────

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([WELCOME_MESSAGE])
    setActiveConversation(null)
  }

  const handlePromptClick = (prompt: PromptCard) => {
    setInput(prompt.label)
    setTimeout(() => sendMessage(prompt.label), 100)
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatDate = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / 86400000)
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  // ─── Render ────────────────────────────────────────────────────

  // ─── Floating Mode (Intercom-style bubble) ─────────────────────
  if (floating) {
    return (
      <div className={`hub-chat-overlay ${floatingOpen ? 'hub-chat-overlay--open' : ''}`}>
        {floatingOpen && (
          <div className="hub-chat-panel">
            <div className="hub-chat-panel-header">
              <div className="hub-chat-panel-title">
                <span className="hub-chat-panel-status" />
                AI Assistant
              </div>
              <div className="hub-chat-panel-header-actions">
                <button
                  className="hub-chat-panel-minimize"
                  onClick={() => setFloatingOpen(false)}
                  title="Minimize"
                >
                  <Icon name="remove" size={16} />
                </button>
                <button
                  className="hub-chat-panel-close"
                  onClick={() => setFloatingOpen(false)}
                  title="Close"
                >
                  <Icon name="close" size={16} />
                </button>
              </div>
            </div>
            <div className="hub-chat-panel-body">
              {/* Inline chat content (no toolbar, no sidebar) */}
              <div className="assistui-body" style={{ height: '100%' }}>
                <div className="assistui-body-inner">
                  <div className="assistui-messages" style={{ maxHeight: 'calc(100% - 60px)' }}>
                    {messages.map(msg => (
                      <div key={msg.id} className={`assistui-message assistui-message--${msg.role}`}>
                        <div className="assistui-message-header">
                          <span className="assistui-message-role">
                            {msg.role === 'user' ? 'You' : 'Assistant'}
                          </span>
                          <span className="assistui-message-time">{formatTime(msg.timestamp)}</span>
                        </div>
                        <div className="assistui-message-body assistui-prose">
                          {renderMarkdown(msg.content)}
                        </div>
                      </div>
                    ))}
                    {loading && (
                      <div className="assistui-loading">
                        <span className="assistui-loading-dot" />
                        <span className="assistui-loading-dot" />
                        <span className="assistui-loading-dot" />
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                  <div className="assistui-footer">
                    <div className="assistui-input-wrapper">
                      <textarea
                        ref={inputRef as any}
                        className="assistui-input"
                        placeholder={snackbarStatus === 'online' ? 'Ask me anything...' : 'Type a message (AI offline)...'}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={loading}
                        rows={1}
                      />
                      <button
                        className={`assistui-send-btn ${input.trim() && !loading ? 'assistui-send-btn--active' : ''}`}
                        onClick={() => sendMessage()}
                        disabled={!input.trim() || loading}
                        title="Send message"
                      >
                        <Icon name="send" size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        <button
          className="hub-chat-bubble"
          onClick={() => setFloatingOpen(prev => !prev)}
          title={floatingOpen ? 'Close chat' : 'Open chat'}
          aria-label="Toggle chat panel"
        >
          {floatingOpen ? (
            <Icon name="close" size={24} />
          ) : (
            <Icon name="chat" size={24} />
          )}
        </button>
      </div>
    )
  }

  // ─── Full-Page Mode ────────────────────────────────────────────
  return (
    <div className="assistui-surface">

      {/* Global Toolbar — show bolt icon as active since we're on AssistUI */}
      {!hideToolbar && (
        <GlobalToolbar
          tabs={[]}
          chatMode="closed"
          onToggleChat={() => {}}
          onOpenSettings={() => {}}
          hideChatToggle
          assistUIActive
        />
      )}

      {/* ─── Conversation List Sidebar ─────────────────────────── */}
      {conversationListOpen && (
        <div className="assistui-conv-sidebar">
          <div className="assistui-conv-sidebar-header">
            <h3>Conversations</h3>
            <button className="assistui-conv-close" onClick={() => setConversationListOpen(false)}>
              <Icon name="close" size={16} />
            </button>
          </div>
          <div className="assistui-conv-list">
            {conversations.length === 0 ? (
              <div className="assistui-conv-empty">
                <Icon name="chat" size={24} />
                <span>No saved conversations</span>
              </div>
            ) : (
              [...conversations]
                .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
                .map(conv => (
                  <div
                    key={conv.id}
                    className={`assistui-conv-item ${activeConversation === conv.id ? 'assistui-conv-item--active' : ''}`}
                    onClick={() => loadConversation(conv.id)}
                  >
                    <div className="assistui-conv-item-info">
                      <span className="assistui-conv-item-title">{conv.title}</span>
                      <span className="assistui-conv-item-meta">
                        {conv.messages.length} messages · {formatDate(conv.updatedAt)}
                      </span>
                    </div>
                    <button
                      className="assistui-conv-item-delete"
                      onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id) }}
                      title="Delete conversation"
                    >
                      <Icon name="close" size={12} />
                    </button>
                  </div>
                ))
            )}
          </div>
        </div>
      )}

      {/* ─── Main Content ──────────────────────────────────────── */}
      <div className="assistui-main">
        {/* Chat Body */}
        <div className="assistui-body">
          <div className="assistui-body-inner">

            {/* ─── Agent Selector + Model Picker + Status Bar (inline, inside main) ──── */}
            <div className="assistui-topbar">
              {/* Agent pills */}
              <div className="assistui-agent-bar">
                <span className="assistui-agent-label">Agent</span>
                {AGENTS.map(agent => (
                  <button
                    key={agent.id}
                    className={`assistui-agent-pill ${activeAgent === agent.id ? 'assistui-agent-pill--active' : ''}`}
                    onClick={() => setActiveAgent(agent.id)}
                    title={agent.desc}
                  >
                    <Icon name={agent.icon} size={14} />
                    <span>{agent.label}</span>
                  </button>
                ))}
              </div>

              {/* Model picker */}
              <div className="assistui-model-section">
                <button
                  className="assistui-model-btn"
                  onClick={() => setModelPickerOpen(!modelPickerOpen)}
                  title="Select model"
                >
                  <Icon name="smart_toy" size={14} />
                  <span>{models.find(m => m.id === selectedModel)?.name || selectedModel}</span>
                  <Icon name="expand_more" size={14} />
                </button>

                {modelPickerOpen && (
                  <div className="assistui-model-dropdown">
                    {models.map(model => (
                      <button
                        key={model.id}
                        className={`assistui-model-option ${selectedModel === model.id ? 'assistui-model-option--active' : ''}`}
                        onClick={() => { setSelectedModel(model.id); setModelPickerOpen(false) }}
                      >
                        <span className="assistui-model-provider">{model.provider}</span>
                        <span className="assistui-model-name">{model.name}</span>
                        {selectedModel === model.id && <Icon name="check" size={14} />}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Status + Actions */}
              <div className="assistui-status-bar">
                <span className={`assistui-status-dot ${snackbarStatus === 'online' ? 'assistui-status-dot--online' : ''}`} />
                <span className="assistui-status-text">
                  {snackbarStatus === 'online' ? 'AI Online' : snackbarStatus === 'checking' ? 'Connecting...' : 'AI Offline'}
                </span>
                <span className="assistui-status-sep" />
                <button className="assistui-action-btn" onClick={newConversation} title="New conversation">
                  <Icon name="add" size={14} />
                  New
                </button>
                <button className="assistui-action-btn" onClick={() => setConversationListOpen(!conversationListOpen)} title="Conversations">
                  <Icon name="history" size={14} />
                  History
                </button>
                <button className="assistui-action-btn" onClick={clearChat} title="Clear">
                  <Icon name="delete" size={14} />
                  Clear
                </button>
              </div>
            </div>

            {/* Messages (scrollable area — messages first, then prompt cards below intro) */}
            <div className="assistui-messages">
              {messages.map(msg => (
                <div key={msg.id} className={`assistui-message assistui-message--${msg.role}`}>
                  <div className="assistui-message-header">
                    <span className="assistui-message-role">
                      {msg.role === 'user' ? 'You' : 'Assistant'}
                    </span>
                    <span className="assistui-message-time">{formatTime(msg.timestamp)}</span>
                  </div>
                  <div className="assistui-message-body assistui-prose">
                    {renderMarkdown(msg.content)}
                  </div>
                </div>
              ))}
              {prompts.length > 0 && messages.length <= 1 && (
                <div className="assistui-prompt-row">
                  {prompts.map(prompt => (
                    <div
                      key={prompt.id}
                      className="assistui-prompt-card"
                      onClick={() => handlePromptClick(prompt)}
                    >
                      <Icon name={resolveIcon(prompt.icon)} size={18} className="assistui-prompt-card-icon" />
                      <span className="assistui-prompt-card-label">{prompt.label}</span>
                      {prompt.context && (
                        <span className="assistui-prompt-card-context">{prompt.context}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {loading && (
                <div className="assistui-loading">
                  <span className="assistui-loading-dot" />
                  <span className="assistui-loading-dot" />
                  <span className="assistui-loading-dot" />
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="assistui-footer">
              <div className="assistui-input-wrapper">
                <textarea
                  ref={inputRef as any}
                  className="assistui-input"
                  placeholder={snackbarStatus === 'online' ? 'Ask me anything...' : 'Type a message (AI offline)...'}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={loading}
                  rows={1}
                  autoFocus
                />
                <button
                  className={`assistui-send-btn ${input.trim() && !loading ? 'assistui-send-btn--active' : ''}`}
                  onClick={() => sendMessage()}
                  disabled={!input.trim() || loading}
                  title="Send message"
                >
                  <Icon name="send" size={16} />
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}
