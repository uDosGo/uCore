/* ═══════════════════════════════════════════════════════════════════
   SnackMachineSurface — USX Schema v3.1 Snack Management Surface
   ═══════════════════════════════════════════════════════════════════
   Dedicated surface for snack management, MCP integration, vault sync,
   and Dev Mode scheduling/autonomous execution patterns.
   Project Type: Operational (OP) | Autonomy Level: L3 (Collaborator)
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import { FilepickerSidebar, type SidebarNavItem } from '../../components/FilepickerSidebar'
import { renderMarkdown } from '../../utils/renderMarkdown'
import '../../styles/surfaces/snackmachine.css'

// ─── Types ──────────────────────────────────────────────────────
type SnackMachineTab = 'snacks' | 'workflows' | 'mcp' | 'vault' | 'variables' | 'scheduler'

interface SnackEntry {
  id: string
  type: string
  priority: string
  status: string
  source: string
  timestamp: string
  content?: Record<string, unknown>
}

interface WorkflowDefinition {
  id: string
  name: string
  description: string
  schedule: string
  created_at: string
  steps: Array<{ skill_id: string; params: Record<string, unknown> }>
  enabled: boolean
}

interface MCPServer {
  id: string
  name: string
  status: 'online' | 'offline' | 'connecting'
  transport: string
  tools: string[]
}

interface VariableEntry {
  key: string
  value: string
  scope: 'system' | 'user' | 'global'
  source: 'env' | 'vault' | 'config'
  last_modified: string
}

interface ScheduleEntry {
  id: string
  workflow_id: string
  workflow_name: string
  next_run: string
  cron: string
  enabled: boolean
}

const SNACKBAR_API = 'http://localhost:8484'

// ─── Sidebar Navigation ───────────────────────────────────────
const SIDEBAR_ITEMS: SidebarNavItem[] = [
  { id: 'snacks', icon: 'restaurant_menu', label: 'Snacks Queue', onClick: () => {} },
  { id: 'workflows', icon: 'account_tree', label: 'Workflows', onClick: () => {} },
  { id: 'mcp', icon: 'sync_alt', label: 'MCP Bridge', onClick: () => {} },
  { id: 'vault', icon: 'sync', label: 'Vault Sync', onClick: () => {} },
  { id: 'variables', icon: 'tune', label: 'Variables', onClick: () => {} },
  { id: 'scheduler', icon: 'schedule', label: 'Scheduler', onClick: () => {} },
]

// ─── Toolbar Tabs ───────────────────────────────────────────────
const TOOLBAR_TABS: ToolbarTab[] = [
  { id: 'snacks', icon: 'restaurant_menu', label: 'Snacks', onClick: () => {} },
  { id: 'workflows', icon: 'account_tree', label: 'Workflows', onClick: () => {} },
  { id: 'mcp', icon: 'sync_alt', label: 'MCP', onClick: () => {} },
  { id: 'vault', icon: 'sync', label: 'Vault', onClick: () => {} },
  { id: 'variables', icon: 'tune', label: 'Variables', onClick: () => {} },
  { id: 'scheduler', icon: 'schedule', label: 'Scheduler', onClick: () => {} },
]

// ─── Main Surface ─────────────────────────────────────────────
export default function SnackMachineSurface() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sidebarOpen, toggleSidebar } = useSurfaceShell()

  // Tab state from URL
  const tabState = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const raw = (params.get('tab') || 'snacks').toLowerCase()
    const validTab = ['snacks', 'workflows', 'mcp', 'vault', 'variables', 'scheduler'].includes(raw)
      ? raw as SnackMachineTab
      : 'snacks'
    return { raw, selectedTab: validTab }
  }, [location.search])

  const [tab, setTab] = useState<SnackMachineTab>(tabState.selectedTab)
  const [snacks, setSnacks] = useState<SnackEntry[]>([])
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([])
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([])
  const [variables, setVariables] = useState<VariableEntry[]>([])
  const [schedules, setSchedules] = useState<ScheduleEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Ensure sidebar is open on mount
    if (!sidebarOpen) toggleSidebar()
  }, [sidebarOpen, toggleSidebar])
  useEffect(() => {
    if (tabState.raw !== tabState.selectedTab) {
      navigate(`/snackmachine?tab=${tabState.selectedTab}`, { replace: true })
    }
  }, [navigate, tabState.raw, tabState.selectedTab])
  useEffect(() => { setTab(tabState.selectedTab) }, [tabState.selectedTab])

  // ─── Data Loading ───────────────────────────────────────────
  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [snacksRes, workflowsRes, mcpRes, varsRes, schedRes] = await Promise.all([
        fetch(`${SNACKBAR_API}/api/snacks`, { signal: AbortSignal.timeout(4000) }).catch(() => null),
        fetch(`${SNACKBAR_API}/api/workflows`, { signal: AbortSignal.timeout(4000) }).catch(() => null),
        fetch(`${SNACKBAR_API}/api/mcp/peers`, { signal: AbortSignal.timeout(4000) }).catch(() => null),
        fetch(`${SNACKBAR_API}/api/secrets/env`, { signal: AbortSignal.timeout(4000) }).catch(() => null),
        fetch(`${SNACKBAR_API}/api/scheduler`, { signal: AbortSignal.timeout(4000) }).catch(() => null),
      ])

      if (snacksRes?.ok) {
        const data = await snacksRes.json()
        setSnacks(Array.isArray(data.snacks) ? data.snacks : [])
      }
      if (workflowsRes?.ok) {
        const data = await workflowsRes.json()
        setWorkflows(Array.isArray(data.workflows) ? data.workflows : [])
      }
      if (mcpRes?.ok) {
        const data = await mcpRes.json()
        setMcpServers(Array.isArray(data.servers) ? data.servers : [])
      }
      if (varsRes?.ok) {
        const data = await varsRes.json()
        setVariables(Array.isArray(data.env_vars) ? data.env_vars : [])
      }
      if (schedRes?.ok) {
        const data = await schedRes.json()
        setSchedules(Array.isArray(data.schedules) ? data.schedules : [])
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 10000)
    return () => clearInterval(interval)
  }, [loadData])

  // ─── Tab Content Renderers ───────────────────────────────────
  const renderSnacksTab = () => (
    <div className="sm-tab-content">
      <div className="sm-section">
        <div className="sm-section-header">
          <Icon name="restaurant_menu" />
          <h3>Snacks Queue</h3>
          <span className="sm-badge">{snacks.length} items</span>
        </div>
        <div className="sm-card-content">
          {snacks.length === 0 ? (
            <p className="sm-text">No snacks in queue. System is idle.</p>
          ) : (
            <div className="sm-snacks-list">
              {snacks.slice(0, 50).map(snack => (
                <div key={snack.id} className="sm-snack-item">
                  <span className="sm-snack-time">{snack.timestamp?.slice(11, 19) || '--:--:--'}</span>
                  <span className="sm-snack-type">{snack.type}</span>
                  <span className={`sm-snack-status ${snack.status === 'failed' ? 'error' : 'info'}`}>
                    {snack.status}
                  </span>
                  <span className="sm-snack-source">{snack.source}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderWorkflowsTab = () => (
    <div className="sm-tab-content">
      <div className="sm-section">
        <div className="sm-section-header">
          <Icon name="account_tree" />
          <h3>Workflow Definitions</h3>
          <span className="sm-badge">{workflows.length} workflows</span>
        </div>
        <div className="sm-card-content">
          {workflows.length === 0 ? (
            <p className="sm-text">No workflows defined. Create one in the Workflow surface.</p>
          ) : (
            <div className="sm-workflows-list">
              {workflows.map(wf => (
                <div key={wf.id} className="sm-workflow-item">
                  <div className="sm-workflow-header">
                    <span className="sm-workflow-name">{wf.name}</span>
                    <span className={`sm-workflow-schedule ${wf.schedule === 'manual' ? 'manual' : ''}`}>
                      {wf.schedule}
                    </span>
                  </div>
                  <p className="sm-workflow-desc">{wf.description}</p>
                  <div className="sm-workflow-steps">
                    {wf.steps.map((step, i) => (
                      <span key={i} className="sm-step-badge">{step.skill_id}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderMCPTab = () => (
    <div className="sm-tab-content">
      <div className="sm-section">
        <div className="sm-section-header">
          <Icon name="sync_alt" />
          <h3>MCP Bridge Status</h3>
        </div>
        <div className="sm-card-content">
          {mcpServers.length === 0 ? (
            <p className="sm-text">No MCP servers configured.</p>
          ) : (
            <div className="sm-mcp-list">
              {mcpServers.map(server => (
                <div key={server.id} className="sm-mcp-item">
                  <span className={`sm-mcp-status ${server.status}`} />
                  <span className="sm-mcp-name">{server.name}</span>
                  <span className="sm-mcp-transport">{server.transport}</span>
                  <span className="sm-mcp-tools">{server.tools.length} tools</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderVaultTab = () => (
    <div className="sm-tab-content">
      <div className="sm-section">
        <div className="sm-section-header">
          <Icon name="sync" />
          <h3>Vault Sync Status</h3>
        </div>
        <div className="sm-card-content">
          <p className="sm-text">Vault synchronization for snacks and workflows.</p>
          <div className="sm-vault-actions">
            <button className="sm-action-btn" onClick={() => console.log('Sync triggered')}>
              <Icon name="sync" /> Trigger Sync
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderVariablesTab = () => (
    <div className="sm-tab-content">
      <div className="sm-section">
        <div className="sm-section-header">
          <Icon name="tune" />
          <h3>Consolidated Variables</h3>
          <span className="sm-badge">{variables.length} variables</span>
        </div>
        <div className="sm-card-content">
          {variables.length === 0 ? (
            <p className="sm-text">No variables found. Check system configuration.</p>
          ) : (
            <div className="sm-variables-list">
              {variables.slice(0, 30).map(v => (
                <div key={v.key} className="sm-variable-item">
                  <code className="sm-var-key">{v.key}</code>
                  <span className="sm-var-scope" data-scope={v.scope}>{v.scope}</span>
                  <span className="sm-var-source" data-source={v.source}>{v.source}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderSchedulerTab = () => (
    <div className="sm-tab-content">
      <div className="sm-section">
        <div className="sm-section-header">
          <Icon name="schedule" />
          <h3>Scheduled Workflows</h3>
          <span className="sm-badge">{schedules.length} schedules</span>
        </div>
        <div className="sm-card-content">
          {schedules.length === 0 ? (
            <p className="sm-text">No scheduled workflows. Enable auto-scheduling in Dev Mode.</p>
          ) : (
            <div className="sm-schedules-list">
              {schedules.map(sched => (
                <div key={sched.id} className="sm-schedule-item">
                  <span className="sm-schedule-workflow">{sched.workflow_name}</span>
                  <code className="sm-schedule-cron">{sched.cron}</code>
                  <span className="sm-schedule-next">{sched.next_run}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  // ─── Render ───────────────────────────────────────────────────
  const renderTabContent = () => {
    switch (tab) {
      case 'snacks': return renderSnacksTab()
      case 'workflows': return renderWorkflowsTab()
      case 'mcp': return renderMCPTab()
      case 'vault': return renderVaultTab()
      case 'variables': return renderVariablesTab()
      case 'scheduler': return renderSchedulerTab()
      default: return renderSnacksTab()
    }
  }

  // Update toolbar tabs with active state
  const activeToolbarTabs = TOOLBAR_TABS.map(t => ({
    ...t,
    active: t.id === tab,
    onClick: () => navigate(`/snackmachine?tab=${t.id}`, { replace: true }),
  }))

  return (
    <div className="usx-surface-layout">
      <GlobalToolbar
        tabs={activeToolbarTabs}
        onToggleSidebar={toggleSidebar}
        sidebarOpen={sidebarOpen}
        sidebarToggleLabel="SnackMachine sidebar"
        rightExtra={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span className="hub-status-badge">{loading ? 'Loading...' : `${snacks.length} snacks`}</span>
          </div>
        }
      />

      <div className="usx-surface-body">
        <FilepickerSidebar
          open={sidebarOpen}
          showModeTabs
          sidebarMode="server"
          serverNavItems={SIDEBAR_ITEMS}
        />

        <main className="usx-surface-main">
          {error && (
            <div className="sm-error-banner">
              <Icon name="error" />
              <span>{error}</span>
            </div>
          )}
          {renderTabContent()}
        </main>
      </div>
    </div>
  )
}