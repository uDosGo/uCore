<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">MCP Servers</h3>
      <UBadge :type="onlineCount > 0 ? 'success' : 'warning'" size="sm">
        {{ loading ? '...' : onlineCount + '/' + servers.length + ' online' }}
      </UBadge>
    </div>
    <div class="developer-card-list">
      <div v-for="server in servers" :key="server.id" class="developer-card">
        <div class="developer-card-header">
          <UIcon name="dns" />
          <span class="developer-card-title">{{ server.name }}</span>
          <UBadge :type="server.online ? 'success' : 'error'" size="sm">
            {{ server.online ? 'online' : 'offline' }}
          </UBadge>
        </div>
        <p class="developer-card-desc">{{ server.description }}</p>
        <div class="developer-card-meta">
          <span>{{ server.endpoint }}</span>
          <span>{{ server.tools }} tools</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component MCPServersPanel
 * @description MCP server status and configuration panel.
 * @category surfaces/developer
 */
import { ref, computed, onMounted } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

interface MCPServer {
  id: string
  name: string
  online: boolean
  endpoint: string
  tools: number
  description: string
}

const servers = ref<MCPServer[]>([])
const loading = ref(true)

async function fetchServers() {
  loading.value = true
  try {
    // Fetch MCP tools - group by server
    const res = await fetch(`${API_BASE}/api/mcp/tools`, {
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) {
      const data = await res.json()
      const tools = data.tools || data || []
      // Group tools by server
      const serverMap = new Map<string, { tools: number; endpoint: string }>()
      for (const t of tools) {
        const srv = t.server || 'unknown'
        const entry = serverMap.get(srv) || { tools: 0, endpoint: t.endpoint || '' }
        entry.tools++
        if (!entry.endpoint && t.endpoint) entry.endpoint = t.endpoint
        serverMap.set(srv, entry)
      }

      const knownServers: Record<string, { desc: string; id: string }> = {
        'snackbar': { desc: 'Core MCP server — clipboard, maintenance, workflows, skills', id: 'snackbar' },
        'ucore': { desc: 'Knowledge, surfaces, health, MCP tool registry', id: 'ucore' },
        'vault': { desc: 'AppFlowy vault search and document indexing', id: 'vault' },
        'gridsmith': { desc: 'Grid rendering, spatial algebra, map generation', id: 'gridsmith' },
      }

      servers.value = Array.from(serverMap.entries()).map(([name, info]) => ({
        id: knownServers[name]?.id || name.toLowerCase(),
        name: name.charAt(0).toUpperCase() + name.slice(1),
        online: true,
        endpoint: info.endpoint || '—',
        tools: info.tools,
        description: knownServers[name]?.desc || 'MCP Server',
      }))
    }
  } catch {
    // Backend offline — check known ports
    const checks = [
      { id: 'snackbar', name: 'Snackbar', endpoint: 'localhost:8484', port: 8484, desc: 'Core MCP server' },
      { id: 'hivemind', name: 'Hivemind', endpoint: 'localhost:8490', port: 8490, desc: 'AI agent routing' },
      { id: 'vault', name: 'Vault Indexer', endpoint: 'localhost:8765', port: 8765, desc: 'Vault search' },
      { id: 'gridsmith', name: 'GridSmith', endpoint: 'localhost:8888', port: 8888, desc: 'Grid rendering' },
    ]
    servers.value = checks.map(c => ({
      id: c.id,
      name: c.name,
      online: false,
      endpoint: c.endpoint,
      tools: 0,
      description: c.desc,
    }))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchServers()
})

const onlineCount = computed(() => servers.value.filter(s => s.online).length)
</script>

<style scoped>
.developer-panel { max-width: calc(var(--usx-spacing-2xl) * 25); }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }
.developer-card_list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--usx-color-background); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-semibold); flex: 1; }
.developer-card-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin: 0 0 var(--usx-spacing-xs); }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
</style>
