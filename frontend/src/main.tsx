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
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import DashboardSurface from './surfaces/dashboard/DashboardSurface'
import { SystemPage, parseSystemRoute } from './SystemPage'
import { SurfaceShellProvider, useSurfaceShell } from './components/SurfaceShellContext'
import VaultSidebar from './components/VaultSidebar'
import UCodeSurface from './surfaces/ucode/UCodeSurface'
import BrowserUISurface from './surfaces/browserui/BrowserUISurface'
import AssistUISurface from './surfaces/assistui/AssistUISurface'
import DeveloperSurface from './surfaces/developer/DeveloperSurface'
import DocumentationSurface from './surfaces/documentation/DocumentationSurface'
import UServerSurface from './surfaces/userver/UServerSurface'
import WorkflowSurface from './surfaces/workflow/WorkflowSurface'
import USystemSurface from './surfaces/system/USystemSurface'
import DefaultSidebar from './components/DefaultSidebar'
import { DevModeProvider, useDevMode } from './hooks/useDevMode'
import { S_PAGE_COMPONENTS } from './pages/spage-registry'

import './styles/usx/usx-icons.css'
import './styles/usx/usx-base.css'
import './styles/usx/usx-typography.css'
import './styles/usx/usx-typography-prose.css'
import './styles/tokens.css'
/* nestframe must come before hub to establish Pico base styles */
import './styles/nestframe.css'
/* USX standardization: spacing scale + Pico reset (before surface styles) */
import './styles/usx/usx-spacing-scale.css'
import './styles/usx/usx-pico-reset.css'
/* CENTRALIZED LAYOUT SYSTEM - must come before all surface CSS */
import './styles/usx/usx-layout-system.css'
/* Pico CSS integration: nav, buttons, forms, cards, badges */
import './styles/usx/usx-pico-integration.css'
/* Icon refinement: sizing, spacing, animations */
import './styles/usx/usx-icon-refinement.css'
/* Typography globals: apply font family/size overrides */
import './styles/typography-global-apply.css'
import './styles/hub/index.css'
import './styles/surface-host.css'
import './styles/global-toolbar.css'
import './styles/surfaces/developer.css'
import './styles/surfaces/ucode.css'
import './styles/vault-sidebar.css'
import './surfaces/browserui/styles/browserui.css'

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

/**
 * Surfaces that already render their own VaultSidebar.
 * RootLayout skips the fallback sidebar for these to avoid double-render.
 */
const SURFACES_WITH_SIDEBAR = new Set([
  '/workflow',
  '/ucode',
  '/developer',
  '/server',
  '/system',
  '/',
])

function RootLayout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useSurfaceShell()
  const location = useLocation()
  // Normalize path: root "/" stays as "/", otherwise use first segment
  const normalizedPath = location.pathname === '/'
    ? '/'
    : '/' + (location.pathname.split('/').filter(Boolean)[0] || '')
  const hasOwnSidebar = SURFACES_WITH_SIDEBAR.has(normalizedPath)
  
  // Surfaces with their own layout shouldn't be wrapped
  if (hasOwnSidebar) {
    return <>{children}</>
  }
  
  // Other routes get the default sidebar + main layout
  return (
    <div className="usx-surface-body" style={{ display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <DefaultSidebar open={sidebarOpen} />
      <main className="usx-surface-main" style={{ flex: 1, overflow: 'auto' }}>
        {children}
      </main>
    </div>
  )
}

function Root() {
  return (
    <BrowserRouter>
      <SurfaceShellProvider>
        <DevModeProvider>
          <RootLayout>
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
          </RootLayout>
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