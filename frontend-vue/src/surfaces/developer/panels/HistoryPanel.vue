<template>
  <div class="history-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Action History</h3>
      <UBadge type="info">{{ stats.total || actions.length }} actions</UBadge>
    </div>

    <!-- Toolbar -->
    <div class="history-toolbar">
      <UButton variant="primary" size="sm" @click="createSnapshot">
        <UIcon name="camera" :size="14" />
        Snapshot
      </UButton>
      <UButton variant="secondary" size="sm" @click="undoLast" :disabled="actions.length === 0">
        <UIcon name="undo" :size="14" />
        Undo Last
      </UButton>
      <UButton variant="ghost" size="sm" @click="refresh">
        <UIcon name="refresh" :size="14" />
        Refresh
      </UButton>
    </div>

    <!-- Stats bar -->
    <div v-if="stats.by_type" class="history-stats-bar">
      <span v-if="stats.snapshots" class="history-stat">
        {{ stats.snapshots }} snapshots
      </span>
      <span v-if="stats.by_type.file_edit" class="history-stat">
        {{ stats.by_type.file_edit }} edits
      </span>
      <span v-if="stats.by_type.skill_run" class="history-stat">
        {{ stats.by_type.skill_run }} skill runs
      </span>
    </div>

    <!-- Action list -->
    <div v-if="loading" class="history-loading">Loading history...</div>
    <div v-else-if="actions.length === 0" class="history-empty">
      No actions recorded yet. Create a snapshot to begin tracking.
    </div>
    <div v-else class="history-list">
      <div
        v-for="action in actions"
        :key="action.id"
        class="history-item"
        :class="'history-item--' + action.status"
      >
        <div class="history-item__icon">
          <UIcon :name="typeIcon(action.action_type)" :size="16" />
        </div>
        <div class="history-item__body">
          <div class="history-item__header">
            <span class="history-item__type">{{ action.action_type }}</span>
            <span class="history-item__time">{{ relativeTime(action.timestamp) }}</span>
            <span class="history-item__status">{{ action.status }}</span>
          </div>
          <div class="history-item__desc">{{ action.description || '—' }}</div>
          <div v-if="action.file_path" class="history-item__file">
            {{ action.file_path }}
          </div>
          <div v-if="action.diff_json" class="history-item__diff">
            {{ action.diff_json }}
          </div>
        </div>
        <div class="history-item__actions">
          <UButton
            v-if="action.action_type === 'snapshot'"
            variant="ghost"
            size="sm"
            :title="'Restore snapshot #' + action.id"
            @click="restoreSnapshot(action.id)"
          >
            <UIcon name="restore" :size="14" />
          </UButton>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="history-error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component HistoryPanel
 * @description Action history with snapshots, undo, and rollback.
 * Shows every significant action (file edits, skill runs, snapshots)
 * tracked via the HistoryService backed by SQLite + git.
 * @category surfaces/developer
 */
import { ref, onMounted } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'
import { useDeveloperStore } from '../../../stores/developer'

const dev = useDeveloperStore()
const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

interface HistoryAction {
  id: number
  timestamp: string
  action_type: string
  lane: string
  workspace?: string
  file_path?: string
  skill_id?: string
  description: string
  git_commit_hash?: string
  diff_json?: string
  status: string
  metadata_json?: string
}

const actions = ref<HistoryAction[]>([])
const stats = ref<Record<string, any>>({ total: 0 })
const loading = ref(true)
const error = ref<string | null>(null)

function typeIcon(actionType: string): string {
  const map: Record<string, string> = {
    snapshot: 'camera',
    file_edit: 'edit',
    skill_run: 'play_arrow',
    rollback: 'undo',
    restart: 'restart_alt',
  }
  return map[actionType] || 'circle'
}

function relativeTime(ts: string): string {
  try {
    const then = new Date(ts).getTime()
    const now = Date.now()
    const diff = Math.floor((now - then) / 1000)
    if (diff < 60) return 'just now'
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
  } catch {
    return ts?.slice(0, 16) || ''
  }
}

