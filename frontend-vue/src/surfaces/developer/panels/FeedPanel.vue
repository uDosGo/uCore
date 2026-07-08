<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Feed</h3>
      <div class="feed-header-actions">
        <select v-model="store.sourceFilter" @change="store.setSourceFilter(store.sourceFilter)" class="feed-source-select">
          <option value="all">All Sources</option>
          <option value="browser">Browser</option>
          <option value="email">Email</option>
          <option value="message">Messages</option>
          <option value="alert">Alerts</option>
          <option value="search">Search</option>
        </select>
        <button class="feed-btn" @click="refresh" :disabled="store.loading">
          {{ store.loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
    </div>

    <div v-if="store.error" class="feed-error">{{ store.error }}</div>

    <div class="developer-card-list">
      <div v-for="item in filteredActivities" :key="item.id" class="developer-card feed-card">
        <div class="developer-card-header">
          <span class="feed-source-badge" :class="'feed-source--' + item.source">
            {{ item.source }}
          </span>
          <span class="developer-card-title">{{ item.title || 'Untitled' }}</span>
          <span class="feed-importance" :style="{ color: importanceColor(item.importance) }">
            {{ (item.importance * 100).toFixed(0) }}%
          </span>
        </div>
        <p class="developer-card-desc" v-if="item.content">
          {{ item.content.slice(0, 200) }}{{ item.content.length > 200 ? '...' : '' }}
        </p>
        <div class="developer-card-meta">
          <span>{{ formatTime(item.timestamp) }}</span>
          <span>{{ item.type }}</span>
          <button class="feed-link-btn" @click="onLink(item)" :title="'Link to task: ' + item.id">
            Link to Task
          </button>
        </div>
      </div>
      <div v-if="!store.loading && filteredActivities.length === 0" class="feed-empty">
        No feed activity yet. Use POST /api/feed/ingest to add events.
      </div>
    </div>

    <div v-if="suggestions.length > 0" class="feed-suggestions">
      <h4 class="feed-suggestions-title">Suggested Binders</h4>
      <div v-for="sug in suggestions" :key="sug.name" class="developer-card feed-suggestion-card">
        <div class="developer-card-header">
          <span class="developer-card-title">{{ sug.name }}</span>
          <span class="feed-confidence">
            {{ (sug.confidence * 100).toFixed(0) }}% confidence
          </span>
        </div>
        <p class="developer-card-desc">{{ sug.description }}</p>
        <div class="developer-card-meta">
          <span>{{ sug.activity_count }} activities</span>
          <span>{{ sug.source }}</span>
        </div>
      </div>
    </div>

    <button class="feed-suggest-btn" @click="loadSuggestions" :disabled="store.loading">
      Check for Binder Suggestions
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useFeedStore } from '../../../stores/feed'
import type { FeedActivity } from '../../../stores/feed'

const store = useFeedStore()
const suggestions = ref<any[]>([])

const filteredActivities = computed(() => store.filteredActivities)

function importanceColor(importance: number): string {
  if (importance > 0.8) return 'var(--usx-color-danger)'
  if (importance > 0.5) return 'var(--usx-color-warning)'
  return 'var(--usx-color-success)'
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleString()
  } catch {
    return ts
  }
}

async function refresh() {
  await store.fetchActivities()
}

async function onLink(item: FeedActivity) {
  const taskId = prompt('Enter task ID to link:', 'task.feed.' + item.id)
  if (taskId) {
    await store.linkToTask(taskId, item.id)
  }
}

async function loadSuggestions() {
  suggestions.value = await store.fetchSuggestions(0.5)
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
.developer-panel { max-width: 900px; }
.developer-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--usx-spacing-md);
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
}
.developer-panel-title {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0;
}
.developer-card-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}
.developer-card {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
}
.developer-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-xs);
}
.developer-card-title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  flex: 1;
}
.developer-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin: 0 0 var(--usx-spacing-xs);
}
.developer-card-meta {
  display: flex;
  gap: var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  align-items: center;
}

.feed-header-actions { display: flex; gap: var(--usx-spacing-sm); align-items: center; }
.feed-source-select {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
}
.feed-btn {
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  background: var(--usx-color-primary);
  color: #fff;
  border: none;
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
}
.feed-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.feed-error {
  background: color-mix(in srgb, var(--usx-color-danger) 15%, transparent);
  color: var(--usx-color-danger);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  margin-bottom: var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
}
.feed-source-badge {
  padding: 2px 8px;
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
}
.feed-source--browser { background: color-mix(in srgb, var(--usx-color-info) 15%, transparent); color: var(--usx-color-info); }
.feed-source--email { background: color-mix(in srgb, var(--usx-color-success) 15%, transparent); color: var(--usx-color-success); }
.feed-source--message { background: color-mix(in srgb, var(--usx-color-accent) 15%, transparent); color: var(--usx-color-accent); }
.feed-source--alert { background: color-mix(in srgb, var(--usx-color-warning) 15%, transparent); color: var(--usx-color-warning); }
.feed-source--search { background: color-mix(in srgb, var(--usx-color-info) 10%, transparent); color: var(--usx-color-info); }
.feed-importance { font-size: var(--usx-font-size-xs); font-weight: var(--usx-font-weight-semibold); }
.feed-link-btn {
  background: none;
  border: 1px solid var(--usx-color-border);
  color: var(--usx-color-primary);
  padding: 2px 8px;
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
}
.feed-link-btn:hover { background: var(--usx-color-border); }
.feed-empty {
  padding: var(--usx-spacing-xl);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}
.feed-suggestions { margin-top: var(--usx-spacing-xl); }
.feed-suggestions-title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0 0 var(--usx-spacing-sm);
}
.feed-suggestion-card {
  margin-bottom: var(--usx-spacing-sm);
  border-left: 3px solid var(--usx-color-primary);
}
.feed-confidence { font-size: var(--usx-font-size-xs); color: var(--usx-color-primary); }
.feed-suggest-btn {
  margin-top: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg);
  background: var(--usx-color-background);
  color: var(--usx-color-primary);
  border: 1px solid var(--usx-color-primary);
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
}
.feed-suggest-btn:disabled { opacity: 0.5; }
</style>