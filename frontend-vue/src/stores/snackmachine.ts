/**
 * @module stores/snackmachine
 * @description SnackMachine surface state — snacks, workflows, MCP, vault, variables, scheduler.
 * Wired to backend endpoints (no hardcoded sample data).
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type SnackMachineTab = 'snacks' | 'workflows' | 'mcp' | 'vault' | 'variables' | 'scheduler'

export interface SnackEntry {
  id: string
  type: string
  priority: string
  status: string
  source: string
  timestamp: string
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
  const workflows = ref<WorkflowEntry[]>([])
  const schedule = ref<ScheduleEntry[]>([])
  const variables = ref<VariableEntry[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const backendOk = ref(false)

  function setTab(tab: SnackMachineTab) {
    activeTab.value = tab
  }

  async function fetchSnacks(): Promise<void> {
    try {
      const r = await fetch('http://localhost:5175/snackmachine')
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
    } catch (e: any) {
      backendOk.value = false
      console.warn('SnackMachine fetch failed:', e.message)
    }
  }

  async function fetchMCP(): Promise<void> {
    try {
      const res = await fetch('/api/mcp/tools')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const servers = data.servers || data.tools || []
      mcpServers.value = Array.isArray(servers)
        ? servers.map((s: any) => ({
            id: s.id || s.name || 'unknown',
            name: s.name || s.id || 'MCP Server',
            status: (s.status === 'online' ? 'online' : 'offline') as MCPServer['status'],
            transport: s.transport || 'http',
            tools: s.tools || [],
          }))
        : []
    } catch (e: any) {
      console.warn('MCP fetch failed:', e.message)
    }
  }

  async function fetchWorkflows(): Promise<void> {
    try {
      const res = await fetch('/api/workflows')
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
    }
  }

  async function fetchVariables(): Promise<void> {
    try {
      const res = await fetch('/api/variables')
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
    workflows,
    schedule,
    variables,
    loading,
    error,
    backendOk,
    setTab,
    fetchSnacks,
    fetchMCP,
    fetchWorkflows,
    fetchVariables,
    fetchAll,
  }
})