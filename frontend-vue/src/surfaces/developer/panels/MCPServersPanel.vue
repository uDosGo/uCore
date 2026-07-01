<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">MCP Servers</h3>
      <UBadge :type="onlineCount > 0 ? 'success' : 'warning'" size="sm">
        {{ onlineCount }}/{{ servers.length }} online
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
import { computed } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const servers = [
  { id: 'snackbar', name: 'Snackbar', online: true, endpoint: 'localhost:8484', tools: 12, description: 'Core MCP server — clipboard, maintenance, workflows, skills' },
  { id: 'ucore', name: 'uCore Backend', online: true, endpoint: 'localhost:8000', tools: 8, description: 'Knowledge, surfaces, health, MCP tool registry' },
  { id: 'vault', name: 'Vault Indexer', online: false, endpoint: 'localhost:8765', tools: 5, description: 'AppFlowy vault search and document indexing' },
  { id: 'gridsmith', name: 'GridSmith', online: false, endpoint: 'localhost:8888', tools: 6, description: 'Grid rendering, spatial algebra, map generation' },
]

const onlineCount = computed(() => servers.filter(s => s.online).length)
</script>

<style scoped>
.developer-panel { max-width: 800px; }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: 600; margin: 0; }
.developer-card_list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--pico-background-color, #30363d); border-radius: var(--usx-border-radius-lg); background: var(--pico-card-background-color, #161b22); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: 600; flex: 1; }
.developer-card-desc { font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); margin: 0 0 var(--usx-spacing-xs); }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); }
</style>
