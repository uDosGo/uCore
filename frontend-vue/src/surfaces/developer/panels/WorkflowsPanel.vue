<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Dev Flow</h3>
      <UBadge type="info">{{ loading ? '...' : workflows.length + ' runs' }}</UBadge>
    </div>
    <div class="developer-card-list">
      <div v-for="run in workflows" :key="run.id" class="developer-card">
        <div class="developer-card-header">
          <UIcon :name="statusIcon(run.status)" />
          <span class="developer-card-title">{{ run.name }}</span>
          <UBadge :type="statusColor(run.status)" size="sm">{{ run.status }}</UBadge>
        </div>
        <div class="developer-card-meta">
          <span>{{ run.trigger }}</span>
          <span>{{ run.duration }}</span>
          <span>{{ run.time }}</span>
        </div>
        <div v-if="run.steps?.length" class="workflow-steps">
          <div v-for="step in run.steps" :key="step.name" class="workflow-step">
            <UIcon :name="step.status === 'done' ? 'check_circle' : step.status === 'running' ? 'sync' : 'circle'" />
            <span>{{ step.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component WorkflowsPanel
 * @description Dev workflow runs panel — history, status, step progress.
 * Wired to /api/workflows and /api/workflows/runs.
 * @category surfaces/developer
 */
import { ref, onMounted } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

interface WorkflowRun {
  id: string
  name: string
  status: string
  trigger: string
  duration: string
  time: string
  steps?: Array<{ name: string; status: string }>
}

const workflows = ref<WorkflowRun[]>([])
const loading = ref(true)

async function fetchWorkflows() {
  loading.value = true
  try {
    // Fetch workflow runs
    const runsRes = await fetch(`${API_BASE}/api/workflows/runs?limit=20`, {
      signal: AbortSignal.timeout(5000),
    })
    if (runsRes.ok) {
      const data = await runsRes.json()
      const runs = data.runs || data || []
      workflows.value = runs.map((r: any) => ({
        id: r.id || r.run_id || String(Date.now()),
        name: r.name || r.workflow_name || r.title || 'Workflow Run',
        status: r.status || 'pending',
        trigger: r.trigger || 'manual',
        duration: r.duration || '—',
        time: r.started_at || r.created_at || '—',
        steps: (r.steps || []).map((s: any) => ({
          name: s.name || s.step_name || 'Step',
          status: s.status || 'pending',
        })),
      }))
    }
  } catch {
    // Backend offline
  } finally {
    loading.value = false
  }
}

onMounted(() => { fetchWorkflows() })

function statusIcon(status: string): string {
  const map: Record<string, string> = { done: 'check_circle', running: 'sync', failed: 'error', pending: 'circle' }
  return map[status] || 'circle'
}

function statusColor(status: string): 'success' | 'warning' | 'error' | 'info' {
  const map: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
    done: 'success', running: 'warning', failed: 'error', pending: 'info',
  }
  return map[status] || 'info'
}
</script>

<style scoped>
.developer-panel { max-width: calc(var(--usx-spacing-2xl) * 25); }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }
.developer-card-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--usx-color-background); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-semibold); flex: 1; }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.workflow-steps { display: flex; gap: var(--usx-spacing-sm); margin-top: var(--usx-spacing-sm); flex-wrap: wrap; }
.workflow-step { display: flex; align-items: center; gap: var(--usx-spacing-xs); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
</style>