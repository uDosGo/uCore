<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">Service Logs</h3>
      <UButton variant="secondary" size="sm" icon="refresh" @click="() => srv.fetchLogs(20)">Refresh</UButton>
    </div>
    <div class="server-logs">
      <div v-if="srv.logs.length === 0" class="server-muted-text">No log entries available.</div>
      <div v-for="(log, i) in srv.logs" :key="i" class="log-entry" :class="'log-entry--' + log.level">
        <span class="log-timestamp">{{ log.timestamp }}</span>
        <span class="log-service">{{ log.service }}</span>
        <span class="log-level" :class="'log-level--' + log.level">{{ log.level }}</span>
        <span class="log-message">{{ log.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useServerStore } from '../../../stores/server'
import UButton from '../../../skills/atoms/UButton.vue'

const srv = useServerStore()
</script>

<style scoped>
.server-logs { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); font-family: var(--usx-font-family-mono); font-size: var(--usx-font-size-sm); }
.server-muted-text { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); padding: var(--usx-spacing-md); }
.log-entry { display: flex; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); border-radius: var(--usx-radius-sm); align-items: baseline; }
.log-timestamp { color: var(--usx-color-on-surface-muted); flex-shrink: 0; }
.log-service { color: var(--usx-color-primary); flex-shrink: 0; min-width: 8ch; }
.log-level { flex-shrink: 0; min-width: 4ch; font-weight: var(--usx-font-weight-semibold); text-transform: uppercase; font-size: var(--usx-font-size-xs); }
.log-level--info { color: var(--usx-color-primary); }
.log-level--warn { color: var(--usx-color-warning); }
.log-level--error { color: var(--usx-color-danger); }
.log-message { color: var(--usx-color-on-surface); }
</style>