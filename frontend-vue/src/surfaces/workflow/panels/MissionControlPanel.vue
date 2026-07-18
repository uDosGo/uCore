<template>
  <div class="wf-panel">
    <div class="surface__panel">
      <div class="wf-panel-header">
        <h3 class="surface__panel-title">Mission Control</h3>
        <div class="wf-panel-badges">
          <UBadge type="info" size="sm">User Workflow</UBadge>
          <UBadge
            :type="wf.workflowStatus?.appflowy?.available ? 'success' : 'warning'"
            size="sm"
          >
            AppFlowy {{ wf.workflowStatus?.appflowy?.available ? 'Available' : 'Optional' }}
          </UBadge>
        </div>
      </div>
      <p class="surface__panel-description">Track progress across your missions and keep markdown first.</p>
      <div class="wf-actions-row">
        <UButton
          size="sm"
          variant="secondary"
          icon="archive"
          :disabled="!!busyAction"
          @click="archiveState"
        >
          {{ busyAction === 'archive' ? 'Archiving...' : 'Archive State' }}
        </UButton>
        <UButton
          size="sm"
          variant="secondary"
          icon="add"
          :disabled="!!busyAction"
          @click="seedState"
        >
          {{ busyAction === 'seed' ? 'Seeding...' : 'Seed User Tasks' }}
        </UButton>
        <UButton
          size="sm"
          variant="primary"
          icon="refresh"
          class="wf-button-warning"
          :disabled="!!busyAction"
          @click="resetState"
        >
          {{ busyAction === 'reset' ? 'Resetting...' : 'Reset + Seed' }}
        </UButton>
      </div>
      <div v-if="lastActionMessage" class="wf-action-message">{{ lastActionMessage }}</div>
    </div>

    <!-- Stats cards -->
    <div class="wf-stats">
      <div class="wf-stat">
        <span class="wf-stat-value">{{ wf.totalTasks }}</span>
        <span class="wf-stat-label">Total Tasks</span>
      </div>
      <div class="wf-stat">
        <span class="wf-stat-value wf-stat-value--info">{{ wf.inProgressCount }}</span>
        <span class="wf-stat-label">In Progress</span>
      </div>
      <div class="wf-stat">
        <span class="wf-stat-value wf-stat-value--success">{{ wf.completedCount }}</span>
        <span class="wf-stat-label">Completed</span>
      </div>
      <div class="wf-stat">
        <span class="wf-stat-value wf-stat-value--warning">{{ wf.missions.length }}</span>
        <span class="wf-stat-label">Missions</span>
      </div>
    </div>

    <!-- Loading / Error -->
    <div v-if="wf.loading" class="wf-loading">
      <UIcon name="sync" /> Loading workflow data...
    </div>
    <div v-else-if="wf.error" class="wf-error">
      <UIcon name="error" />
      {{ wf.error }}
      <UButton size="sm" variant="secondary" icon="refresh" @click="wf.fetchAll()">Retry</UButton>
    </div>

    <!-- Tasker Boards from backend -->
    <div v-if="wf.workflowStatus?.tasker?.boards" class="wf-section">
      <h4 class="wf-section-title">Tasker Boards</h4>
      <div class="wf-board-grid">
        <div
          v-for="board in wf.workflowStatus.tasker.boards"
          :key="board.name"
          class="wf-board-card"
        >
          <div class="wf-board-card-header">
            <UIcon name="view_kanban" />
            <span>{{ board.name }}</span>
            <UBadge type="info" size="sm" circle>{{ board.count }}</UBadge>
          </div>
        </div>
      </div>
    </div>

    <div v-if="wf.workflowStatus?.next_actions?.length" class="wf-section">
      <h4 class="wf-section-title">Next Actions</h4>
      <ul class="wf-next-actions">
        <li v-for="(item, idx) in wf.workflowStatus.next_actions" :key="idx">{{ item }}</li>
      </ul>
    </div>

    <!-- Missions card grid (Dashboard-style) -->
    <div class="wf-section">
      <h4 class="wf-section-title">Active Missions</h4>
      <div class="wf-mission-grid">
        <div v-for="mission in wf.missions" :key="mission.id" class="wf-mission-card">
          <div class="wf-mission-card-icon">
            <UIcon name="flag" />
          </div>
          <div class="wf-mission-card-content">
            <h4 class="wf-mission-card-title">{{ mission.title }}</h4>
            <p class="wf-mission-card-desc">{{ mission.description }}</p>
            <div class="wf-mission-card-badges">
              <UBadge
                :type="mission.status === 'active' ? 'success' : mission.status === 'completed' ? 'info' : 'warning'"
                size="sm"
              >
                {{ mission.status }}
              </UBadge>
              <UBadge
                :type="mission.priority === 'high' ? 'error' : mission.priority === 'medium' ? 'warning' : 'info'"
                size="sm"
              >
                {{ mission.priority }}
              </UBadge>
              <span class="wf-mission-task-count">{{ mission.taskIds.length }} tasks</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent runs from backend — card style matching mission cards -->
    <div v-if="wf.workflowRuns.length > 0" class="wf-section">
      <h4 class="wf-section-title">Recent Workflow Runs</h4>
      <div class="wf-run-grid">
        <div
          v-for="run in wf.workflowRuns.slice(0, 5)"
          :key="run.run_id"
          class="wf-run-card"
        >
          <div class="wf-run-card-icon">
            <UIcon :name="run.status === 'completed' ? 'check_circle' : run.status === 'failed' ? 'error' : 'schedule'" />
          </div>
          <div class="wf-run-card-content">
            <span class="wf-run-card-name">{{ run.workflow_name || run.workflow_id }}</span>
            <span class="wf-run-card-time">{{ formatTime(run.started_at) }}</span>
          </div>
          <UBadge
            :type="run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'warning'"
            size="sm"
            pill
          >
            {{ run.status }}
          </UBadge>
        </div>
      </div>
    </div>

    <!-- Mini Binder Launchpad widget -->
    <div class="wf-section">
      <div class="wf-mini-binder">
        <div class="wf-mini-binder-header">
          <UIcon name="folder" />
          <span>Binder Launchpad</span>
          <UButton size="sm" variant="secondary" icon="open_in_new" @click="openFullBinder">Open Binder</UButton>
        </div>
        <p class="wf-mini-binder-desc">Drop files here to quickly compile a binder, or open the full Binder tab.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'
