/**
 * @module stores/snackmachine
 * @description SnackMachine surface state — snacks, workflows, MCP, vault, variables, scheduler.
 * Wired to backend endpoints (no hardcoded sample data).
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type SnackMachineTab = 'snacks' | 'workflows' | 'mcp' | 'vault' | 'variables' | 'scheduler'

export interface SnackEntry {
  id: string
  type: string
  priority: string
  status: string
  source: string
  timestamp: string
}

export interface SystemSnackEntry {
  id: string
  name: string
  kind: string
  icon?: string
}

export interface MCPServer {
  id: string
  name: string
  status: 'online' | 'offline' | 'connecting'
  transport: string
  tools: string[]
}

export interface WorkflowEntry {
  id: string
  name: string
  description: string
  schedule: string
  enabled: boolean
  steps: { skill_id: string; params: Record<string, unknown> }[]
}

export interface ScheduleEntry {
  id: string
  workflow_id: string
  workflow_name: string
  cron: string
  next_run: string
  enabled: boolean
}

export interface VariableEntry {
  key: string
  value: string
  scope: string
}

export interface ImportJobEntry {
  id: string
  status: string
  progress: number
  message: string
  timestamp: string
}

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

export const SNACKMACHINE_TABS: { id: SnackMachineTab; label: string; icon: string }[] = [
  { id: 'snacks', label: 'Snacks', icon: 'restaurant_menu' },
  { id: 'workflows', label: 'Workflows', icon: 'account_tree' },
  { id: 'mcp', label: 'MCP Bridge', icon: 'sync_alt' },
  { id: 'vault', label: 'Vault Sync', icon: 'sync' },
  { id: 'variables', label: 'Variables', icon: 'tune' },
  { id: 'scheduler', label: 'Scheduler', icon: 'schedule' },
]

export const useSnackMachineStore = defineStore('snackmachine', () => {
  const activeTab = ref<SnackMachineTab>('snacks')
  const snacks = ref<SnackEntry[]>([])
  const mcpServers = ref<MCPServer[]>([])
  const systemSnacks = ref<SystemSnackEntry[]>([])
  const workflows = ref<WorkflowEntry[]>([])
  const schedule = ref<ScheduleEntry[]>([])
  const variables = ref<VariableEntry[]>([])
  const importJobs = ref<ImportJobEntry[]>([])
  const indexCoverage = ref<{ coverage_pct: number; total_docs: number } | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const backendOk = ref(false)
  const syncingVault = ref(false)

  const latestImportJob = computed(() => importJobs.value[0] || null)

  function setTab(tab: SnackMachineTab) {
    activeTab.value = tab
  }

  async function fetchSnacks(): Promise<void> {
    try {
      const r = await fetch(`${API_BASE}/api/snacks`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      backendOk.value = true
      const data = await r.json()
      const raw = (data as any)?.snacks ?? []
      snacks.value = raw.map((s: any, i: number) => ({
        id: s.id ?? `backend-${i}`,
        type: s.type ?? 'snack',
        priority: s.priority ?? 'normal',
        status: s.status ?? 'unknown',
        source: s.source ?? 'backend',
        timestamp: s.timestamp ?? new Date().toISOString(),
      }))

      const sysRes = await fetch(`${API_BASE}/api/snacks/system`)
      if (sysRes.ok) {
        const sysData = await sysRes.json()
        const sysRaw = (sysData as any)?.snacks || []
        systemSnacks.value = sysRaw.map((s: any) => ({
          id: s.id || '',
          name: s.name || s.id || 'System Snack',
          kind: s.kind || 'action',
          icon: s.icon,
        }))
      }
    } catch (e: any) {
      backendOk.value = false
      console.warn('SnackMachine fetch failed:', e.message)
    }
  }

  async function fetchMCP(): Promise<void> {
    try {
      const res = await fetch(`${API_BASE}/api/mcp/tools`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const tools = data?.result?.tools || data?.tools || []
      mcpServers.value = [
        {
          id: 'mcp-discovery',
          name: 'MCP Tool Registry',
          status: 'online',
          transport: 'jsonrpc',
          tools: Array.isArray(tools) ? tools.map((t: any) => t?.name || 'tool').filter(Boolean) : [],
        },
      ]
    } catch (e: any) {
      console.warn('MCP fetch failed:', e.message)
      mcpServers.value = []
    }
  }

  async function fetchWorkflows(): Promise<void> {
    try {
      const res = await fetch(`${API_BASE}/api/workflows`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const raw = data.workflows || data || []
      workflows.value = Array.isArray(raw)
        ? raw.map((w: any) => ({
            id: w.id || w.name?.toLowerCase() || '',
            name: w.name || 'Workflow',
            description: w.description || '',
            schedule: w.schedule || 'manual',
            enabled: w.enabled !== false,
            steps: w.steps || [],
          }))
        : []
    } catch (e: any) {
      console.warn('Workflows fetch failed:', e.message)
      workflows.value = []
    }
  }

  async function fetchVariables(): Promise<void> {
    try {
      const res = await fetch(`${API_BASE}/api/variables`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const vars = data.variables || data || {}
      variables.value = Object.entries(vars).map(([key, value]: [string, any]) => ({
        key,
        value: typeof value === 'string' ? value : JSON.stringify(value),
        scope: key.startsWith('VITE_') ? 'global' : 'system',
      }))
    } catch (e: any) {
      console.warn('Variables fetch failed:', e.message)
      variables.value = []
    }
  }

  async function fetchVaultSyncStatus(): Promise<void> {
    try {
      const [statusRes, coverageRes] = await Promise.all([
        fetch(`${API_BASE}/api/knowledge/import/status`),
        fetch(`${API_BASE}/api/knowledge/index/coverage`),
      ])

      if (statusRes.ok) {
        const statusData = await statusRes.json()
        const jobs = (statusData?.jobs || []) as any[]
        importJobs.value = jobs.map((j: any) => ({
          id: j.id || '',
          status: j.status || 'unknown',
          progress: Number(j.progress || 0),
          message: j.message || '',
          timestamp: j.timestamp || '',
        }))
      }

      if (coverageRes.ok) {
        const coverageData = await coverageRes.json()
        indexCoverage.value = {
          coverage_pct: Number(coverageData?.coverage_pct || 0),
          total_docs: Number(coverageData?.total_docs || 0),
        }
      }
    } catch (e: any) {
      console.warn('Vault sync status fetch failed:', e.message)
    }
  }

  async function syncVault(source = 'User Vault'): Promise<void> {
    syncingVault.value = true
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchVaultSyncStatus()
    } catch (e: any) {
      console.warn('Vault sync failed:', e.message)
    } finally {
      syncingVault.value = false
    }
  }

  async function seedDefaultSnacks(): Promise<void> {
    const defaults = [
      { type: 'message', priority: 'normal', source: 'snackmachine', content: { title: 'Welcome', text: 'SnackMachine is live.' } },
      { type: 'notification', priority: 'low', source: 'snackmachine', content: { title: 'Vault', text: 'Use Vault Sync tab to mirror User Vault.' } },
      { type: 'event', priority: 'low', source: 'snackmachine', content: { title: 'Tip', text: 'System snacks are available below the queue.' } },
    ]
    try {
      await Promise.all(defaults.map((payload) =>
        fetch(`${API_BASE}/api/snacks`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }),
      ))
      await fetchSnacks()
    } catch (e: any) {
      console.warn('Seed default snacks failed:', e.message)
    }
  }

  async function fetchAll(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await Promise.all([
        fetchSnacks(),
        fetchMCP(),
        fetchWorkflows(),
        fetchVariables(),
        fetchVaultSyncStatus(),
      ])
    } catch (e: any) {
      error.value = e.message || 'Failed to load SnackMachine data'
    } finally {
      loading.value = false
    }
  }

  return {
    activeTab,
    snacks,
    mcpServers,
    systemSnacks,
    workflows,
    schedule,
    variables,
    importJobs,
    latestImportJob,
    indexCoverage,
    loading,
    error,
    backendOk,
    syncingVault,
    setTab,
    fetchSnacks,
    fetchMCP,
    fetchWorkflows,
    fetchVariables,
    fetchVaultSyncStatus,
    syncVault,
    seedDefaultSnacks,
    fetchAll,
  }
})