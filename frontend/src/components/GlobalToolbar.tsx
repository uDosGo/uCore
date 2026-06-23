/* ═══════════════════════════════════════════════════════════════════
   GlobalToolbar — Consistent top toolbar across all UI Hub surfaces
   ═══════════════════════════════════════════════════════════════════
   Left:   Home icon + Sidebar toggle + Web Reader (Globe) + AssistUI (bolt)
   Middle: Surface-specific tab links (optional, passed via props)
   Right:  Dev Mode + Settings + extra
   ═══════════════════════════════════════════════════════════════════
   Dev Mode toggle shown only when dev server is detected running.
   Clicking OFF stops dev server and hides the toggle.
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon } from './Icon'
import { useDevMode } from '../hooks/useDevMode'

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
  /** Optional custom label for sidebar toggle button (e.g. "Server sidebar") */
  sidebarToggleLabel?: string
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
  sidebarToggleLabel,
  onOpenSettings,
  hideGlobe,
  hideAssistUI,
  assistUIActive,
  hideFeeds,
  onToggleFeeds,
  feedsOpen,
}: GlobalToolbarProps) {
  const navigate = useNavigate()
  const resolvedSidebarLabel = sidebarToggleLabel || 'Filepicker sidebar'
  const { devServerRunning, loading, toggleDevMode } = useDevMode()

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
            title={sidebarOpen ? `Close ${resolvedSidebarLabel.toLowerCase()}` : `Open ${resolvedSidebarLabel.toLowerCase()}`}
            aria-label={`Toggle ${resolvedSidebarLabel.toLowerCase()}`}
          >
            <Icon name="folder" size={18} />
          </button>
        )}
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

      {/* ─── Right: Dev Mode + Settings + extra ─── */}
      <div className="usx-header-right">
        {rightExtra}

        {/* Dev Mode toggle — only appears when dev server is running */}
        {devServerRunning && (
          <button
            className="usx-header-btn usx-header-btn--dev"
            onClick={toggleDevMode}
            disabled={loading}
            title="Dev Mode active — click to stop dev server"
            style={{
              color: '#f97583',
              borderColor: 'rgba(249, 117, 131, 0.3)',
              background: 'rgba(249, 117, 131, 0.08)',
            }}
          >
            <Icon name="tune" size={16} />
            <span style={{ fontSize: 11, marginLeft: 4 }}>Dev</span>
          </button>
        )}

        {/* Settings gear */}
        <button
          className="usx-header-btn"
          onClick={() => {
            if (onOpenSettings) onOpenSettings()
            navigate('/server?tab=settings')
          }}
          title="Settings"
        >
          <Icon name="settings" size={18} />
        </button>
      </div>
    </header>
  )
}

export default GlobalToolbar