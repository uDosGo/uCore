<template>
  <div class="live-feed">
    <div class="live-feed__header">
      <span class="live-feed__title">Live Feed</span>
      <div class="live-feed__filters">
        <button
          v-for="src in sources"
          :key="src"
          class="live-feed__filter-btn"
          :class="{ 'live-feed__filter-btn--active': activeSource === src }"
          @click="activeSource = src"
        >
          {{ src === 'all' ? 'All' : src }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="live-feed__loading">Loading feed...</div>
    <div v-else-if="activities.length === 0" class="live-feed__empty">
      No feed activity yet.
    </div>
    <div v-else class="live-feed__list">
      <div
        v-for="item in filteredActivities"
        :key="item.id"
        class="live-feed__item"
        :class="{ 'live-feed__item--unprocessed': !item.processed }"
      >
        <UIcon :name="sourceIcon(item.source)" class="live-feed__source-icon" />
        <div class="live-feed__content">
          <span class="live-feed__item-title">{{ item.title || 'Untitled' }}</span>
          <span class="live-feed__item-detail">{{ item.content?.slice(0, 100) || '' }}</span>
        </div>
        <span class="live-feed__importance" :style="{ color: importanceColor(item.importance) }">
          {{ item.importance ? (item.importance * 100).toFixed(0) + '%' : '' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import UIcon from '../../../../skills/atoms/UIcon.vue'

interface FeedItem {
  id: number
  source: string
  type?: string
  title: string
  content?: string
  importance: number
  timestamp: string
  processed: boolean
}

const props = defineProps<{
  activities: FeedItem[]
  loading?: boolean
}>()

const activeSource = ref('all')
const sources = ['all', 'browser', 'email', 'message', 'alert', 'search']

const filteredActivities = computed(() => {
  if (activeSource.value === 'all') return props.activities
  return props.activities.filter((a) => a.source === activeSource.value)
})

const sourceIcons: Record<string, string> = {
  browser: 'public',
  email: 'mail',
  message: 'chat',
  alert: 'warning',
  search: 'search',
}

function sourceIcon(source: string): string {
  return sourceIcons[source] || 'push_pin'
}

function importanceColor(importance: number): string {
  if (importance > 0.8) return 'var(--usx-color-danger)'
  if (importance > 0.5) return 'var(--usx-color-warning)'
  return 'var(--usx-color-success)'
}
</script>

<style scoped>
.live-feed {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.live-feed__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
}

.live-feed__title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.live-feed__filters {
  display: flex;
  gap: 2px;
}

.live-feed__filter-btn {
  padding: 1px 6px;
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  transition: all 0.15s ease;
}

.live-feed__filter-btn:hover {
  color: var(--usx-color-on-surface);
}

.live-feed__filter-btn--active {
  background: var(--usx-color-primary-disabled);
  color: var(--usx-color-primary);
}

.live-feed__loading,
.live-feed__empty {
  padding: var(--usx-spacing-lg);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.live-feed__list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 320px;
  overflow-y: auto;
}

.live-feed__item {
  display: flex;
  align-items: flex-start;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  transition: background 0.1s ease;
}

.live-feed__item:hover {
  background: var(--usx-color-surface-hover);
}

.live-feed__item--unprocessed {
  border-left: 2px solid var(--usx-color-primary);
}

.live-feed__source-icon {
  font-size: var(--usx-font-size-base);
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.live-feed__content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.live-feed__item-title {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
}

.live-feed__item-detail {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.live-feed__importance {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  flex-shrink: 0;
}
</style>