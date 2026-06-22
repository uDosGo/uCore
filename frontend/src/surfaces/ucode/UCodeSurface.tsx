import React, { useEffect, useMemo, useState } from 'react'
import { Icon } from '../../components/Icon'
import VaultSidebar, { type SidebarNavItem } from '../../components/VaultSidebar'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { GridUIContext, useGridUIStore } from '../gridui/GridUIStore'
import { TerminalPanel } from '../gridui/panels/TerminalPanel'
import { TeletextGrid } from '../gridui/panels/TeletextGrid'
import { GRID_TOOL_VIEWS } from './gridToolset'

type UCodeTopTab = 'terminal' | 'teletext'
type SidebarMode = 'server' | 'filepicker'
type DashboardToolTab = 'overview' | 'grid-editor' | 'layer-composer' | 'svg-font-mapper' | 'map-rendering' | 'spatial-algebra'

export default function UCodeSurface() {
  const store = useGridUIStore()
  const [topTab, setTopTab] = useState<UCodeTopTab>('terminal')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarMode, setSidebarMode] = useState<SidebarMode>('server')
  const [toolTab, setToolTab] = useState<DashboardToolTab>('overview')

  useEffect(() => {
    store.setActivePanel(topTab)
  }, [store, topTab])

  const toolbarTabs: ToolbarTab[] = useMemo(
    () => [
      {
        id: 'terminal',
        icon: 'terminal',
        label: 'Terminal',
        active: topTab === 'terminal',
        onClick: () => setTopTab('terminal'),
      },
      {
        id: 'teletext',
        icon: 'tv',
        label: 'Teletext',
        active: topTab === 'teletext',
        onClick: () => setTopTab('teletext'),
      },
    ],
    [topTab],
  )

  const serverNavItems: SidebarNavItem[] = [
    { id: 'overview', icon: 'dashboard', label: 'Dashboard', active: toolTab === 'overview', onClick: () => setToolTab('overview') },
    { id: 'grid-editor', icon: 'draw', label: 'Grid Editor', active: toolTab === 'grid-editor', onClick: () => setToolTab('grid-editor') },
    { id: 'layer-composer', icon: 'layers', label: 'Layer Composer', active: toolTab === 'layer-composer', onClick: () => setToolTab('layer-composer') },
    { id: 'svg-font-mapper', icon: 'font_download', label: 'SVG Font Mapper', active: toolTab === 'svg-font-mapper', onClick: () => setToolTab('svg-font-mapper') },
    { id: 'map-rendering', icon: 'map', label: 'Map Rendering', active: toolTab === 'map-rendering', onClick: () => setToolTab('map-rendering') },
    { id: 'spatial-algebra', icon: 'explore', label: 'Spatial Algebra', active: toolTab === 'spatial-algebra', onClick: () => setToolTab('spatial-algebra') },
  ]

  const activeTool = GRID_TOOL_VIEWS.find(view => view.id === toolTab)

  return (
    <GridUIContext.Provider value={store}>
      <div className="ucode-surface">
        <GlobalToolbar
          tabs={toolbarTabs}
          onToggleSidebar={() => setSidebarOpen(prev => !prev)}
          sidebarOpen={sidebarOpen}
          sidebarToggleLabel="uCode sidebar"
          hideGlobe
        />

        <div className="usx-surface-body ucode-body">
          <VaultSidebar
            open={sidebarOpen}
            showModeTabs
            sidebarMode={sidebarMode}
            onSidebarModeChange={setSidebarMode}
            serverNavItems={serverNavItems}
          />

          <main className="usx-surface-main ucode-main">
            <section className="ucode-main-viewport">
              <div className="ucode-main-viewport-header">
                <span className="ucode-pill">uCode Surface</span>
                <span className="ucode-pill ucode-pill--accent">{topTab === 'terminal' ? 'Terminal Mode' : 'Teletext Mode'}</span>
              </div>
              <div className="ucode-main-viewport-body">
                {topTab === 'terminal' ? <TerminalPanel /> : <TeletextGrid />}
              </div>
            </section>

            <aside className="ucode-dashboard">
              <div className="ucode-dashboard-header">
                <div>
                  <h2>Unified Grid Toolset</h2>
                  <p>Consolidated GridCore upgrade track and implementation status.</p>
                </div>
                <span className="ucode-pill">LOCKED BRIEF</span>
              </div>

              {toolTab === 'overview' ? (
                <div className="ucode-tool-grid">
                  {GRID_TOOL_VIEWS.map(view => (
                    <button key={view.id} className="ucode-tool-card" onClick={() => setToolTab(view.id as DashboardToolTab)}>
                      <div className="ucode-tool-card-title">{view.name}</div>
                      <div className="ucode-tool-card-subtitle">{view.subtitle}</div>
                      <div className="ucode-tool-card-summary">{view.summary}</div>
                    </button>
                  ))}
                </div>
              ) : activeTool ? (
                <div className="ucode-tool-detail">
                  <h3>{activeTool.name}</h3>
                  <p>{activeTool.summary}</p>

                  <div className="ucode-tool-detail-section">
                    <h4>API Surface</h4>
                    <ul>
                      {activeTool.apis.map(api => (
                        <li key={api}>{api}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="ucode-tool-detail-section">
                    <h4>Upgrade Goals</h4>
                    <ul>
                      {activeTool.upgrade.map(item => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>

                  <button className="ucode-back-btn" onClick={() => setToolTab('overview')}>
                    <Icon name="arrow_back" size={14} />
                    Back to Dashboard
                  </button>
                </div>
              ) : null}
            </aside>
          </main>
        </div>
      </div>
    </GridUIContext.Provider>
  )
}
