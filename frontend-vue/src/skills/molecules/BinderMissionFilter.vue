<template>
  <div class="binder-mission-filter">
    <label class="binder-mission-filter__label">Binder / Mission</label>
    <select v-model="selectedBinder" class="binder-mission-filter__select" @change="onChange">
      <option value="">All Binders</option>
      <option v-for="binder in binders" :key="binder.id" :value="binder.id">
        {{ binder.name }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
/**
 * @component BinderMissionFilter
 * @description Binder/Mission selector filter for the filepicker.
 * Dynamically populated from search results.
 * @category molecules
 * @emits {string} binder-change - Selected binder ID
 * @usage <BinderMissionFilter @binder-change="onBinderChange" />
 */
import { ref } from 'vue'

interface Binder {
  id: string
  name: string
}

const selectedBinder = ref('')
const binders = ref<Binder[]>([
  { id: 'active', name: 'Active' },
  { id: 'docs', name: 'Documentation' },
  { id: 'archive', name: 'Archive' },
])

const emit = defineEmits<{
  'binder-change': [binder: string]
}>()

function onChange() {
  emit('binder-change', selectedBinder.value)
}

// Allow external population of binders from search results
function setBinders(newBinders: Binder[]) {
  binders.value = newBinders
}

defineExpose({ setBinders })
</script>

<style scoped>
.binder-mission-filter {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.binder-mission-filter__label {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
  color: var(--usx-color-on-surface-muted);
  letter-spacing: var(--usx-letter-spacing-wide);
}

.binder-mission-filter__select {
  padding: var(--usx-spacing-xs) var(--usx-spacing-lg) var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-background);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
  border: var(--usx-border-width) solid color-mix(in srgb, var(--usx-color-primary) 15%, transparent);
  cursor: pointer;
  appearance: auto;
}

.binder-mission-filter__select:focus {
  border-color: var(--usx-color-primary);
  outline: none;
}
</style>