import { useWorkflowStore } from '../../../stores/workflow'

const wf = useWorkflowStore()
const router = useRouter()
const busyAction = ref('')
const lastActionMessage = ref('')

function openFullBinder() {
  router.push('/workflow?tab=binder')
}

function formatTime(iso: string): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString()
  } catch {
    return iso
  }
}

async function archiveState() {
  busyAction.value = 'archive'
  lastActionMessage.value = ''
  try {
    const payload: any = await wf.archiveUserWorkflow('manual-user-archive')
    const dir = payload?.archive?.archive_dir || 'archive created'
    lastActionMessage.value = `Archive complete: ${dir}`
  } catch (e: any) {
    lastActionMessage.value = `Archive failed: ${e.message || e}`
  } finally {
    busyAction.value = ''
  }
}

async function resetState() {
  const ok = window.confirm('Archive current user workflow and reset to fresh seed data?')
  if (!ok) return

  busyAction.value = 'reset'
  lastActionMessage.value = ''
  try {
    const payload: any = await wf.resetUserWorkflow('user-reset-seed')
    const count = payload?.seed?.tasks?.created_count || 0
    lastActionMessage.value = `Reset complete. Seeded ${count} tasks.`
  } catch (e: any) {
    lastActionMessage.value = `Reset failed: ${e.message || e}`
  } finally {
    busyAction.value = ''
  }
}

async function seedState() {
  busyAction.value = 'seed'
  lastActionMessage.value = ''
  try {
    const payload: any = await wf.seedUserWorkflow('user-seed-only')
    const count = payload?.seed?.tasks?.created_count || 0
    lastActionMessage.value = `Seed complete. Added or refreshed ${count} tasks.`
  } catch (e: any) {
    lastActionMessage.value = `Seed failed: ${e.message || e}`
  } finally {
    busyAction.value = ''
  }
}

