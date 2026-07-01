<template>
  <div class="editor-panel">
    <!-- Single shared toolbar -->
    <div class="editor-panel__toolbar">
      <div class="editor-panel__toolbar-left">
        <UIcon name="article" />
        <span class="editor-panel__title">{{ title || 'Untitled' }}</span>
      </div>
      <div class="editor-panel__toolbar-right">
        <UButton
          size="sm"
          variant="ghost"
          icon="edit"
          :title="showEditor ? 'Hide edit pane' : 'Show edit pane'"
          :class="{ 'editor-panel__toggle--active': showEditor }"
          @click="emit('toggle-editor')"
        />
        <UButton
          v-if="showEditor"
          size="sm"
          variant="ghost"
          :icon="paneLayout === 'split' ? 'view_column' : 'view_day'"
          :title="paneLayout === 'split' ? 'Switch to stacked layout' : 'Switch to side-by-side layout'"
          @click="emit('toggle-layout')"
        />
        <UButton
          v-if="!readOnly"
          size="sm"
          variant="primary"
          icon="save"
          @click="handleSave"
        >
          Save
        </UButton>
        <UButton
          size="sm"
          variant="ghost"
          icon="close"
          title="Close editor"
          @click="emit('close')"
        />
      </div>
    </div>

    <!-- Panes: side-by-side (split) when editing, stacked when layout toggled -->
    <div
      class="editor-panel__panes"
      :class="{
        'editor-panel__panes--split': showEditor && paneLayout === 'split',
        'editor-panel__panes--stacked': showEditor && paneLayout === 'stacked',
      }"
    >
      <!-- Preview Pane — always visible, the default view -->
      <div class="editor-panel__preview-pane">
        <div class="editor-panel__pane-header">
          <UIcon name="visibility" />
          <span>Preview</span>
        </div>
        <div class="editor-panel__pane-body">
          <MarkdownPreview
            :content="localContent"
            :preview-id="`editor-panel-preview-${instanceId}`"
          />
        </div>
      </div>

      <!-- Editing Pane — appears side-by-side when pencil is toggled -->
      <div v-if="showEditor" class="editor-panel__edit-pane">
        <div class="editor-panel__pane-header">
          <UIcon name="edit" />
          <span>Edit</span>
        </div>
        <div class="editor-panel__pane-body">
          <MarkdownEditor
            v-model="localContent"
            :preview="false"
            :toolbars="editorToolbars"
            @save="handleSave"
            @change="onContentChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component EditorPanel
 * @description Reusable markdown editor organism with shared toolbar.
 *   - Default: Preview pane only (single pane, prose output).
 *   - Pencil toggle: Edit pane slides in alongside Preview (side by side).
 * Single shared toolbar across both panes.
 * @category skills/organisms
 * @props {string} content - Markdown content (v-model)
 * @props {string} title - Display title
 * @props {boolean} readOnly - Disable edits
 * @props {boolean} showEditor - Edit pane visible (default: false)
 * @props {'split' | 'stacked'} paneLayout - Layout direction when both panes visible
 * @emits {string} update:content - v-model update
 * @emits {void} save - Save requested
 * @emits {void} close - Close entire editor
 * @emits {void} toggle-editor - Toggle edit pane
 * @emits {void} toggle-layout - Toggle pane layout (split ↔ stacked)
 */
import { ref, watch, withDefaults } from 'vue'
import UIcon from '../atoms/UIcon.vue'
import UButton from '../atoms/UButton.vue'
import MarkdownEditor from '../molecules/editor/MarkdownEditor.vue'
import MarkdownPreview from '../molecules/editor/MarkdownPreview.vue'

// ─── Props ───────────────────────────────────────────────────────────
interface Props {
  content?: string
  title?: string
  readOnly?: boolean
  showEditor?: boolean
  paneLayout?: 'split' | 'stacked'
}

const props = withDefaults(defineProps<Props>(), {
  content: '',
  title: 'Untitled',
  readOnly: false,
  showEditor: false,
  paneLayout: 'split',
})

const emit = defineEmits<{
  'update:content': [value: string]
  save: [value: string]
  close: []
  'toggle-editor': []
  'toggle-layout': []
}>()

// ─── State ───────────────────────────────────────────────────────────
const localContent = ref(props.content)
const instanceId = Math.random().toString(36).slice(2, 8)

// ─── Toolbar config for the CodeMirror editor ────────────────────────
const editorToolbars = [
  'bold', 'underline', 'italic', 'strikeThrough', '-',
  'title', 'sub', 'sup', 'quote', 'unorderedList', 'orderedList', 'task', '-',
  'codeRow', 'code', 'link', 'image', 'table', 'mermaid', 'katex', '-',
  'revoke', 'next', 'save', '=', 'prettier', 'pageFullscreen', 'fullscreen', 'catalog', 'github',
]

// ─── Sync props ──────────────────────────────────────────────────────
watch(() => props.content, (val) => {
  localContent.value = val
})

// ─── Handlers ────────────────────────────────────────────────────────
function onContentChange(value: string) {
  localContent.value = value
  emit('update:content', value)
}

function handleSave() {
  emit('save', localContent.value)
}
</script>

<style scoped>
.editor-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

/* ─── Shared Toolbar ──────────────────────────────────────────────── */
.editor-panel__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
  min-height: var(--usx-touch-min-sm, 40px);
}

.editor-panel__toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.editor-panel__title {
  font-size: var(--usx-font-size-sm);
  font-weight: 600;
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.editor-panel__toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.editor-panel__toggle--active {
  color: var(--usx-color-primary);
  background: var(--usx-color-primary-disabled);
}

/* ─── Panes container — horizontal row by default ──────────────── */
.editor-panel__panes {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Side-by-side (default): left = preview, right = edit */
.editor-panel__panes--split {
  flex-direction: row;
}

/* Stacked: top = edit, bottom = preview */
.editor-panel__panes--stacked {
  flex-direction: column;
}

/* ─── Preview Pane — always visible, takes full width when alone ── */
.editor-panel__preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* ─── Edit Pane — appears alongside/above preview when toggled ──── */
.editor-panel__edit-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.editor-panel__panes--split .editor-panel__edit-pane {
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  min-width: 0;
}

.editor-panel__panes--stacked .editor-panel__edit-pane {
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

/* ─── Pane header ────────────────────────────────────────────────── */
.editor-panel__pane-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: 500;
  color: var(--usx-color-on-surface-muted);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
}

.editor-panel__pane-header span {
  flex: 1;
}

/* ─── Pane body ──────────────────────────────────────────────────── */
.editor-panel__pane-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>