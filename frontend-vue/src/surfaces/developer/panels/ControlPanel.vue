<template>
  <div class="control-panel">
    <!-- Status bar — always visible, non-blocking -->
    <div v-if="!data && loading" class="control-status-bar control-status-bar--loading">
      <UIcon name="sync" spin :size="14" />
      <span>Connecting...</span>
    </div>
    <div v-else-if="!data" class="control-status-bar control-status-bar--offline">
      <UIcon name="cloud_off" :size="14" />
      <span>Ecosystem offline — tap Retry to connect</span>
      <UButton variant="ghost" size="sm" @click="retry">Retry</UButton>
    </div>
    <div v-else-if="error" class="control-status-bar control-status-bar--error">
      <UIcon name="error" :size="14" />
      <span>Update failed — showing last known data</span>
      <UButton variant="ghost" size="sm" @click="retry">Retry</UButton>
    </div>

    <!-- Alert Banner -->
    <div v-if="alerts.length > 0" class="control-alerts">
      <div
        v-for="(alert, i) in alerts"
        :key="i"
        class="control-alert"
        :class="'control-alert--' + alert.type"
      >
        <span class="control-alert__message">{{ alert.message }}</span>
      </div>
    </div>

    <!-- Status Badges (Top Bar) -->
    <StatusBadges
      :statuses="data?.statuses ?? null"
      @badge-click="handleBadgeClick"
    />

    <!-- Main Content: Left (60%) + Right (40%) -->
    <div class="control-main">
      <!-- Left Panel -->
      <div class="control-main__left">
        <!-- Live Feed -->
        <section class="control-section">
          <LiveFeedStream
            :activities="feedActivities"
            :loading="loading"
          />
        </section>

        <!-- Agent Status -->
        <section class="control-section">
          <AgentStatusCard :agents="data?.agents ?? null" />
        </section>
      </div>

      <!-- Right Panel -->
      <div class="control-main__right">
        <!-- Cost Dashboard -->
        <section class="control-section">
          <CostDashboard :cost="data?.cost ?? null" />
        </section>

        <!-- Active Mission -->
        <section class="control-section">
          <ActiveMission :mission="data?.mission ?? null" />
        </section>
      </div>
    </div>

    <!-- Bottom Bar -->
    <BottomBar
      :tasker="data?.tasker ?? null"
      :mcp="data?.mcp ?? null"
      :slates="data?.slates ?? null"
      :updated-at="data?.updated_at"
    />

    <!-- Quick Actions -->
    <QuickActions
      :loading="actionLoading"
      @action="handleAction"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * @component ControlPanel
 * @description Unified Control Panel — single-source-of-truth ecosystem dashboard.
 * Replaces scattered status checks across 11 tabs with one consolidated view.
 * Layout: alerts → status badges → left(feed + agents) | right(cost + mission) → bottom bar → quick actions.
 * @category surfaces/developer
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import StatusBadges from './components/StatusBadges.vue'
import LiveFeedStream from './components/LiveFeedStream.vue'
import AgentStatusCard from './components/AgentStatusCard.vue'
import CostDashboard from './components/CostDashboard.vue'
import ActiveMission from './components/ActiveMission.vue'
import BottomBar from './components/BottomBar.vue'
import QuickActions from './components/QuickActions.vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UButton from '../../../skills/atoms/UButton.vue'

interface ControlData {
  statuses: Record<string, { online: boolean; detail: string }>
  feed: { recent: Array<{ id: number; source: string; title: string; content?: string; importance: number; timestamp: string; processed: boolean }>; unprocessed: number }
  agents: Record<string, unknown>
  cost: Record<string, unknown>
  mission: Record<string, unknown>
  tasker: Record<string, unknown>
  mcp: Array<{ name: string; online: boolean }>
  slates: Array<{ name: string }>
  alerts: Array<{ type: string; message: string }>
  updated_at: string
}

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

const data = ref<ControlData | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const actionLoading = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const feedActivities = computed(() => data.value?.feed?.recent ?? [])
const alerts = computed(() => data.value?.alerts ?? [])

