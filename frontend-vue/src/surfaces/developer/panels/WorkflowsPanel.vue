<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Dev Flow</h3>
      <UBadge type="info">{{ workflows.length }} runs</UBadge>
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
 * @category surfaces/developer
 */
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const workflows = [
  { id: '1', name: 'Vue Port — AssistUI', status: 'done', trigger: 'manual', duration: '4m 12s', time: 'Today', steps: [{ name: 'Scaffold', status: 'done' }, { name: 'Port store', status: 'done' }, { name: 'Port template', status: 'done' }, { name: 'Style', status: 'done' }] },
  { id: '2', name: 'Vue Port — Developer', status: 'running', trigger: 'manual', duration: '2m 30s', time: 'Today', steps: [{ name: 'Scaffold', status: 'done' }, { name: 'Port panels', status: 'running' }, { name: 'Wire APIs', status: 'pending' }] },
  { id: '3', name: 'Vendor md-editor-v3', status: 'done', trigger: 'manual', duration: '1m 45s', time: 'Today', steps: [{ name: 'Clone', status: 'done' }, { name: 'Build', status: 'done' }, { name: 'Wire Skills', status: 'done' }] },
  { id: '4', name: 'Foundation Scaffold', status: 'done', trigger: 'manual', duration: '3m 20s', time: 'Yesterday', steps: [{ name: 'Vue + Vite + Pinia', status: 'done' }, { name: 'Router', status: 'done' }, { name: 'Stores', status: 'done' }, { name: 'Atoms', status: 'done' }] },
]

function statusIcon(status: string): string {
  const map: Record<string, string> = { done: 'check_circle', running: 'sync', failed: 'error', pending: 'circle' }
  return map[status] || 'circle'
}

function statusColor(status: string): 'success' | 'warning' | 'error' | 'info' {
  const map: Record<string, 'success' | 'warning' | 'error' | 'info'> = { done: 'success', running: 'warning', failed: 'error', pending: 'info' }
  return map[status] || 'info'
}
</script>

<style scoped>
.developer-panel { max-width: 800px; }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: 600; margin: 0; }
.developer-card-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--pico-background-color, #30363d); border-radius: var(--usx-border-radius-lg); background: var(--pico-card-background-color, #161b22); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: 600; flex: 1; }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); }
.workflow-steps { display: flex; gap: var(--usx-spacing-sm); margin-top: var(--usx-spacing-sm); flex-wrap: wrap; }
.workflow-step { display: flex; align-items: center; gap: var(--usx-spacing-xs); font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); }
</style>
