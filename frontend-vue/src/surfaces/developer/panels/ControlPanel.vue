<template>
  <div class="control-panel">
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
const loading = ref(true)
const error = ref<string | null>(null)
const actionLoading = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const feedActivities = computed(() => data.value?.feed?.recent ?? [])
const alerts = computed(() => data.value?.alerts ?? [])

async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/control/status`, {
      signal: AbortSignal.timeout(10000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    data.value = await res.json()
    error.value = null
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch status'
    console.warn('Control panel status fetch failed:', e.message)
  } finally {
    loading.value = false
  }
}

function handleBadgeClick(id: string) {
  // Navigation to detail views based on badge type
  const navMap: Record<string, string> = {
    cline: 'cline-cli',
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

onMounted(() => {
  fetchStatus()
  // Poll every 30 seconds for live updates
  pollTimer = setInterval(fetchStatus, 30000)
})

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
  max-width: 1100px;
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
  background: #2e2a1a;
  border: 1px solid #d29922;
  color: #d29922;
}

.control-alert--error {
  background: #3a1a1a;
  border: 1px solid #f85149;
  color: #f85149;
}

.control-alert--info {
  background: #1a2e3a;
  border: 1px solid #58a6ff;
  color: #58a6ff;
}

.control-alert__message {
  font-size: var(--usx-font-size-sm);
}

/* ─── Main Content Grid ────────────────────────────── */
.control-main {
  display: grid;
  grid-template-columns: 6fr 4fr;
  gap: var(--usx-spacing-md);
}

@media (max-width: 800px) {
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
  background: var(--usx-color-surface, #161b22);
  border-radius: var(--usx-radius-lg, 8px);
  border: var(--usx-border-width, 1px) solid var(--usx-color-border, #30363d);
}
</style>