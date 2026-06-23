/* ═══════════════════════════════════════════════════════════════════
   UServerSurface — USX Schema v3.1 Server Management Surface
   ═══════════════════════════════════════════════════════════════════
   uServer backend services — secret server, OAuth, sync, and surface
   definitions. Uses USX surface header pattern with GlobalToolbar.
   System pages: S100-S899 (fallbacks S100-S190)
   Project Type: Technical (TC) | Autonomy Level: L4 (Delegator)
   Binder: ⚙️ Technical/Infrastructure | Tags: #server #backend #services
   Wiki: [[Server Management Hub]] | Backlinks: [[uServer Backend]]
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { GlobalToolbar } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar, { SidebarNavItem } from '../../components/VaultSidebar'
import AssistUISurface from '../assistui/AssistUISurface'
import SystemToolsSurface, { ToolsPanel, SystemPagesPanel } from '../systemtools/SystemToolsSurface'
import { SettingsPanel } from '../system/SettingsPanel'
import SecretStorePanel from '../system/SecretStorePanel'
import type { RouterAgent, RouterStats } from '../../shared/types/agent-router'
import '../../styles/userver.css'

// ─── Constants ───────────────────────────────────────────────────────
const SNACKBAR_API = 'http://localhost:8484'

// ─── Legacy Tab Mapping ──────────────────────────────────────────────
const LEGACY_TAB_MAP: Record<string, string> = {
  'overview': 'dashboard',
  'secrets-store': 'secrets',
  'service-status': 'services',
  'workflow-status': 'workflows',
  'agent-router': 'agents',
}

// ─── Types ──────────────────────────────────────────────────────────
// Core backend ops: no admin/config tabs (pages, tools, secrets, settings → /system)
const SERVER_TABS = [
  'dashboard',
  'ingest',
  'missions',
  'story',
  'services',
  'logs',
  'workflows',
  'budget',
  'agents',
  'snacks',
] as const
type UServerTab = typeof SERVER_TABS[number]

interface ServiceStatus {
  name: string
  status: 'up' | 'degraded' | 'down'
  port: number
  uptime: number
  type: 'system' | 'user'
  description: string
}

interface LogEntry {
  timestamp: string
  service: string
  level: 'info' | 'warn' | 'error'
  message: string
}

interface SnackEntry {
  id: string
  type: string
  priority: string
  status: string
  source: string
  timestamp: string
  content?: Record<string, unknown>
}

interface Workflow {
  name: string
  status: 'running' | 'idle' | 'failed' | 'completed'
  lastRun: string
  schedule: string
}

interface WorkflowDefinition {
  id: string
  name: string
  description: string
  schedule: string
  step_count: number
}

interface WorkflowRunResponse {
  run_id: string
  workflow_id: string
  status: 'completed' | 'failed'
  finished_at: string
}

interface BudgetStatusResponse {
  usage: {
    period_start: string
    period_end: string
    total_cost: number
    total_calls: number
    blocked_calls: number
    monthly_limit: number
    remaining_budget: number
    over_limit: boolean
  }
  policy: {
    monthly_usd_limit: number
    default_estimated_cost: number
    guarded_endpoints: string[]
    per_model_limits: Record<string, number>
  }
}

interface BudgetUsageEntry {
  ts: string
  endpoint: string
  provider: string
  model: string
  estimated_cost: number
  actual_cost: number
  status_code: number
  blocked: number
}

interface AgentInfo {
  name: string
  status: 'active' | 'idle'
  model: string
  tasks: number
  uptime: string
}

interface SurfaceInfo {
  name: string
  label: string
  description: string
  port: number
  status: 'running' | 'stopped' | 'error'
  icon: string
  color: string
  url: string
}

type KnowledgeWorkspace = {
  id: string
  name: string
  source: string
}

type KnowledgeDocument = {
  id: string
  title: string
  type: string
  updated_at: string
}

type AdapterRow = {
  id: string
  mission: string
  task: string
  binder: string
  updated_at: string | null
}

type SourceStatus = {
  name: string
  local_path: string
  enabled: boolean
  file_count: number
  tags: string[]
}

type IndexCoverageSource = {
  source: string
  expected_count: number
  indexed_count: number
  coverage_pct: number
  workspace: string
  last_indexed_at: string | null
}

type IndexCoverageResponse = {
  status: string
  source_count: number
  indexed_total: number
  expected_total: number
  coverage_pct: number
  sources: IndexCoverageSource[]
}

// ─── Default Data ───────────────────────────────────────────────────
const DEFAULT_SERVICES: ServiceStatus[] = [
  { name: 'snackbar', status: 'up', port: 8484, uptime: 99.9, type: 'system', description: 'Container orchestrator & workflow runner' },
  { name: 'secret-server', status: 'up', port: 30001, uptime: 99.8, type: 'user', description: 'AES-256-GCM encrypted secret vault' },
  { name: 'hivemind', status: 'up', port: 8485, uptime: 99.7, type: 'system', description: 'AI orchestration & agent routing' },
  { name: 'feed-spool', status: 'up', port: 8486, uptime: 99.5, type: 'system', description: 'Feed spooler & transport' },
  { name: 'vault-mcp', status: 'degraded', port: 0, uptime: 95.2, type: 'user', description: 'MCP server for Vault access' },
  { name: 'email-feed', status: 'down', port: 0, uptime: 0, type: 'user', description: 'Email to feed processor' },
]

const DEFAULT_LOGS: LogEntry[] = [
  { timestamp: '2026-05-23 16:15:22', service: 'snackbar', level: 'info', message: 'Workflow "daily-docs-sync" completed successfully' },
  { timestamp: '2026-05-23 16:14:00', service: 'hivemind', level: 'info', message: 'Agent "code-reviewer" dispatched to PR #42' },
  { timestamp: '2026-05-23 16:12:45', service: 'secret-server', level: 'info', message: 'Secret retrieved: vault/imap_config' },
  { timestamp: '2026-05-23 16:10:30', service: 'email-feed', level: 'error', message: 'IMAP connection failed: invalid credentials' },
  { timestamp: '2026-05-23 16:08:00', service: 'snackbar', level: 'warn', message: 'Container "feed-watcher" restarting (OOM)' },
  { timestamp: '2026-05-23 16:05:00', service: 'vault-mcp', level: 'info', message: 'MCP client connected: uCode2 Gateway' },
  { timestamp: '2026-05-23 16:00:00', service: 'feed-spool', level: 'info', message: 'Spool rotation completed: 42 entries archived' },
  { timestamp: '2026-05-23 15:55:00', service: 'hivemind', level: 'info', message: 'Health check: all agents responsive' },
  { timestamp: '2026-05-23 15:50:00', service: 'snackbar', level: 'info', message: 'Snack "auto-label@developer" executed' },
  { timestamp: '2026-05-23 15:45:00', service: 'secret-server', level: 'warn', message: 'Token rotation recommended (30 days since last)' },
]

const DEFAULT_WORKFLOWS: Workflow[] = [
  { name: 'daily-docs-sync', status: 'completed', lastRun: '2026-05-23 04:00', schedule: '0 4 * * *' },
  { name: 'health-check', status: 'running', lastRun: '2026-05-23 16:00', schedule: '0 * * * *' },
  { name: 'auto-label-issues', status: 'idle', lastRun: '2026-05-23 15:30', schedule: '*/30 * * * *' },
  { name: 'backup-vault', status: 'completed', lastRun: '2026-05-23 02:00', schedule: '0 2 * * *' },
  { name: 'feed-poll', status: 'failed', lastRun: '2026-05-23 16:10', schedule: '*/15 * * * *' },
]

