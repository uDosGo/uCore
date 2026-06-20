/* ═══════════════════════════════════════════════════════════════════
   ProseUISurfaceView — Document-oriented Surface View
   Uses shared components from components/ for modularity.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useLocation } from 'react-router-dom'
import { useProseUIStore } from './stores/proseUIStore'
import { Icon } from '../../components/Icon'
import KanbanBoard from '../../components/KanbanBoard'
import DataTable from '../../components/DataTable'
import ProseView from '../../components/ProseView'
import EditorView from '../../components/EditorView'
import StoryView from '../../components/StoryView'
import type { KanbanItem, KanbanColumn } from '../../components/KanbanBoard'
import type { TableColumn, TableRow } from '../../components/DataTable'
import { statusColor } from '../../utils/statusColor'
import './styles/proseui-theme.css'

// ─── Types ───────────────────────────────────────────────────────
interface ChatMessage { role: 'user' | 'assistant'; content: string }

const INITIAL_KANBAN: KanbanColumn[] = [
  { id: 'draft', title: 'Draft', color: '#94a3b8', items: [
    { id: 'd1', title: 'Getting Started Guide', type: 'doc', date: '2d ago' },
    { id: 'd2', title: 'API Reference v2', type: 'doc', date: '3d ago' },
    { id: 'd3', title: 'Tutorial: Kanban Setup', type: 'tutorial', date: '5d ago' },
  ]},
  { id: 'review', title: 'Review', color: '#f59e0b', items: [
    { id: 'r1', title: 'Architecture Overview', type: 'doc', date: '1d ago' },
    { id: 'r2', title: 'Workflow Automation', type: 'guide', date: '2d ago' },
  ]},
  { id: 'published', title: 'Published', color: '#22c55e', items: [
    { id: 'p1', title: 'Quickstart Guide', type: 'doc', date: '1w ago' },
    { id: 'p2', title: 'USXD Format Spec', type: 'spec', date: '2w ago' },
    { id: 'p3', title: 'uCode1 User Manual', type: 'manual', date: '3w ago' },
    { id: 'p4', title: 'Vault Integration', type: 'guide', date: '1m ago' },
  ]},
]

const INITIAL_TABLE: TableRow[] = [
  { id: '1', title: 'Getting Started Guide', status: 'draft', type: 'doc', date: '2026-05-14' },
  { id: '2', title: 'API Reference v2', status: 'draft', type: 'doc', date: '2026-05-13' },
  { id: '3', title: 'Architecture Overview', status: 'review', type: 'doc', date: '2026-05-15' },
  { id: '4', title: 'Workflow Automation', status: 'review', type: 'guide', date: '2026-05-14' },
  { id: '5', title: 'Quickstart Guide', status: 'published', type: 'doc', date: '2026-05-09' },
  { id: '6', title: 'USXD Format Spec', status: 'published', type: 'spec', date: '2026-05-02' },
  { id: '7', title: 'uCode1 User Manual', status: 'published', type: 'manual', date: '2026-04-25' },
  { id: '8', title: 'Vault Integration', status: 'published', type: 'guide', date: '2026-04-16' },
]

const TABLE_COLUMNS: TableColumn[] = [
  { key: 'title', label: 'Title' },
  { key: 'status', label: 'Status', render: (val: string) => (
    <span className={`status-badge ${val}`} style={{ background: `${statusColor(val)}20`, color: statusColor(val) }}>{val}</span>
  )},
  { key: 'type', label: 'Type' },
  { key: 'date', label: 'Date' },
]

/* ═══════════════════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════════════════ */
const ProseUISurface: React.FC = () => {
  const store = useProseUIStore()
  const location = useLocation()

  // Derive active view from URL path
  const pathTab = location.pathname.split('/').pop() || 'board'
  const activeView = pathTab === 'board' ? 'kanban' : pathTab === 'list' ? 'table' : pathTab

  /* ── Kanban state ── */
  const [kanbanColumns, setKanbanColumns] = useState<KanbanColumn[]>(INITIAL_KANBAN)

  /* ── Table state ── */
  const [tableItems] = useState<TableRow[]>(INITIAL_TABLE)
  const [selectedRow, setSelectedRow] = useState<string | null>(null)

  /* ── Editor state ── */
  const [editorContent, setEditorContent] = useState(() => {
    try { return localStorage.getItem('proseui-editor') || '# New Document\n\nStart writing your content here...\n\n## Section 1\n\nLorem ipsum dolor sit amet.\n\n## Section 2\n\n- Item one\n- Item two\n- Item three\n' }
    catch { return '# New Document\n\nStart writing your content here...\n\n## Section 1\n\nLorem ipsum dolor sit amet.\n\n## Section 2\n\n- Item one\n- Item two\n- Item three\n' }
  })
  const [publishStatus, setPublishStatus] = useState<string | null>(null)

  /* ── Chat state ── */
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Hello! I can help you with documents, publishing, and more. Try asking me something.' },
  ])
  const chatMessagesRef = useRef<HTMLDivElement>(null)

  /* ── Save editor to localStorage ── */
  useEffect(() => {
    try { localStorage.setItem('proseui-editor', editorContent) } catch {}
  }, [editorContent])

  /* ── Chat scroll ── */
  const scrollChat = useCallback(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight
    }
  }, [])

  /* ── Kanban callbacks ── */
  const handleKanbanItemClick = useCallback((item: KanbanItem, column: KanbanColumn) => {
    store.setSelectedDoc({
      title: item.title,
      type: item.type,
      status: column.title,
      date: item.date,
    })
  }, [store])

  const handleKanbanItemDelete = useCallback((itemId: string) => {
    setKanbanColumns(prev => prev.map(col => ({
      ...col,
      items: col.items.filter(i => i.id !== itemId),
    })))
  }, [])

  const handleKanbanItemMove = useCallback((item: KanbanItem, fromColId: string, toColId: string) => {
    setKanbanColumns(prev => {
      const next = prev.map(col => ({ ...col, items: [...col.items] }))
      const srcCol = next.find(c => c.id === fromColId)
      const tgtCol = next.find(c => c.id === toColId)
      if (!srcCol || !tgtCol) return prev
      const idx = srcCol.items.findIndex(i => i.id === item.id)
      if (idx === -1) return prev
      const [moved] = srcCol.items.splice(idx, 1)
      tgtCol.items.push(moved)
      return next
    })
  }, [])

  const handleKanbanAddCard = useCallback((colId: string, title: string) => {
    const newItem: KanbanItem = {
      id: `card-${Date.now()}`,
      title,
      type: 'doc',
      date: 'just now',
    }
    setKanbanColumns(prev => prev.map(col =>
      col.id === colId ? { ...col, items: [...col.items, newItem] } : col
    ))
  }, [])

  /* ── Table callbacks ── */
  const handleTableRowClick = useCallback((row: TableRow) => {
    setSelectedRow(prev => prev === row.id ? null : row.id)
    store.setSelectedDoc({
      title: row.title,
      type: row.type,
      status: row.status,
      date: row.date,
    })
  }, [store])

  /* ── Publish callback ── */
  const handlePublish = useCallback((content: string) => {
    setPublishStatus('Document published successfully!')
    setTimeout(() => setPublishStatus(null), 3000)
  }, [])

  /* ── Chat ── */
  const getChatResponse = (text: string): string => {
    const lower = text.toLowerCase()
    if (lower.includes('publish') || lower.includes('publish')) {
      return 'I can help you publish documents. Use the Editor view to write content, then click the Publish button. Or type `publish` in the command bar below.'
    }
    if (lower.includes('status') || lower.includes('how many')) {
      const draftCount = kanbanColumns.find(c => c.id === 'draft')?.items.length ?? 0
      const reviewCount = kanbanColumns.find(c => c.id === 'review')?.items.length ?? 0
      const publishedCount = kanbanColumns.find(c => c.id === 'published')?.items.length ?? 0
      return `Current workspace status:\n- **Draft**: ${draftCount} documents\n- **Review**: ${reviewCount} documents\n- **Published**: ${publishedCount} documents`
    }
    if (lower.includes('help')) {
      return 'I can help with:\n- **Publishing** — Ask about publishing documents\n- **Status** — Ask about workspace status\n- **Navigation** — Use the tabs in the header\n- **Editor** — Write and preview Markdown\n- **Kanban** — Drag cards between columns'
    }
    if (lower.includes('hello') || lower.includes('hi')) {
      return 'Hello! How can I help you with your workspace today?'
    }
    return `I understand you're asking about "${text}". I can help with publishing, workspace status, navigation, and more. Try asking me about "status" or "help".`
  }

  const sendChat = () => {
    const text = chatInput.trim()
    if (!text) return
    setChatMessages(prev => [...prev, { role: 'user', content: text }])
    setChatInput('')
    setTimeout(() => {
      setChatMessages(prev => [...prev, { role: 'assistant', content: getChatResponse(text) }])
      scrollChat()
    }, 300)
    scrollChat()
  }

  /* ═══════════════════════════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════════════════════════ */
  return (
    <div className="proseui-surface">
      <div className="proseui-surface-body">
        <main className="proseui-surface-content">
          {/* ═══ KANBAN ═══ */}
          {activeView === 'kanban' && (
            <KanbanBoard
              columns={kanbanColumns}
              onItemClick={handleKanbanItemClick}
              onItemDelete={handleKanbanItemDelete}
              onItemMove={handleKanbanItemMove}
              onAddCard={handleKanbanAddCard}
            />
          )}

          {/* ═══ TABLE ═══ */}
          {activeView === 'table' && (
            <DataTable
              columns={TABLE_COLUMNS}
              rows={tableItems}
              onRowClick={handleTableRowClick}
              selectedId={selectedRow}
              defaultSortField="date"
              defaultSortDir="desc"
            />
          )}

          {/* ═══ PROSE ═══ */}
          {activeView === 'prose' && <ProseView />}

          {/* ═══ EDITOR ═══ */}
          {activeView === 'editor' && (
            <EditorView
              content={editorContent}
              onChange={setEditorContent}
              onPublish={handlePublish}
              publishStatus={publishStatus}
            />
          )}

          {/* ═══ STORY ═══ */}
          {activeView === 'story' && <StoryView />}
        </main>
      </div>

      {/* ═══ Chat Sheet (bottom-right) ═══ */}
      <div className="proseui-chat-sheet">
        <div className="proseui-chat-messages" ref={chatMessagesRef}>
          {chatMessages.map((msg, i) => (
            <div key={i} className={`proseui-chat-message proseui-chat-message--${msg.role}`}>
              <div className="proseui-chat-avatar">
                {msg.role === 'assistant' ? <Icon name="smart_toy" size={14} /> : <Icon name="person" size={14} />}
              </div>
              <div className="proseui-chat-bubble">{msg.content}</div>
            </div>
          ))}
        </div>
        <div className="proseui-chat-input-row">
          <input
            className="proseui-chat-input"
            type="text"
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') sendChat() }}
            placeholder="Ask about documents, publishing..."
          />
          <button className="proseui-chat-send" onClick={sendChat} title="Send">
            <Icon name="send" size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default ProseUISurface
