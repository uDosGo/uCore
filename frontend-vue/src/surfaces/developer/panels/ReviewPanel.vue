<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Recent Changes</h3>
      <UBadge type="info">{{ loading ? '...' : reviews.length + ' files' }}</UBadge>
    </div>
    <div class="developer-review-list">
      <div v-for="(entry, i) in reviews" :key="i" class="developer-review-card">
        <div class="developer-review-header">
          <UIcon :name="statusIcon(entry.status)" />
          <span class="developer-review-status" :class="'developer-review-status--' + entry.status">
            {{ entry.status }}
          </span>
          <span class="developer-review-lines">+{{ entry.lines }} lines</span>
        </div>
        <div class="developer-review-file">{{ entry.file }}</div>
        <p class="developer-review-summary">{{ entry.summary }}</p>
        <div class="developer-review-actions">
          <UButton variant="ghost" size="sm">Preview</UButton>
          <UButton variant="ghost" size="sm">Review</UButton>
          <UButton variant="secondary" size="sm">Stage</UButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component ReviewPanel
 * @description Code review panel — recent changes, file status, staging.
 * @category surfaces/developer
 */
import { ref, onMounted } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'
import { useDeveloperStore } from '../../../stores/developer'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'
const dev = useDeveloperStore()

interface ReviewEntry {
  file: string
  status: string
  lines: number
  summary: string
}

const reviews = ref<ReviewEntry[]>([])
const loading = ref(true)

async function fetchReviews() {
  loading.value = true
  try {
    // Try uCore repo first (most common dev target)
    const res = await fetch(`${API_BASE}/api/developer/repos/uCore/review`, {
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) {
      const data = await res.json()
      reviews.value = data.review || []
    }
  } catch {
    // Fallback to store samples
    reviews.value = dev.reviews
  } finally {
    loading.value = false
  }
}

onMounted(() => { fetchReviews() })

function statusIcon(status: string): string {
  const map: Record<string, string> = { modified: 'edit_note', added: 'add_circle', deleted: 'delete' }
  return map[status] || 'description'
}
</script>

<style scoped>
.developer-panel { max-width: calc(var(--usx-spacing-2xl) * 25); }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }
.developer-review-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-review-card { padding: var(--usx-spacing-md); background: var(--usx-color-background); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); }
.developer-review-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-review-status { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-semibold); text-transform: uppercase; }
.developer-review-status--modified { color: var(--usx-color-warning); }
.developer-review-status--added { color: var(--usx-color-success); }
.developer-review-status--deleted { color: var(--usx-color-danger); }
.developer-review-lines { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.developer-review-file { font-size: var(--usx-font-size-sm); font-family: var(--usx-font-family-mono); margin-bottom: var(--usx-spacing-xs); }
.developer-review-summary { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin: 0 0 var(--usx-spacing-sm); }
.developer-review-actions { display: flex; gap: var(--usx-spacing-xs); }
</style>