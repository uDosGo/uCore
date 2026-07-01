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
  if (importance > 0.8) return '#f85149'
  if (importance > 0.5) return '#d29922'
  return '#3fb950'
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
  font-weight: 600;
  margin: 0;
}
.developer-card-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}
.developer-card {
  padding: var(--usx-spacing-md);
  background: var(--pico-card-background-color, #161b22);
  border-radius: var(--usx-border-radius-lg);
}
.developer-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-xs);
}
.developer-card-title {
  font-size: var(--usx-font-size-base);
  font-weight: 600;
  flex: 1;
}
.developer-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color, #8b949e);
  margin: 0 0 var(--usx-spacing-xs);
}
.developer-card-meta {
  display: flex;
  gap: var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color, #8b949e);
  align-items: center;
}

.feed-header-actions { display: flex; gap: var(--usx-spacing-sm); align-items: center; }
.feed-source-select {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--pico-background-color, #0d1117);
  color: var(--pico-color, #c9d1d9);
  border: 1px solid var(--pico-border-color, #30363d);
  border-radius: var(--usx-border-radius-md);
  font-size: var(--usx-font-size-sm);
}
.feed-btn {
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  background: var(--pico-primary, #58a6ff);
  color: #fff;
  border: none;
  border-radius: var(--usx-border-radius-md);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
}
.feed-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.feed-error {
  background: #490202;
  color: #f85149;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-border-radius-md);
  margin-bottom: var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
}
.feed-source-badge {
  padding: 2px 8px;
  border-radius: var(--usx-border-radius-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
}
.feed-source--browser { background: #1a365d; color: #63b3ed; }
.feed-source--email { background: #22543d; color: #68d391; }
.feed-source--message { background: #553c9a; color: #b794f4; }
.feed-source--alert { background: #744210; color: #f6ad55; }
.feed-source--search { background: #234e52; color: #4fd1c5; }
.feed-importance { font-size: var(--usx-font-size-xs); font-weight: 600; }
.feed-link-btn {
  background: none;
  border: 1px solid var(--pico-border-color, #30363d);
  color: var(--pico-primary, #58a6ff);
  padding: 2px 8px;
  border-radius: var(--usx-border-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
}
.feed-link-btn:hover { background: var(--pico-border-color, #30363d); }
.feed-empty {
  padding: var(--usx-spacing-xl);
  text-align: center;
  color: var(--pico-muted-color, #8b949e);
  font-size: var(--usx-font-size-sm);
}
.feed-suggestions { margin-top: var(--usx-spacing-xl); }
.feed-suggestions-title {
  font-size: var(--usx-font-size-base);
  font-weight: 600;
  margin: 0 0 var(--usx-spacing-sm);
}
.feed-suggestion-card {
  margin-bottom: var(--usx-spacing-sm);
  border-left: 3px solid var(--pico-primary, #58a6ff);
}
.feed-confidence { font-size: var(--usx-font-size-xs); color: var(--pico-primary, #58a6ff); }
.feed-suggest-btn {
  margin-top: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg);
  background: var(--pico-background-color, #0d1117);
  color: var(--pico-primary, #58a6ff);
  border: 1px solid var(--pico-primary, #58a6ff);
  border-radius: var(--usx-border-radius-md);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
}
.feed-suggest-btn:disabled { opacity: 0.5; }
</style>