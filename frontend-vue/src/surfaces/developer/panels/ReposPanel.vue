<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Repositories</h3>
      <UBadge type="info">{{ dev.repos.length }} repos</UBadge>
    </div>
    <UInput v-model="filter" placeholder="Filter repos..." icon="search" class="developer-panel-search" />
    <div class="developer-card-list">
      <div v-for="repo in filteredRepos" :key="repo.name" class="developer-card">
        <div class="developer-card-header">
          <UIcon name="folder" />
          <span class="developer-card-title">{{ repo.name }}</span>
          <UBadge :type="repo.status === 'clean' ? 'success' : 'warning'" size="sm">
            {{ repo.status === 'clean' ? '✓ Clean' : `⚠ ${repo.changes} changes` }}
          </UBadge>
        </div>
        <div class="developer-card-meta">
          <span>⎇ {{ repo.branch }}</span>
          <span>{{ repo.path }}</span>
        </div>
        <div class="developer-card-remote">{{ repo.remote }}</div>
        <div class="developer-card-actions">
          <UButton variant="secondary" size="sm" @click="dev.browseRepo(repo.name)">Browse</UButton>
          <UButton variant="ghost" size="sm">Pull</UButton>
          <UButton variant="ghost" size="sm">Status</UButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component ReposPanel
 * @description Repository browser panel — list, filter, browse repos.
 * @category surfaces/developer
 */
import { ref, computed } from 'vue'
import UInput from '../../../skills/atoms/UInput.vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'
import { useDeveloperStore } from '../../../stores/developer'

const dev = useDeveloperStore()
const filter = ref('')

const filteredRepos = computed(() => {
  if (!filter.value) return dev.repos
  const q = filter.value.toLowerCase()
  return dev.repos.filter(r => r.name.toLowerCase().includes(q))
})
</script>

<style scoped>
.developer-panel { max-width: 800px; }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: 600; margin: 0; }
.developer-panel-search { margin-bottom: var(--usx-spacing-md); }
.developer-card-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--pico-background-color, #30363d); border-radius: var(--usx-border-radius-lg); background: var(--pico-card-background-color, #161b22); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: 600; flex: 1; }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); margin-bottom: var(--usx-spacing-xs); }
.developer-card-remote { font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); margin-bottom: var(--usx-spacing-sm); }
.developer-card-actions { display: flex; gap: var(--usx-spacing-xs); }
</style>
