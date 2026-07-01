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
 * Ported from KanbanBoard.tsx (React).
 * @category surfaces/developer
 */
import { ref } from 'vue'
import UButton from '../../../skills/atoms/UButton.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

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
  {
    id: 'backlog', title: 'Backlog', color: '#6b7280',
    items: [
      { id: '1', title: 'Port Server surface to Vue', type: 'task', date: 'Today' },
      { id: '2', title: 'Add Vitest unit tests', type: 'task', date: 'This week' },
      { id: '3', title: 'Storybook for Skills', type: 'feature', date: 'Next' },
    ],
  },
  {
    id: 'progress', title: 'In Progress', color: '#58a6ff',
    items: [
      { id: '4', title: 'Port Developer surface to Vue', type: 'task', date: 'Today' },
      { id: '5', title: 'Wire UIHub to Vue dashboard', type: 'task', date: 'Today' },
    ],
  },
  {
    id: 'review', title: 'Review', color: '#d29922',
    items: [
      { id: '6', title: 'AssistUI Vue port', type: 'review', date: 'Today' },
    ],
  },
  {
    id: 'done', title: 'Done', color: '#2ea043',
    items: [
      { id: '7', title: 'Vue 3 foundation scaffold', type: 'task', date: 'Yesterday' },
      { id: '8', title: 'AssistUI chat surface', type: 'task', date: 'Today' },
      { id: '9', title: 'md-editor-v3 vendor integration', type: 'task', date: 'Today' },
    ],
  },
])

const dragItem = ref<{ item: KanbanItem; colId: string } | null>(null)

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
    id: `card-${Date.now()}`,
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
</script>

<style scoped>
.developer-panel { max-width: 100%; }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: 600; margin: 0; }

.kanban-board {
  display: grid;
  grid-template-columns: repeat(4, minmax(220px, 1fr));
  gap: var(--usx-spacing-md);
  overflow-x: auto;
}

.kanban-column {
  background: var(--pico-card-background-color, #161b22);
  background: var(--pico-background-color, #30363d);
  border-radius: var(--usx-border-radius-lg);
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
  font-weight: 600;
}

.kanban-cards {
  padding: var(--usx-spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.kanban-card {
  padding: var(--usx-spacing-sm);
  background: var(--pico-background-color, #0d1117);
  background: var(--pico-background-color, #30363d);
  border-radius: var(--usx-border-radius-md);
  cursor: grab;
  transition: all 0.15s ease;
}

.kanban-card:hover {
  border-color: var(--pico-primary, #58a6ff);
  transform: translateY(-1px);
}

.kanban-card:active {
  cursor: grabbing;
}

.kanban-card-title {
  font-size: var(--usx-font-size-sm);
  font-weight: 500;
  margin-bottom: var(--usx-spacing-xs);
}

.kanban-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kanban-card-date {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color, #8b949e);
}
</style>
