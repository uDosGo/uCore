/* ═══════════════════════════════════════════════════════════════════
   USystemSurface — USX Schema v3.1 System Administration Surface
   ═══════════════════════════════════════════════════════════════════
   System admin config: pages, tools, secrets, settings.
   Extracted from UServerSurface to separate admin from backend ops.
   Project Type: Technical (TC) | Autonomy Level: L4 (Delegator)
   Binder: ⚙️ Technical/Infrastructure | Tags: #system #admin #config
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar, { type SidebarNavItem } from '../../components/VaultSidebar'
import { ToolsPanel, SystemPagesPanel } from '../systemtools/SystemToolsSurface'
import { SettingsPanel } from '../system/SettingsPanel'
import SecretStorePanel from '../system/SecretStorePanel'

type SystemTab = 'pages' | 'tools' | 'secrets' | 'settings'

const SYSTEM_TABS: SystemTab[] = ['pages', 'tools', 'secrets', 'settings']

function PagesTab() {
  return (
    <div className="workflow-panel">
      <div className="workflow-panel-header">
        <h3>System Pages</h3>
        <span className="workflow-panel-count">S100-S899</span>
      </div>
      <SystemPagesPanel />
    </div>
  )
}

function ToolsTab() {
  return (
    <div className="workflow-panel">
      <div className="workflow-panel-header">
        <h3>Tools</h3>
        <span className="workflow-panel-count">Tool Registry</span>
      </div>
      <ToolsPanel />
    </div>
  )
}

function SecretsTab() {
  return (
    <div className="workflow-panel">
      <div className="workflow-panel-header">
        <h3>Secret Store</h3>
        <span className="workflow-panel-count">AES-256-GCM</span>
      </div>
      <SecretStorePanel />
    </div>
  )
}

function SettingsTab() {
  return (
    <div className="workflow-panel">
      <div className="workflow-panel-header">
        <h3>Settings</h3>
        <span className="workflow-panel-count">Configuration</span>
      </div>
      <SettingsPanel />
    </div>
  )
}

export default function USystemSurface() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sidebarOpen, toggleSidebar } = useSurfaceShell()

  const tabState = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const raw = (params.get('tab') || 'pages').toLowerCase()
    const candidate = raw as SystemTab
    return { selectedTab: SYSTEM_TABS.includes(candidate) ? candidate : 'pages' }
  }, [location.search])

  const [activeTab, setActiveTab] = useState<SystemTab>(tabState.selectedTab)

  const setTabAndRoute = (nextTab: SystemTab) => {
    setActiveTab(nextTab)
    navigate(`/system?tab=${nextTab}`)
  }

  const systemNavItems: SidebarNavItem[] = [
    { id: 'pages', icon: 'dashboard', label: 'System Pages', active: activeTab === 'pages', onClick: () => setTabAndRoute('pages') },
    { id: 'tools', icon: 'build', label: 'Tools', active: activeTab === 'tools', onClick: () => setTabAndRoute('tools') },
    { id: 'secrets', icon: 'key', label: 'Secret Store', active: activeTab === 'secrets', onClick: () => setTabAndRoute('secrets') },
    { id: 'settings', icon: 'settings', label: 'Settings', active: activeTab === 'settings', onClick: () => setTabAndRoute('settings') },
  ]

  const toolbarTabs: ToolbarTab[] = [
    { id: 'pages', icon: 'dashboard', label: 'Pages', active: activeTab === 'pages', onClick: () => setTabAndRoute('pages') },
    { id: 'tools', icon: 'build', label: 'Tools', active: activeTab === 'tools', onClick: () => setTabAndRoute('tools') },
    { id: 'secrets', icon: 'key', label: 'Secrets', active: activeTab === 'secrets', onClick: () => setTabAndRoute('secrets') },
    { id: 'settings', icon: 'settings', label: 'Settings', active: activeTab === 'settings', onClick: () => setTabAndRoute('settings') },
  ]

  return (
    <div className="workflow-surface">
      <GlobalToolbar
        tabs={toolbarTabs}
        onToggleSidebar={toggleSidebar}
        sidebarOpen={sidebarOpen}
        sidebarToggleLabel="System sidebar"
      />
      <div className="usx-surface-body" style={{ position: 'relative' }}>
        <VaultSidebar
          open={sidebarOpen}
          showModeTabs
          sidebarMode="server"
          serverNavItems={systemNavItems}
        />
        <main className="usx-surface-main workflow-surface-main">
          {activeTab === 'pages' && <PagesTab />}
          {activeTab === 'tools' && <ToolsTab />}
          {activeTab === 'secrets' && <SecretsTab />}
          {activeTab === 'settings' && <SettingsTab />}
        </main>
      </div>
    </div>
  )
}