<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="srv.activeTab"
      :tabs="SERVER_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <!-- Panel Content -->
    <div class="surface__content">
      <!-- Dashboard -->
      <div v-if="srv.activeTab === 'dashboard'" class="server-dashboard">
        <div class="surface__panel">
          <div class="server-dashboard-header">
            <div>
              <h2 class="usx-no-margin">Server Operations</h2>
              <p class="usx-mt-xs server-muted-text">{{ srv.services.length }} services · {{ upCount }} online</p>
            </div>
            <div class="health-ring" :style="{ borderColor: healthColor, color: healthColor }">
              {{ healthPct }}%
            </div>
          </div>
          <div class="server-stats-row">
            <div class="server-stat"><span class="server-stat-value server-stat-value--up">{{ upCount }}</span><span class="server-stat-label">Up</span></div>
            <div class="server-stat"><span class="server-stat-value server-stat-value--degraded">{{ degradedCount }}</span><span class="server-stat-label">Degraded</span></div>
            <div class="server-stat"><span class="server-stat-value server-stat-value--down">{{ downCount }}</span><span class="server-stat-label">Down</span></div>
            <div class="server-stat"><span class="server-stat-value server-stat-value--budget">${{ srv.budgetRemaining?.toFixed(2) ?? '—' }}</span><span class="server-stat-label">Budget</span></div>
          </div>
        </div>

        <div class="surface__panel">
          <h3 class="surface__panel-title">Services</h3>
          <div v-for="svc in srv.services" :key="svc.name" class="server-service-row">
            <div class="server-service-info">
              <span class="server-service-dot" :class="`server-service-dot--${svc.status}`" />
              <span class="server-service-name">{{ svc.name }}</span>
              <span class="server-service-desc">{{ svc.description }}</span>
            </div>
            <span class="server-service-uptime">{{ svc.uptime }}%</span>
          </div>
        </div>
      </div>

      <!-- Services -->
      <div v-else-if="srv.activeTab === 'services'">
        <h3 class="surface__panel-title">All Services</h3>
        <div class="server-services-grid">
          <div v-for="svc in srv.services" :key="svc.name" class="surface__panel">
            <div class="usx-flex-row">
              <UIcon :name="svc.type === 'system' ? 'settings' : 'person'" />
              <span class="server-service-name-cell">{{ svc.name }}</span>
              <UBadge :type="svc.status === 'up' ? 'success' : svc.status === 'degraded' ? 'warning' : 'error'" size="sm">
                {{ svc.status }}
              </UBadge>
            </div>
            <p class="usx-mt-sm server-muted-text-sm">{{ svc.description }}</p>
            <div class="usx-flex-row usx-gap-md server-muted-text-sm">
              <span>Port :{{ svc.port || 'N/A' }}</span>
              <span>Uptime {{ svc.uptime }}%</span>
              <span>{{ svc.type }}</span>
            </div>
            <div class="usx-flex-row usx-gap-xs usx-mt-sm">
              <UButton variant="ghost" size="sm">Restart</UButton>
              <UButton variant="ghost" size="sm">Logs</UButton>
            </div>
          </div>
        </div>
      </div>

      <!-- Logs -->
      <div v-else-if="srv.activeTab === 'logs'">
        <h3 class="surface__panel-title">Service Logs</h3>
        <div class="server-logs">
          <div v-for="(log, i) in srv.logs" :key="i" class="log-entry" :class="`log-entry--${log.level}`">
            <span class="log-timestamp">{{ log.timestamp }}</span>
            <span class="log-service">{{ log.service }}</span>
            <span class="log-level" :class="`log-level--${log.level}`">{{ log.level }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>

      <!-- Models -->
      <div v-else-if="srv.activeTab === 'models'">
        <h3 class="surface__panel-title">Server Models</h3>
        <p class="usx-mb-md server-muted-text-sm">Models are managed from the Developer surface. This panel shows runtime model usage.</p>
        <div class="server-model-usage">
          <div v-for="m in modelUsage" :key="m.id" class="model-usage-row">
            <span>{{ m.name }}</span>
            <div class="model-usage-bar"><div class="model-usage-fill" :style="{ width: m.pct + '%' }" /></div>
            <span>{{ m.calls }} calls</span>
          </div>
        </div>
      </div>

      <!-- Agents -->
      <div v-else-if="srv.activeTab === 'agents'">
        <h3 class="surface__panel-title">Runtime Agents</h3>
        <div class="server-agents-list">
          <div v-for="agent in runtimeAgents" :key="agent.id" class="surface__panel">
            <div class="usx-flex-row">
              <UIcon :name="agent.icon" />
              <span class="server-agent-name">{{ agent.name }}</span>
              <UBadge :type="agent.active ? 'success' : 'info'" size="sm">{{ agent.active ? 'running' : 'idle' }}</UBadge>
            </div>
            <p class="server-agent-desc">{{ agent.description }}</p>
          </div>
        </div>
      </div>

      <!-- Budget -->
      <div v-else-if="srv.activeTab === 'budget'">
        <h3 class="surface__panel-title">Budget & Usage</h3>
        <div class="budget-overview">
          <div class="budget-stat">
            <span class="budget-stat-label">Remaining</span>
            <span class="budget-stat-value">${{ srv.budgetRemaining?.toFixed(2) ?? '—' }}</span>
          </div>
          <div class="budget-stat">
            <span class="budget-stat-label">Monthly Limit</span>
            <span class="budget-stat-value">$50.00</span>
          </div>
          <div class="budget-stat">
            <span class="budget-stat-label">Used</span>
            <span class="budget-stat-value">$7.50</span>
          </div>
          <div class="budget-stat">
            <span class="budget-stat-label">Status</span>
            <UBadge :type="srv.budgetOverLimit ? 'error' : 'success'" size="sm">
              {{ srv.budgetOverLimit ? 'OVER LIMIT' : 'OK' }}
            </UBadge>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component ServerSurface
 * @description Server operations surface — dashboard, services, logs, models,
 * runtime agents, budget.
 * Uses USX surface classes from usx-standard.css.
 * @category surfaces
 * @usage Routed at '/server/*'
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useShellStore } from '../../stores/shell'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'
import UButton from '../../skills/atoms/UButton.vue'
import { useServerStore, SERVER_TABS } from '../../stores/server'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

