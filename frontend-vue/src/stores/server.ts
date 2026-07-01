/**
 * @module stores/server
 * @description Server operations state — services, logs, budget, snacks.
 * Ported from UServerSurface.tsx (React).
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ServerTab = 'dashboard' | 'services' | 'logs' | 'models' | 'agents' | 'budget' | 'story' | 'snacks'

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

export const SERVER_TABS: { id: ServerTab; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'services', label: 'Services', icon: 'dns' },
  { id: 'logs', label: 'Logs', icon: 'article' },
  { id: 'models', label: 'Models', icon: 'smart_toy' },
  { id: 'agents', label: 'Runtime Agents', icon: 'group' },
  { id: 'budget', label: 'Budget', icon: 'attach_money' },
  { id: 'story', label: 'Story', icon: 'auto_stories' },
  { id: 'snacks', label: 'Snacks', icon: 'food_croissant' },
]

export const useServerStore = defineStore('server', () => {
  const activeTab = ref<ServerTab>('dashboard')
  const services = ref<ServiceStatus[]>(DEFAULT_SERVICES)
  const logs = ref<LogEntry[]>(DEFAULT_LOGS)
  const budgetRemaining = ref<number | null>(42.50)
  const budgetOverLimit = ref(false)

  function setTab(tab: ServerTab) {
    activeTab.value = tab
  }

  return { activeTab, services, logs, budgetRemaining, budgetOverLimit, setTab }
})

const DEFAULT_SERVICES: ServiceStatus[] = [
  { name: 'snackbar', status: 'up', port: 8484, uptime: 99.9, type: 'system', description: 'Container orchestrator & workflow runner' },
  { name: 'secret-server', status: 'up', port: 30001, uptime: 99.8, type: 'user', description: 'AES-256-GCM encrypted secret vault' },
  { name: 'hivemind', status: 'up', port: 8485, uptime: 99.7, type: 'system', description: 'AI orchestration & agent routing' },
  { name: 'feed-spool', status: 'up', port: 8486, uptime: 99.5, type: 'system', description: 'Feed spooler & transport' },
  { name: 'vault-mcp', status: 'degraded', port: 0, uptime: 95.2, type: 'user', description: 'MCP server for Vault access' },
  { name: 'email-feed', status: 'down', port: 0, uptime: 0, type: 'user', description: 'Email to feed processor' },
]

const DEFAULT_LOGS: LogEntry[] = [
  { timestamp: '2026-06-28 18:15:22', service: 'snackbar', level: 'info', message: 'Workflow "vue-port-developer" completed successfully' },
  { timestamp: '2026-06-28 18:14:00', service: 'hivemind', level: 'info', message: 'Agent "code-reviewer" dispatched to PR #142' },
  { timestamp: '2026-06-28 18:10:30', service: 'email-feed', level: 'error', message: 'IMAP connection failed: invalid credentials' },
  { timestamp: '2026-06-28 18:05:00', service: 'vault-mcp', level: 'info', message: 'MCP client connected: uCode Gateway' },
  { timestamp: '2026-06-28 18:00:00', service: 'snackbar', level: 'warn', message: 'Budget threshold at 80% — review usage' },
]
