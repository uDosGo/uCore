/**
 * @module stores/server
 * @description Server operations state — services, logs, budget, models, agents.
 * Wired to /api/server/* backend endpoints.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ServerTab = 'dashboard' | 'services' | 'logs' | 'models' | 'agents' | 'budget'

export interface ServiceStatus {
  name: string
  status: 'up' | 'degraded' | 'down'
  port: number
  uptime: number
  type: 'system' | 'user'
  description: string
}

export interface LogEntry {
  timestamp: string
  service: string
  level: 'info' | 'warn' | 'error'
  message: string
}

export interface ModelUsage {
  id: string
  name: string
  pct: number
  calls: number
}

export interface AgentInfo {
  id: string
  name: string
  icon: string
  active: boolean
  description: string
}

export interface BudgetInfo {
  remaining: number
  used: number
  limit: number
  over_limit: boolean
}

export interface HealthInfo {
  services: ServiceStatus[]
  count: number
  up: number
  degraded: number
  down: number
  health_pct: number
}

export const SERVER_TABS: { id: ServerTab; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'services', label: 'Services', icon: 'dns' },
  { id: 'logs', label: 'Logs', icon: 'article' },
  { id: 'models', label: 'Models', icon: 'smart_toy' },
  { id: 'agents', label: 'Runtime Agents', icon: 'group' },
  { id: 'budget', label: 'Budget', icon: 'attach_money' },
]

export const useServerStore = defineStore('server', () => {
  const activeTab = ref<ServerTab>('dashboard')
  const services = ref<ServiceStatus[]>([])
  const logs = ref<LogEntry[]>([])
  const modelUsage = ref<ModelUsage[]>([])
  const agents = ref<AgentInfo[]>([])
  const budgetRemaining = ref<number | null>(null)
  const budgetLimit = ref<number>(50.00)
  const budgetUsed = ref<number>(0.00)
  const budgetOverLimit = ref(false)
  const healthPct = ref(0)
  const upCount = ref(0)
  const degradedCount = ref(0)
  const downCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  function setTab(tab: ServerTab) {
    activeTab.value = tab
  }

  async function fetchHealth(): Promise<void> {
    try {
      const res = await fetch('/api/server/health')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: HealthInfo = await res.json()
      services.value = data.services
      upCount.value = data.up
      degradedCount.value = data.degraded
      downCount.value = data.down
      healthPct.value = data.health_pct
    } catch (e: any) {
      console.warn('Server health fetch failed:', e.message)
    }
  }

  async function fetchServices(): Promise<void> {
    try {
      const res = await fetch('/api/server/services')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      services.value = data.services || []
    } catch (e: any) {
      console.warn('Server services fetch failed:', e.message)
    }
  }

  async function fetchLogs(limit = 20): Promise<void> {
    try {
      const res = await fetch(`/api/server/logs?limit=${limit}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      logs.value = data.logs || []
    } catch (e: any) {
      console.warn('Server logs fetch failed:', e.message)
    }
  }

  async function fetchModels(): Promise<void> {
    try {
      const res = await fetch('/api/server/models')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      modelUsage.value = data.models || []
    } catch (e: any) {
      console.warn('Server models fetch failed:', e.message)
    }
  }

  async function fetchAgents(): Promise<void> {
    try {
      const res = await fetch('/api/server/agents')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      agents.value = data.agents || []
    } catch (e: any) {
      console.warn('Server agents fetch failed:', e.message)
    }
  }

  async function fetchBudget(): Promise<void> {
    try {
      const res = await fetch('/api/server/budget')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: BudgetInfo = await res.json()
      budgetRemaining.value = data.remaining
      budgetUsed.value = data.used
      budgetLimit.value = data.limit
      budgetOverLimit.value = data.over_limit
    } catch (e: any) {
      console.warn('Server budget fetch failed:', e.message)
    }
  }

  async function fetchAll(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await Promise.all([
        fetchHealth(),
        fetchLogs(),
        fetchModels(),
        fetchAgents(),
        fetchBudget(),
      ])
    } catch (e: any) {
      error.value = e.message || 'Failed to load server data'
    } finally {
      loading.value = false
    }
  }

  return {
    activeTab,
    services,
    logs,
    modelUsage,
    agents,
    budgetRemaining,
    budgetLimit,
    budgetUsed,
    budgetOverLimit,
    healthPct,
    upCount,
    degradedCount,
    downCount,
    loading,
    error,
    setTab,
    fetchHealth,
    fetchServices,
    fetchLogs,
    fetchModels,
    fetchAgents,
    fetchBudget,
    fetchAll,
  }
})