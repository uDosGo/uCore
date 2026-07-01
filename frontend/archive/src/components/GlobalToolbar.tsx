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
import { useSurfaceShell } from './SurfaceShellContext'
import '../styles/global-toolbar.css'

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
  const { sidebarOpen: contextSidebarOpen, toggleSidebar: contextToggleSidebar } = useSurfaceShell()
  const resolvedSidebarLabel = sidebarToggleLabel || 'Filepicker sidebar'
  const { devServerRunning, loading, toggleDevMode } = useDevMode()

  const handleHome = () => {
    navigate('/')
  }

  const handleGlobe = () => {
    navigate('/browserui')
  }

  const handleFilepickerToggle = () => {
    // Call the provided callback if available, otherwise use context
    if (onToggleSidebar) {
      onToggleSidebar()
    } else {
      contextToggleSidebar()
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
          <Icon name="home" />
        </button>
        <button
          className={`usx-header-btn ${sidebarOpen || contextSidebarOpen ? 'active' : ''}`}
          onClick={handleFilepickerToggle}
          title={(sidebarOpen || contextSidebarOpen) ? `Close ${resolvedSidebarLabel.toLowerCase()}` : `Open ${resolvedSidebarLabel.toLowerCase()}`}
          aria-label={`Toggle ${resolvedSidebarLabel.toLowerCase()}`}
        >
          <Icon name="folder" />
        </button>
        <button
          className="usx-header-btn"
          onClick={() => {
            const index = document.querySelector('.ucore-index-overlay')
            if (index) {
              (index as HTMLElement).style.display = 'flex'
            }
          }}
          title="uCore Index"
          aria-label="uCore Index"
        >
          <Icon name="database" />
        </button>
        {!hideGlobe && (
          <button
            className="usx-header-btn"
            onClick={handleGlobe}
            title="Web Reader Surface"
            aria-label="Web Reader"
          >
            <Icon name="map" />
          </button>
        )}
        {!hideAssistUI && (
          <button
            className={`usx-header-btn ${assistUIActive ? 'active' : ''}`}
            onClick={() => navigate('/assistui')}
            title={assistUIActive ? 'Assist UI (active)' : 'Open Assist UI (full-page AI chat)'}
          >
            <Icon name="bolt" />
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
              <Icon name={tab.icon} />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      )}

       {/* ─── Right: extra ─── */}
       <div className="usx-header-right">
         {rightExtra}
       </div>

       {/* ─── Far Right: Dev Mode badge + Settings (locked to right edge) ─── */}
       <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 'var(--usx-spacing-xs, 4px)', flexShrink: 0 }}>
         {devServerRunning && (
           <button
             className="dev-mode-badge"
             onClick={toggleDevMode}
             disabled={loading}
             title="Dev Mode active — click to stop dev server"
           >
             <Icon name="tune" />
             <span>Dev</span>
           </button>
         )}

         {/* Settings gear → System Surface */}
         <button
           className="usx-header-btn"
           onClick={() => {
             if (onOpenSettings) onOpenSettings()
             navigate('/system?tab=settings')
           }}
           title="System Settings"
         >
           <Icon name="settings" />
         </button>
       </div>
    </header>
  )
}

export default GlobalToolbar