const DEFAULT_AGENTS: AgentInfo[] = [
  { name: 'code-reviewer', status: 'active', model: 'gpt-4', tasks: 42, uptime: '12h' },
  { name: 'hivemind-orchestrator', status: 'active', model: 'gpt-4', tasks: 128, uptime: '7d' },
  { name: 'feed-watcher', status: 'idle', model: 'gpt-3.5', tasks: 0, uptime: '3d' },
  { name: 'auto-labeler', status: 'active', model: 'gpt-3.5', tasks: 256, uptime: '14d' },
  { name: 'doc-syncer', status: 'idle', model: 'gpt-4', tasks: 18, uptime: '5d' },
]

const MISSION_CONTROL_NOTES = [
  { id: 1, title: 'Surface Consolidation', status: 'active', priority: 'high', description: 'Consolidate surfaces into canonical lineup.' },
  { id: 2, title: 'USX Component Audit', status: 'active', priority: 'medium', description: 'Audit and standardise USX components.' },
  { id: 3, title: 'Documentation Refresh', status: 'planned', priority: 'low', description: 'Update documentation after UI/server consolidation.' },
]

const DEFAULT_SURFACES: SurfaceInfo[] = [
  { name: 'gridui', label: 'uCode1', description: 'Grid Layer Composer', port: 5178, status: 'running', icon: 'widgets', color: '#f0883e', url: 'http://localhost:5178' },
  { name: 'chatui', label: 'Chat UI', description: 'AI Chat Interface', port: 5182, status: 'running', icon: 'chat', color: '#58a6ff', url: 'http://localhost:5182' },
  { name: 'browserui', label: 'Web Reader', description: 'Research Bookmarks', port: 5179, status: 'running', icon: 'visibility', color: '#f59e0b', url: 'http://localhost:5179' },
]

