<template>
  <div class="surface">
    <!-- Content area (tabs are in GlobalToolbar) -->
    <div class="surface__content">
      <div class="workflow-layout">
        <!-- Left/Main panel: the active tab content -->
        <div v-if="wf.activeTab !== 'editor'" class="workflow-panel" :class="{ 'workflow-panel--narrow': wf.editorOpen }">
          <MissionControlPanel v-if="wf.activeTab === 'mission-control'" />
          <BinderPanel v-else-if="wf.activeTab === 'binder'" />
          <TasksPanel v-else-if="wf.activeTab === 'tasks'" />
          <PublishPanel v-else-if="wf.activeTab === 'publish'" />
        </div>

        <!-- Editor as standalone tab (no task selected) -->
        <div v-if="wf.activeTab === 'editor' && !wf.selectedTask" class="workflow-panel">
          <div class="wf-editor-empty">
            <UIcon name="article" />
            <p>Select a task from the Tasks tab to edit its content.</p>
            <UButton size="sm" variant="primary" @click="wf.setTab('tasks')">
              Go to Tasks
            </UButton>
          </div>
        </div>

        <!-- Right/Editor column: slides in when a task is selected -->
        <div v-if="wf.editorOpen && wf.selectedTask" class="workflow-editor" :class="editorColumnClass">
          <EditorPanel
            :content="wf.selectedTask.description"
            :title="wf.selectedTask.title"
            :show-editor="wf.showEditorPane"
            :pane-layout="wf.paneLayout"
            @update:content="onEditorContentUpdate"
            @save="onEditorSave"
            @close="wf.closeEditor()"
            @toggle-editor="wf.toggleEditorPane()"
            @toggle-layout="wf.togglePaneLayout()"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component WorkflowSurface
 * @description Workflow surface with mission control, kanban tasks, binder cross-reference,
 * and workflow publish/run management. Uses USX canonical .surface / .surface__tabs / .surface__content classes.
 *
 * Editor layout:
 *   - No editor: [Main Panel 100%]
 *   - Editor open, edit pane visible: [Main Panel 50%] | [Edit 25% | Preview 25%]
 *   - Editor open, edit pane hidden:  [Main Panel 50%] | [Preview 50%]
 *
 * @category surfaces
 * @usage Routed at '/workflow?tab=mission-control'
 */
import { computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import MissionControlPanel from './panels/MissionControlPanel.vue'
import MissionsPanel from './panels/MissionsPanel.vue'
import BinderPanel from './panels/BinderPanel.vue'
import TasksPanel from './panels/TasksPanel.vue'
import PublishPanel from './panels/PublishPanel.vue'
import { EditorPanel } from '../../skills'
import UIcon from '../../skills/atoms/UIcon.vue'
import UButton from '../../skills/atoms/UButton.vue'

const wf = useWorkflowStore()

function onEditorContentUpdate(value: string) {
  if (wf.selectedTask) {
    wf.selectedTask.description = value
  }
}

function onEditorSave(value: string) {
  if (wf.selectedTask) {
    wf.selectedTask.description = value
    console.log('[Workflow] Task saved:', wf.selectedTask.id, wf.selectedTask.title)
  }
}

/**
 * Dynamic column class based on edit pane visibility:
 *   - Edit pane open: wider column (50% for both panes stacked vertically)
 *   - Edit pane hidden: narrower column (50% — preview fills it)
 */
const editorColumnClass = computed(() => {
  return wf.showEditorPane ? 'workflow-editor--wide' : 'workflow-editor--single'
})
</script>

<style scoped>
/* ─── Layout ──────────────────────────────────────────────────────── */
.workflow-layout {
  display: flex;
  flex-direction: row;
  height: 100%;
  gap: 0;
}

/* ─── Main Panel — fill full height ──────────────────────────── */
.workflow-panel {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.workflow-panel > * {
  flex: 1;
  min-height: 0;
}

/* When editor is open, main panel gets less space */
.workflow-panel--narrow {
  /* flex: 1 still applies — the editor column takes the rest */
}

/* ─── Editor Column — right sidebar, full height ──────────────── */
.workflow-editor {
  flex-shrink: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-background);
}

/* Single pane: 50-50 split with main panel */
.workflow-editor--single {
  width: 50%;
  min-width: 360px;
}

/* Both panes: 50-50 even split with main panel */
.workflow-editor--wide {
  width: 55%;
  min-width: 480px;
}

/* ─── Empty editor state ──────────────────────────────────────────── */
.wf-editor-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-2xl);
  color: var(--usx-color-on-surface-muted);
  text-align: center;
}
</style>
