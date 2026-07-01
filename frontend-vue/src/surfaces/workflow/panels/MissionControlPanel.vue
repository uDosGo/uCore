<template>
  <div class="wf-panel">
    <div class="surface__panel">
      <h3 class="surface__panel-title">Mission Control</h3>
      <p class="surface__panel-description">Track progress across all migration missions</p>
    </div>

    <!-- Stats cards -->
    <div class="wf-stats">
      <div class="wf-stat">
        <span class="wf-stat-value">{{ wf.totalTasks }}</span>
        <span class="wf-stat-label">Total Tasks</span>
      </div>
      <div class="wf-stat">
        <span class="wf-stat-value" style="color:#58a6ff">{{ wf.inProgressCount }}</span>
        <span class="wf-stat-label">In Progress</span>
      </div>
      <div class="wf-stat">
        <span class="wf-stat-value" style="color:#3fb950">{{ wf.completedCount }}</span>
        <span class="wf-stat-label">Completed</span>
      </div>
      <div class="wf-stat">
        <span class="wf-stat-value" style="color:#d29922">{{ wf.missions.length }}</span>
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
      <button class="usx-button" @click="wf.fetchAll()">Retry</button>
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
            <UBadge type="info" size="sm">{{ board.count }}</UBadge>
          </div>
        </div>
      </div>
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

    <!-- Recent runs from backend -->
    <div v-if="wf.workflowRuns.length > 0" class="wf-section">
      <h4 class="wf-section-title">Recent Workflow Runs</h4>
      <div class="wf-run-list">
        <div
          v-for="run in wf.workflowRuns.slice(0, 5)"
          :key="run.run_id"
          class="wf-run-row"
        >
          <UBadge
            :type="run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'warning'"
            size="sm"
          >
            {{ run.status }}
          </UBadge>
          <span class="wf-run-name">{{ run.workflow_name || run.workflow_id }}</span>
          <span class="wf-run-time">{{ formatTime(run.started_at) }}</span>
        </div>
      </div>
    </div>

    <!-- Mini Binder Launchpad widget -->
    <div class="wf-section">
      <div class="wf-mini-binder">
        <div class="wf-mini-binder-header">
          <UIcon name="folder" />
          <span>Binder Launchpad</span>
          <button class="usx-button" @click="openFullBinder">
            <UIcon name="open_in_new" /> Open Binder
          </button>
        </div>
        <p class="wf-mini-binder-desc">Drop files here to quickly compile a binder, or open the full Binder tab.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import { useWorkflowStore } from '../../../stores/workflow'

const wf = useWorkflowStore()
const router = useRouter()

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

onMounted(() => {
  wf.fetchAll()
})
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
}

.wf-stats {
  display: flex;
  gap: var(--usx-spacing-md);
  flex-wrap: wrap;
}

.wf-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-md);
  background: var(--pico-card-background-color);
  border-radius: var(--usx-border-radius-lg);
  min-width: 90px;
  flex: 1;
}

.wf-stat-value {
  font-size: var(--usx-font-size-xl);
  font-weight: 700;
  line-height: var(--usx-line-height-tight);
}

.wf-stat-label {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
}

.wf-loading,
.wf-error {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-border-radius-md);
  font-size: var(--usx-font-size-sm);
}

.wf-loading {
  color: var(--pico-muted-color);
}

.wf-error {
  color: #f85149;
  background: rgba(248, 81, 73, 0.1);
  border: 1px solid rgba(248, 81, 73, 0.2);
}

.wf-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-section-title {
  margin: 0;
  font-size: var(--usx-font-size-sm);
  font-weight: 600;
  color: var(--pico-muted-color);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.wf-board-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--usx-spacing-sm);
}

.wf-board-card {
  padding: var(--usx-spacing-md);
  background: var(--pico-card-background-color);
  border-radius: var(--usx-border-radius-md);
}

.wf-board-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  font-weight: 500;
}

/* Dashboard-style mission card grid */
.wf-mission-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--usx-spacing-md);
}

.wf-mission-card {
  display: flex;
  align-items: flex-start;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-lg);
  background: var(--pico-card-background-color);
  border: 1px solid rgba(88, 166, 255, 0.08);
  border-radius: var(--usx-border-radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
}

.wf-mission-card:hover {
  background: rgba(88, 166, 255, 0.04);
  border-color: rgba(88, 166, 255, 0.2);
  transform: translateY(-1px);
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
  font-weight: 600;
  margin: 0 0 var(--usx-spacing-xs) 0;
  color: var(--pico-color);
}

.wf-mission-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
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
  font-size: var(--usx-font-size-xs);
  color: var(--pico-muted-color);
  margin-left: auto;
}

.wf-run-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.wf-run-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--pico-card-background-color);
  border-radius: var(--usx-border-radius-md);
  font-size: var(--usx-font-size-sm);
}

.wf-run-name {
  flex: 1;
  font-weight: 500;
}

.wf-run-time {
  color: var(--pico-muted-color);
  font-size: var(--usx-font-size-xs);
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

.wf-mini-binder-header .usx-button {
  margin-left: auto;
  font-size: var(--usx-font-size-sm);
}

.wf-mini-binder-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin: 0;
}
</style>