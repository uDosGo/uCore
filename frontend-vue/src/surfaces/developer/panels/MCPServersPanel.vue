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
          <span v-if="server.capabilityGroups.length">{{ server.capabilityGroups.length }} groups</span>
        </div>
        <div v-if="server.capabilityGroups.length" class="developer-card-groups">
          <span
            v-for="group in server.capabilityGroups.slice(0, 4)"
            :key="`${server.id}-${group.name}`"
            class="developer-group-chip"
          >
            {{ group.name }} {{ group.count }}
          </span>
          <span v-if="server.capabilityGroups.length > 4" class="developer-group-chip">
            +{{ server.capabilityGroups.length - 4 }} more
          </span>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
  capabilityGroups: Array<{ name: string; count: number }>
}

const servers = ref<MCPServer[]>([])
const loading = ref(true)

const KNOWN_SERVERS: Array<{
  id: string
  name: string
  endpoint: string
  healthUrl: string
  description: string
}> = [
  {
    id: 'snackbar',
    name: 'Snackbar',
    endpoint: 'localhost:8484',
    healthUrl: `${API_BASE}/api/health`,
    description: 'Core MCP server',
  },
  {
    id: 'hivemind',
    name: 'Hivemind',
    endpoint: 'localhost:8490',
    healthUrl: 'http://localhost:8490/health',
    description: 'AI agent routing',
  },
  {
    id: 'vault',
    name: 'Vault Indexer',
    endpoint: 'localhost:8765',
    healthUrl: 'http://localhost:8765/health',
    description: 'Vault search',
  },
  {
    id: 'gridsmith',
    name: 'GridSmith',
    endpoint: 'localhost:8888',
    healthUrl: 'http://localhost:8888/health',
    description: 'Grid rendering',
  },
]

async function probeKnownServers(): Promise<MCPServer[]> {
  const checks = await Promise.all(
    KNOWN_SERVERS.map(async (srv) => {
      try {
        const res = await fetch(srv.healthUrl, {
          signal: AbortSignal.timeout(2000),
        })
        return {
          id: srv.id,
          name: srv.name,
          online: res.ok,
          endpoint: srv.endpoint,
          tools: 0,
          description: srv.description,
          capabilityGroups: [],
        }
      } catch {
        return {
          id: srv.id,
          name: srv.name,
          online: false,
          endpoint: srv.endpoint,
          tools: 0,
          description: srv.description,
          capabilityGroups: [],
        }
      }
    }),
  )
  return checks
}

function normalizeServerId(raw: string): string {
  const value = raw.toLowerCase()
  if (value.includes('hive')) return 'hivemind'
  if (value.includes('vault')) return 'vault'
  if (value.includes('grid')) return 'gridsmith'
  if (value.includes('snackbar') || value.includes('ucore')) return 'snackbar'
  return 'snackbar'
}

function capabilityGroupForTool(name: string): string {
  const n = name.toLowerCase()

  if (n.startsWith('knowledge_') || n.includes('vault')) return 'Knowledge'
  if (n.startsWith('clipboard_')) return 'Clipboard'
  if (n.startsWith('tasker_') || n.includes('tasker')) return 'Tasking'
  if (n.startsWith('gridsmith_') || n.includes('grid')) return 'Grid'
  if (n.startsWith('flow_router_') || n.includes('workflow')) return 'Flow'
  if (n.startsWith('toon_')) return 'Toon'

  if (n.includes('roundtable') || n.includes('hivemind') || n.includes('route_task')) return 'Orchestration'
  if (n.includes('git') || n.includes('gh-workflow') || n.includes('dev-mode') || n.includes('file_edit') || n.includes('lint') || n.includes('modularisation')) return 'Dev Tools'
  if (n.includes('recover') || n.includes('restart') || n.includes('reset')) return 'Recovery'
  if (n.includes('backup') || n.includes('archive') || n.includes('spool_backup') || n.includes('daily_backup')) return 'Backup'
  if (n.includes('maintenance') || n.includes('cleanup') || n.includes('prune') || n.includes('destroy')) return 'Maintenance'
  if (n.includes('diagnose') || n.includes('health') || n.includes('self_heal') || n.includes('audit')) return 'Health'
  if (n.includes('docs') || n.includes('attach_context') || n.includes('devlog')) return 'Documentation'
  if (n.includes('usx')) return 'USX UI'
  if (n.includes('nugget')) return 'Nuggets'

  if (n.startsWith('skill_')) return 'Automation'
  return 'General'
}

