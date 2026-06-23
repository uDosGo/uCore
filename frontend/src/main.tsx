/* ═══════════════════════════════════════════════════════════════════
   ui-hub — React Entry Point
   ═══════════════════════════════════════════════════════════════════
   Canonical Surface Routes:
     /              → DashboardSurface (surface hub dashboard)
     /[ps]\d{3}     → SystemPage (P: surface status, S: system pages)
     /ucode/*       → UCodeSurface (Terminal + Teletext + Grid)
     /browserui/*   → BrowserUISurface (web reader)
     /assistui/*    → AssistUISurface (canonical AI chat)
     /documentation/* → DocumentationSurface (learning hub)
     /server/*      → UServerSurface (backend ops)
     /system/*      → USystemSurface (admin config)
     /workflow/*    → WorkflowSurface (daily missions, tasks, activity)
     /developer/**  → DeveloperSurface (gated by Dev Mode runtime probe)
   Legacy compat (kept):
     /gridui/*      → Redirect to /ucode
     /userver/*     → Redirect to /server
   Removed: proseui, gridcore, story-builder, user-setup-story, story/gtx-form,
     devstudio, system-legacy (all dead/absorbed/consolidated)
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import DashboardSurface from './surfaces/dashboard/DashboardSurface'
import { SystemPage, parseSystemRoute } from './SystemPage'
import { SurfaceShellProvider } from './components/SurfaceShellContext'
import UCodeSurface from './surfaces/ucode/UCodeSurface'
import BrowserUISurface from './surfaces/browserui/BrowserUISurface'
import AssistUISurface from './surfaces/assistui/AssistUISurface'
import DeveloperSurface from './surfaces/developer/DeveloperSurface'
import DocumentationSurface from './surfaces/documentation/DocumentationSurface'
import UServerSurface from './surfaces/userver/UServerSurface'
import WorkflowSurface from './surfaces/workflow/WorkflowSurface'
import USystemSurface from './surfaces/system/USystemSurface'
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
    if (code.startsWith('s')) {
      const SPage = S_PAGE_COMPONENTS[code]
      if (SPage) return <SPage />
    }
    return <SystemPage {...route} />
  }
  return <DashboardSurface />
}

/** Dev route guard — reads from runtime context instead of build-time env */
function DevRouteGuard({ children }: { children: React.ReactNode }) {
  const { devServerRunning, probing } = useDevMode()
  if (probing) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--pico-muted-color)', fontSize: 14 }}>
        Checking dev server status...
      </div>
    )
  }
  if (!devServerRunning) return <Navigate to="/" replace />
  return <>{children}</>
}

function Root() {
  return (
    <BrowserRouter>
      <SurfaceShellProvider>
        <DevModeProvider>
          <Routes>
            {/* Legacy dead surfaces — consolidated */}
            <Route path="/gridui/*" element={<Navigate to="/ucode" replace />} />
            <Route path="/userver/*" element={<UserverRedirect />} />

            {/* Canonical surfaces */}
            <Route path="/workflow/*" element={<WorkflowSurface />} />
            <Route path="/ucode/*" element={<UCodeSurface />} />
            <Route path="/browserui/*" element={<BrowserUISurface />} />
            <Route path="/assistui/*" element={<AssistUISurface />} />
            <Route path="/documentation/*" element={<DocumentationSurface />} />
            <Route path="/developer" element={<DevRouteGuard><DeveloperSurface /></DevRouteGuard>} />
            <Route path="/developer/*" element={<DevRouteGuard><DeveloperSurface /></DevRouteGuard>} />
            <Route path="/server/*" element={<UServerSurface />} />
            <Route path="/system/*" element={<USystemSurface />} />
            <Route path="/*" element={<App />} />
          </Routes>
          <FloatingChatWrapper />
        </DevModeProvider>
      </SurfaceShellProvider>
    </BrowserRouter>
  )
}

function UserverRedirect() {
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
  return <AssistUISurface floating />
}

ReactDOM.createRoot(document.getElementById('app')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
)