/* ════════════════════════════════════════════════════════════════════
   ⚠️  ARCHIVED — React frontend (legacy)
   ════════════════════════════════════════════════════════════════════
   This React codebase is being migrated to Vue 3.
   Active development: frontend-vue/
   Migration docs: docs/VUE_REFACTOR_SURFACE_TAGGING.md
// To access Vue dashboard: http://localhost:5175
   ════════════════════════════════════════════════════════════════════
   ui-hub — React Entry Point
   ════════════════════════════════════════════════════════════════════
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
   ════════════════════════════════════════════════════════════════════ */
import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import DashboardSurface from './surfaces/dashboard/DashboardSurface'
import { SystemPage, parseSystemRoute } from './SystemPage'
import { SurfaceShellProvider, useSurfaceShell } from './components/SurfaceShellContext'
import { FilepickerSidebar } from './components/FilepickerSidebar'
import { UCoreIndex } from './components/UCoreIndex'
import UCodeSurface from './surfaces/ucode/UCodeSurface'
import BrowserUISurface from './surfaces/browserui/BrowserUISurface'
import AssistUISurface from './surfaces/assistui/AssistUISurface'
import DeveloperSurface from './surfaces/developer/DeveloperSurface'
import DocumentationSurface from './surfaces/documentation/DocumentationSurface'
import UServerSurface from './surfaces/userver/UServerSurface'
import WorkflowSurface from './surfaces/workflow/WorkflowSurface'
import USystemSurface from './surfaces/system/USystemSurface'
import SnackMachineSurface from './surfaces/snackmachine/SnackMachineSurface'
import DefaultSidebar from './components/DefaultSidebar'
import { DevModeProvider, useDevMode } from './hooks/useDevMode'
import { S_PAGE_COMPONENTS } from './pages/spage-registry'

import './styles/usx/legacy/usx-icons.css'
import './styles/usx/usx-base.css'
import './styles/usx/usx-typography-standard.css'
import './styles/usx/usx-typography-responsive.css'
import './styles/tokens.css'
import './styles/nestframe.css'
import './styles/usx/usx-spacing-scale.css'
import './styles/usx/usx-pico-reset.css'
import './styles/usx/usx-layout-system.css'
import './styles/usx/usx-pico-integration.css'
import './styles/hub/index.css'
import './styles/surface-host.css'
import './styles/global-toolbar.css'
import './styles/surfaces/developer.css'
import './styles/surfaces/ucode.css'
import './styles/surfaces/gridcore-dashboard.css'
import './styles/surfaces/snackmachine.css'
import './styles/vault-sidebar.css'
import './styles/filepicker-sidebar.css'
import './styles/ucore-index.css'
import './surfaces/browserui/styles/browserui.css'

// ═══════════════════════════════════════════════════════════════════
// MIGRATION NOTICE: React → Vue 3 Rewrite
// ═══════════════════════════════════════════════════════════════════
// This React frontend is being migrated to Vue 3.
// The new Vue dashboard runs at: http://localhost:5175
// Source: frontend-vue/  |  Docs: docs/VUE_REFACTOR_SURFACE_TAGGING.md
// ═══════════════════════════════════════════════════════════════════

const VUE_DEV_URL = 'http://localhost:5175'

// Show migration banner on all React surfaces
function MigrationBanner() {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null
  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 9999,
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      borderTop: '2px solid #58a6ff', padding: '12px 20px',
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16,
      fontSize: 13, color: '#c9d1d9',
    }}>
      <span>⚡ <strong>Vue 3 Dashboard</strong> is now live — This React surface is archived.</span>
      <a href={VUE_DEV_URL} style={{
        background: '#58a6ff', color: '#fff', padding: '6px 16px',
        borderRadius: 6, textDecoration: 'none', fontWeight: 600, fontSize: 13,
      }}>Open Vue Dashboard →</a>
      <button onClick={() => setDismissed(true)} style={{
        background: 'transparent', border: '1px solid #30363d', color: '#8b949e',
        padding: '4px 10px', borderRadius: 4, cursor: 'pointer', fontSize: 12,
      }}>Dismiss</button>
    </div>
  )
}

/* Force Pico primary color override AFTER all USX CSS loads */
const style = document.createElement('style');
style.textContent = `
  :root {
    --pico-primary: #58a6ff !important;
    --pico-primary-hover: #3b82f6 !important;
    --pico-primary-focus: #2563eb !important;
  }
  
  /* Ensure Inter font is applied globally */
  html, body, button, input, select, textarea, [role="button"] {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
  }
`;
document.head.appendChild(style);

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
 * Surfaces that already render their own FilepickerSidebar.
 * RootLayout skips the fallback sidebar for these to avoid double-render.
 */
const SURFACES_WITH_SIDEBAR = new Set([
  '/workflow',
  '/ucode',
  '/developer',
  '/server',
  '/system',
  '/snackmachine',
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
  const [filepickerOpen, setFilepickerOpen] = useState(false)

  return (
    <BrowserRouter>
      <SurfaceShellProvider>
        <DevModeProvider>
          <MigrationBanner />
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
              <Route path="/snackmachine/*" element={<SnackMachineSurface />} />
              <Route path="/*" element={<App />} />
            </Routes>
          </RootLayout>
          <FloatingChatWrapper />
          <UCoreIndex open={false} />
          <FilepickerSidebar open={filepickerOpen} onToggle={() => setFilepickerOpen(!filepickerOpen)} />
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
ReactDOM.createRoot(document.getElementById('app')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
)
