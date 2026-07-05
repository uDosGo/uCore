<template>
  <div class="server-dashboard" v-if="!srv.loading">
    <div class="surface__panel">
      <div class="server-dashboard-header">
        <div>
          <h2 class="usx-no-margin">Server Operations</h2>
          <p class="usx-mt-xs server-muted-text">
            {{ srv.services.length }} services · {{ srv.upCount }} online
          </p>
        </div>
        <div
          class="health-ring"
          :style="{ borderColor: healthColor, color: healthColor }"
        >
          {{ srv.healthPct }}%
        </div>
      </div>
      <div class="server-stats-row">
        <div class="server-stat">
          <span class="server-stat-value server-stat-value--up">{{ srv.upCount }}</span>
          <span class="server-stat-label">Up</span>
        </div>
        <div class="server-stat">
          <span class="server-stat-value server-stat-value--degraded">{{ srv.degradedCount }}</span>
          <span class="server-stat-label">Degraded</span>
        </div>
        <div class="server-stat">
          <span class="server-stat-value server-stat-value--down">{{ srv.downCount }}</span>
          <span class="server-stat-label">Down</span>
        </div>
        <div class="server-stat">
          <span class="server-stat-value server-stat-value--budget">${{ budgetDisplay }}</span>
          <span class="server-stat-label">Budget</span>
        </div>
      </div>
    </div>
    <div class="surface__panel">
      <h3 class="surface__panel-title">Services</h3>
      <div v-for="svc in srv.services" :key="svc.name" class="server-service-row">
        <div class="server-service-info">
          <span class="server-service-dot" :class="'server-service-dot--' + svc.status" />
          <span class="server-service-name">{{ svc.name }}</span>
          <span class="server-service-desc">{{ svc.description }}</span>
        </div>
        <span class="server-service-uptime">{{ svc.uptime }}%</span>
      </div>
    </div>
  </div>
  <div v-else class="server-loading">Loading server data...</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useServerStore } from '../../../stores/server'

const srv = useServerStore()

const budgetDisplay = computed(() =>
  srv.budgetRemaining != null ? srv.budgetRemaining.toFixed(2) : '—'
)
const healthColor = computed(() => {
  const pct = srv.healthPct
  return pct >= 80 ? '#3fb950' : pct >= 50 ? '#d29922' : '#f85149'
})
</script>

<style scoped>
.server-loading { padding: var(--usx-spacing-lg); text-align: center; color: var(--usx-color-on-surface-muted); }
.server-dashboard { display: flex; flex-direction: column; gap: var(--usx-spacing-md); max-width: 900px; }
.server-dashboard-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--usx-spacing-md); }
.server-muted-text { color: var(--usx-color-on-surface-muted); }
.server-stats-row { display: flex; gap: var(--usx-spacing-lg); margin-top: var(--usx-spacing-md); }
.server-stat { display: flex; flex-direction: column; }
.server-stat-value { font-size: var(--usx-font-size-2xl); font-weight: var(--usx-font-weight-bold); }
.server-stat-value--up { color: #3fb950; }
.server-stat-value--degraded { color: #d29922; }
.server-stat-value--down { color: #f85149; }
.server-stat-value--budget { color: #58a6ff; }
.server-stat-label { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); text-transform: uppercase; }
.health-ring { width: 56px; height: 56px; border-radius: 50%; border: 3px solid; display: flex; align-items: center; justify-content: center; font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-bold); flex-shrink: 0; }
.server-service-row { display: flex; align-items: center; justify-content: space-between; padding: var(--usx-spacing-sm) 0; }
.server-service-info { display: flex; align-items: center; gap: var(--usx-spacing-sm); flex: 1; min-width: 0; }
.server-service-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.server-service-dot--up { background: #3fb950; }
.server-service-dot--degraded { background: #d29922; }
.server-service-dot--down { background: #f85149; }
.server-service-name { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-medium); }
.server-service-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.server-service-uptime { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
</style>