onMounted(() => {
  wf.fetchAll()
})
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
  height: 100%;
}

.wf-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
  flex-wrap: wrap;
}

.wf-panel-badges {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.wf-actions-row {
  display: flex;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
  margin-top: var(--usx-spacing-sm);
}

.wf-action-message {
  margin-top: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface-muted);
}

.wf-button-warning :deep(.u-button) {
  background: var(--usx-color-warning);
  color: var(--usx-color-on-warning);
}

.wf-button-warning :deep(.u-button:hover) {
  background: color-mix(in srgb, var(--usx-color-warning) 86%, var(--usx-color-danger));
}

.wf-next-actions {
  margin: 0;
  padding-left: var(--usx-spacing-lg);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.wf-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--usx-spacing-md);
}

.wf-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
  min-width: 12ch;
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.wf-stat-value {
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
  line-height: var(--usx-line-height-tight);
}

.wf-stat-label {
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface-muted);
}

.wf-stat-value--success { color: var(--usx-color-success); }
.wf-stat-value--info { color: var(--usx-color-primary); }
.wf-stat-value--warning { color: var(--usx-color-warning); }

.wf-loading,
.wf-error {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
}

.wf-loading {
  color: var(--usx-color-on-surface-muted);
}

.wf-error {
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 10%, transparent);
  border: var(--usx-border-width) solid color-mix(in srgb, var(--usx-color-danger) 20%, transparent);
}

.wf-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-section-title {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
  letter-spacing: var(--usx-letter-spacing-wide);
}

.wf-board-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--usx-spacing-sm);
}

.wf-board-card {
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.wf-board-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-medium);
}

/* Dashboard-style mission card grid */
.wf-mission-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--usx-spacing-md);
}

.wf-mission-card {
  display: flex;
  align-items: flex-start;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  transition: background var(--usx-transition-fast), border-color var(--usx-transition-fast), transform var(--usx-transition-fast);
}

.wf-mission-card:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 4%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-primary) 20%, transparent);
  transform: translateY(calc(var(--usx-spacing-1) * -1));
}

.wf-mission-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
  flex-shrink: 0;
  font-size: var(--usx-icon-size-lg);
}

.wf-mission-card:hover .wf-mission-card-icon {
  background: var(--usx-color-primary-disabled);
  color: var(--usx-color-primary);
}

.wf-mission-card-content {
  flex: 1;
  min-width: 0;
}

.wf-mission-card-title {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0 0 var(--usx-spacing-xs) 0;
  color: var(--usx-color-on-surface);
}

.wf-mission-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin: 0 0 var(--usx-spacing-sm) 0;
  line-height: var(--usx-line-height-tight);
}

.wf-mission-card-badges {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.wf-mission-task-count {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-left: auto;
}

.wf-run-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--usx-spacing-md);
}

.wf-run-card {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  transition: border-color var(--usx-transition-fast), transform var(--usx-transition-fast);
}

.wf-run-card:hover {
  border-color: var(--usx-color-primary);
  transform: translateY(calc(var(--usx-spacing-2) * -1));
}

.wf-run-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
  flex-shrink: 0;
  font-size: var(--usx-icon-size-lg);
}

.wf-run-card-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.wf-run-card-name {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wf-run-card-time {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  font-family: var(--usx-font-family-mono);
}

/* ─── Mini Binder Launchpad widget ───────────────────────────────── */
.wf-mini-binder {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
}

.wf-mini-binder-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-semibold);
  margin-bottom: var(--usx-spacing-xs);
}

.wf-mini-binder-header :deep(.u-button) {
  margin-left: auto;
}

.wf-mini-binder-desc {
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface-muted);
  margin: 0;
}

@media (max-width: calc(var(--usx-spacing-2xl) * 32)) {
  .wf-stats,
  .wf-board-grid,
  .wf-mission-grid,
  .wf-run-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: calc(var(--usx-spacing-2xl) * 18)) {
  .wf-stats,
  .wf-board-grid,
  .wf-mission-grid,
  .wf-run-grid {
    grid-template-columns: 1fr;
  }
}
</style>