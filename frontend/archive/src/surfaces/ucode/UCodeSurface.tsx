import React, { useMemo, useState } from 'react'
import { FilepickerSidebar, type SidebarNavItem } from '../../components/FilepickerSidebar'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import { GridUIContext, useGridUIStore } from '../gridui/GridUIStore'
import { TerminalPanel } from '../gridui/panels/TerminalPanel'
import { TeletextGrid } from '../gridui/panels/TeletextGrid'
import { GridCoreDashboard } from './GridCoreDashboard'

type DashboardTab = 'dashboard' | 'terminal' | 'teletext'
type DashboardToolTab = 'overview' | 'gridsmith' | 'grid-editor' | 'layer-composer' | 'svg-font-mapper' | 'map-rendering' | 'spatial-algebra'

export default function UCodeSurface() {
  const shell = useSurfaceShell()
  const { sidebarOpen, setSidebarOpen } = shell
  const store = useGridUIStore()
  const [dashTab, setDashTab] = useState<DashboardTab>('dashboard')
  const [toolTab, setToolTab] = useState<DashboardToolTab>('overview')

  // No toolbar tabs - Dashboard is the default view with Terminal/Teletext as sub-tabs
  const dashTabs: ToolbarTab[] = useMemo(() => [], [])

  // Sidebar nav items - Dashboard is active when viewing dashboard content
  const sidebarNavItems: SidebarNavItem[] = [
    { id: 'dashboard', icon: 'dashboard', label: 'Dashboard', active: dashTab === 'dashboard', onClick: () => setDashTab('dashboard') },
  ]

  // Tool tabs shown in sidebar - only active when on dashboard and that tool is selected
  const toolNavItems: SidebarNavItem[] = [
    { id: 'overview', icon: 'grid_view', label: 'Toolset', active: dashTab === 'dashboard' && toolTab === 'overview', onClick: () => { setDashTab('dashboard'); setToolTab('overview'); } },
    { id: 'gridsmith', icon: 'smart_toy', label: 'GridSmith', active: dashTab === 'dashboard' && toolTab === 'gridsmith', onClick: () => { setDashTab('dashboard'); setToolTab('gridsmith'); } },
    { id: 'grid-editor', icon: 'draw', label: 'Grid Editor', active: dashTab === 'dashboard' && toolTab === 'grid-editor', onClick: () => { setDashTab('dashboard'); setToolTab('grid-editor'); } },
    { id: 'layer-composer', icon: 'layers', label: 'Layer Composer', active: dashTab === 'dashboard' && toolTab === 'layer-composer', onClick: () => { setDashTab('dashboard'); setToolTab('layer-composer'); } },
    { id: 'svg-font-mapper', icon: 'font_download', label: 'SVG Font Mapper', active: dashTab === 'dashboard' && toolTab === 'svg-font-mapper', onClick: () => { setDashTab('dashboard'); setToolTab('svg-font-mapper'); } },
    { id: 'map-rendering', icon: 'map', label: 'Map Rendering', active: dashTab === 'dashboard' && toolTab === 'map-rendering', onClick: () => { setDashTab('dashboard'); setToolTab('map-rendering'); } },
    { id: 'spatial-algebra', icon: 'explore', label: 'Spatial Algebra', active: dashTab === 'dashboard' && toolTab === 'spatial-algebra', onClick: () => { setDashTab('dashboard'); setToolTab('spatial-algebra'); } },
  ]

  const allNavItems = [...sidebarNavItems, ...toolNavItems]

  return (
    <GridUIContext.Provider value={store}>
      <div className="ucode-surface">
        <GlobalToolbar
          tabs={dashTabs}
          onToggleSidebar={() => setSidebarOpen(prev => !prev)}
          sidebarOpen={sidebarOpen}
          sidebarToggleLabel="uCode sidebar"
          hideGlobe
        />

        <div className="usx-surface-body ucode-body">
          <FilepickerSidebar
            open={sidebarOpen}
            showModeTabs={false}
            sidebarMode="server"
            serverNavItems={allNavItems}
          />

          <main className="usx-surface-main ucode-main">
            <section className="ucode-main-viewport">
              <div className="ucode-main-viewport-header">
                <span className="ucode-pill">uCode Surface</span>
                <span className="ucode-pill ucode-pill--accent">
                  {dashTab === 'dashboard' ? 'GridCore Dashboard' : dashTab === 'terminal' ? 'Terminal' : 'Teletext'}
                </span>
              </div>
              {/* Sub-tabs for Dashboard view */}
              {dashTab === 'dashboard' && (
                <div className="ucode-sub-tabs">
                  <button className={`ucode-sub-tab ${toolTab === 'overview' ? 'active' : ''}`} onClick={() => setToolTab('overview')}>
                    <Icon name="dashboard" size={14} />
                    <span>Overview</span>
                  </button>
                  <button className={`ucode-sub-tab ${dashTab === 'terminal' ? 'active' : ''}`} onClick={() => setDashTab('terminal')}>
                    <Icon name="terminal" size={14} />
                    <span>Terminal</span>
                  </button>
                  <button className={`ucode-sub-tab ${dashTab === 'teletext' ? 'active' : ''}`} onClick={() => setDashTab('teletext')}>
                    <Icon name="tv" size={14} />
                    <span>Teletext</span>
                  </button>
                </div>
              )}
              <div className="ucode-main-viewport-body">
                {dashTab === 'dashboard' ? (
                  <GridCoreDashboard />
                ) : dashTab === 'terminal' ? (
                  <TerminalPanel />
                ) : (
                  <TeletextGrid />
                )}
              </div>
            </section>
          </main>
        </div>
      </div>
    </GridUIContext.Provider>
  )
}
