<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="wf.activeTab"
      :tabs="WORKFLOW_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <!-- Content area -->
    <div class="surface__content">
      <div class="workflow-layout" :class="{ 'workflow-layout--editor-tab': wf.activeTab === 'editor' }">
        <!-- Left/Main panel: the active tab content -->
        <div v-if="wf.activeTab !== 'editor'" class="workflow-panel">
          <MissionControlPanel v-if="wf.activeTab === 'mission-control'" />
          <BinderPanel v-else-if="wf.activeTab === 'binder'" />
          <TasksPanel v-else-if="wf.activeTab === 'tasks'" />
          <PublishPanel v-else-if="wf.activeTab === 'publish'" />
        </div>

        <!-- Editor tab: full-width document workspace -->
        <div v-if="wf.activeTab === 'editor'" class="workflow-panel workflow-panel--editor">
          <EditorPanel
            v-if="activeEditorItem"
            :content="editorContent"
            :title="editorTitle"
            :read-only="editorReadOnly"
            :show-editor="wf.showEditorPane"
            :pane-layout="wf.paneLayout"
            @update:content="onEditorContentUpdate"
            @save="onEditorSave"
            @close="wf.closeEditor()"
            @toggle-editor="wf.toggleEditorPane()"
            @toggle-layout="wf.togglePaneLayout()"
          />
          <div v-else class="wf-editor-empty">
            <UIcon name="article" />
            <p>Select a file from the User Vault sidebar or a task from Tasks.</p>
            <div class="wf-editor-empty__actions">
              <UButton size="sm" variant="primary" @click="shell.toggleSidebar()">
                Open File Browser
              </UButton>
              <UButton size="sm" variant="secondary" @click="wf.setTab('tasks')">
                Go to Tasks
              </UButton>
            </div>
          </div>
        </div>

        <!-- Right/Editor column: sidecar for non-editor tabs -->
        <div v-if="wf.activeTab !== 'editor' && wf.editorOpen && activeEditorItem" class="workflow-editor" :class="editorColumnClass">
          <EditorPanel
            :content="editorContent"
            :title="editorTitle"
            :read-only="editorReadOnly"
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
 *   - Preview only: [Main Panel 2/3] | [Preview 1/3]
 *   - Both panes:  [Main Panel 1/3] | [Edit 1/3 | Preview 1/3]
 *
 * @category surfaces
 * @usage Routed at '/workflow?tab=mission-control'
 */
import { computed, defineAsyncComponent, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useShellStore } from '../../stores/shell'
import { useWorkflowStore, WORKFLOW_TABS } from '../../stores/workflow'
import type { WorkflowTab } from '../../stores/workflow'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'
import MissionControlPanel from './panels/MissionControlPanel.vue'
const MissionsPanel = defineAsyncComponent(() => import('./panels/MissionsPanel.vue'))
const BinderPanel = defineAsyncComponent(() => import('./panels/BinderPanel.vue'))
const TasksPanel = defineAsyncComponent(() => import('./panels/TasksPanel.vue'))
const PublishPanel = defineAsyncComponent(() => import('./panels/PublishPanel.vue'))
import { EditorPanel } from '../../skills'
import UIcon from '../../skills/atoms/UIcon.vue'
import UButton from '../../skills/atoms/UButton.vue'

const shell = useShellStore()
const wf = useWorkflowStore()
const route = useRoute()
const router = useRouter()

const VALID_WORKFLOW_TABS = new Set(WORKFLOW_TABS.map(t => t.id))

function asWorkflowTab(tab: string): WorkflowTab | null {
  return VALID_WORKFLOW_TABS.has(tab as WorkflowTab) ? (tab as WorkflowTab) : null
}

onMounted(() => {
  const routeTab = String(route.query.tab || '').trim()
  const safeTab = asWorkflowTab(routeTab)
  if (safeTab) {
    wf.setTab(safeTab)
    return
  }
  router.replace({
    path: '/workflow',
    query: { ...route.query, tab: wf.activeTab },
  })
})

watch(
  () => route.query.tab,
  (value) => {
    const routeTab = String(value || '').trim()
    const safeTab = asWorkflowTab(routeTab)
    if (!safeTab) return
    if (wf.activeTab !== routeTab) {
      wf.setTab(safeTab)
    }
  },
)

watch(
  () => wf.activeTab,
  (tab) => {
    const current = String(route.query.tab || '')
    if (current === tab) return
    router.replace({
      path: '/workflow',
      query: { ...route.query, tab },
    })
  },
)

function onEditorContentUpdate(value: string) {
  wf.updateEditorContent(value)
}

function onEditorSave(value: string) {
  wf.updateEditorContent(value)
  const itemId = wf.selectedTask?.id || wf.selectedFile?.path
  console.log('[Workflow] Editor saved:', itemId)
}

const activeEditorItem = computed(() => wf.selectedTask || wf.selectedFile)
const editorTitle = computed(() => (
  wf.selectedTask?.title || wf.selectedFile?.filename || 'Untitled'
))
const editorContent = computed(() => (
  wf.selectedTask?.description || wf.selectedFile?.content || ''
))
const editorReadOnly = computed(() => Boolean(wf.selectedFile?.readOnly))

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
  gap: var(--usx-spacing-md);
}

.workflow-layout--editor-tab {
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

.workflow-panel--editor {
  overflow: hidden;
  background: var(--usx-color-background);
}

/* ─── Editor Column — right sidebar, full height ──────────────── */
.workflow-editor {
  flex-shrink: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--usx-color-background);
}

/* Preview only: editor takes 1/3, main panel takes 2/3 */
.workflow-editor--single {
  width: 33.33%;
  min-width: 22ch;
}

/* Both edit + preview: editor takes 2/3, main panel takes 1/3,
   then edit/preview split evenly inside = 1/3 each of full width */
.workflow-editor--wide {
  width: 66.66%;
  min-width: 32ch;
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

.wf-editor-empty__actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}
</style>
