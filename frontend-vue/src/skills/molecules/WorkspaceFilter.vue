<template>
  <div class="workspace-filter">
    <label class="workspace-filter__label">Vault Layer</label>
    <select v-model="selectedWorkspace" class="workspace-filter__select" @change="onChange">
      <option value="">All Layers</option>
      <option v-for="ws in vaultLayers" :key="ws.id" :value="ws.id">
        {{ ws.label }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
/**
 * @component WorkspaceFilter
 * @description Vault layer selector filter for the filepicker.
 * Dynamically loads vault layers from the library index stats API.
 * @category molecules
 * @emits {string} source-change - Selected vault layer ID
 * @usage <WorkspaceFilter @source-change="onSourceChange" />
 */
import { ref, onMounted } from 'vue'
import { ucoreApi } from '../../api/client'

interface VaultLayer {
  id: string
  label: string
  icon: string
  description: string
}

const selectedWorkspace = ref('')
const vaultLayers = ref<VaultLayer[]>([
  { id: 'user', label: 'User Vault', icon: 'mdi:account', description: '~/Vault/' },
  { id: 'shared', label: 'Shared', icon: 'mdi:account-group', description: '~/Shared/' },
  { id: 'global', label: 'Global Knowledge', icon: 'mdi:book-open-variant', description: '~/Public/global-knowledge/' },
  { id: 'public', label: 'Published', icon: 'mdi:web', description: '~/Public/doc-sites/' },
  { id: 'code', label: 'Code', icon: 'mdi:code-tags', description: '~/Code/' },
])

const emit = defineEmits<{
  'source-change': [source: string]
}>()

function onChange() {
  emit('source-change', selectedWorkspace.value)
}

// Optionally fetch real stats to show file counts
onMounted(async () => {
  try {
    const res = await ucoreApi.library.stats()
    if (res.ok) {
      const data = res.data as any
      if (data?.by_source) {
        const bySource = data.by_source as Record<string, number>
        vaultLayers.value = vaultLayers.value.map(layer => ({
          ...layer,
          fileCount: bySource[layer.id] || 0,
        }))
      }
    }
  } catch {
    // Silently fall back to static list
  }
})
</script>

<style scoped>
.workspace-filter {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.workspace-filter__label {
  font-size: var(--usx-font-size-sm);
  font-weight: 600;
  text-transform: uppercase;
  color: var(--pico-muted-color);
  letter-spacing: 0.5px;
}

.workspace-filter__select {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--pico-background-color);
  border-radius: var(--usx-border-radius-sm);
  font-size: var(--usx-font-size-sm);
  color: var(--pico-color);
  border: 1px solid rgba(88, 166, 255, 0.15);
  cursor: pointer;
  appearance: auto;
}

.workspace-filter__select:focus {
  border-color: #58a6ff;
  outline: none;
}
</style>
