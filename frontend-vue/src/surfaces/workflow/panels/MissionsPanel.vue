<template>
  <div class="wf-panel">
    <div class="surface__panel">
      <h3 class="surface__panel-title">Missions</h3>
      <p class="surface__panel-description">Track and manage migration missions with progress tracking</p>
    </div>

    <div v-if="wf.loading" class="wf-loading">
      <UIcon name="sync" /> Loading missions...
    </div>

    <div class="wf-mission-list">
      <div v-for="mission in wf.missions" :key="mission.id" class="wf-mission-card">
        <div class="wf-mission-card-header">
          <UIcon name="flag" />
          <span class="wf-mission-card-title">{{ mission.title }}</span>
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
        </div>
        <p class="wf-mission-card-desc">{{ mission.description }}</p>
        <div class="wf-progress-row">
          <progress class="wf-progress-bar" :value="missionProgress(mission)" max="100" />
          <span class="wf-progress-text">{{ missionProgress(mission) }}%</span>
        </div>
        <div class="wf-mission-task-count">{{ mission.taskIds.length }} tasks</div>
        <div class="wf-mission-card-meta">
          <UBadge v-for="tid in mission.taskIds.slice(0, 12)" :key="tid" type="info" size="sm">
            {{ tid }}
          </UBadge>
          <span v-if="mission.taskIds.length > 12" class="wf-more">+{{ mission.taskIds.length - 12 }} more</span>
        </div>
      </div>
    </div>

    <div v-if="wf.missions.length === 0 && !wf.loading" class="wf-empty">
      No missions found. Import tasks with mission context to populate this view.
    </div>
  </div>
</template>

<script setup lang="ts">
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import { useWorkflowStore } from '../../../stores/workflow'
import type { Mission } from '../../../stores/workflow'

const wf = useWorkflowStore()

function missionProgress(mission: Mission): number {
  if (mission.taskIds.length === 0) return 0
  const done = wf.tasks.filter(
    t => mission.taskIds.includes(t.id) && t.status === 'completed'
  ).length
  return Math.round((done / mission.taskIds.length) * 100)
}
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
}

.wf-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.wf-mission-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-mission-card {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
  border-left: calc(var(--usx-border-width) + var(--usx-border-width-thick)) solid var(--usx-color-primary);
  transition: border-color var(--usx-transition-fast);
}

.wf-mission-card:hover {
  border-left-color: var(--usx-color-primary-hover);
}

.wf-mission-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-xs);
}

.wf-mission-card-title {
  font-weight: var(--usx-font-weight-semibold);
  flex: 1;
}

.wf-mission-card-desc {
  margin: 0 0 var(--usx-spacing-sm) 0;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.wf-progress-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-xs);
}

.wf-progress-bar {
  flex: 1;
  width: 100%;
  height: var(--usx-spacing-xs);
  appearance: none;
  border: none;
  background: var(--usx-color-primary);
  border-radius: var(--usx-radius-full);
  overflow: hidden;
}

.wf-progress-bar::-webkit-progress-bar {
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-full);
}

.wf-progress-bar::-webkit-progress-value {
  background: var(--usx-color-primary);
  border-radius: var(--usx-radius-full);
  transition: width var(--usx-transition-fast);
}

.wf-progress-bar::-moz-progress-bar {
  background: var(--usx-color-primary);
  border-radius: var(--usx-radius-full);
  transition: width var(--usx-transition-fast);
}

.wf-progress-text {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-primary);
  min-width: 4ch;
  text-align: right;
}

.wf-mission-task-count {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-bottom: var(--usx-spacing-xs);
}

.wf-mission-card-meta {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
  align-items: center;
}

.wf-more {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.wf-empty {
  padding: var(--usx-spacing-xl);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}
</style>