async function fetchHistory() {
  loading.value = true
  error.value = null
  try {
    const lane = dev.activeLane
    const [actionsRes, statsRes] = await Promise.all([
      fetch(`${API_BASE}/api/history/actions?lane=${lane}&limit=50`),
      fetch(`${API_BASE}/api/history/stats?lane=${lane}`),
    ])
    if (actionsRes.ok) {
      const data = await actionsRes.json()
      actions.value = data.actions || []
    }
    if (statsRes.ok) {
      stats.value = await statsRes.json()
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to load history'
  } finally {
    loading.value = false
  }
}

async function createSnapshot() {
  const label = prompt('Snapshot label:', `Manual snapshot at ${new Date().toLocaleTimeString()}`)
  if (!label) return
  try {
    const res = await fetch(`${API_BASE}/api/history/snapshot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label, lane: dev.activeLane }),
    })
    const result = await res.json()
    if (result.success) {
      await fetchHistory()
    } else {
      error.value = result.error || 'Snapshot failed'
    }
  } catch (e: any) {
    error.value = e.message || 'Snapshot request failed'
  }
}

async function undoLast() {
  if (!confirm('Undo the most recent action?')) return
  try {
    const res = await fetch(`${API_BASE}/api/history/undo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lane: dev.activeLane }),
    })
    const result = await res.json()
    if (result.success) {
      await fetchHistory()
    } else {
      error.value = result.error || 'Undo failed'
    }
  } catch (e: any) {
    error.value = e.message || 'Undo request failed'
  }
}

async function restoreSnapshot(actionId: number) {
  if (!confirm(`Restore to snapshot #${actionId}? This will revert all changes.`)) return
  try {
    const res = await fetch(`${API_BASE}/api/history/restore/${actionId}`, {
      method: 'POST',
    })
    const result = await res.json()
    if (result.success) {
      await fetchHistory()
    } else {
      error.value = result.error || 'Restore failed'
    }
  } catch (e: any) {
    error.value = e.message || 'Restore request failed'
  }
}

function refresh() {
  fetchHistory()
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.history-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

/* ─── Toolbar ────────────────────────────────── */
.history-toolbar {
  display: flex;
  gap: var(--usx-spacing-sm);
}

/* ─── Stats bar ──────────────────────────────── */
.history-stats-bar {
  display: flex;
  gap: var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.history-loading,
.history-empty {
  padding: var(--usx-spacing-xl);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.history-error {
  padding: var(--usx-spacing-sm);
  background: color-mix(in srgb, var(--usx-color-danger) 10%, transparent);
  color: var(--usx-color-danger);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
}

/* ─── Action list ────────────────────────────── */
.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.history-item--completed {
  border-left-color: var(--usx-color-success);
}

.history-item--reverted {
  opacity: 0.5;
  border-left-color: var(--usx-color-on-surface-muted);
}

.history-item--failed {
  border-left-color: var(--usx-color-danger);
}

.history-item__icon {
  color: var(--usx-color-on-surface-muted);
  margin-top: var(--usx-spacing-1);
}

.history-item__body {
  flex: 1;
  min-width: 0;
}

.history-item__header {
  display: flex;
  gap: var(--usx-spacing-sm);
  align-items: center;
}

.history-item__type {
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-sm);
  text-transform: capitalize;
}

.history-item__time {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.history-item__status {
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-1) var(--usx-spacing-xs);
  border-radius: var(--usx-radius-sm);
  background: color-mix(in srgb, var(--usx-color-success) 10%, transparent);
  color: var(--usx-color-success);
}

.history-item--reverted .history-item__status {
  background: color-mix(in srgb, var(--usx-color-on-surface-muted) 10%, transparent);
  color: var(--usx-color-on-surface-muted);
}

.history-item__desc {
  font-size: var(--usx-font-size-sm);
  margin-top: var(--usx-spacing-1);
}

.history-item__file {
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-on-surface-muted);
  margin-top: var(--usx-spacing-1);
}

.history-item__diff {
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-on-surface-muted);
  margin-top: var(--usx-spacing-xs);
  white-space: pre-wrap;
}

.history-item__actions {
  display: flex;
}
</style>