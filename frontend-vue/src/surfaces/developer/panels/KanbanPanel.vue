<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Kanban</h3>
      <UButton variant="secondary" size="sm" icon="add" @click="addCard">Add Card</UButton>
    </div>
    <div class="kanban-board">
      <div
        v-for="column in columns"
        :key="column.id"
        class="kanban-column"
        @dragover.prevent
        @drop="handleDrop(column.id)"
      >
        <div class="kanban-column-header" :style="{ borderTopColor: column.color }">
          <span class="kanban-column-title">{{ column.title }}</span>
          <UBadge type="info" size="sm">{{ column.items.length }}</UBadge>
        </div>
        <div class="kanban-cards">
          <div
            v-for="item in column.items"
            :key="item.id"
            class="kanban-card"
            draggable="true"
            @dragstart="dragItem = { item, colId: column.id }"
          >
            <div class="kanban-card-title">{{ item.title }}</div>
            <div class="kanban-card-meta">
              <UBadge :type="typeColor(item.type)" size="sm">{{ item.type }}</UBadge>
              <span class="kanban-card-date">{{ item.date }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component KanbanPanel
 * @description Kanban board for task management with drag-and-drop.
 * Wired to Tasker API (/api/tasker/tasks).
 * @category surfaces/developer
 */
import { ref, onMounted } from 'vue'
import UButton from '../../../skills/atoms/UButton.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

interface KanbanItem {
  id: string
  title: string
  type: string
  date: string
}

interface KanbanColumn {
  id: string
  title: string
  color: string
  items: KanbanItem[]
}

const columns = ref<KanbanColumn[]>([
  { id: 'backlog', title: 'Backlog', color: 'var(--usx-color-on-surface-muted)', items: [] },
  { id: 'progress', title: 'In Progress', color: 'var(--usx-color-primary)', items: [] },
  { id: 'review', title: 'Review', color: 'var(--usx-color-warning)', items: [] },
  { id: 'done', title: 'Done', color: 'var(--usx-color-success)', items: [] },
])

const dragItem = ref<{ item: KanbanItem; colId: string } | null>(null)

const statusToColumn: Record<string, string> = {
  'backlog': 'backlog',
  'pending': 'backlog',
  'todo': 'backlog',
  'in-progress': 'progress',
  'in_progress': 'progress',
  'active': 'progress',
  'review': 'review',
  'done': 'done',
  'completed': 'done',
}

async function fetchTasks() {
  try {
    const res = await fetch(`${API_BASE}/api/tasker/tasks?limit=100`, {
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) return
    const data = await res.json()
    const tasks = Array.isArray(data) ? data : (data.tasks || [])
    if (tasks.length === 0) return

    // Reset columns
    for (const col of columns.value) col.items = []

    for (const t of tasks) {
      const colId = statusToColumn[t.status] || 'backlog'
      const column = columns.value.find(c => c.id === colId)
      if (column) {
        column.items.push({
          id: t.id || t.task_id || String(Date.now()),
          title: t.title || t.name || 'Untitled',
          type: t.type || 'task',
          date: t.updated_at || t.date || '—',
        })
      }
    }
  } catch {
    // Backend offline — leave columns empty
  }
}

function handleDrop(targetColId: string) {
  if (!dragItem.value || dragItem.value.colId === targetColId) {
    dragItem.value = null
    return
  }
  const srcCol = columns.value.find(c => c.id === dragItem.value!.colId)
  const tgtCol = columns.value.find(c => c.id === targetColId)
  if (!srcCol || !tgtCol) return

  const idx = srcCol.items.findIndex(i => i.id === dragItem.value!.item.id)
  if (idx === -1) return
  const [moved] = srcCol.items.splice(idx, 1)
  tgtCol.items.push(moved)
  dragItem.value = null
}

function addCard() {
  const title = prompt('Card title:')
  if (!title) return
  columns.value[0].items.push({
    id: 'card-' + Date.now(),
    title,
    type: 'task',
    date: 'Today',
  })
}

function typeColor(type: string): 'info' | 'success' | 'warning' | 'error' {
  const map: Record<string, 'info' | 'success' | 'warning' | 'error'> = {
    task: 'info', feature: 'success', review: 'warning', bug: 'error',
  }
  return map[type] || 'info'
}

onMounted(() => { fetchTasks() })
</script>

<style scoped>
.developer-panel { max-width: 100%; }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }

.kanban-board {
  display: grid;
  grid-template-columns: repeat(4, minmax(220px, 1fr));
  gap: var(--usx-spacing-md);
  overflow-x: auto;
}

.kanban-column {
  background: var(--usx-color-surface);
  background: var(--usx-color-background);
  border-radius: var(--usx-radius-lg);
  min-height: 300px;
}

.kanban-column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-top: 3px solid;
}

.kanban-column-title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
}

.kanban-cards {
  padding: var(--usx-spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.kanban-card {
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-background);
  border-radius: var(--usx-radius-md);
  cursor: grab;
  transition: all 0.15s ease;
}

.kanban-card:hover {
  border-color: var(--usx-color-primary);
  transform: translateY(-1px);
}

.kanban-card:active { cursor: grabbing; }

.kanban-card-title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  margin-bottom: var(--usx-spacing-xs);
}

.kanban-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kanban-card-date {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}
</style>