// ─── Default Tab Components ───────────────────────────────────────────
function DashboardTab({ services, workflows, logs, surfaces, onSecretStoreClick }: {
  services: ServiceStatus[]
  workflows: Workflow[]
  logs: LogEntry[]
  surfaces: SurfaceInfo[]
  onSecretStoreClick?: () => void
}) {
  const upCount = services.filter(s => s.status === 'up').length
  const degradedCount = services.filter(s => s.status === 'degraded').length
  const downCount = services.filter(s => s.status === 'down').length
  const runningWorkflows = workflows.filter(w => w.status === 'running').length

  return (
    <div className="userver-grid">
      <div className="userver-card userver-welcome-card">
        <div className="userver-card-content">
          <h2 className="userver-heading">Server Operations</h2>
          <p className="userver-text">
            Monitoring {services.length} services · {workflows.length} workflows · {logs.length} log entries
          </p>
          <div className="userver-stats-row">
            <div className="userver-stat">
              <span className="userver-stat-value">{upCount}</span>
              <span className="userver-stat-label">Up</span>
            </div>
            <div className="userver-stat">
              <span className="userver-stat-value">{degradedCount}</span>
              <span className="userver-stat-label">Degraded</span>
            </div>
            <div className="userver-stat">
              <span className="userver-stat-value">{downCount}</span>
              <span className="userver-stat-label">Down</span>
            </div>
            <div className="userver-stat">
              <span className="userver-stat-value">{runningWorkflows}</span>
              <span className="userver-stat-label">Running</span>
            </div>
          </div>
        </div>
      </div>

      <div className="userver-card" style={{ borderLeft: '3px solid #f0883e', background: 'linear-gradient(135deg, rgba(240,136,62,0.08), rgba(240,136,62,0.02))' }}>
        <div className="userver-card-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
            <Icon name="key" size={18} style={{ color: '#f0883e' }} />
            Secret Store
          </h3>
          <span className="userver-card-subtitle">AES-256-GCM encrypted credentials</span>
        </div>
        <div className="userver-card-content">
          <p className="userver-text" style={{ marginBottom: 12 }}>
            Manage API keys, tokens, and encrypted credentials. All secrets are stored at rest with AES-256-GCM encryption.
          </p>
          <button
            className="userver-action-btn"
            onClick={onSecretStoreClick}
            style={{ background: '#f0883e20', color: '#f0883e', border: '1px solid #f0883e40' }}
          >
            <Icon name="key" size={14} style={{ marginRight: 6 }} />
            Open Secret Store
          </button>
        </div>
      </div>

      <div className="userver-card">
        <div className="userver-card-header">
          <h3>Surfaces</h3>
          <span className="userver-card-subtitle">uDos Connect surface registry</span>
        </div>
        <div className="userver-card-content">
          {surfaces.map(surface => (
            <div key={surface.name} className="userver-service-row">
              <div className="userver-service-info">
                <span className="userver-service-name">
                  <Icon name={surface.icon} size={16} style={{ marginRight: 6, color: surface.color }} />
                  {surface.label}
                </span>
                <span className="userver-service-desc">{surface.description}</span>
              </div>
              <div className="userver-service-meta">
                <a href={surface.url} className="userver-surface-link" style={{ color: surface.color }}>
                  :{surface.port}
                </a>
                <span className={`userver-service-status ${surface.status}`}>
                  {surface.status === 'running' ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="userver-card">
        <div className="userver-card-header">
          <h3>Service Status</h3>
        </div>
        <div className="userver-card-content">
          {services.slice(0, 4).map(svc => (
            <div key={svc.name} className="userver-service-row">
              <div className="userver-service-info">
                <span className="userver-service-name">{svc.name}</span>
                <span className="userver-service-desc">{svc.description}</span>
              </div>
              <div className="userver-service-meta">
                <span className={`userver-service-status ${svc.status}`}>
                  {svc.status === 'up' ? 'Online' : svc.status === 'degraded' ? 'Degraded' : 'Offline'}
                </span>
                {svc.port > 0 && <span className="userver-service-port">:{svc.port}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="userver-card">
        <div className="userver-card-header">
          <h3>Recent Logs</h3>
        </div>
        <div className="userver-card-content">
          {logs.slice(0, 5).map((log, idx) => (
            <div key={idx} className="userver-log-entry">
              <span className="userver-log-time">{log.timestamp}</span>
              <span className="userver-log-service">{log.service}</span>
              <span className={`userver-log-level ${log.level}`}>{log.level}</span>
              <span className="userver-log-message">{log.message}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="userver-card">
        <div className="userver-card-header">
          <h3>Workflows</h3>
        </div>
        <div className="userver-card-content">
          {workflows.slice(0, 3).map(wf => (
            <div key={wf.name} className="userver-workflow-row">
              <div className="userver-workflow-info">
                <span className="userver-workflow-name">{wf.name}</span>
                <span className="userver-workflow-schedule">{wf.schedule}</span>
              </div>
              <div className="userver-workflow-meta">
                <span className={`userver-workflow-status ${wf.status}`}>
                  {wf.status.charAt(0).toUpperCase() + wf.status.slice(1)}
                </span>
                <span className="userver-workflow-lastrun">{wf.lastRun}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ServicesTab({ services }: { services: ServiceStatus[] }) {
  return (
    <div>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Services</h2>
        </div>
      </div>
      <div className="userver-grid">
        {services.map(svc => (
          <div key={svc.name} className="userver-card">
            <div className="userver-card-header">
              <h3>{svc.name}</h3>
              <span className={`userver-service-status ${svc.status}`}>
                {svc.status === 'up' ? 'Online' : svc.status === 'degraded' ? 'Degraded' : 'Offline'}
              </span>
            </div>
            <div className="userver-card-content">
              <p className="userver-text" style={{ marginBottom: 8 }}>{svc.description}</p>
              <div className="userver-service-details">
                {svc.port > 0 && <span>Port: <strong>{svc.port}</strong></span>}
                <span>Type: <strong>{svc.type}</strong></span>
                <span>Uptime: <strong>{svc.uptime}%</strong></span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function LogsTab({
  logs,
  loading,
  error,
  onRefresh,
}: {
  logs: LogEntry[]
  loading: boolean
  error: string | null
  onRefresh: () => void
}) {
  const [filter, setFilter] = useState('')
  const filtered = filter
    ? logs.filter(log =>
        log.service.toLowerCase().includes(filter.toLowerCase()) ||
        log.message.toLowerCase().includes(filter.toLowerCase()) ||
        log.level.includes(filter.toLowerCase())
      )
    : logs

  return (
    <div>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Logs</h2>
        </div>
        <div className="userver-toolbar-actions" style={{ marginLeft: 'auto' }}>
          <button className="userver-action-btn" onClick={onRefresh} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>
      {error && (
        <div className="userver-card" style={{ margin: '0 16px 12px', borderLeft: '3px solid #f85149' }}>
          <div className="userver-card-content">
            <p className="userver-text" style={{ color: '#f85149' }}>{error}</p>
          </div>
        </div>
      )}
      <div className="userver-log-filter">
        <input
          type="text"
          placeholder="Filter by service, level, or message..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
        {filter && (
          <button className="userver-action-btn" onClick={() => setFilter('')}>Clear</button>
        )}
      </div>
      <div className="userver-card">
        <div className="userver-card-header">
          <h3>Log Entries ({filtered.length})</h3>
        </div>
        <div className="userver-card-content">
          {filtered.length === 0 ? (
            <p className="userver-text" style={{ textAlign: 'center', padding: 20 }}>
              No log entries match your filter.
            </p>
          ) : (
            filtered.map((log, idx) => (
              <div key={idx} className="userver-log-entry">
                <span className="userver-log-time">{log.timestamp}</span>
                <span className="userver-log-service">{log.service}</span>
                <span className={`userver-log-level ${log.level}`}>{log.level}</span>
                <span className="userver-log-message">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function WorkflowsTab({ workflows }: { workflows: Workflow[] }) {
  const [definitions, setDefinitions] = useState<WorkflowDefinition[]>([])
  const [selectedId, setSelectedId] = useState<string>('')
  const [workflowName, setWorkflowName] = useState('')
  const [skillId, setSkillId] = useState('tasker_sync')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string>('')
  const [logs, setLogs] = useState<string[]>([])

  const loadDefinitions = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/workflows`, {
        signal: AbortSignal.timeout(4000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const items = Array.isArray(data.workflows) ? data.workflows : []
      setDefinitions(items)
      if (!selectedId && items.length > 0) {
        setSelectedId(String(items[0].id || ''))
      }
      setMessage('')
    } catch (e: any) {
      setMessage(e?.message || 'Failed to load workflow definitions')
    } finally {
      setLoading(false)
    }
  }, [selectedId])

  useEffect(() => {
    void loadDefinitions()
  }, [loadDefinitions])

  const createWorkflow = async () => {
    if (!workflowName.trim() || !skillId.trim()) {
      setMessage('Name and Skill ID are required')
      return
    }
    setLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: workflowName.trim(),
          steps: [{ type: 'skill', skill_id: skillId.trim(), params: {} }],
        }),
        signal: AbortSignal.timeout(6000),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`)
      setWorkflowName('')
      setSelectedId(String(data.id || ''))
      setMessage('Workflow created')
      await loadDefinitions()
    } catch (e: any) {
      setMessage(e?.message || 'Failed to create workflow')
    } finally {
      setLoading(false)
    }
  }

  const runWorkflow = async () => {
    if (!selectedId) {
      setMessage('Select a workflow to run')
      return
    }
    setLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/workflows/${encodeURIComponent(selectedId)}/run`, {
        method: 'POST',
        signal: AbortSignal.timeout(15000),
      })
      const data: WorkflowRunResponse | any = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`)
      setMessage(`Run ${data.run_id} finished with status=${data.status}`)

      const logsRes = await fetch(`${SNACKBAR_API}/api/workflows/${encodeURIComponent(selectedId)}/logs?limit=20`, {
        signal: AbortSignal.timeout(6000),
      })
      if (logsRes.ok) {
        const logsData = await logsRes.json()
        const rows = Array.isArray(logsData.logs) ? logsData.logs : []
        setLogs(rows.map((row: any) => `${row.timestamp || ''} · ${row.event || 'event'} · ${row.message || ''}`))
      }
    } catch (e: any) {
      setMessage(e?.message || 'Failed to run workflow')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Workflows</h2>
        </div>
        <div className="userver-toolbar-actions" style={{ marginLeft: 'auto' }}>
          <button className="userver-action-btn" onClick={loadDefinitions} disabled={loading}>
            {loading ? 'Working...' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Runtime Controls</h3>
        </div>
        <div className="userver-card-content" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Workflow name"
            value={workflowName}
            onChange={e => setWorkflowName(e.target.value)}
            style={{ minWidth: 220 }}
          />
          <input
            type="text"
            placeholder="Skill ID (e.g. tasker_sync)"
            value={skillId}
            onChange={e => setSkillId(e.target.value)}
            style={{ minWidth: 220 }}
          />
          <button className="userver-action-btn" onClick={createWorkflow} disabled={loading}>
            Create
          </button>
          <select value={selectedId} onChange={e => setSelectedId(e.target.value)} style={{ minWidth: 240 }}>
            <option value="">Select workflow</option>
            {definitions.map(def => (
              <option key={def.id} value={def.id}>{def.name} ({def.step_count} steps)</option>
            ))}
          </select>
          <button className="userver-action-btn" onClick={runWorkflow} disabled={loading || !selectedId}>
            Run
          </button>
        </div>
        {message && (
          <div className="userver-card-content" style={{ paddingTop: 0 }}>
            <p className="userver-text">{message}</p>
          </div>
        )}
      </div>

      {logs.length > 0 && (
        <div className="userver-card" style={{ margin: '0 16px 16px' }}>
          <div className="userver-card-header">
            <h3>Latest Run Logs</h3>
          </div>
          <div className="userver-card-content">
            {logs.slice(0, 10).map((row, idx) => (
              <div key={idx} className="userver-log-entry">
                <span className="userver-log-message">{row}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="userver-grid">
        {workflows.map(wf => (
          <div key={wf.name} className="userver-card">
            <div className="userver-card-header">
              <h3>{wf.name}</h3>
              <span className={`userver-workflow-status ${wf.status}`}>
                {wf.status.charAt(0).toUpperCase() + wf.status.slice(1)}
              </span>
            </div>
            <div className="userver-card-content">
              <div className="userver-service-details">
                <span>Schedule: <strong>{wf.schedule}</strong></span>
                <span>Last run: <strong>{wf.lastRun}</strong></span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function BudgetTab() {
  const [status, setStatus] = useState<BudgetStatusResponse | null>(null)
  const [usage, setUsage] = useState<BudgetUsageEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string>('')

  const loadBudget = useCallback(async () => {
    setLoading(true)
    try {
      const [statusRes, usageRes] = await Promise.all([
        fetch(`${SNACKBAR_API}/api/budget/status`, { signal: AbortSignal.timeout(4000) }),
        fetch(`${SNACKBAR_API}/api/budget/usage?limit=20`, { signal: AbortSignal.timeout(4000) }),
      ])

      if (!statusRes.ok) throw new Error(`status HTTP ${statusRes.status}`)
      const statusData = await statusRes.json()
      setStatus(statusData)

      if (usageRes.ok) {
        const usageData = await usageRes.json()
        setUsage(Array.isArray(usageData.entries) ? usageData.entries : [])
      }

      setMessage('')
    } catch (e: any) {
      setMessage(e?.message || 'Failed to load budget data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadBudget()
  }, [loadBudget])

  const reloadPolicy = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/budget/reload`, {
        method: 'POST',
        signal: AbortSignal.timeout(4000),
      })
      if (!res.ok) throw new Error(`reload HTTP ${res.status}`)
      setMessage('Budget policy reloaded')
      await loadBudget()
    } catch (e: any) {
      setMessage(e?.message || 'Failed to reload budget policy')
      setLoading(false)
    }
  }

  const runSample = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/skills/route_task/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: 'Write a simple hello world function in Python',
          complexity: 'simple',
          execute: false,
        }),
        signal: AbortSignal.timeout(8000),
      })
      if (!res.ok) throw new Error(`run sample HTTP ${res.status}`)
      const data = await res.json()
      setMessage(`Sample executed. Budget check: ${data.success ? 'ALLOWED' : 'BLOCKED'}`)
      await loadBudget()
    } catch (e: any) {
      setMessage(e?.message || 'Failed to run sample')
      setLoading(false)
    }
  }

  const usageStats = status?.usage
  const policy = status?.policy

  return (
    <div>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Budget</h2>
          <span className="userver-card-subtitle">Usage logging and cost guardrails</span>
        </div>
        <div className="userver-toolbar-actions" style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="userver-action-btn" onClick={runSample} disabled={loading} title="Execute a sample task to test budget enforcement">
            {loading ? 'Running...' : 'Run Sample'}
          </button>
          <button className="userver-action-btn" onClick={loadBudget} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <button className="userver-action-btn" onClick={reloadPolicy} disabled={loading}>
            Reload Policy
          </button>
        </div>
      </div>

      {message && (
        <div className="userver-card" style={{ margin: '0 16px 16px' }}>
          <div className="userver-card-content">
            <p className="userver-text">{message}</p>
          </div>
        </div>
      )}

      <div className="userver-grid">
        <div className="userver-card">
          <div className="userver-card-header">
            <h3>Current Period</h3>
          </div>
          <div className="userver-card-content">
            <div className="userver-service-details" style={{ flexWrap: 'wrap', gap: 8 }}>
              <span>Total Cost: <strong>${usageStats?.total_cost?.toFixed(4) || '0.0000'}</strong></span>
              <span>Monthly Limit: <strong>${usageStats?.monthly_limit?.toFixed(2) || '0.00'}</strong></span>
              <span>Remaining: <strong>${usageStats?.remaining_budget?.toFixed(4) || '0.0000'}</strong></span>
              <span>Calls: <strong>{usageStats?.total_calls ?? 0}</strong></span>
              <span>Blocked: <strong>{usageStats?.blocked_calls ?? 0}</strong></span>
            </div>
            {usageStats?.over_limit && (
              <p className="userver-text" style={{ color: '#f85149', marginTop: 8 }}>
                Budget limit currently exceeded.
              </p>
            )}
          </div>
        </div>

        <div className="userver-card">
          <div className="userver-card-header">
            <h3>Policy</h3>
          </div>
          <div className="userver-card-content">
            <div className="userver-service-details" style={{ flexWrap: 'wrap', gap: 8 }}>
              <span>Default Cost: <strong>${policy?.default_estimated_cost?.toFixed(4) || '0.0000'}</strong></span>
              <span>Guarded Endpoints: <strong>{policy?.guarded_endpoints?.length ?? 0}</strong></span>
              <span>Per-Model Limits: <strong>{Object.keys(policy?.per_model_limits || {}).length}</strong></span>
            </div>
            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {(policy?.guarded_endpoints || []).map(endpoint => (
                <span key={endpoint} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 8, background: 'var(--pico-card-sectioning-background-color, #1c2128)' }}>
                  {endpoint}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Recent Usage</h3>
        </div>
        <div className="userver-card-content">
          {usage.length === 0 ? (
            <p className="userver-text">No usage entries recorded yet.</p>
          ) : (
            usage.slice(0, 20).map((row, idx) => (
              <div key={`${row.ts}-${idx}`} className="userver-log-entry">
                <span className="userver-log-time">{row.ts?.slice(11, 19) || '--:--:--'}</span>
                <span className="userver-log-service">{row.endpoint}</span>
                <span className={`userver-log-level ${row.blocked ? 'error' : 'info'}`}>
                  {row.blocked ? 'blocked' : `HTTP ${row.status_code}`}
                </span>
                <span className="userver-log-message">
                  cost=${Number(row.actual_cost || 0).toFixed(4)}
                  {row.model ? ` · model=${row.model}` : ''}
                  {row.provider ? ` · provider=${row.provider}` : ''}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

const AGENT_ROUTER_URL = 'http://localhost:8484'

function AgentsTab() {
  const [routerAgents, setRouterAgents] = useState<RouterAgent[]>([])
  const [routerStats, setRouterStats] = useState<RouterStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function fetchData() {
      try {
        const [agentsRes, statsRes] = await Promise.all([
          fetch(`${AGENT_ROUTER_URL}/api/agents`, { signal: AbortSignal.timeout(3000) }),
          fetch(`${AGENT_ROUTER_URL}/api/agents/stats`, { signal: AbortSignal.timeout(3000) }),
        ])
        if (agentsRes.ok) {
          const data = await agentsRes.json()
          if (!cancelled) setRouterAgents(data.agents || [])
        }
        if (statsRes.ok) {
          const data = await statsRes.json()
          if (!cancelled) setRouterStats(data)
        }
      } catch (e: any) {
        if (!cancelled) setError(e.message || 'Agent Router unreachable')
      }
      if (!cancelled) setLoading(false)
    }
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])

  if (loading) {
    return (
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Agents</h2>
          <span className="userver-card-subtitle">Loading from Agent Router...</span>
        </div>
      </div>
    )
  }

  if (error || routerAgents.length === 0) {
    return (
      <div>
        <div className="userver-toolbar">
          <div className="userver-toolbar-left">
            <h2 className="userver-heading">Agents</h2>
          </div>
        </div>
        <div className="userver-card" style={{ margin: 16, padding: 24, textAlign: 'center' }}>
          <p className="userver-text" style={{ color: 'var(--pico-del-color, #f85149)' }}>
            ⚠️ Agents API unavailable on port 8484
          </p>
          <p className="userver-text" style={{ marginTop: 8, fontSize: 12 }}>
            {error || 'No agents registered'}
          </p>
        </div>
      </div>
    )
  }

  const onlineCount = routerAgents.filter(a => a.status === 'online').length
  const totalRouted = routerStats?.totalRouted || 0
  const totalErrors = routerStats?.totalErrors || 0

  return (
    <div>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Agents</h2>
          <span className="userver-card-subtitle">
            {onlineCount}/{routerAgents.length} online · {totalRouted} routed · {totalErrors} errors
          </span>
        </div>
      </div>
      <div className="userver-grid">
        {routerAgents.map(agent => {
          const loadMatch = agent.load.match(/(\d+)\/(\d+)/)
          const currentLoad = loadMatch ? parseInt(loadMatch[1]) : 0
          const maxLoad = loadMatch ? parseInt(loadMatch[2]) : 1
          const loadPct = Math.round((currentLoad / maxLoad) * 100)
          const isOnline = agent.status === 'online'
          const agentTasks = routerStats?.byAgent?.[agent.id] || 0

          return (
            <div key={agent.id} className="userver-card" style={{ borderLeft: `3px solid ${isOnline ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-del-color, #f85149)'}` }}>
              <div className="userver-card-header">
                <h3>{agent.name}</h3>
                <span className={`userver-service-status ${isOnline ? 'up' : 'down'}`}>
                  {isOnline ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="userver-card-content">
                <div className="userver-service-details" style={{ flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
                  <span>Cost: <strong>${agent.costPerTask.toFixed(4)}</strong></span>
                  <span>Latency: <strong>{agent.avgLatencyMs}ms</strong></span>
                  <span>Success: <strong>{(agent.successRate * 100).toFixed(0)}%</strong></span>
                  <span>Tasks: <strong>{agentTasks}</strong></span>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--pico-muted-color, #8b949e)', marginBottom: 2 }}>
                    <span>Load</span>
                    <span>{agent.load}</span>
                  </div>
                  <div style={{ height: 4, background: 'var(--pico-border-color, #30363d)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ width: `${loadPct}%`, height: '100%', background: isOnline ? 'var(--pico-ins-color, #3fb950)' : 'var(--pico-del-color, #f85149)', borderRadius: 2, transition: 'width 0.5s' }} />
                  </div>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {agent.capabilities.map(cap => (
                    <span key={cap} style={{
                      fontSize: 10, padding: '1px 5px', borderRadius: 3,
                      background: 'var(--pico-card-sectioning-background-color, #1c2128)',
                      color: 'var(--pico-primary, #58a6ff)',
                      fontFamily: 'monospace',
                    }}>
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {routerStats?.recentRoutes && routerStats.recentRoutes.length > 0 && (
        <div className="userver-card" style={{ margin: '0 16px 16px' }}>
          <div className="userver-card-header">
            <h3>Recent Routes</h3>
          </div>
          <div className="userver-card-content">
            {routerStats.recentRoutes.slice(-5).reverse().map((route, i) => (
              <div key={i} className="userver-log-entry">
                <span className="userver-log-time">{route.timestamp?.slice(11, 19) || '--:--:--'}</span>
                <span className="userver-log-service">{route.agent}</span>
                <span style={{ fontSize: 10, padding: '1px 4px', borderRadius: 3, background: 'var(--pico-card-sectioning-background-color, #1c2128)', color: 'var(--pico-primary, #58a6ff)', fontFamily: 'monospace' }}>
                  {route.capability}
                </span>
                <span className="userver-log-message">{route.task}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function MissionTaskBinderTab() {
  const [workspaces, setWorkspaces] = useState<KnowledgeWorkspace[]>([])
  const [rows, setRows] = useState<AdapterRow[]>([])
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [missionCount, setMissionCount] = useState<number>(0)
  const [binderCount, setBinderCount] = useState<number>(0)

  const loadWorkspaces = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/workspaces`, {
        signal: AbortSignal.timeout(3000),
      })
      if (!res.ok) return
      const data = await res.json()
      const list = data.workspaces || []
      setWorkspaces(list)
      if (list.length > 0) {
        setSelectedWorkspace(prev => prev || list[0].id)
      }
    } catch {
      // keep graceful empty state
    }
  }, [])

  const loadProjection = useCallback(async (workspaceId: string) => {
    if (!workspaceId) return
    try {
      const res = await fetch(
        `${SNACKBAR_API}/api/knowledge/adapter/mission-task-binder?workspace_id=${workspaceId}&limit=200`,
        { signal: AbortSignal.timeout(3000) },
      )
      if (!res.ok) return
      const data = await res.json()
      setRows(data.rows || [])
      setMissionCount(Number(data.mission_count || 0))
      setBinderCount(Number(data.binder_count || 0))
    } catch {
      // keep graceful empty state
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    loadWorkspaces().finally(() => setLoading(false))
  }, [loadWorkspaces])

  useEffect(() => {
    if (!selectedWorkspace) return
    loadProjection(selectedWorkspace)
  }, [selectedWorkspace, loadProjection])

  return (
    <div>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Mission Control</h2>
          <span className="userver-card-subtitle">
            AppFlowy adapter view · {missionCount} missions · {rows.length} tasks · {binderCount} binders
          </span>
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Mission Notes</h3>
          <span className="userver-card-subtitle">Merged from legacy UIHub Missions view</span>
        </div>
        <div className="userver-card-content">
          {MISSION_CONTROL_NOTES.map(note => (
            <div key={note.id} className="userver-log-entry">
              <span className="userver-log-service">{note.title}</span>
              <span style={{ fontSize: 11, color: 'var(--pico-primary, #58a6ff)' }}>{note.priority}</span>
              <span className="userver-log-message">{note.description}</span>
              <span className="userver-log-time">{note.status}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Workspace Source</h3>
        </div>
        <div className="userver-card-content" style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {loading ? (
            <span className="userver-text">Loading AppFlowy workspaces...</span>
          ) : workspaces.length === 0 ? (
            <span className="userver-text">No AppFlowy workspaces discovered.</span>
          ) : (
            workspaces.map(ws => (
              <button
                key={ws.id}
                className="userver-action-btn"
                onClick={() => setSelectedWorkspace(ws.id)}
                style={{
                  borderColor: selectedWorkspace === ws.id ? 'var(--pico-primary, #58a6ff)' : undefined,
                  color: selectedWorkspace === ws.id ? 'var(--pico-primary, #58a6ff)' : undefined,
                }}
              >
                {ws.name}
              </button>
            ))
          )}
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Adapter Projection</h3>
          <span className="userver-card-subtitle">mission = title prefix, task = title body, binder = document type</span>
        </div>
        <div className="userver-card-content">
          {rows.length === 0 ? (
            <p className="userver-text">No documents available for projection.</p>
          ) : (
            rows.slice(0, 40).map(row => (
              <div key={row.id} className="userver-log-entry">
                <span className="userver-log-service">{row.mission}</span>
                <span style={{ fontSize: 11, color: 'var(--pico-primary, #58a6ff)' }}>{row.binder}</span>
                <span className="userver-log-message">{row.task}</span>
                <span className="userver-log-time">
                  {row.updated_at ? new Date(row.updated_at).toLocaleDateString() : '--'}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function IngestTab() {
  const [sources, setSources] = useState<SourceStatus[]>([])
  const [selectedSource, setSelectedSource] = useState<string>('all')
  const [coverage, setCoverage] = useState<IndexCoverageResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [running, setRunning] = useState<boolean>(false)
  const [dragActive, setDragActive] = useState<boolean>(false)
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [mission, setMission] = useState<string>('')
  const [binder, setBinder] = useState<string>('')
  const [statusMessage, setStatusMessage] = useState<string>('')

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/status`, {
        signal: AbortSignal.timeout(4000),
      })
      if (!res.ok) return
      const data = await res.json()
      setSources(data.sources || [])
    } catch {
      // graceful fallback
    }
  }, [])

  const fetchCoverage = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/index/status`, {
        signal: AbortSignal.timeout(5000),
      })
      if (!res.ok) return
      const data = await res.json()
      setCoverage(data)
    } catch {
      // graceful fallback
    }
  }, [])

  const refreshAll = useCallback(async () => {
    await Promise.all([fetchStatus(), fetchCoverage()])
  }, [fetchStatus, fetchCoverage])

  useEffect(() => {
    setLoading(true)
    refreshAll().finally(() => setLoading(false))
  }, [refreshAll])

  const handleImport = useCallback(async () => {
    setRunning(true)
    setStatusMessage('')
    try {
      const payload: {
        source?: string
        mission?: string
        binder?: string
        files?: string[]
      } = {}
      if (selectedSource !== 'all') {
        payload.source = selectedSource
      }
      const missionValue = mission.trim()
      const binderValue = binder.trim()
      if (missionValue) payload.mission = missionValue
      if (binderValue) payload.binder = binderValue
      if (selectedFiles.length > 0) payload.files = selectedFiles

      const res = await fetch(`${SNACKBAR_API}/api/knowledge/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(8000),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setStatusMessage(data.error || 'Import failed to start')
      } else {
        const ingestContext = [
          mission ? `mission=${mission}` : '',
          binder ? `binder=${binder}` : '',
          selectedFiles.length > 0 ? `files=${selectedFiles.length}` : '',
        ]
          .filter(Boolean)
          .join(' · ')
        const suffix = ingestContext ? ` (${ingestContext})` : ''
        setStatusMessage(`${data.message || 'Import started'}${suffix}`)
      }
    } catch {
      setStatusMessage('Import request failed')
    } finally {
      setRunning(false)
      // Refresh quickly after trigger so index coverage updates when import settles.
      window.setTimeout(() => { void refreshAll() }, 1200)
    }
  }, [selectedSource, mission, binder, selectedFiles.length, refreshAll])

  const onDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragActive(false)
    const files = Array.from(event.dataTransfer.files || [])
    setSelectedFiles(files.map(file => file.name))
  }

  return (
    <div>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Drop Import</h2>
          <span className="userver-card-subtitle">
            Import vault sources into AppFlowy and track index coverage.
          </span>
        </div>
        <div className="userver-toolbar-right">
          <button className="userver-action-btn" onClick={() => void refreshAll()} disabled={loading || running}>
            Refresh
          </button>
          <button className="userver-action-btn" onClick={() => void handleImport()} disabled={running || loading}>
            {running ? 'Starting Import...' : 'Run Import'}
          </button>
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Ingest Controls</h3>
          <span className="userver-card-subtitle">Mission and binder labels are tracked for operator context.</span>
        </div>
        <div className="userver-card-content" style={{ display: 'grid', gap: 12 }}>
          <div style={{ display: 'grid', gap: 8, gridTemplateColumns: '1fr 1fr 1fr' }}>
            <label style={{ display: 'grid', gap: 4 }}>
              <span className="userver-text" style={{ fontSize: 12 }}>Source</span>
              <select
                value={selectedSource}
                onChange={e => setSelectedSource(e.target.value)}
                style={{ background: 'var(--pico-card-sectioning-background-color, #1c2128)', color: 'var(--pico-color, #c9d1d9)', border: '1px solid var(--pico-border-color, #30363d)', borderRadius: 6, padding: '8px 10px' }}
              >
                <option value="all">All enabled sources</option>
                {sources.map(src => (
                  <option key={src.name} value={src.name}>{src.name}</option>
                ))}
              </select>
            </label>
            <label style={{ display: 'grid', gap: 4 }}>
              <span className="userver-text" style={{ fontSize: 12 }}>Mission</span>
              <input
                type="text"
                value={mission}
                onChange={e => setMission(e.target.value)}
                placeholder="e.g. Vault Consolidation"
                style={{ background: 'var(--pico-card-sectioning-background-color, #1c2128)', color: 'var(--pico-color, #c9d1d9)', border: '1px solid var(--pico-border-color, #30363d)', borderRadius: 6, padding: '8px 10px' }}
              />
            </label>
            <label style={{ display: 'grid', gap: 4 }}>
              <span className="userver-text" style={{ fontSize: 12 }}>Binder</span>
              <input
                type="text"
                value={binder}
                onChange={e => setBinder(e.target.value)}
                placeholder="e.g. runbook"
                style={{ background: 'var(--pico-card-sectioning-background-color, #1c2128)', color: 'var(--pico-color, #c9d1d9)', border: '1px solid var(--pico-border-color, #30363d)', borderRadius: 6, padding: '8px 10px' }}
              />
            </label>
          </div>

          <div
            onDragOver={event => { event.preventDefault(); setDragActive(true) }}
            onDragLeave={() => setDragActive(false)}
            onDrop={onDrop}
            style={{
              border: `2px dashed ${dragActive ? 'var(--pico-primary, #58a6ff)' : 'var(--pico-border-color, #30363d)'}`,
              borderRadius: 8,
              padding: 16,
              background: dragActive ? 'rgba(88,166,255,0.08)' : 'transparent',
              transition: 'all 120ms ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <Icon name="upload_file" size={16} />
              <strong>Drop Panel</strong>
            </div>
            <p className="userver-text" style={{ margin: 0, fontSize: 12 }}>
              Drag local files here for mission planning context. This panel records selected names and runs configured source import.
            </p>
            {selectedFiles.length > 0 && (
              <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {selectedFiles.slice(0, 8).map(file => (
                  <span key={file} className="hub-status-badge">{file}</span>
                ))}
                {selectedFiles.length > 8 && <span className="hub-status-badge">+{selectedFiles.length - 8} more</span>}
              </div>
            )}
          </div>

          {statusMessage && (
            <div className="hub-status-badge" style={{ width: 'fit-content' }}>
              {statusMessage}
            </div>
          )}
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Source Status</h3>
        </div>
        <div className="userver-card-content">
          {sources.length === 0 ? (
            <p className="userver-text">No configured sources discovered.</p>
          ) : (
            sources.map(src => (
              <div key={src.name} className="userver-service-row">
                <div className="userver-service-info">
                  <span className="userver-service-name">{src.name}</span>
                  <span className="userver-service-desc">{src.local_path}</span>
                </div>
                <div className="userver-service-meta">
                  <span className={`userver-service-status ${src.enabled ? 'up' : 'down'}`}>
                    {src.enabled ? 'enabled' : 'disabled'}
                  </span>
                  <span className="userver-service-port">{src.file_count} files</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Index Coverage</h3>
          <span className="userver-card-subtitle">
            {coverage ? `${coverage.indexed_total}/${coverage.expected_total} indexed (${coverage.coverage_pct}%)` : 'No coverage data yet'}
          </span>
        </div>
        <div className="userver-card-content">
          {!coverage || !coverage.sources || coverage.sources.length === 0 ? (
            <p className="userver-text">Coverage metrics not available.</p>
          ) : (
            coverage.sources.map(src => (
              <div key={src.source} className="userver-service-row">
                <div className="userver-service-info">
                  <span className="userver-service-name">{src.source}</span>
                  <span className="userver-service-desc">workspace: {src.workspace}</span>
                </div>
                <div className="userver-service-meta" style={{ display: 'grid', justifyItems: 'end' }}>
                  <span className="hub-status-badge">{src.indexed_count}/{src.expected_count} ({src.coverage_pct}%)</span>
                  <span className="userver-service-port" style={{ fontSize: 11 }}>
                    {src.last_indexed_at ? new Date(src.last_indexed_at).toLocaleString() : 'not indexed yet'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function StoryLinksTab({ onNavigate }: { onNavigate: (path: string) => void }) {
  const links = [
    {
      title: 'User Setup Story',
      subtitle: 'Legacy alias',
      description: 'Opens Story Builder via /user-setup-story alias.',
      path: '/user-setup-story',
      icon: 'flag',
    },
    {
      title: 'Story Builder',
      subtitle: 'S101 page',
      description: 'Core story workspace for creating and managing stories.',
      path: '/story-builder',
      icon: 'auto_stories',
    },
    {
      title: 'Story/gtx-form Styles & Examples',
      subtitle: 'Legacy alias',
      description: 'Opens the Story Builder route for gtx-form style/example workflows.',
      path: '/story/gtx-form',
      icon: 'design_services',
    },
  ]

  return (
    <div>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Story Links</h2>
          <span className="userver-card-subtitle">Quick links for story setup, builder, and gtx-form aliases.</span>
        </div>
      </div>
      <div className="userver-grid">
        {links.map(link => (
          <div key={link.path} className="userver-card">
            <div className="userver-card-header">
              <h3>{link.title}</h3>
              <span className="userver-card-subtitle">{link.subtitle}</span>
            </div>
            <div className="userver-card-content">
              <p className="userver-text" style={{ marginBottom: 12 }}>{link.description}</p>
              <button className="userver-action-btn" onClick={() => onNavigate(link.path)}>
                <Icon name={link.icon} size={14} style={{ marginRight: 6 }} />
                Open {link.path}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Snacks/Snackbar Tab (New Component) ───────────────────────────────
function SnacksTab() {
  const [queue, setQueue] = useState<SnackEntry[]>([])
  const [history, setHistory] = useState<SnackEntry[]>([])
  const [badges, setBadges] = useState<Record<string, unknown>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSnacks = useCallback(async () => {
    try {
      setError(null)
      const [queueRes, historyRes, badgesRes] = await Promise.all([
        fetch(`${SNACKBAR_API}/api/snacks`, { signal: AbortSignal.timeout(4000) }),
        fetch(`${SNACKBAR_API}/api/snacks/history?limit=20`, { signal: AbortSignal.timeout(4000) }),
        fetch(`${SNACKBAR_API}/api/snacks/system/badges`, { signal: AbortSignal.timeout(4000) }),
      ])

      if (queueRes.ok) {
        const data = await queueRes.json()
        setQueue(Array.isArray(data.snacks) ? data.snacks : [])
      }

      if (historyRes.ok) {
        const data = await historyRes.json()
        setHistory(Array.isArray(data.snacks) ? data.snacks : [])
      }

      if (badgesRes.ok) {
        const data = await badgesRes.json()
        setBadges(data.badges && typeof data.badges === 'object' ? data.badges : {})
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load snacks data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      await loadSnacks()
      if (cancelled) return
    })()
    return () => {
      cancelled = true
    }
  }, [loadSnacks])

  const handleClearQueue = async () => {
    try {
      await fetch(`${SNACKBAR_API}/api/snacks/queue`, {
        method: 'DELETE',
        signal: AbortSignal.timeout(4000),
      })
      await loadSnacks()
    } catch (e: any) {
      setError(e?.message || 'Failed to clear queue')
    }
  }

  return (
    <div>
      <div className="userver-toolbar">
        <div className="userver-toolbar-left">
          <h2 className="userver-heading">Snacks & Snackbar</h2>
          <span className="userver-card-subtitle">
            {loading ? 'Loading snacks…' : `${queue.length} queued · ${history.length} recent`}
          </span>
        </div>
        <div className="userver-toolbar-actions" style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="userver-action-btn" onClick={loadSnacks} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button className="userver-action-btn" onClick={handleClearQueue} disabled={loading || queue.length === 0}>
            Clear Queue
          </button>
        </div>
      </div>

      {error && (
        <div className="userver-card" style={{ margin: '0 16px 16px', borderLeft: '3px solid #f85149' }}>
          <div className="userver-card-content">
            <p className="userver-text" style={{ color: '#f85149' }}>{error}</p>
          </div>
        </div>
      )}

      <div className="userver-card" style={{ margin: '16px' }}>
        <div className="userver-card-header">
          <h3>Snackbar Service Status</h3>
        </div>
        <div className="userver-card-content">
          <div className="userver-service-details" style={{ flexWrap: 'wrap', gap: 12 }}>
            <span>Queue: <strong>{queue.length}</strong></span>
            <span>History: <strong>{history.length}</strong></span>
            <span>Endpoint: <strong>{SNACKBAR_API}</strong></span>
          </div>
          {Object.keys(badges).length > 0 && (
            <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {Object.entries(badges).map(([key, value]) => (
                <span key={key} style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  borderRadius: 8,
                  background: 'var(--pico-card-sectioning-background-color, #1c2128)',
                }}>
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Pending Queue</h3>
        </div>
        <div className="userver-card-content">
          {queue.length === 0 ? (
            <p className="userver-text">No snacks currently queued.</p>
          ) : (
            queue.slice(0, 25).map(snack => (
              <div key={snack.id} className="userver-log-entry">
                <span className="userver-log-time">{snack.timestamp?.slice(11, 19) || '--:--:--'}</span>
                <span className="userver-log-service">{snack.type}</span>
                <span className="userver-log-level info">{snack.priority}</span>
                <span className="userver-log-message">{snack.status} · {snack.source}</span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="userver-card" style={{ margin: '0 16px 16px' }}>
        <div className="userver-card-header">
          <h3>Recent History</h3>
        </div>
        <div className="userver-card-content">
          {history.length === 0 ? (
            <p className="userver-text">No snack history yet.</p>
          ) : (
            history.slice(0, 25).map(snack => (
              <div key={snack.id} className="userver-log-entry">
                <span className="userver-log-time">{snack.timestamp?.slice(11, 19) || '--:--:--'}</span>
                <span className="userver-log-service">{snack.type}</span>
                <span className={`userver-log-level ${snack.status === 'failed' ? 'error' : 'info'}`}>
                  {snack.status}
                </span>
                <span className="userver-log-message">{snack.source}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Main Surface ───────────────────────────────────────────────────
export default function UServerSurface() {
  const location = useLocation()
  const navigate = useNavigate()
  const tabState = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const raw = (params.get('tab') || 'dashboard').toLowerCase()
    const mapped = LEGACY_TAB_MAP[raw] || raw
    const candidate = mapped as UServerTab
    return {
      raw,
      mapped,
      selectedTab: SERVER_TABS.includes(candidate) ? candidate : 'dashboard',
    }
  }, [location.search])
  const [tab, setTab] = useState<UServerTab>(tabState.selectedTab)
  const [services, setServices] = useState<ServiceStatus[]>(DEFAULT_SERVICES)
  const [logs, setLogs] = useState<LogEntry[]>(DEFAULT_LOGS)
  const [logsLoading, setLogsLoading] = useState(false)
  const [logsError, setLogsError] = useState<string | null>(null)
  const [workflows] = useState<Workflow[]>(DEFAULT_WORKFLOWS)
  const [agents] = useState<AgentInfo[]>(DEFAULT_AGENTS)
  const [surfaces] = useState<SurfaceInfo[]>(DEFAULT_SURFACES)
  const [budgetRemaining, setBudgetRemaining] = useState<number | null>(null)
  const [budgetOverLimit, setBudgetOverLimit] = useState<boolean>(false)
  const [chatOpen, setChatOpen] = useState(false)
  const [sidebarMode, setSidebarMode] = useState<'server' | 'filepicker'>('server')
  const { sidebarOpen, setSidebarOpen, toggleSidebar } = useSurfaceShell()
  const runningCount = surfaces.filter(s => s.status === 'running').length

  useEffect(() => {
    if (tabState.mapped !== tabState.raw) {
      navigate(`/server?tab=${tabState.mapped}`, { replace: true })
    }
  }, [navigate, tabState.mapped, tabState.raw])

  useEffect(() => {
    setTab(tabState.selectedTab)
  }, [tabState.selectedTab])

  useEffect(() => {
    setSidebarOpen(true)
  }, [setSidebarOpen])

  const refreshServices = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/system`, {
        signal: AbortSignal.timeout(4000),
      })
      if (!res.ok) return

      const data = await res.json()
      const svc = data?.services || {}

      const normalizeStatus = (value: unknown): ServiceStatus['status'] => {
        const text = String(value || '').toLowerCase()
        if (text === 'running' || text === 'up') return 'up'
        if (text === 'stopped' || text === 'down' || text === 'unavailable') return 'down'
        return 'degraded'
      }

      const liveServices: ServiceStatus[] = [
        {
          name: 'ucore',
          status: normalizeStatus(svc.ucore || 'running'),
          port: 8484,
          uptime: 99.0,
          type: 'system',
          description: 'uCore backend API',
        },
        {
          name: 'ollama',
          status: normalizeStatus(svc.ollama),
          port: 11434,
          uptime: svc.ollama === 'running' ? 99.0 : 0,
          type: 'system',
          description: 'Local model runtime',
        },
        {
          name: 'docker',
          status: normalizeStatus(svc.docker),
          port: 0,
          uptime: svc.docker === 'running' ? 99.0 : 0,
          type: 'system',
          description: 'Container engine',
        },
        {
          name: 'frontend-dev',
          status: 'up',
          port: 5173,
          uptime: 99.0,
          type: 'user',
          description: 'Vite development server',
        },
        {
          name: 'hivemind',
          status: 'down',
          port: 8485,
          uptime: 0,
          type: 'system',
          description: 'Standalone Agent Router (not deployed)',
        },
      ]
      setServices(liveServices)
    } catch {
      // Keep previous values for graceful fallback.
    }
  }, [])

  const refreshLogs = useCallback(async () => {
    setLogsLoading(true)
    setLogsError(null)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/spool/feed?max=50`, {
        signal: AbortSignal.timeout(5000),
      })
      if (!res.ok) {
        throw new Error(`Failed to load logs (${res.status})`)
      }
      const data = await res.json()
      const entries = Array.isArray(data.entries) ? data.entries : []
      const mapped: LogEntry[] = entries.map((entry: any) => {
        const rawLevel = String(entry.level || 'INFO').toLowerCase()
        let level: LogEntry['level'] = 'info'
        if (rawLevel.includes('error') || rawLevel.includes('critical')) level = 'error'
        else if (rawLevel.includes('warn')) level = 'warn'

        return {
          timestamp: String(entry.timestamp || ''),
          service: String(entry.module || entry.source || 'unknown'),
          level,
          message: String(entry.message || ''),
        }
      })
      setLogs(mapped)
    } catch (e: any) {
      setLogsError(e?.message || 'Failed to load logs')
    } finally {
      setLogsLoading(false)
    }
  }, [])

  const refreshBudget = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/budget/status`, {
        signal: AbortSignal.timeout(4000),
      })
      if (!res.ok) return
      const data = await res.json()
      const usage = data?.usage || {}
      const remaining = Number(usage.remaining_budget)
      setBudgetRemaining(Number.isFinite(remaining) ? remaining : null)
      setBudgetOverLimit(Boolean(usage.over_limit))
    } catch {
      // Keep existing badge value if fetch fails.
    }
  }, [])

  useEffect(() => {
    refreshServices()
  }, [refreshServices])

  useEffect(() => {
    refreshLogs()
    const interval = setInterval(refreshLogs, 30000)
    return () => clearInterval(interval)
  }, [refreshLogs])

  useEffect(() => {
    refreshBudget()
    const interval = setInterval(refreshBudget, 30000)
    return () => clearInterval(interval)
  }, [refreshBudget])

  const setTabAndRoute = (nextTab: UServerTab) => {
    setTab(nextTab)
    navigate(`/server?tab=${nextTab}`)
  }

  const serverNavItems: SidebarNavItem[] = [
    { id: 'dashboard', icon: 'home', label: 'Dashboard', active: tab === 'dashboard', onClick: () => setTabAndRoute('dashboard') },
    { id: 'ingest', icon: 'upload_file', label: 'Import', active: tab === 'ingest', onClick: () => setTabAndRoute('ingest') },
    { id: 'missions', icon: 'account_tree', label: 'Mission Control', active: tab === 'missions', onClick: () => setTabAndRoute('missions') },
    { id: 'story', icon: 'auto_stories', label: 'Story Links', active: tab === 'story', onClick: () => setTabAndRoute('story') },
    { id: 'services', icon: 'dns', label: 'Services', active: tab === 'services', onClick: () => setTabAndRoute('services') },
    { id: 'logs', icon: 'article', label: 'Logs', active: tab === 'logs', onClick: () => setTabAndRoute('logs') },
    { id: 'workflows', icon: 'layers', label: 'Workflows', active: tab === 'workflows', onClick: () => setTabAndRoute('workflows') },
    { id: 'budget', icon: 'monitoring', label: 'Budget', active: tab === 'budget', onClick: () => setTabAndRoute('budget') },
    { id: 'agents', icon: 'smart_toy', label: 'Agents', active: tab === 'agents', onClick: () => setTabAndRoute('agents') },
    { id: 'snacks', icon: 'fast_forward', label: 'Snacks', active: tab === 'snacks', onClick: () => setTabAndRoute('snacks') },
    { id: '_admin', icon: 'settings', label: '⚙ Admin → /system', active: false, onClick: () => navigate('/system?tab=pages') },
  ]

  return (
    <div className="userver-surface">
      <GlobalToolbar
        chatMode={chatOpen ? 'panel' : 'closed'}
        onToggleChat={() => setChatOpen(prev => !prev)}
        onToggleSidebar={toggleSidebar}
        sidebarOpen={sidebarOpen}
        sidebarToggleLabel="Server sidebar"
        rightExtra={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span className="hub-status-badge">
              <span className={`hub-status-dot ${runningCount > 0 ? 'hub-status-dot--online' : ''}`} />
              {runningCount}/{surfaces.length} online
            </span>
            <span
              className="hub-status-badge"
              title="Monthly API budget remaining"
              style={budgetOverLimit ? { borderColor: '#f85149', color: '#f85149' } : undefined}
            >
              Budget: {budgetRemaining === null ? 'n/a' : `$${budgetRemaining.toFixed(2)}`}
            </span>
          </div>
        }
      />

      <div className="usx-surface-body" style={{ position: 'relative' }}>
        <VaultSidebar
          open={sidebarOpen}
          showModeTabs
          sidebarMode={sidebarMode}
          onSidebarModeChange={setSidebarMode}
          serverNavItems={serverNavItems}
        />

        {/* ─── Chat Panel — overlays ALL surfaces (absolute, z-index) ─── */}
        {chatOpen && (
          <div className="hub-chat-panel" style={{ position: 'absolute', top: 0, right: 0, bottom: 0, width: 380, zIndex: 1000, display: 'flex', flexDirection: 'column' }}>
            <div className="hub-chat-panel-header">
              <span className="hub-chat-panel-title">Chat</span>
              <button className="usx-header-btn" onClick={() => setChatOpen(false)} title="Close chat">
                <Icon name="close" size={16} />
              </button>
            </div>
            <div className="hub-chat-panel-body" style={{ flex: 1, overflow: 'hidden' }}>
              <AssistUISurface hideToolbar />
            </div>
          </div>
        )}

        <main className="usx-surface-main">
          {tab === 'dashboard' && <DashboardTab services={services} workflows={workflows} logs={logs} surfaces={surfaces} />}
          {tab === 'ingest' && <IngestTab />}
          {tab === 'missions' && <MissionTaskBinderTab />}
          {tab === 'story' && <StoryLinksTab onNavigate={path => navigate(path)} />}
          {tab === 'services' && <ServicesTab services={services} />}
          {tab === 'logs' && <LogsTab logs={logs} loading={logsLoading} error={logsError} onRefresh={refreshLogs} />}
          {tab === 'workflows' && <WorkflowsTab workflows={workflows} />}
          {tab === 'budget' && <BudgetTab />}
          {tab === 'agents' && <AgentsTab />}
          {tab === 'snacks' && <SnacksTab />}
        </main>
      </div>
    </div>
  )
}