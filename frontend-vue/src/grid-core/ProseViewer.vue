<template>
  <div class="prose-viewer" :style="{ maxWidth: proseMaxWidth }">
    <div class="prose-viewer__content" v-html="html"></div>
  </div>
</template>

<script setup lang="ts">
/**
 * ProseViewer — Standard Prose Reading View
 *
 * Renders markdown as a traditional scrolling document using
 * responsive column widths via the Grid Algebra.
 * Slide separators (---) are automatically stripped.
 *
 * The column width auto-resolves based on viewport width:
 *   <480px:  1×40ch  480px: 2×35ch  768px: 2×40ch
 *   1024px: 3×35ch  1440px: 3×40ch  1920px+: 4×40ch
 *
 * Usage:
 *   <ProseViewer :source="markdownString" />
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { renderMarkdown } from '../composables/useMarkdown'
import { resolveColumns } from './algebra'
import type { ColumnSpec } from './types'

const props = defineProps<{
  source: string
}>()

const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)
const spec = ref<ColumnSpec>(resolveColumns(viewportWidth.value))

const html = computed(() => renderMarkdown(props.source))

const proseMaxWidth = computed(() => {
  const s = spec.value
  return s.count === 1 ? s.width : s.maxWidth
})

function onResize() {
  viewportWidth.value = window.innerWidth
  spec.value = resolveColumns(viewportWidth.value)
}

onMounted(() => {
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.prose-viewer {
  margin: 0 auto;
  padding: var(--gridcore-viewer-padding);
  line-height: var(--gridcore-line-height-prose);
  color: var(--gridcore-color-text);
  width: 100%;
}

.prose-viewer__content {
  width: 100%;
}

.prose-viewer__content :deep(h1),
.prose-viewer__content :deep(h2),
.prose-viewer__content :deep(h3),
.prose-viewer__content :deep(h4) {
  margin-top: var(--gridcore-viewer-heading-margin-top);
  margin-bottom: var(--gridcore-viewer-margin-sm);
  font-weight: var(--gridcore-font-weight-semibold);
  line-height: var(--gridcore-line-height-tight);
}

.prose-viewer__content :deep(h1) { font-size: 2em; }
.prose-viewer__content :deep(h2) { font-size: 1.5em; }
.prose-viewer__content :deep(h3) { font-size: 1.25em; }
.prose-viewer__content :deep(h4) { font-size: 1.1em; }

.prose-viewer__content :deep(p) {
  margin-bottom: var(--gridcore-viewer-margin-lg);
}

.prose-viewer__content :deep(a) {
  color: var(--gridcore-color-primary);
  text-decoration: none;
}

.prose-viewer__content :deep(a:hover) {
  text-decoration: underline;
}

.prose-viewer__content :deep(code) {
  background: var(--gridcore-color-surface-muted);
  padding: var(--gridcore-marker-pad-x) calc(var(--gridcore-marker-pad-x) * 2);
  border-radius: var(--gridcore-control-radius);
  font-size: var(--gridcore-font-size-body);
}

.prose-viewer__content :deep(pre) {
  background: var(--gridcore-color-surface-muted);
  padding: var(--gridcore-space-lg);
  border-radius: var(--gridcore-radius-md);
  overflow-x: auto;
  margin-bottom: var(--gridcore-viewer-margin-lg);
}

.prose-viewer__content :deep(pre code) {
  background: none;
  padding: 0;
}

.prose-viewer__content :deep(blockquote) {
  border-left: calc(var(--gridcore-viewer-blockquote-width) + var(--gridcore-border-width)) solid var(--gridcore-color-primary);
  padding-left: var(--gridcore-space-lg);
  margin-left: 0;
  color: var(--gridcore-color-text-muted);
}

.prose-viewer__content :deep(ul),
.prose-viewer__content :deep(ol) {
  padding-left: 1.5em;
  margin-bottom: 1em;
}

.prose-viewer__content :deep(li) {
  margin-bottom: 0.25em;
}

.prose-viewer__content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: var(--gridcore-viewer-margin-lg);
}

.prose-viewer__content :deep(th),
.prose-viewer__content :deep(td) {
  padding: var(--gridcore-viewer-margin-sm) var(--gridcore-viewer-margin-md);
  border: var(--gridcore-border);
  text-align: left;
}

.prose-viewer__content :deep(th) {
  background: var(--gridcore-color-surface);
  font-weight: var(--gridcore-font-weight-semibold);
}

.prose-viewer__content :deep(hr) {
  border: none;
  border-top: var(--gridcore-border);
  margin: 2em 0;
}
</style>
