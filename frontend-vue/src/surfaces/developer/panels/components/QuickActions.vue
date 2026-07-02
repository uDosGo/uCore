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
      <span v-if="loading === action.id" class="quick-actions__spinner">⟳</span>
      <span v-else class="quick-actions__icon">{{ action.icon }}</span>
      <span class="quick-actions__label">{{ action.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  loading?: string | null
}>()

defineEmits<{
  (e: 'action', id: string): void
}>()

const actions = [
  { id: 'destroy-rebuild', icon: '🔄', label: 'Destroy/Rebuild' },
  { id: 'ingest-feed', icon: '📥', label: 'Ingest Feed' },
  { id: 'suggest-binder', icon: '⚡', label: 'Suggest Binder' },
  { id: 'export-cost', icon: '📊', label: 'Export Cost' },
  { id: 'create-task', icon: '📋', label: 'Create Task' },
]
</script>

<style scoped>
.quick-actions {
  display: flex;
  gap: var(--usx-spacing-xs);
  justify-content: flex-end;
}

.quick-actions__btn {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  transition: all 0.15s ease;
  white-space: nowrap;
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
  animation: spin 1s linear infinite;
}

.quick-actions__label {
  font-weight: var(--usx-font-weight-medium);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>