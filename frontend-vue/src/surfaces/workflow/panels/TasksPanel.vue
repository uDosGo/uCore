<template>
  <div class="wf-panel">
    <div class="surface__panel">
      <h3 class="surface__panel-title">Tasks</h3>
      <p class="surface__panel-description">Kanban board with drag-and-drop task management</p>
    </div>

    <div v-if="wf.loading" class="wf-loading">
      <UIcon name="sync" /> Loading tasks...
    </div>

    <div class="kanban-board">
      <div
        v-for="(items, status) in wf.tasksByStatus"
        :key="status"
        class="kanban-column"
      >
        <div class="kanban-column-header" :class="`kanban-column-header--${status}`">
          <span>{{ formatStatus(status as string) }}</span>
          <UBadge type="info" size="sm">{{ items.length }}</UBadge>
        </div>
        <div class="kanban-cards">
          <div v-if="items.length === 0" class="kanban-empty">No tasks</div>
          <div
            v-for="task in items"
            :key="task.id"
            class="kanban-card"
            :class="{ 'kanban-card--selected': wf.selectedTask?.id === task.id }"
            @click="wf.selectTask(task)"
          >
            <div class="kanban-card-title">{{ task.title }}</div>
            <p class="kanban-card-desc">{{ truncate(task.description, 80) }}</p>
            <div class="kanban-card-meta">
              <UBadge
                :type="task.priority === 'high' ? 'error' : task.priority === 'medium' ? 'warning' : 'info'"
                size="sm"
              >
                {{ task.priority }}
              </UBadge>
              <span v-for="tag in task.tags" :key="tag" class="kanban-tag">{{ tag }}</span>
            </div>
            <div class="kanban-card-board">
              <UIcon name="view_kanban" />
              {{ task.board }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import { useWorkflowStore } from '../../../stores/workflow'

const wf = useWorkflowStore()

const STATUS_LABELS: Record<string, string> = {
  todo: 'To Do',
  'in-progress': 'In Progress',
  review: 'Review',
  blocked: 'Blocked',
  completed: 'Done',
}

function formatStatus(status: string): string {
  return STATUS_LABELS[status] || status
}

function truncate(text: string, maxLength: number): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trim() + '...'
}
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
}

.wf-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.kanban-board {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--usx-spacing-md);
  align-items: start;
}

.kanban-column {
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
  display: flex;
  flex-direction: column;
  min-height: 200px;
}

.kanban-column-header {
  padding: var(--usx-spacing-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-sm);
  border-top: 3px solid;
}

.kanban-column-header--completed { border-top-color: var(--usx-color-success); }
.kanban-column-header--in-progress { border-top-color: var(--usx-color-primary); }
.kanban-column-header--review { border-top-color: var(--usx-color-warning); }
.kanban-column-header--blocked { border-top-color: var(--usx-color-danger); }
.kanban-column-header--todo { border-top-color: var(--usx-color-on-surface-muted); }

.kanban-cards {
  flex: 1;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md) var(--usx-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.kanban-empty {
  padding: var(--usx-spacing-lg);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  font-style: italic;
}

.kanban-card {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-background);
  border-radius: var(--usx-radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
}

.kanban-card:hover {
  border-color: var(--usx-color-primary);
}

.kanban-card--selected {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 6%, transparent);
}

.kanban-card-title {
  font-weight: var(--usx-font-weight-semibold);
  margin-bottom: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
}

.kanban-card-desc {
  margin: 0 0 var(--usx-spacing-sm) 0;
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  line-height: var(--usx-line-height-tight);
}

.kanban-card-meta {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
  font-size: var(--usx-font-size-xs);
  margin-bottom: var(--usx-spacing-xs);
}

.kanban-tag {
  padding: var(--usx-spacing-xs) var(--usx-spacing-xs);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}

.kanban-card-board {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}
</style>