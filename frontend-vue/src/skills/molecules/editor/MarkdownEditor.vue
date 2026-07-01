<template>
  <div class="markdown-editor" :class="{ 'markdown-editor--fullscreen': fullscreen }">
    <MdEditor
      v-model="content"
      :theme="markdown.theme"
      :language="markdown.language"
      :toolbars="toolbars"
      :preview="preview"
      :html-preview="htmlPreview"
      :no-upload-img="noUpload"
      :on-change="handleChange"
      :on-save="handleSave"
      :on-upload-img="handleUploadImg"
      :on-fullscreen="handleFullscreen"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * @component MarkdownEditor
 * @description Full-featured markdown editor Skill wrapping vendored md-editor-v3.
 * Supports: toolbar customization, mermaid diagrams, katex math, image upload,
 * prettier formatting, fullscreen mode, dark/light themes.
 * @category skills/molecules
 * @props {string} modelValue - v-model markdown content
 * @props {string[]} toolbars - Custom toolbar configuration
 * @props {boolean} preview - Show live preview
 * @props {boolean} htmlPreview - Enable HTML preview
 * @props {boolean} noUpload - Disable image upload
 * @props {boolean} autofocus - Auto-focus on mount
 * @emits {string} update:modelValue - v-model update
 * @emits {string} save - Ctrl+S save event
 * @emits {string} change - Content changed
 * @usage
 *   <MarkdownEditor
 *     v-model="doc.content"
 *     :toolbars="['bold', 'italic', '|', 'preview']"
 *     @save="handleSave"
 *   />
 */
import { ref, watch, withDefaults } from 'vue'
import { MdEditor } from '@vendor/md-editor'
import '@vendor/md-editor-style'
import { useMarkdownStore } from '../../../stores/markdown'

interface Props {
  modelValue?: string
  toolbars?: string[]
  preview?: boolean
  htmlPreview?: boolean
  noUpload?: boolean
  autofocus?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  toolbars: undefined,
  preview: true,
  htmlPreview: false,
  noUpload: false,
  autofocus: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  save: [value: string]
  change: [value: string]
}>()

const markdown = useMarkdownStore()
const content = ref(props.modelValue)
const fullscreen = ref(false)

// Use custom toolbars or fall back to store defaults
const toolbars = props.toolbars ?? markdown.defaultToolbars

// Sync v-model
watch(() => props.modelValue, (val) => {
  content.value = val
})

function handleChange(value: string) {
  content.value = value
  emit('update:modelValue', value)
  emit('change', value)
}

function handleSave(value: string) {
  emit('save', value)
}

function handleFullscreen(status: boolean) {
  fullscreen.value = status
  markdown.setFullscreen(status)
}

function handleUploadImg(files: File[], callback: (urls: string[]) => void) {
  // TODO: Wire to uCore backend upload endpoint
  // For now, create local object URLs
  const urls = files.map((file: File) => URL.createObjectURL(file))
  callback(urls)
}
</script>

<style scoped>
.markdown-editor {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.markdown-editor--fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: var(--pico-background-color);
}

/* Ensure md-editor-v3 fills container */
:deep(.md-editor) {
  height: 100%;
}
</style>
