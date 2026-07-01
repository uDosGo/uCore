<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Recent Changes</h3>
      <UBadge type="info">{{ dev.reviews.length }} files</UBadge>
    </div>
    <div class="developer-review-list">
      <div v-for="(entry, i) in dev.reviews" :key="i" class="developer-review-card">
        <div class="developer-review-header">
          <UIcon :name="statusIcon(entry.status)" />
          <span class="developer-review-status" :class="`developer-review-status--${entry.status}`">
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
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'
import { useDeveloperStore } from '../../../stores/developer'

const dev = useDeveloperStore()

function statusIcon(status: string): string {
  const map: Record<string, string> = { modified: 'edit_note', added: 'add_circle', deleted: 'delete' }
  return map[status] || 'description'
}
</script>

<style scoped>
.developer-panel { max-width: 800px; }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: 600; margin: 0; }
.developer-review-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-review-card { padding: var(--usx-spacing-md); background: var(--pico-background-color, #30363d); border-radius: var(--usx-border-radius-lg); background: var(--pico-card-background-color, #161b22); }
.developer-review-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-review-status { font-size: var(--usx-font-size-sm); font-weight: 600; text-transform: uppercase; }
.developer-review-status--modified { color: #d29922; }
.developer-review-status--added { color: #3fb950; }
.developer-review-status--deleted { color: #f85149; }
.developer-review-lines { font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); }
.developer-review-file { font-size: var(--usx-font-size-sm); font-family: monospace; margin-bottom: var(--usx-spacing-xs); }
.developer-review-summary { font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); margin: 0 0 var(--usx-spacing-sm); }
.developer-review-actions { display: flex; gap: var(--usx-spacing-xs); }
</style>
