<template>
  <div class="editor-panel">
    <!-- Unified toolbar — full-size icons, pane indicators inline -->
    <div class="editor-panel__toolbar">
      <div class="editor-panel__toolbar-left">
        <UIcon name="article" />
        <span class="editor-panel__title">{{ title || 'Untitled' }}</span>
      </div>
      <div class="editor-panel__toolbar-center">
        <span v-if="showEditor" class="editor-panel__pane-tab" :class="{ 'editor-panel__pane-tab--active': true }">
          <UIcon name="edit" />
          <span>Edit</span>
        </span>
        <span class="editor-panel__pane-tab editor-panel__pane-tab--active">
          <UIcon name="visibility" />
          <span>Preview</span>
        </span>
      </div>
      <div class="editor-panel__toolbar-right">
        <button
          class="editor-panel__nav-btn"
          :class="{ 'editor-panel__nav-btn--active': showEditor }"
          :title="showEditor ? 'Hide edit pane' : 'Show edit pane'"
          @click="emit('toggle-editor')"
        >
          <UIcon name="edit" />
        </button>
        <button
          v-if="showEditor"
          class="editor-panel__nav-btn"
          :title="paneLayout === 'split' ? 'Switch to stacked layout' : 'Switch to side-by-side layout'"
          @click="emit('toggle-layout')"
        >
          <UIcon :name="paneLayout === 'split' ? 'view_column' : 'view_day'" />
        </button>
        <button
          v-if="!readOnly"
          class="editor-panel__nav-btn editor-panel__nav-btn--save"
          @click="handleSave"
          title="Save"
        >
          <UIcon name="save" />
        </button>
        <button
          class="editor-panel__nav-btn"
          title="Close editor"
          @click="emit('close')"
        >
          <UIcon name="close" />
        </button>
      </div>
    </div>

    <!-- Panes — no individual headers, all controls are in the unified toolbar -->
    <div
      class="editor-panel__panes"
      :class="{
        'editor-panel__panes--split': showEditor && paneLayout === 'split',
        'editor-panel__panes--stacked': showEditor && paneLayout === 'stacked',
      }"
    >
      <!-- Editing Pane — appears on the left when pencil is toggled -->
      <div v-if="showEditor" class="editor-panel__edit-pane">
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

      <!-- Preview Pane — always visible, stays on the right -->
      <div class="editor-panel__preview-pane">
        <div class="editor-panel__pane-body">
          <MarkdownPreview
            :content="localContent"
            :preview-id="`editor-panel-preview-${instanceId}`"
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
  background: var(--usx-color-background);
}

/* ─── Unified Toolbar — nav-link buttons, compact height ─────────── */
.editor-panel__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
  min-height: var(--usx-touch-min-sm);
  gap: var(--usx-spacing-sm);
}

.editor-panel__toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  min-width: 0;
  font-size: 1.25em;
}

.editor-panel__title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.editor-panel__toolbar-center {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
}

.editor-panel__pane-tab {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface-muted);
  padding: var(--usx-spacing-2) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
}

.editor-panel__pane-tab--active {
  color: var(--usx-color-primary);
}

.editor-panel__toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-2);
}

/* ─── Nav-link buttons — no borders, transparent bg, hover only ── */
.editor-panel__nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  padding: 0;
  border: none;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: 1.25em;
  transition: color var(--usx-transition-fast), background var(--usx-transition-fast);
}

.editor-panel__nav-btn:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.editor-panel__nav-btn--active {
  color: var(--usx-color-primary);
  background: var(--usx-color-primary-disabled);
}

.editor-panel__nav-btn--save {
  color: var(--usx-color-primary);
}

.editor-panel__nav-btn--save:hover {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}

.editor-panel__toggle--active {
  color: var(--usx-color-primary);
  background: var(--usx-color-primary-disabled);
}

/* ─── Panes container ─────────────────────────────────────────────── */
.editor-panel__panes {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.editor-panel__panes--split {
  flex-direction: row;
}

.editor-panel__panes--stacked {
  flex-direction: column-reverse;
}

.editor-panel__preview-pane,
.editor-panel__edit-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  min-height: 0;
}

.editor-panel__panes--split .editor-panel__edit-pane {
  border-right: var(--usx-border-width) solid var(--usx-color-border);
}

.editor-panel__panes--stacked .editor-panel__edit-pane {
  border-top: var(--usx-border-width) solid var(--usx-color-border);
}

/* ─── Pane body — content fills full height, no extra padding ── */
.editor-panel__pane-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>