function summarizeCapabilityGroups(toolNames: string[]): Array<{ name: string; count: number }> {
  const groups = new Map<string, number>()
  const groupOrder: Record<string, number> = {
    Health: 1,
    Recovery: 2,
    Backup: 3,
    Maintenance: 4,
    'Dev Tools': 5,
    Flow: 6,
    Knowledge: 7,
    Tasking: 8,
    Orchestration: 9,
    Grid: 10,
    Documentation: 11,
    Clipboard: 12,
    Nuggets: 13,
    'USX UI': 14,
    Toon: 15,
    Automation: 16,
    General: 17,
  }
  for (const name of toolNames) {
    const group = capabilityGroupForTool(name)
    groups.set(group, (groups.get(group) || 0) + 1)
  }

  return Array.from(groups.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => {
      const orderA = groupOrder[a.name] ?? 999
      const orderB = groupOrder[b.name] ?? 999
      if (orderA !== orderB) return orderA - orderB
      if (b.count !== a.count) return b.count - a.count
      return a.name.localeCompare(b.name)
    })
}

async function fetchServers() {
  loading.value = true
  try {
    const [probed, controlRes, toolsRes] = await Promise.all([
      probeKnownServers(),
      fetch(`${API_BASE}/api/control/status`, { signal: AbortSignal.timeout(5000) }),
      fetch(`${API_BASE}/api/mcp/tools`, { signal: AbortSignal.timeout(5000) }),
    ])

    const merged = new Map(probed.map((srv) => [srv.id, srv]))

    if (controlRes.ok) {
      const data = await controlRes.json()
      const mcp = Array.isArray(data?.mcp) ? data.mcp : []
      for (const srv of mcp) {
        const id = String(srv?.name || 'unknown').toLowerCase()
        const known = KNOWN_SERVERS.find((entry) => entry.id === id)
        const current = merged.get(id)
        merged.set(id, {
          id,
          name: known?.name || String(srv?.name || current?.name || 'Unknown'),
          online: Boolean(srv?.online) || Boolean(current?.online),
          endpoint: String(srv?.endpoint || known?.endpoint || current?.endpoint || '—'),
          tools: Number(srv?.tools || current?.tools || 0),
          description: known?.description || current?.description || 'MCP Server',
          capabilityGroups: current?.capabilityGroups || [],
        })
      }
    }

    if (toolsRes.ok) {
      const toolsPayload = await toolsRes.json()
      const tools = Array.isArray(toolsPayload?.result?.tools)
        ? toolsPayload.result.tools
        : (Array.isArray(toolsPayload?.tools) ? toolsPayload.tools : [])

      const toolsByServer = new Map<string, string[]>()
      for (const item of tools) {
        const name = String(item?.name || '').trim()
        if (!name) continue
        const serverId = normalizeServerId(String(item?.server || item?.source || 'snackbar'))
        const bucket = toolsByServer.get(serverId) || []
        bucket.push(name)
        toolsByServer.set(serverId, bucket)
      }

      for (const [serverId, names] of toolsByServer.entries()) {
        const server = merged.get(serverId)
        if (!server) continue
        server.tools = Math.max(server.tools, names.length)
        server.capabilityGroups = summarizeCapabilityGroups(names)
        merged.set(serverId, server)
      }
    }

    for (const known of KNOWN_SERVERS) {
      if (!merged.has(known.id)) {
        merged.set(known.id, {
          id: known.id,
          name: known.name,
          online: false,
          endpoint: known.endpoint,
          tools: 0,
          description: known.description,
            capabilityGroups: [],
        })
      }
    }
    servers.value = Array.from(merged.values())
  } catch {
    servers.value = await probeKnownServers()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchServers()
  pollTimer = window.setInterval(fetchServers, 10000)
})

let pollTimer: number | undefined

onUnmounted(() => {
  if (pollTimer !== undefined) {
    window.clearInterval(pollTimer)
    pollTimer = undefined
  }
})

const onlineCount = computed(() => servers.value.filter(s => s.online).length)
</script>

<style scoped>
.developer-panel { max-width: calc(var(--usx-spacing-2xl) * 25); }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }
.developer-card-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--usx-color-background); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-semibold); flex: 1; }
.developer-card-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin: 0 0 var(--usx-spacing-xs); }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.developer-card-groups { display: flex; flex-wrap: wrap; gap: var(--usx-spacing-xs); margin-top: var(--usx-spacing-xs); }
.developer-group-chip {
  display: inline-flex;
  align-items: center;
  padding: 0 var(--usx-spacing-xs);
  min-height: var(--usx-touch-target-compact);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: color-mix(in srgb, var(--usx-color-primary) 10%, var(--usx-color-surface));
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
}
</style>
