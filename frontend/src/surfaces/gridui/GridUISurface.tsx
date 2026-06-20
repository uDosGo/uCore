/* ═══════════════════════════════════════════════════════════════════
   GridUISurface — Terminal & Teletext Surface
   ═══════════════════════════════════════════════════════════════════
   Stripped down to just Terminal and Teletext panels.
   Map, Grid, Assets, Feeds, Settings moved to USystemSurface.
   ═══════════════════════════════════════════════════════════════════
   ⚠️  IMPORTANT: GridUI uses its own grid-based CSS styles that are
   intentionally SEPARATE from USX styles. Do NOT merge gridui styles
   with USX styles — they have unique rendering requirements (grid
   algebra, teletext, character maps) that conflict with USX layout.
   When updating USX, keep grid-styles in their own files.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'

import { Icon } from '../../components/Icon'
import { GridUIContext, useGridUIStore, PANELS } from './GridUIStore'
import type { GridPanelId } from './GridUIStore'
import { GlobalToolbar, ToolbarTab } from '../../components/GlobalToolbar'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar from '../../components/VaultSidebar'
import AssistUISurface from '../assistui/AssistUISurface'

import { TerminalPanel } from './panels/TerminalPanel'
import { TeletextGrid } from './panels/TeletextGrid'
import { ViewportSettingsPopup } from './panels/ViewportSettingsPopup'

// ─── Panels that use overlay sidebar (terminal/teletext — viewport-sensitive) ──
const OVERLAY_SIDEBAR_PANELS = new Set(['terminal', 'teletext'])

// ─── Snackbar ───────────────────────────────────────────────────────
function Snackbar() {
  const store = React.useContext(GridUIContext)
  if (!store.activeSnackbar) return null
  const typeColors: Record<string, string> = { info: '#58a6ff', success: '#238636', warning: '#d29922', error: '#E76F51' }
  return (
    <div className="gridui-snackbar" style={{ border: `1px solid ${typeColors[store.activeSnackbar.type || 'info']}40` }}>
      <span className="gridui-snackbar-dot" style={{ background: typeColors[store.activeSnackbar.type || 'info'] }} />
      <span className="gridui-snackbar-message">{store.activeSnackbar.message}</span>
      {store.activeSnackbar.action && <button className="gridui-snackbar-btn" onClick={store.dismissSnackbar}>{store.activeSnackbar.action}</button>}
      <button className="gridui-snackbar-close" onClick={store.dismissSnackbar}><Icon name="close" size={12} /></button>
    </div>
  )
}

// ─── Display Settings Button ────────────────────────────────────────
function DisplaySettingsBtn() {
  const store = React.useContext(GridUIContext)
  const isGridPanel = store.activePanel === 'terminal' || store.activePanel === 'teletext'
  if (!isGridPanel) return null
  return (
    <button
      className={`gridui-display-settings-btn ${store.viewportPopupOpen ? 'active' : ''}`}
      onClick={store.toggleViewportPopup}
      title="Viewport settings"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
        <line x1="8" y1="21" x2="16" y2="21"/>
        <line x1="12" y1="17" x2="12" y2="21"/>
      </svg>
    </button>
  )
}

// ─── Main Surface Component ────────────────────────────────────────
export default function GridUISurface() {
  const store = useGridUIStore()
  const shell = useSurfaceShell()
  const location = useLocation()

  // Check URL for ?panel= param on mount
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const panel = params.get('panel')
    if (panel === 'feeds') {
      window.location.href = '/system?tab=feeds'
    } else if (panel === 'teletext') {
      store.setActivePanel('teletext')
    } else if (panel === 'terminal') {
      store.setActivePanel('terminal')
    }
  }, [location.search, store])

  const isOverlayPanel = OVERLAY_SIDEBAR_PANELS.has(store.activePanel)

  // ─── Render content based on active panel ──────────────────────────
  const renderContent = () => {
    if (store.activePanel === 'terminal') return <TerminalPanel />
    if (store.activePanel === 'teletext') return <TeletextGrid />
    return <TerminalPanel />
  }

  // ─── Nav rail tabs: Terminal + Teletext ────────────────────────────
  const navTabs: ToolbarTab[] = PANELS.filter(p => p.id === 'terminal' || p.id === 'teletext').map(panel => ({
    id: panel.id,
    icon: panel.icon,
    label: panel.label,
    active: store.activePanel === panel.id,
    onClick: () => store.setActivePanel(panel.id as GridPanelId),
  }))

  return (
    <GridUIContext.Provider value={store}>
      <div className="gridui-root">
        {/* Global Toolbar */}
        <GlobalToolbar
          tabs={navTabs}
          chatMode={shell.chatOpen ? 'panel' : 'closed'}
          onToggleChat={shell.toggleChat}
          onToggleSidebar={shell.toggleSidebar}
          sidebarOpen={shell.sidebarOpen}
          rightExtra={<DisplaySettingsBtn />}
          hideGlobe
          hideAssistUI
          hideFeeds
        />

        {/* USX v3.1 Surface Body */}
        <div className="usx-surface-body" style={{ display: 'flex', overflow: 'hidden', position: 'relative' }}>
          {/* Vault Sidebar — overlays for terminal/teletext */}
          {isOverlayPanel ? (
            <div className={`gridui-overlay gridui-overlay--left ${shell.sidebarOpen ? 'gridui-overlay--open' : ''}`}>
              <VaultSidebar
                open={shell.sidebarOpen}
                onToggle={shell.toggleSidebar}
                onNewFile={(binderId) => console.log('New file in', binderId)}
                onFileSelect={(file) => console.log('Selected:', file.name)}
              />
            </div>
          ) : (
            <VaultSidebar
              open={shell.sidebarOpen}
              onToggle={shell.toggleSidebar}
              onNewFile={(binderId) => console.log('New file in', binderId)}
              onFileSelect={(file) => console.log('Selected:', file.name)}
            />
          )}

          <main className="usx-surface-main" style={{ minHeight: 0 }}>
            {renderContent()}
          </main>

          {/* Shared Chat Panel */}
          {shell.chatOpen && (
            <div className="gridui-overlay gridui-overlay--right gridui-overlay--open" style={{ zIndex: 1000 }}>
              <div className="hub-chat-panel" style={{ height: '100%' }}>
                <div className="hub-chat-panel-header">
                  <span className="hub-chat-panel-title">Chat</span>
                  <button className="usx-header-btn" onClick={shell.toggleChat} title="Close chat">
                    <Icon name="close" size={16} />
                  </button>
                </div>
                <div className="hub-chat-panel-body">
                  <AssistUISurface hideToolbar />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      <Snackbar />
      <ViewportSettingsPopup />
    </GridUIContext.Provider>
  )
}
