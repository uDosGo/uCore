/* ═══════════════════════════════════════════════════════════════════
   TeletextSurface — Ceefax Teletext Page Viewer
   ═══════════════════════════════════════════════════════════════════
   Standalone Teletext surface with its own route.
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import { GridUIContext, useGridUIStore } from '../gridui/GridUIStore'
import { TeletextGrid } from '../gridui/panels/TeletextGrid'

function TeletextSurfaceInner() {
  const { sidebarOpen, setSidebarOpen } = useSurfaceShell()

  const toolbarTabs: ToolbarTab[] = []

  return (
    <div className="ucode-surface">
      <GlobalToolbar
        tabs={toolbarTabs}
        onToggleSidebar={() => setSidebarOpen(prev => !prev)}
        sidebarOpen={sidebarOpen}
        sidebarToggleLabel="Teletext sidebar"
        hideGlobe
      />
      <div className="usx-surface-body ucode-body">
        <main className="usx-surface-main ucode-main" style={{ display: 'block' }}>
          <section className="ucode-main-viewport" style={{ height: 'calc(100vh - 56px)' }}>
            <div className="ucode-main-viewport-header">
              <span className="ucode-pill">Teletext</span>
              <span className="ucode-pill ucode-pill--accent">Ceefax</span>
            </div>
            <div className="ucode-main-viewport-body">
              <TeletextGrid />
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}

export default function TeletextSurface() {
  const store = useGridUIStore()
  return (
    <GridUIContext.Provider value={store}>
      <TeletextSurfaceInner />
    </GridUIContext.Provider>
  )
}
