/* ═══════════════════════════════════════════════════════════════════
   GlobalToolbar — Consistent top toolbar across all UI Hub surfaces
   ═══════════════════════════════════════════════════════════════════
   Left:   Home icon + Sidebar toggle + Web Reader (Globe) + AssistUI (bolt)
   Middle: Surface-specific tab links (optional, passed via props)
   Right:  Dev Mode + Settings + extra
   ═══════════════════════════════════════════════════════════════════
   Chat toggle removed from toolbar — now a floating Intercom-style
   launcher button in ProseSurfaceManager (bottom-right, fixed).
   Feeds (rss_feed) removed — now a tab in USystemSurface.
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon } from './Icon'

export interface ToolbarTab {
  id: string
  icon: string
  label: string
  active?: boolean
  onClick: () => void
}

export type ChatMode = 'closed' | 'panel'

interface GlobalToolbarProps {
  /** Surface-specific tabs shown in the middle area (optional — empty = zen mode) */
  tabs?: ToolbarTab[]
  /** Current chat panel mode */
  chatMode?: ChatMode
  /** Toggle chat panel callback */
  onToggleChat?: () => void
  /** When true, hides the chat toggle button (used on ChatUI full-page view) */
  hideChatToggle?: boolean
  /** Additional right-side elements (e.g. status badges) */
  rightExtra?: React.ReactNode
  /** Toggle filepicker sidebar callback */
  onToggleSidebar?: () => void
  /** Whether filepicker sidebar is currently open */
  sidebarOpen?: boolean
  /** Open settings panel callback */
  onOpenSettings?: () => void
  /** When true, hides the Globe/Web Reader button (used on BrowserUI itself) */
  hideGlobe?: boolean
  /** When true, hides the AssistUI button */
  hideAssistUI?: boolean
  /** When true, highlights the AssistUI button as active (used on AssistUI surface) */
  assistUIActive?: boolean
  /** When true, hides the Feeds button */
  hideFeeds?: boolean
  /** Callback when Feeds icon is clicked (default: navigate to /gridui?panel=feeds) */
  onToggleFeeds?: () => void
  /** Whether the Feeds panel is currently open */
  feedsOpen?: boolean
}



export function GlobalToolbar({
  tabs,
  chatMode,
  onToggleChat,
  hideChatToggle,
  rightExtra,
  onToggleSidebar,
  sidebarOpen,
  onOpenSettings,
  hideGlobe,
  hideAssistUI,
  assistUIActive,
  hideFeeds,
  onToggleFeeds,
  feedsOpen,
}: GlobalToolbarProps) {


  const navigate = useNavigate()

  const handleHome = () => {
    navigate('/?tab=surfaces')
  }

  const handleGlobe = () => {
    navigate('/browserui')
  }

  const handleFeeds = () => {
    if (onToggleFeeds) {
      onToggleFeeds()
    } else {
      navigate('/gridui?panel=feeds')
    }
  }

  return (
    <header className="usx-surface-header global-toolbar">
      {/* ─── Left: Home + Sidebar toggle + Globe + Feeds + Bolt ─── */}
      <div className="usx-header-left">
        <button
          className="usx-header-btn"
          onClick={handleHome}
          title="Back to UI Hub (Surfaces tab)"
          aria-label="Home"
        >
          <Icon name="home" size={18} />
        </button>
        {onToggleSidebar && (
          <button
            className={`usx-header-btn ${sidebarOpen ? 'active' : ''}`}
            onClick={onToggleSidebar}
            title={sidebarOpen ? 'Close filepicker sidebar' : 'Open filepicker sidebar'}
            aria-label="Toggle filepicker sidebar"
          >
            <Icon name="folder" size={18} />
          </button>
        )}
        {/* ─── Web Reader (Globe) — always shows globe icon ─── */}
        {!hideGlobe && (
          <button
            className="usx-header-btn"
            onClick={handleGlobe}
            title="Web Reader Surface"
            aria-label="Web Reader"
          >
            <Icon name="map" size={18} />
          </button>
        )}
        {/* ─── Feeds (rss_feed) — REMOVED from global bar ─── */}
        {/* Feeds now lives as a tab in USystemSurface. If you need it back,
            uncomment the block below and pass hideFeeds={false} from callers.
        {!hideFeeds && (
          <button
            className={`usx-header-btn ${feedsOpen ? 'active' : ''}`}
            onClick={handleFeeds}
            title="Feeds Panel"
            aria-label="Feeds"
          >
            <Icon name="rss_feed" size={18} />
          </button>
        )} */}
        {/* ─── AssistUI (bolt) — highlighted when on AssistUI surface ─── */}
        {!hideAssistUI && (
          <button
            className={`usx-header-btn ${assistUIActive ? 'active' : ''}`}
            onClick={() => navigate('/assistui')}
            title={assistUIActive ? 'Assist UI (active)' : 'Open Assist UI (full-page AI chat)'}
          >
            <Icon name="bolt" size={18} />
          </button>
        )}
      </div>


      {/* ─── Middle: Surface-specific tabs (zen mode if empty) ─── */}
      {tabs && tabs.length > 0 && (
        <nav className="global-toolbar-nav">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`global-toolbar-nav-btn ${tab.active ? 'active' : ''}`}
              onClick={tab.onClick}
              title={tab.label}
            >
              <Icon name={tab.icon} size={16} />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      )}

      {/* ─── Right: Settings + extra ─── */}
      <div className="usx-header-right">
        {rightExtra}
        {/* ─── Settings gear — always visible, navigates to /system?tab=settings ─── */}
        <button
          className="usx-header-btn"
          onClick={() => {
            if (onOpenSettings) {
              onOpenSettings()
            } else {
              navigate('/system?tab=settings')
            }
          }}
          title="Settings"
        >
          <Icon name="settings" size={18} />
        </button>
        {/* ─── Chat panel toggle — REMOVED: now a floating launcher in ProseSurfaceManager ─── */}
      </div>
    </header>
  )
}

export default GlobalToolbar
