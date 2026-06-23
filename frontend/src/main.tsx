/* ═══════════════════════════════════════════════════════════════════
   ui-hub — React Entry Point
   ═══════════════════════════════════════════════════════════════════
   Surfaces (after consolidation):
     /              → MissionControlSurface (dashboard + missions)
     /[ps]\d{3}     → SystemPage  (P: surface status, S: system pages)
     /assistui/*    → AssistUISurface (canonical AI chat)
     /ucode/*       → UCodeSurface (Terminal + Teletext + Grid)
    /gridui/*      → Redirect to /ucode (archived)
    /gridcore/*    → Redirect to /ucode?panel=terminal (archived)
     /proseui/*     → Redirects to / (absorbed into MissionControl)
     /browserui/*   → BrowserUISurface (kept)
     /server/*      → UServerSurface (kept)
     /workflow/*    → WorkflowSurface (daily missions, tasks, activity)
     /developer/**  → DeveloperSurface (gated by Dev Mode)
    /system/*      → Redirect to /server?tab=... (legacy compatibility)
   Removed: HomeNestSurface, WorldMapSurface, Code3UISurface, VibeSurface, GridUISurface (dead)
   Absorbed: ChatUISurface → AssistUI, FloatingChatPanel → AssistUI, USystemRouter → UIHubManager
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import MissionControlSurface from './surfaces/missioncontrol/MissionControlSurface'
import { SystemPage, parseSystemRoute } from './SystemPage'
import { SurfaceShellProvider } from './components/SurfaceShellContext'
import UCodeSurface from './surfaces/ucode/UCodeSurface'
import BrowserUISurface from './surfaces/browserui/BrowserUISurface'
import AssistUISurface from './surfaces/assistui/AssistUISurface'
import DeveloperSurface from './surfaces/developer/DeveloperSurface'
import DocumentationSurface from './surfaces/documentation/DocumentationSurface'
import UServerSurface from './surfaces/userver/UServerSurface'
import WorkflowSurface from './surfaces/workflow/WorkflowSurface'
import { DevModeProvider, useDevMode } from './hooks/useDevMode'

// S-pages (system pages)
import S100ToolBuilder from './pages/S100ToolBuilder'
import S101StoryBuilder from './pages/S101StoryBuilder'
import S300WorkflowBuilder from './pages/S300WorkflowBuilder'
import S310ClipboardOrchestration from './pages/S310ClipboardOrchestration'
import S320KnowledgeTools from './pages/S320KnowledgeTools'
import S330MigrationDashboard from './pages/S330MigrationDashboard'
import S600Learning from './pages/S600Learning'

import './styles/tokens.css'
import './styles/hub/index.css'
import './styles/nestframe.css'
import './styles/surface-host.css'
import './styles/global-toolbar.css'
import './styles/surfaces/developer.css'
import './styles/surfaces/ucode.css'
import './styles/vault-sidebar.css'
import './surfaces/browserui/styles/browserui.css'

// ─── S-page component map ──────────────────────────────────────────
const S_PAGE_COMPONENTS: Record<string, React.ComponentType> = {
  s100: S100ToolBuilder,
  s101: S101StoryBuilder,
  s300: S300WorkflowBuilder,
  s310: S310ClipboardOrchestration,
  s320: S320KnowledgeTools,
  s330: S330MigrationDashboard,
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

/** Dev route guard — reads from runtime context instead of build-time env */
function DevRouteGuard({ children }: { children: React.ReactNode }) {
  const { devServerRunning, probing } = useDevMode()
  // Show loading spinner while still probing (avoids premature redirect)
  if (probing) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--pico-muted-color)', fontSize: 14 }}>
        Checking dev server status...
      </div>
    )
  }
  if (!devServerRunning) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}

function Root() {
  return (
    <BrowserRouter>
      <SurfaceShellProvider>
        <DevModeProvider>
          <Routes>
            <Route path="/proseui/*" element={<Navigate to="/" replace />} />
            <Route path="/gridui/*" element={<Navigate to="/ucode" replace />} />
            <Route path="/story-builder" element={<Navigate to="/s101" replace />} />
            <Route path="/user-setup-story" element={<Navigate to="/s101" replace />} />
            <Route path="/story/gtx-form" element={<Navigate to="/s101" replace />} />
            <Route path="/workflow/*" element={<WorkflowSurface />} />
            <Route path="/ucode/*" element={<UCodeSurface />} />
            <Route path="/browserui/*" element={<BrowserUISurface />} />
            <Route path="/assistui/*" element={<AssistUISurface />} />
            <Route path="/documentation/*" element={<DocumentationSurface />} />
            <Route path="/devstudio" element={<Navigate to="/developer" replace />} />
            <Route path="/devstudio/*" element={<Navigate to="/developer" replace />} />
            <Route path="/developer" element={<DevRouteGuard><DeveloperSurface /></DevRouteGuard>} />
            <Route path="/developer/*" element={<DevRouteGuard><DeveloperSurface /></DevRouteGuard>} />
            <Route path="/server/*" element={<UServerSurface />} />
            <Route path="/userver/*" element={<UserverRouteRedirect />} />
            <Route path="/system" element={<SystemRouteRedirect />} />
            <Route path="/system/*" element={<SystemRouteRedirect />} />
            <Route path="/system-legacy" element={<Navigate to="/server?tab=settings" replace />} />
            <Route path="/system-legacy/*" element={<Navigate to="/server?tab=settings" replace />} />
            <Route path="/gridcore/*" element={<Navigate to="/ucode?panel=terminal" replace />} />
            <Route path="/*" element={<App />} />
          </Routes>
          {/* Floating chat bubble + panel — hidden on /assistui since full-page AssistUI is shown */}
          <FloatingChatWrapper />
        </DevModeProvider>
      </SurfaceShellProvider>
    </BrowserRouter>
  )
}

function SystemRouteRedirect() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const rawTab = params.get('tab') || 'install'
  const legacyMap: Record<string, string> = {
    install: 'settings',
    modules: 'settings',
    feeds: 'settings',
    story: 'story',
    'story-builder': 'story',
    'user-setup-story': 'story',
    'gtx-form': 'story',
    'secret-store': 'secrets',
    secrets: 'secrets',
    pages: 'missions',
    publishing: 'workflows',
  }
  const tab = legacyMap[rawTab] || rawTab
  const validTabs = new Set([
    'dashboard',
    'ingest',
    'missions',
    'story',
    'secrets',
    'settings',
    'services',
    'logs',
    'workflows',
    'agents',
  ])
  const nextTab = validTabs.has(tab) ? tab : 'settings'
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
  if (location.pathname.startsWith('/ucode')) return null
  if (location.pathname.startsWith('/gridcore')) return null
  return <AssistUISurface floating />
}

ReactDOM.createRoot(document.getElementById('app')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
)