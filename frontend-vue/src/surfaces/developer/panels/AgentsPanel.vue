<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Agents</h3>
      <UBadge type="success">{{ loading ? '...' : activeCount + ' active' }}</UBadge>
    </div>
    <div class="developer-card-list">
      <div v-for="agent in agents" :key="agent.id" class="developer-card">
        <div class="developer-card-header">
          <UIcon :name="agent.icon" />
          <span class="developer-card-title">{{ agent.name }}</span>
          <UBadge :type="agent.active ? 'success' : 'info'" size="sm">
            {{ agent.active ? 'active' : 'idle' }}
          </UBadge>
        </div>
        <p class="developer-card-desc">{{ agent.description }}</p>
        <div class="developer-card-meta">
          <span>{{ agent.model }}</span>
          <span>{{ agent.tasks }} tasks</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component AgentsPanel
 * @description Dev agents management panel.
 * @category surfaces/developer
 */
import { ref, watch, onMounted } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

interface Agent {
  id: string
  name: string
  icon: string
  active: boolean
  model: string
  tasks: number
  description: string
}

const agents = ref<Agent[]>([])
const loading = ref(true)

async function fetchAgents() {
  loading.value = true
  try {
    // Fetch agent list
    const res = await fetch(`${API_BASE}/api/agents`, {
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) {
      const data = await res.json()
      const list = data.agents || data || []
      agents.value = list.map((a: any) => ({
        id: a.id || a.name?.toLowerCase() || 'unknown',
        name: a.name || a.id || 'Unknown Agent',
        icon: a.icon || 'smart_toy',
        active: a.active !== false,
        model: a.model || a.default_model || '—',
        tasks: a.tasks || a.task_count || 0,
        description: a.description || a.specialization || '',
      }))
    }

    // Try stats endpoint for richer data
    try {
      const statsRes = await fetch(`${API_BASE}/api/agents/stats`, {
        signal: AbortSignal.timeout(3000),
      })
      if (statsRes.ok) {
        const stats = await statsRes.json()
        // Merge stats into agents
        for (const agent of agents.value) {
          if (stats[agent.id]) {
            agent.active = stats[agent.id].active !== false
            agent.tasks = stats[agent.id].tasks || agent.tasks
          }
        }
      }
    } catch {
      // Stats optional
    }
  } catch {
    // Backend offline — show fallback
    agents.value = [
      { id: 'backend-offline', name: 'Hivemind Backend', icon: 'dns', active: false, model: '—', tasks: 0, description: 'Agent backend unreachable. Start the Hivemind server.' },
    ]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAgents()
})

const activeCount = ref(0)

// Update activeCount whenever agents change
watch(agents, (val) => {
  activeCount.value = val.filter(a => a.active).length
}, { immediate: true })
</script>

<style scoped>
.developer-panel { max-width: 800px; }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }
.developer-card-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--usx-color-background); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-semibold); flex: 1; }
.developer-card-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin: 0 0 var(--usx-spacing-xs); }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
</style>
