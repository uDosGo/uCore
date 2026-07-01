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
  font-weight: 600;
  text-transform: uppercase;
  color: var(--pico-muted-color);
  letter-spacing: 0.5px;
}

.binder-mission-filter__select {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--pico-background-color);
  border-radius: var(--usx-border-radius-sm);
  font-size: var(--usx-font-size-sm);
  color: var(--pico-color);
  border: 1px solid rgba(88, 166, 255, 0.15);
  cursor: pointer;
  appearance: auto;
}

.binder-mission-filter__select:focus {
  border-color: #58a6ff;
  outline: none;
}
</style>
