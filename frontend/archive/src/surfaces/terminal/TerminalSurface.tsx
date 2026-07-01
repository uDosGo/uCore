/* ═══════════════════════════════════════════════════════════════════
   TerminalSurface — BBC BASIC Terminal (BBCSDL-backed)
   ═══════════════════════════════════════════════════════════════════
   Standalone Terminal surface with its own route.
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import { GridUIContext, useGridUIStore } from '../gridui/GridUIStore'
import { TerminalPanel } from '../gridui/panels/TerminalPanel'

function TerminalSurfaceInner() {
  const { sidebarOpen, setSidebarOpen } = useSurfaceShell()

  const toolbarTabs: ToolbarTab[] = []

  return (
    <div className="ucode-surface">
      <GlobalToolbar
        tabs={toolbarTabs}
        onToggleSidebar={() => setSidebarOpen(prev => !prev)}
        sidebarOpen={sidebarOpen}
        sidebarToggleLabel="Terminal sidebar"
        hideGlobe
      />
      <div className="usx-surface-body ucode-body">
        <main className="usx-surface-main ucode-main" style={{ display: 'block' }}>
          <section className="ucode-main-viewport" style={{ height: 'calc(100vh - 56px)' }}>
            <div className="ucode-main-viewport-header">
              <span className="ucode-pill">Terminal</span>
              <span className="ucode-pill ucode-pill--accent">BBC BASIC</span>
            </div>
            <div className="ucode-main-viewport-body">
              <TerminalPanel />
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}

export default function TerminalSurface() {
  const store = useGridUIStore()
  return (
    <GridUIContext.Provider value={store}>
      <TerminalSurfaceInner />
    </GridUIContext.Provider>
  )
}
