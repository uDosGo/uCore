/* ═══════════════════════════════════════════════════════════════════
   BrowserUISurface — USX Schema v3.1 Web Reader
   ═══════════════════════════════════════════════════════════════════
   Clean browser interface with centered search bar, kanban-style card
   stacks for binder groupings, and research bookmarks.
   Project Type: Exploratory (EX) | Autonomy Level: L3 (Executor)
   Binder: 🔬 Exploratory/Research | Tags: #browser #research #bookmarks
   Wiki: [[Web Reader Hub]] | Backlinks: [[Research Binder]]
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useRef } from 'react'
import { GlobalToolbar } from '../../components/GlobalToolbar'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import AssistUISurface from '../assistui/AssistUISurface'
import { Icon } from '../../components/Icon'


// ─── Types ──────────────────────────────────────────────────────────


interface Bookmark {
  id: string
  title: string
  url: string
  description: string
  tags: string[]
  binder: string
  lastVisited: Date
}

interface CardStack {
  id: string
  title: string
  icon: string
  items: Bookmark[]
}

// ─── Sample Data ────────────────────────────────────────────────────

const SAMPLE_STACKS: CardStack[] = [
  {
    id: 'research',
    title: 'Research',
    icon: 'search',
    items: [
      { id: 'r1', title: 'MCP Protocol Spec', url: 'https://modelcontextprotocol.io', description: 'Official MCP specification and docs', tags: ['#mcp', '#protocol'], binder: 'Technical', lastVisited: new Date('2026-06-08') },
      { id: 'r2', title: 'React 19 Release Notes', url: 'https://react.dev/blog/2024/12/05/react-19', description: 'What\'s new in React 19', tags: ['#react', '#frontend'], binder: 'Technical', lastVisited: new Date('2026-06-07') },
      { id: 'r3', title: 'Rust Async Book', url: 'https://rust-lang.github.io/async-book/', description: 'Comprehensive async Rust guide', tags: ['#rust', '#async'], binder: 'Learning', lastVisited: new Date('2026-06-05') },
    ],
  },
  {
    id: 'bookmarks',
    title: 'Bookmarks',
    icon: 'bookmark',
    items: [
      { id: 'b1', title: 'GitHub Copilot Docs', url: 'https://docs.github.com/en/copilot', description: 'GitHub Copilot documentation', tags: ['#tools', '#ai'], binder: 'Technical', lastVisited: new Date('2026-06-09') },
      { id: 'b2', title: 'MDN Web Docs', url: 'https://developer.mozilla.org', description: 'Web platform reference', tags: ['#reference', '#web'], binder: 'Learning', lastVisited: new Date('2026-06-06') },
      { id: 'b3', title: 'Docker Compose Docs', url: 'https://docs.docker.com/compose/', description: 'Multi-container Docker apps', tags: ['#docker', '#devops'], binder: 'Technical', lastVisited: new Date('2026-06-04') },
      { id: 'b4', title: 'Tailwind CSS Docs', url: 'https://tailwindcss.com/docs', description: 'Utility-first CSS framework', tags: ['#css', '#frontend'], binder: 'Technical', lastVisited: new Date('2026-06-03') },
    ],
  },
  {
    id: 'reading-list',
    title: 'Reading List',
    icon: 'book',
    items: [
      { id: 'l1', title: 'Designing Data-Intensive Apps', url: 'https://dataintensive.net', description: 'Foundational systems design book', tags: ['#book', '#architecture'], binder: 'Learning', lastVisited: new Date('2026-05-20') },
      { id: 'l2', title: 'Crafting Interpreters', url: 'https://craftinginterpreters.com', description: 'Build your own programming language', tags: ['#book', '#compilers'], binder: 'Learning', lastVisited: new Date('2026-05-15') },
    ],
  },
  {
    id: 'archive',
    title: 'Archive',
    icon: 'archive',
    items: [
      { id: 'a1', title: 'Old Project Wiki', url: 'https://wiki.example.com', description: 'Legacy project documentation', tags: ['#archive', '#docs'], binder: 'Productive', lastVisited: new Date('2026-04-01') },
    ],
  },
]

// ─── Component ──────────────────────────────────────────────────────

export default function BrowserUISurface() {
  const shell = useSurfaceShell()
  const [searchQuery, setSearchQuery] = useState('')
  const [stacks, setStacks] = useState<CardStack[]>(SAMPLE_STACKS)
  const [activeStack, setActiveStack] = useState<string | null>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)


  // Focus search on mount
  useEffect(() => {
    searchInputRef.current?.focus()
  }, [])

  // Filter stacks based on search
  const filteredStacks = stacks.map(stack => ({
    ...stack,
    items: stack.items.filter(item =>
      !searchQuery ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
    ),
  })).filter(stack => stack.items.length > 0)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      const query = encodeURIComponent(searchQuery.trim())
      window.open(`https://duckduckgo.com/?q=${query}`, '_blank')
    }
  }

  const handleBookmarkClick = (url: string) => {
    window.open(url, '_blank')
  }

  const formatDate = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days}d ago`
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  return (
    <div className="browserui-surface">
      {/* ─── Global Toolbar (consistent across all surfaces) ─── */}
      <GlobalToolbar
        tabs={[]}
        chatMode={shell.chatOpen ? 'panel' : 'closed'}
        onToggleChat={shell.toggleChat}
      />

      <div className="usx-surface-body">
        {/* ─── Chat Panel — overlays ALL surfaces (absolute, z-index) ─── */}
        {shell.chatOpen && (
          <div className="hub-chat-panel">
            <div className="hub-chat-panel-body">
              <AssistUISurface hideToolbar />
            </div>
          </div>
        )}

        <main className="usx-surface-main">
          {/* Search Bar — Pico CSS form style */}
          <div className="browserui-search-section">
            <form onSubmit={handleSearch} role="search" className="browserui-search-form">
              <input
                ref={searchInputRef}
                type="search"
                placeholder="Search the web or filter bookmarks..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                aria-label="Search"
              />
              {searchQuery && (
                <button
                  type="button"
                  className="outline contrast"
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear search"
                  style={{ flexShrink: 0 }}
                >
                  <Icon name="close" size={14} />
                </button>
              )}
            </form>
          </div>

          {/* Kanban Card Stacks */}
          <div className="browserui-stacks">
            {filteredStacks.length === 0 ? (
              <div className="browserui-empty">
                <Icon name="search" size={32} className="browserui-empty-icon" />
                <h3>No bookmarks found</h3>
                <p>Try a different search term</p>
              </div>
            ) : (
              filteredStacks.map(stack => (
                <div key={stack.id} className="browserui-stack">
                  <div className="browserui-stack-header">
                    <span className="browserui-stack-title">
                      <Icon name={stack.icon} size={16} /> {stack.title}
                    </span>
                    <span className="browserui-stack-count">{stack.items.length}</span>
                  </div>
                  {stack.items.map(item => (
                    <div
                      key={item.id}
                      className="browserui-card"
                      onClick={() => handleBookmarkClick(item.url)}
                    >
                      <div className="browserui-card-title">{item.title}</div>
                      <div className="browserui-card-desc">{item.description}</div>
                      <div className="browserui-card-meta">
                        <span className="browserui-tag">{item.binder}</span>
                        <span className="browserui-date">{formatDate(item.lastVisited)}</span>
                      </div>
                      <div className="browserui-tags">
                        {item.tags.slice(0, 3).map(tag => (
                          <span key={tag} className="browserui-tag browserui-tag--dim">{tag}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ))
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
