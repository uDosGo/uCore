<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">Runtime Agents</h3>
      <UButton variant="secondary" size="sm" icon="refresh" @click="srv.fetchAgents">Refresh</UButton>
    </div>
    <div v-if="srv.agents.length === 0" class="server-muted-text">No agents available.</div>
    <div v-else class="server-agents-list">
      <div v-for="agent in srv.agents" :key="agent.id" class="surface__panel">
        <div class="usx-flex-row">
          <UIcon :name="agent.icon" />
          <span class="server-agent-name">{{ agent.name }}</span>
          <UBadge :type="agent.active ? 'success' : 'info'" size="sm">{{ agent.active ? 'running' : 'idle' }}</UBadge>
        </div>
        <p class="server-agent-desc">{{ agent.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useServerStore } from '../../../stores/server'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'

const srv = useServerStore()
</script>

<style scoped>
.server-muted-text { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); padding: var(--usx-spacing-md); }
.server-agent-name { font-weight: var(--usx-font-weight-semibold); flex: 1; }
.server-agent-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin: 0; }
.server-agents-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
</style>