const shell = useShellStore()
const srv = useServerStore()
const $router = useRouter()

const upCount = computed(() => srv.services.filter(s => s.status === 'up').length)
const degradedCount = computed(() => srv.services.filter(s => s.status === 'degraded').length)
const downCount = computed(() => srv.services.filter(s => s.status === 'down').length)
const healthPct = computed(() => srv.services.length ? Math.round((upCount.value / srv.services.length) * 100) : 0)
const healthColor = computed(() => {
  const pct = healthPct.value
  return pct >= 80 ? 'var(--server-color-up)' : pct >= 50 ? 'var(--server-color-degraded)' : 'var(--server-color-down)'
})

const modelUsage = [
  { id: '1', name: 'Llama 3.2', pct: 65, calls: 1240 },
  { id: '2', name: 'GPT-4o', pct: 25, calls: 480 },
  { id: '3', name: 'DeepSeek V3', pct: 10, calls: 190 },
]

const runtimeAgents = [
  { id: 'snackbar', name: 'Snackbar Runner', icon: 'play_arrow', active: true, description: 'Orchestrates container workflows and skill execution' },
  { id: 'hivemind', name: 'Hivemind Router', icon: 'route', active: true, description: 'Routes tasks to specialized AI agents' },
  { id: 'vault-indexer', name: 'Vault Indexer', icon: 'search', active: false, description: 'Indexes AppFlowy vault documents for search' },
  { id: 'feed-spooler', name: 'Feed Spooler', icon: 'dynamic_feed', active: true, description: 'Processes and routes feed content' },
]
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════════
   ServerSurface — USX-standard scoped styles
   Uses --usx-color-* throughout. No --pico-* or hardcoded values.
   ═══════════════════════════════════════════════════════════════════ */

/* ─── Status Color Tokens ──────────────────────────────────────── */
.surface {
  --server-color-up: #3fb950;
  --server-color-degraded: #d29922;
  --server-color-down: #f85149;
  --server-color-budget: #58a6ff;
}

.server-dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-md);
}

.server-muted-text {
  color: var(--usx-color-on-surface-muted);
}

.server-muted-text-sm {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.server-service-name-cell {
  flex: 1;
  font-weight: var(--usx-font-weight-semibold);
}

.server-agent-name {
  font-weight: var(--usx-font-weight-semibold);
  flex: 1;
}

.server-agent-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin: 0;
}

/* ─── Dashboard ────────────────────────────────────────────────── */
.server-dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  max-width: 900px;
}

.server-stats-row {
  display: flex;
  gap: var(--usx-spacing-lg);
  margin-top: var(--usx-spacing-md);
}

.server-stat {
  display: flex;
  flex-direction: column;
}

.server-stat-value {
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
}

.server-stat-value--up { color: #3fb950; }
.server-stat-value--degraded { color: #d29922; }
.server-stat-value--down { color: #f85149; }
.server-stat-value--budget { color: #58a6ff; }

.server-stat-label {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
}

.health-ring {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 3px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-bold);
  flex-shrink: 0;
}

.server-service-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm) 0;
}

.server-service-info {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  flex: 1;
  min-width: 0;
}

.server-service-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.server-service-dot--up { background: #3fb950; }
.server-service-dot--degraded { background: #d29922; }
.server-service-dot--down { background: #f85149; }

.server-service-name {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
}

.server-service-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.server-service-uptime {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.server-services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--usx-spacing-md);
}

.server-logs {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
}

.log-entry {
  display: flex;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  align-items: baseline;
}

.log-timestamp {
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
}

.log-service {
  color: var(--usx-color-primary);
  flex-shrink: 0;
  min-width: 80px;
}

.log-level {
  flex-shrink: 0;
  min-width: 40px;
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
  font-size: var(--usx-font-size-xs);
}

.log-level--info { color: #58a6ff; }
.log-level--warn { color: #d29922; }
.log-level--error { color: #f85149; }

.log-message {
  color: var(--usx-color-on-surface);
}

.server-model-usage {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.model-usage-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
}

.model-usage-row > span:first-child {
  min-width: 100px;
}

.model-usage-bar {
  flex: 1;
  height: 8px;
  background: var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  overflow: hidden;
}

.model-usage-fill {
  height: 100%;
  background: var(--usx-color-primary);
  border-radius: var(--usx-radius-sm);
}

.model-usage-row > span:last-child {
  min-width: 70px;
  text-align: right;
  color: var(--usx-color-on-surface-muted);
}

.server-agents-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.budget-overview {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--usx-spacing-md);
}

.budget-stat {
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-background);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.budget-stat-label {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
}

.budget-stat-value {
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
}
</style>