async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/control/status`, {
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    data.value = await res.json()
    error.value = null
    // Start polling after successful connect
    if (!pollTimer) pollTimer = setInterval(fetchStatus, 60000)
  } catch (e: any) {
    // Only show error if we had data before (refresh failed)
    if (data.value) error.value = 'Update failed'
    console.warn('Control panel status fetch failed:', e.message)
  } finally {
    loading.value = false
  }
}

function handleBadgeClick(id: string) {
  // Navigation to detail views based on badge type
  const navMap: Record<string, string> = {
    cline: 'agents',
    openrouter: 'models',
    hivemind: 'agents',
    roundtable: 'agents',
    ollama: 'models',
    feed: 'feed',
    slate: 'registry',
    budget: 'settings',
  }
  const target = navMap[id]
  if (target) {
    // Dispatch to parent to switch to target tab
    window.dispatchEvent(new CustomEvent('control-nav', { detail: { tab: target } }))
  }
}

async function handleAction(id: string) {
  actionLoading.value = id
  try {
    switch (id) {
      case 'health-check':
        await fetchStatus()
        // Also fetch full health from the new endpoint
        try {
          const healthRes = await fetch(`${API_BASE}/api/health/full`)
          const healthData = await healthRes.json()
          alert(`System Health: ${healthData.status}\n${healthData.passed_checks}/${healthData.total_checks} checks passed\n\n${
            healthData.components.map((c: any) =>
              `${c.ok ? '✓' : '✗'} ${c.name}: ${c.message}`
            ).join('\n')
          }`)
        } catch (e: any) {
          alert('Health check failed: ' + e.message)
        }
        break
      case 'system-repair':
        if (confirm('Run system self-repair? This will attempt to fix MCP structure, reload skills, and verify plates.')) {
          const repairRes = await fetch(`${API_BASE}/api/system/repair`, { method: 'POST' })
          const repairData = await repairRes.json()
          alert(`Repair complete: ${repairData.health_after_repair}\n${repairData.repairs_successful} successful, ${repairData.repairs_failed} failed`)
          await fetchStatus()
        }
        break
      case 'ingest-feed':
        await fetch(`${API_BASE}/api/feed/ingest`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source: 'browser',
            type: 'manual',
            title: 'Manual feed ingest triggered',
            importance: 0.3,
          }),
        })
        break
      case 'suggest-binder':
        await fetch(`${API_BASE}/api/feed/suggest?min_confidence=0.5`)
        break
      case 'export-cost':
        exportCostReport()
        break
      case 'destroy-rebuild':
        if (confirm('Trigger DESTROY/REBUILD? This resets Dev Mode to active Slate.')) {
          await fetch(`${API_BASE}/api/dev/probe`, { method: 'POST' })
        }
        break
      case 'create-task': {
        const title = prompt('Task title:')
        if (title) {
          await fetch(`${API_BASE}/api/tasker/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, status: 'pending' }),
          })
        }
        break
      }
    }
    // Refresh after action
    await fetchStatus()
  } catch (e: any) {
    console.warn(`Action ${id} failed:`, e.message)
  } finally {
    actionLoading.value = null
  }
}

function exportCostReport() {
  if (!data.value?.cost) return
  const report = JSON.stringify(data.value.cost, null, 2)
  const blob = new Blob([report], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ucore-cost-report-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function retry() {
  loading.value = true
  error.value = null
  fetchStatus()
}

// No auto-fetch on mount — user clicks Retry when ready
onMounted(() => {})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.control-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  max-width: calc(var(--usx-spacing-2xl) * 34 + var(--usx-spacing-md));
}

/* ─── Status Bar (non-blocking) ─────────────────── */
.control-status-bar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  margin-bottom: var(--usx-spacing-sm);
}
.control-status-bar--loading {
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
  color: var(--usx-color-primary);
}
.control-status-bar--error {
  background: color-mix(in srgb, var(--usx-color-danger) 6%, transparent);
  color: var(--usx-color-danger);
}
.control-status-bar--offline {
  background: color-mix(in srgb, var(--usx-color-on-surface-muted) 6%, transparent);
  color: var(--usx-color-on-surface-muted);
}
.control-status-bar .usx-button {
  margin-left: auto;
}

/* ─── Alert Banner ─────────────────────────────────── */
.control-alerts {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.control-alert {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
}

.control-alert--warning {
  background: color-mix(in srgb, var(--usx-color-warning) 10%, transparent);
  border: var(--usx-border-width) solid var(--usx-color-warning);
  color: var(--usx-color-warning);
}

.control-alert--error {
  background: color-mix(in srgb, var(--usx-color-danger) 10%, transparent);
  border: var(--usx-border-width) solid var(--usx-color-danger);
  color: var(--usx-color-danger);
}

.control-alert--info {
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
  border: var(--usx-border-width) solid var(--usx-color-primary);
  color: var(--usx-color-primary);
}

.control-alert__message {
  font-size: var(--usx-font-size-sm);
}

/* ─── Main Content Grid ────────────────────────────── */
.control-main {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  gap: var(--usx-spacing-md);
}

@media (max-width: calc(var(--usx-spacing-2xl) * 25)) {
  .control-main {
    grid-template-columns: 1fr;
  }
}

.control-main__left,
.control-main__right {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

/* ─── Section Cards ─────────────────────────────────── */
.control-section {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
  border: var(--usx-border-width) solid var(--usx-color-border);
}
</style>