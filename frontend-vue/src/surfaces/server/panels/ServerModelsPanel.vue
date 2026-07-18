<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">Model Usage</h3>
      <UButton variant="secondary" size="sm" icon="refresh" @click="srv.fetchModels">Refresh</UButton>
    </div>
    <div v-if="srv.modelUsage.length === 0" class="server-muted-text">No model data available.</div>
    <div v-else class="server-model-usage">
      <div v-for="m in srv.modelUsage" :key="m.id" class="model-usage-row">
        <span>{{ m.name }}</span>
        <progress class="model-usage-bar" :value="m.pct" max="100" />
        <span>{{ m.calls }} calls</span>
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
.server-muted-text { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); padding: var(--usx-spacing-md); }
.server-model-usage { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.model-usage-row { display: flex; align-items: center; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); }
.model-usage-row > span:first-child { min-width: 10ch; }
.model-usage-bar { flex: 1; width: 100%; height: var(--usx-spacing-sm); appearance: none; border: none; background: var(--usx-color-border); border-radius: var(--usx-radius-sm); overflow: hidden; }
.model-usage-bar::-webkit-progress-bar { background: var(--usx-color-border); border-radius: var(--usx-radius-sm); }
.model-usage-bar::-webkit-progress-value { background: var(--usx-color-primary); border-radius: var(--usx-radius-sm); }
.model-usage-bar::-moz-progress-bar { background: var(--usx-color-primary); border-radius: var(--usx-radius-sm); }
.model-usage-row > span:last-child { min-width: 7ch; text-align: right; color: var(--usx-color-on-surface-muted); }
</style>