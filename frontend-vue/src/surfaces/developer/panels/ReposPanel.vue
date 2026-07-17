<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Repositories</h3>
      <UBadge type="info">{{ loading ? '...' : (repos.length || dev.repos.length) }} repos</UBadge>
    </div>
    <UInput v-model="filter" placeholder="Filter repos..." icon="search" class="developer-panel-search" />
    <div class="developer-card-list">
      <div v-for="repo in filteredRepos" :key="repo.name" class="developer-card">
        <div class="developer-card-header">
          <UIcon name="folder" />
          <span class="developer-card-title">{{ repo.name }}</span>
          <UBadge :type="repo.status === 'clean' ? 'success' : 'warning'" size="sm">
            <template v-if="repo.status === 'clean'">
              <UIcon name="check" :size="14" /> Clean
            </template>
            <template v-else>
              <UIcon name="warning" :size="14" /> {{ repo.changes }} changes
            </template>
          </UBadge>
        </div>
        <div class="developer-card-meta">
          <span>⎇ {{ repo.branch }}</span>
          <span>{{ repo.path }}</span>
        </div>
        <div class="developer-card-remote">{{ repo.remote }}</div>
        <div class="developer-card-actions">
          <UButton variant="secondary" size="sm" @click="browseRepo(repo.name)">Browse</UButton>
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
import { ref, computed, onMounted } from 'vue'
import UInput from '../../../skills/atoms/UInput.vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'
import { useDeveloperStore } from '../../../stores/developer'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'
const dev = useDeveloperStore()
const filter = ref('')
const loading = ref(true)

interface RepoData {
  id?: string
  name: string
  path: string
  branch: string
  status: string
  changes: number
  remote: string
  fileCount?: number
}

const repos = ref<RepoData[]>([])

async function fetchRepos() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/developer/repos`, {
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) {
      const data = await res.json()
      repos.value = data.repos || []
    }
  } catch {
    // Fallback to store samples
    repos.value = dev.repos.map(r => ({ name: r.name, path: r.path, branch: r.branch, status: r.status, changes: r.changes, remote: r.remote }))
  } finally {
    loading.value = false
  }
}

function browseRepo(name: string) {
  dev.browseRepo(name)
}

onMounted(() => { fetchRepos() })

const filteredRepos = computed(() => {
  const list = repos.value.length > 0 ? repos.value : dev.repos.map(r => ({ name: r.name, path: r.path, branch: r.branch, status: r.status, changes: r.changes, remote: r.remote }))
  if (!filter.value) return list
  const q = filter.value.toLowerCase()
  return list.filter(r => r.name.toLowerCase().includes(q))
})
</script>

<style scoped>
.developer-panel { max-width: calc(var(--usx-spacing-2xl) * 25); }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }
.developer-panel-search { margin-bottom: var(--usx-spacing-md); }
.developer-card-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--usx-color-background); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-semibold); flex: 1; }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: var(--usx-spacing-xs); }
.developer-card-remote { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: var(--usx-spacing-sm); }
.developer-card-actions { display: flex; gap: var(--usx-spacing-xs); }
</style>