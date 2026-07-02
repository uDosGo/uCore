<template>
  <div class="active-mission">
    <span class="active-mission__title">Active Mission</span>

    <div v-if="!mission || !mission.name" class="active-mission__empty">
      No active mission.
    </div>
    <div v-else class="active-mission__card">
      <span class="active-mission__name">{{ mission.name }}</span>
      <div class="active-mission__stats">
        <div class="active-mission__stat">
          <span class="active-mission__stat-value">{{ mission.tasks_done ?? 0 }}</span>
          <span class="active-mission__stat-label">Tasks Done</span>
        </div>
        <div class="active-mission__stat">
          <span class="active-mission__stat-value">{{ mission.tasks_total ?? 0 }}</span>
          <span class="active-mission__stat-label">Total</span>
        </div>
        <div class="active-mission__stat">
          <span class="active-mission__stat-value">{{ mission.binder_count ?? 0 }}</span>
          <span class="active-mission__stat-label">Binders</span>
        </div>
      </div>
      <div class="active-mission__progress">
        <div class="active-mission__progress-track">
          <div
            class="active-mission__progress-fill"
            :style="{ width: (mission.progress_pct ?? 0) + '%' }"
          />
        </div>
        <span class="active-mission__progress-label">{{ mission.progress_pct ?? 0 }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  mission: {
    name?: string
    tasks_total?: number
    tasks_done?: number
    binder_count?: number
    progress_pct?: number
  } | null
}>()
</script>

<style scoped>
.active-mission {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.active-mission__title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.active-mission__empty {
  padding: var(--usx-spacing-md);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.active-mission__card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.active-mission__name {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.active-mission__stats {
  display: flex;
  gap: var(--usx-spacing-lg);
}

.active-mission__stat {
  display: flex;
  flex-direction: column;
}

.active-mission__stat-value {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-bold);
  color: var(--usx-color-on-surface);
}

.active-mission__stat-label {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.active-mission__progress {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.active-mission__progress-track {
  flex: 1;
  height: 8px;
  background: var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  overflow: hidden;
}

.active-mission__progress-fill {
  height: 100%;
  background: var(--usx-color-primary);
  border-radius: var(--usx-radius-sm);
  transition: width 0.3s ease;
}

.active-mission__progress-label {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-primary);
  min-width: 36px;
  text-align: right;
}
</style>