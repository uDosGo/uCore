<template>
  <div class="quick-actions">
    <button
      v-for="action in actions"
      :key="action.id"
      class="quick-actions__btn"
      :title="action.label"
      :disabled="action.disabled || loading === action.id"
      @click="$emit('action', action.id)"
    >
      <UIcon v-if="loading === action.id" name="sync" spin class="quick-actions__spinner" />
      <UIcon v-else :name="action.icon" class="quick-actions__icon" />
      <span class="quick-actions__label">{{ action.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import UIcon from '../../../../skills/atoms/UIcon.vue'

defineProps<{
  loading?: string | null
}>()

const emit = defineEmits<{
  (e: 'action', id: string): void
}>()

const actions: Array<{ id: string; icon: string; label: string; disabled?: boolean }> = [
  { id: 'health-check', icon: 'monitor_heart', label: 'Health Check' },
  { id: 'system-repair', icon: 'build', label: 'System Repair' },
  { id: 'destroy-rebuild', icon: 'sync', label: 'Destroy/Rebuild' },
  { id: 'ingest-feed', icon: 'download', label: 'Ingest Feed' },
  { id: 'suggest-binder', icon: 'bolt', label: 'Suggest Binder' },
  { id: 'export-cost', icon: 'bar_chart', label: 'Export Cost' },
  { id: 'create-task', icon: 'view_kanban', label: 'Create Task' },
]
</script>

<style scoped>
.quick-actions {
  --quick-action-column-min: calc(var(--usx-touch-min) * 4.5);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--quick-action-column-min)), 1fr));
  gap: var(--usx-spacing-xs);
  min-width: 0;
}

.quick-actions__btn {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  transition: background var(--usx-transition-fast), border-color var(--usx-transition-fast), color var(--usx-transition-fast);
  white-space: normal;
}

.quick-actions__btn:hover:not(:disabled) {
  background: var(--usx-color-primary-disabled);
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}

.quick-actions__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quick-actions__icon {
  font-size: var(--usx-font-size-base);
}

.quick-actions__spinner {
  animation: spin var(--usx-motion-duration-spin) linear infinite;
}

.quick-actions__label {
  font-weight: var(--usx-font-weight-medium);
  min-width: 0;
  overflow-wrap: anywhere;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>