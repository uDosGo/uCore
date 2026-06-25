/* ═══════════════════════════════════════════════════════════════════
   USystemSurface — USX Schema v3.1 System Administration Surface
   ═══════════════════════════════════════════════════════════════════
   Tabs: Fallback, Tools, Services, Variables, Global, User
   Supports ?page= parameter to render S-page tools inline with shell.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar, { type SidebarNavItem } from '../../components/VaultSidebar'
import { ServicesPanel, SPageToolsPanel } from '../systemtools/SystemToolsSurface'
import SystemPagesBrowser from './SystemPagesBrowser'
import GlobalSettingsPanel from './GlobalSettingsPanel'
import UserSettingsPanel from './UserSettingsPanel'
import VariablesPanel from './VariablesPanel'
import { S_PAGE_COMPONENTS } from '../../pages/spage-registry'
import './system-surface.css'

type SystemTab = 'pages' | 'tools' | 'services' | 'variables' | 'global-settings' | 'user-settings'

const SYSTEM_TABS: SystemTab[] = ['pages', 'tools', 'services', 'variables', 'global-settings', 'user-settings']

export default function USystemSurface() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sidebarOpen, toggleSidebar } = useSurfaceShell()

  // Resolve tab from ?tab= param
  const tabState = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const raw = (params.get('tab') || 'pages').toLowerCase()
    const candidate = raw as SystemTab
    return { selectedTab: SYSTEM_TABS.includes(candidate) ? candidate : 'pages' }
  }, [location.search])

  // Resolve ?page= for inline S-page tool rendering
  const inlineSPage = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const page = params.get('page') || ''
    if (!page) return null
    const Comp = S_PAGE_COMPONENTS[page.toLowerCase()]
    return Comp ? <Comp /> : null
  }, [location.search])

  const [activeTab, setActiveTab] = useState<SystemTab>(tabState.selectedTab)

  const setTabAndRoute = (nextTab: SystemTab) => {
    setActiveTab(nextTab)
    navigate(`/system?tab=${nextTab}`)
  }

  const systemNavItems: SidebarNavItem[] = [
    { id: 'pages', icon: 'dashboard', label: 'Fallback', active: activeTab === 'pages', onClick: () => setTabAndRoute('pages') },
    { id: 'tools', icon: 'build', label: 'Tools', active: activeTab === 'tools', onClick: () => setTabAndRoute('tools') },
    { id: 'services', icon: 'hub', label: 'Services', active: activeTab === 'services', onClick: () => setTabAndRoute('services') },
    { id: 'variables', icon: 'tune', label: 'Variables', active: activeTab === 'variables', onClick: () => setTabAndRoute('variables') },
    { id: 'global-settings', icon: 'settings', label: 'Global', active: activeTab === 'global-settings', onClick: () => setTabAndRoute('global-settings') },
    { id: 'user-settings', icon: 'person', label: 'User', active: activeTab === 'user-settings', onClick: () => setTabAndRoute('user-settings') },
  ]

  const toolbarTabs: ToolbarTab[] = [
    { id: 'pages', icon: 'dashboard', label: 'Fallback', active: activeTab === 'pages', onClick: () => setTabAndRoute('pages') },
    { id: 'tools', icon: 'build', label: 'Tools', active: activeTab === 'tools', onClick: () => setTabAndRoute('tools') },
    { id: 'services', icon: 'hub', label: 'Services', active: activeTab === 'services', onClick: () => setTabAndRoute('services') },
    { id: 'variables', icon: 'tune', label: 'Variables', active: activeTab === 'variables', onClick: () => setTabAndRoute('variables') },
    { id: 'global-settings', icon: 'settings', label: 'Global', active: activeTab === 'global-settings', onClick: () => setTabAndRoute('global-settings') },
    { id: 'user-settings', icon: 'person', label: 'User', active: activeTab === 'user-settings', onClick: () => setTabAndRoute('user-settings') },
  ]

  return (
    <div className="usx-surface-layout workflow-surface">
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
        <main className="usx-surface-main">
          {activeTab === 'pages' && !inlineSPage && (
            <div className="workflow-panel">
              <div className="workflow-panel-header">
                <h3><Icon name="dashboard" size={16} /> System Pages</h3>
                <span className="workflow-panel-count">S100-S899</span>
              </div>
              <SystemPagesBrowser />
            </div>
          )}
          {activeTab === 'tools' && !inlineSPage && (
            <div className="workflow-panel">
              <div className="workflow-panel-header">
                <h3><Icon name="build" size={16} /> System Tools</h3>
                <span className="workflow-panel-count">S-Page Tools</span>
              </div>
              <SPageToolsPanel />
            </div>
          )}
          {activeTab === 'services' && (
            <div className="workflow-panel">
              <div className="workflow-panel-header">
                <h3><Icon name="hub" size={16} /> System Services</h3>
                <span className="workflow-panel-count">Non-S-page</span>
              </div>
              <ServicesPanel />
            </div>
          )}
          {activeTab === 'variables' && (
            <div className="workflow-panel">
              <div className="workflow-panel-header">
                <h3><Icon name="tune" size={16} /> Variable Store</h3>
                <span className="workflow-panel-count">$Variables</span>
              </div>
              <VariablesPanel />
            </div>
          )}
          {activeTab === 'global-settings' && (
            <div className="workflow-panel">
              <div className="workflow-panel-header">
                <h3><Icon name="settings" size={16} /> Global Settings</h3>
                <span className="workflow-panel-count">System-wide</span>
              </div>
              <GlobalSettingsPanel />
            </div>
          )}
          {activeTab === 'user-settings' && (
            <div className="workflow-panel">
              <div className="workflow-panel-header">
                <h3><Icon name="person" size={16} /> User Settings</h3>
                <span className="workflow-panel-count">Per-user</span>
              </div>
              <UserSettingsPanel />
            </div>
          )}

          {/* Render S-page tool inline when ?page= is set */}
          {inlineSPage && (
            <div className="workflow-panel" style={{ flex: 1, overflow: 'auto' }}>
              {inlineSPage}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}