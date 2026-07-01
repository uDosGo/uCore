<template>
  <div class="markdown-preview">
    <MdPreview
      :id="previewId"
      :model-value="content"
      :theme="markdown.theme"
      :language="markdown.language"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * @component MarkdownPreview
 * @description Read-only markdown renderer Skill wrapping md-editor-v3's MdPreview.
 * Used for displaying rendered markdown content without editing capabilities.
 * @category skills/molecules
 * @props {string} content - Markdown content to render
 * @props {string} previewId - Unique ID for the preview container
 * @usage
 *   <MarkdownPreview :content="doc.content" preview-id="doc-viewer" />
 */
import { withDefaults } from 'vue'
import { MdPreview } from '@vendor/md-editor'
import '@vendor/md-editor-preview'
import { useMarkdownStore } from '../../../stores/markdown'

interface Props {
  content?: string
  previewId?: string
}

withDefaults(defineProps<Props>(), {
  content: '',
  previewId: 'markdown-preview',
})

const markdown = useMarkdownStore()
</script>

<style scoped>
.markdown-preview {
  width: 100%;
  padding: var(--usx-spacing-md);
  overflow-y: auto;
}

:deep(.md-editor-preview) {
  line-height: 1.7;
}
</style>
