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
        <div class="health-ring" :class="healthClass">
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
const healthClass = computed(() => {
  const pct = srv.healthPct
  return pct >= 80 ? 'health-ring--success' : pct >= 50 ? 'health-ring--warning' : 'health-ring--danger'
})
</script>

<style scoped>
.server-loading { padding: var(--usx-spacing-lg); text-align: center; color: var(--usx-color-on-surface-muted); }
.server-dashboard { display: flex; flex-direction: column; gap: var(--usx-spacing-md); width: 100%; }
.server-dashboard-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--usx-spacing-md); }
.server-muted-text { color: var(--usx-color-on-surface-muted); }
.server-stats-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--usx-spacing-lg); margin-top: var(--usx-spacing-md); }
.server-stat { display: flex; flex-direction: column; }
.server-stat-value { font-size: var(--usx-font-size-2xl); font-weight: var(--usx-font-weight-bold); }
.server-stat-value--up { color: var(--usx-color-success); }
.server-stat-value--degraded { color: var(--usx-color-warning); }
.server-stat-value--down { color: var(--usx-color-danger); }
.server-stat-value--budget { color: var(--usx-color-primary); }
.server-stat-label { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); text-transform: uppercase; }
.health-ring { width: calc(var(--usx-touch-min) + var(--usx-spacing-sm)); height: calc(var(--usx-touch-min) + var(--usx-spacing-sm)); border-radius: 50%; border-style: solid; border-width: calc(var(--usx-border-width) + var(--usx-border-width-thick)); display: flex; align-items: center; justify-content: center; font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-bold); flex-shrink: 0; }
.health-ring--success { border-color: var(--usx-color-success); color: var(--usx-color-success); }
.health-ring--warning { border-color: var(--usx-color-warning); color: var(--usx-color-warning); }
.health-ring--danger { border-color: var(--usx-color-danger); color: var(--usx-color-danger); }
.server-service-row { display: flex; align-items: center; justify-content: space-between; padding: var(--usx-spacing-sm) 0; }
.server-service-info { display: flex; align-items: center; gap: var(--usx-spacing-sm); flex: 1; min-width: 0; }
.server-service-dot { width: var(--usx-spacing-sm); height: var(--usx-spacing-sm); border-radius: 50%; flex-shrink: 0; }
.server-service-dot--up { background: var(--usx-color-success); }
.server-service-dot--degraded { background: var(--usx-color-warning); }
.server-service-dot--down { background: var(--usx-color-danger); }
.server-service-name { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-medium); }
.server-service-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.server-service-uptime { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }

@media (max-width: calc(var(--usx-spacing-2xl) * 32)) {
  .server-stats-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: calc(var(--usx-spacing-2xl) * 18)) {
  .server-stats-row { grid-template-columns: 1fr; }
}
</style>