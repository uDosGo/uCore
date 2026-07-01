/**
 * @module stores/snackmachine
 * @description SnackMachine surface state — snacks, workflows, MCP, vault, variables, scheduler.
 * Ported from SnackMachineSurface.tsx (React).
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
  const snacks = ref<SnackEntry[]>(SAMPLE_SNACKS)
  const mcpServers = ref<MCPServer[]>(SAMPLE_MCP)

  function setTab(tab: SnackMachineTab) {
    activeTab.value = tab
  }

  return { activeTab, snacks, mcpServers, setTab }
})

const SAMPLE_SNACKS: SnackEntry[] = [
  { id: '1', type: 'clipboard', priority: 'normal', status: 'active', source: 'system', timestamp: '2026-06-28 18:30' },
  { id: '2', type: 'workflow', priority: 'high', status: 'queued', source: 'manual', timestamp: '2026-06-28 18:25' },
  { id: '3', type: 'maintenance', priority: 'low', status: 'completed', source: 'scheduler', timestamp: '2026-06-28 18:00' },
  { id: '4', type: 'vault-sync', priority: 'normal', status: 'active', source: 'system', timestamp: '2026-06-28 17:45' },
]

const SAMPLE_MCP: MCPServer[] = [
  { id: 'snackbar', name: 'Snackbar', status: 'online', transport: 'http', tools: ['clipboard', 'maintenance', 'workflow', 'tasker_sync', 'vault_sync'] },
  { id: 'ucore', name: 'uCore Backend', status: 'online', transport: 'http', tools: ['knowledge', 'surfaces', 'health', 'mcp_registry'] },
  { id: 'vault', name: 'Vault Indexer', status: 'offline', transport: 'stdio', tools: ['search', 'index', 'export'] },
]
