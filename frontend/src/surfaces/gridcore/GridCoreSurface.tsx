/* ═══════════════════════════════════════════════════════════════════
   GridCoreSurface — Grid Tools Hub (Map, Grid Editor, Assets, Settings)
   ═══════════════════════════════════════════════════════════════════
   ⚠️  IMPORTANT: This surface uses grid-based CSS styles that are
   intentionally SEPARATE from USX styles. Do NOT merge gridui styles
   with USX styles — they have unique rendering requirements (grid
   algebra, teletext, character maps) that conflict with USX layout.
   ═══════════════════════════════════════════════════════════════════
   Panels:
   - Map (spatial navigation, cities, bookmarks)
   - Grid (grid editor, layers, cell editor)
   - Assets (font manager, sprite library, import/export)
   - Settings (system preferences, themes, surface settings)
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'
import { GlobalToolbar, ToolbarTab } from '../../components/GlobalToolbar'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar from '../../components/VaultSidebar'
import { GridUIContext, useGridUIStore } from '../gridui/GridUIStore'
import { MapPanel } from '../gridui/panels/MapPanel'
import { GridEditorPanel } from '../gridui/panels/GridEditorPanel'
import { AssetsPanel } from '../gridui/panels/AssetsPanel'
import { SettingsPanel } from '../gridui/panels/SettingsPanel'
import '../../styles/hub/index.css'
import '../../styles/global-toolbar.css'

// ─── Types ──────────────────────────────────────────────────────────
type GridCoreTab = 'map' | 'grid' | 'assets' | 'settings'

const GRIDCORE_TABS: { id: GridCoreTab; icon: string; label: string }[] = [
  { id: 'map', icon: 'map', label: 'Map' },
  { id: 'grid', icon: 'grid_view', label: 'Grid' },
  { id: 'assets', icon: 'inventory_2', label: 'Assets' },
  { id: 'settings', icon: 'tune', label: 'Grid Settings' },
]

// ─── Main Component ────────────────────────────────────────────────
export default function GridCoreSurface() {
  const [activeTab, setActiveTab] = useState<GridCoreTab>('map')
  const { sidebarOpen, toggleSidebar } = useSurfaceShell()
  const gridStore = useGridUIStore()

  const renderContent = () => {
    switch (activeTab) {
      case 'map':
        return <MapPanel />
      case 'grid':
        return <GridEditorPanel />
      case 'assets':
        return <AssetsPanel />
      case 'settings':
        return <SettingsPanel />
      default:
        return <MapPanel />
    }
  }

  return (
    <GridUIContext.Provider value={gridStore}>
      <div className="usx-surface-layout">
        <GlobalToolbar
          tabs={GRIDCORE_TABS.map(t => ({
            id: t.id,
            icon: t.icon,
            label: t.label,
            active: activeTab === t.id,
            onClick: () => setActiveTab(t.id),
          }))}
          onToggleSidebar={toggleSidebar}
          sidebarOpen={sidebarOpen}
        />
        <div className="usx-surface-body">
          <VaultSidebar open={sidebarOpen} onToggle={toggleSidebar} />
          <main className="usx-surface-main">
            {renderContent()}
          </main>
        </div>
      </div>
    </GridUIContext.Provider>
  )
}
