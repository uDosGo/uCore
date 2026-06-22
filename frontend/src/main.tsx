/* ═══════════════════════════════════════════════════════════════════
   ui-hub — React Entry Point
   ═══════════════════════════════════════════════════════════════════
   Surfaces (after consolidation):
     /              → MissionControlSurface (dashboard + missions + kanban/list + prose/editor + schedule)
     /[ps]\d{3}     → SystemPage  (P: surface status, S: system pages)
     /assistui/*    → AssistUISurface (canonical AI chat)
     /gridui/*      → GridUISurface (Terminal + Teletext)
    /gridcore/*    → Redirect to /gridui?panel=terminal (archived)
     /proseui/*     → Redirects to / (absorbed into MissionControl)
     /browserui/*   → BrowserUISurface (kept)
     /userver/*     → UServerSurface (kept)
     /developer/**   → DeveloperSurface (kept)
    /system/*      → Redirect to /server?tab=... (legacy compatibility)
   Removed: HomeNestSurface, WorldMapSurface, Code3UISurface, VibeSurface (dead)
   Absorbed: ChatUISurface → AssistUI, FloatingChatPanel → AssistUI, USystemRouter → UIHubManager
   ═══════════════════════════════════════════════════════════════════
   NOTE: @usx/styles symlinks to packages/usx/ which is currently
   empty. The CSS imports below are kept for type declarations but
   the actual CSS files need to be rebuilt. For now, the snackbar
   CSS import has been removed from proseui-theme.css (snackbar is
   a runtime, not a style).
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import MissionControlSurface from './surfaces/missioncontrol/MissionControlSurface'
import { SystemPage, parseSystemRoute } from './SystemPage'
import { SurfaceShellProvider } from './components/SurfaceShellContext'
import GridUISurface from './surfaces/gridui/GridUISurface'
import BrowserUISurface from './surfaces/browserui/BrowserUISurface'
import AssistUISurface from './surfaces/assistui/AssistUISurface'
import DeveloperSurface from './surfaces/developer/DeveloperSurface'
import UServerSurface from './surfaces/userver/UServerSurface'

const DEV_MODE_ENABLED = ['1', 'true', 'yes', 'on'].includes(
  String(import.meta.env.VITE_DEV_MODE || '').toLowerCase(),
)

// S-pages (system pages)
import S100ToolBuilder from './pages/S100ToolBuilder'
import S101StoryBuilder from './pages/S101StoryBuilder'
import S300WorkflowBuilder from './pages/S300WorkflowBuilder'
import S310ClipboardOrchestration from './pages/S310ClipboardOrchestration'
import S320KnowledgeTools from './pages/S320KnowledgeTools'
import S600Learning from './pages/S600Learning'

import './styles/tokens.css'
import './styles/hub/index.css'
import './styles/nestframe.css'
import './styles/surface-host.css'
import './styles/gridui.css'
import './styles/gridui-terminal.css'
import './styles/global-toolbar.css'
import './styles/surfaces/developer.css'
import './styles/vault-sidebar.css'
import './surfaces/browserui/styles/browserui.css'

// ─── S-page component map ──────────────────────────────────────────
const S_PAGE_COMPONENTS: Record<string, React.ComponentType> = {
  s100: S100ToolBuilder,
  s101: S101StoryBuilder,
  s300: S300WorkflowBuilder,
  s310: S310ClipboardOrchestration,
  s320: S320KnowledgeTools,
  s600: S600Learning,
}

function App() {
  const route = parseSystemRoute(window.location.pathname)
  if (route) {
    const { pageCode } = route
    const code = pageCode.toLowerCase().replace(/[^ps0-9]/g, '')
    // If we have a dedicated S-page component, render it
    if (code.startsWith('s')) {
      const SPage = S_PAGE_COMPONENTS[code]
      if (SPage) {
        return <SPage />
      }
    }
    // Fall back to generic SystemPage for P-pages and unmapped S-pages
    return <SystemPage {...route} />
  }
  return <MissionControlSurface />
}

function Root() {
  return (
    <BrowserRouter>
      <SurfaceShellProvider>
        <Routes>
          <Route path="/proseui/*" element={<Navigate to="/" replace />} />
          <Route path="/gridui/*" element={<GridUISurface />} />
          <Route path="/browserui/*" element={<BrowserUISurface />} />
          <Route path="/assistui/*" element={<AssistUISurface />} />
          <Route
            path="/developer/**"
            element={DEV_MODE_ENABLED ? <DeveloperSurface /> : <Navigate to="/" replace />}
          />
          <Route path="/server/*" element={<UServerSurface />} />
          <Route path="/userver/*" element={<UserverRouteRedirect />} />
          <Route path="/system" element={<SystemRouteRedirect />} />
          <Route path="/system/*" element={<SystemRouteRedirect />} />
          <Route path="/system-legacy" element={<Navigate to="/server?tab=install" replace />} />
          <Route path="/system-legacy/*" element={<Navigate to="/server?tab=install" replace />} />
          <Route path="/gridcore/*" element={<Navigate to="/gridui?panel=terminal" replace />} />
          <Route path="/*" element={<App />} />
        </Routes>
        {/* Floating chat bubble + panel — hidden on /assistui since full-page AssistUI is shown */}
        <FloatingChatWrapper />
      </SurfaceShellProvider>
    </BrowserRouter>
  )
}

function SystemRouteRedirect() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const rawTab = params.get('tab') || 'install'
  const legacyMap: Record<string, string> = {
    story: 'missions',
    pages: 'missions',
    workflows: 'services',
    agents: 'services',
    publishing: 'services',
  }
  const tab = legacyMap[rawTab] || rawTab
  const validTabs = new Set([
    'dashboard',
    'ingest',
    'missions',
    'install',
    'modules',
    'feeds',
    'settings',
    'services',
    'logs',
  ])
  const nextTab = validTabs.has(tab) ? tab : 'install'
  return <Navigate to={`/server?tab=${encodeURIComponent(nextTab)}`} replace />
}

function UserverRouteRedirect() {
  const location = useLocation()
  const nextPath = location.pathname.replace(/^\/userver/, '/server') || '/server'
  return <Navigate to={`${nextPath}${location.search}`} replace />
}

/** Wraps the floating AssistUI bubble, hiding it on full-page surfaces */
function FloatingChatWrapper() {
  const location = useLocation()
  if (location.pathname.startsWith('/assistui')) return null
  if (location.pathname.startsWith('/developer')) return null
  return <AssistUISurface floating />
}

ReactDOM.createRoot(document.getElementById('app')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
)
